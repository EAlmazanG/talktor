#!/usr/bin/env python3
"""
Interactive Voice WebSocket client for Talktor.

What it does:
- Starts (or reuses) a session via REST
- Opens WS: /api/v1/conversations/{session_id}/realtime
- Streams microphone audio as raw PCM16 (24kHz, mono) binary frames
- Sends optional commands: /commit (manual VAD commit), /end, /mute, /unmute, /help
- Prints streaming transcripts and plays back AI audio replies

Usage:
  python scripts/interactive_audio_ws_client.py --user-id YOUR_USER \
      --base-url http://127.0.0.1:8000

Notes:
- Backend must be running and OPENAI_API_KEY configured on the server side
- Your microphone and speakers should be available
- Sample rate is 24kHz to match OpenAI Realtime pcm16 format
"""
import argparse
import json
import queue
import signal
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
import websocket  # websocket-client
import audioop

try:
    import pyaudio
except ImportError as e:
    print("PyAudio is required. Install it with: pip install PyAudio")
    raise


# Audio constants to match OpenAI Realtime pcm16 (24kHz, mono)
SAMPLE_RATE = 24000
CHANNELS = 1
FORMAT = pyaudio.paInt16  # 16-bit signed PCM
BYTES_PER_SAMPLE = 2
CHUNK_FRAMES = 1024  # frames per buffer for capture and playback


def to_ws_url(base_url: str) -> str:
    parsed = urlparse(base_url)
    if parsed.scheme == "https":
        scheme = "wss"
    elif parsed.scheme == "http":
        scheme = "ws"
    else:
        scheme = "ws"
    netloc = parsed.netloc or parsed.path
    return f"{scheme}://{netloc}"


def start_conversation(base_url: str, user_id: str, session_id: Optional[str] = None) -> dict:
    url = f"{base_url}/api/v1/conversations/start"
    payload = {"user_id": user_id}
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


@dataclass
class AudioState:
    stop_event: threading.Event
    playback_muted: threading.Event
    send_mic_enabled: threading.Event


class AudioIO:
    """Manages microphone capture and speaker playback using PyAudio."""

    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.mic_stream = None
        self.spk_stream = None

        # Queues/buffers
        self.mic_queue: "queue.Queue[bytes]" = queue.Queue(maxsize=50)
        self.playback_buffer = bytearray()
        self.playback_lock = threading.Lock()

    def start(self):
        # Open microphone (input)
        self.mic_stream = self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            input=True,
            frames_per_buffer=CHUNK_FRAMES,
        )

        # Open speaker (output) with callback draining from playback_buffer
        def speaker_callback(in_data, frame_count, time_info, status):
            bytes_needed = frame_count * BYTES_PER_SAMPLE
            with self.playback_lock:
                if len(self.playback_buffer) >= bytes_needed:
                    out = bytes(self.playback_buffer[:bytes_needed])
                    del self.playback_buffer[:bytes_needed]
                else:
                    # If not enough data, pad with silence
                    out = bytes(self.playback_buffer)
                    missing = bytes_needed - len(out)
                    self.playback_buffer.clear()
                    if missing > 0:
                        out += b"\x00" * missing
            return (out, pyaudio.paContinue)

        self.spk_stream = self.pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=SAMPLE_RATE,
            output=True,
            stream_callback=speaker_callback,
            frames_per_buffer=CHUNK_FRAMES,
        )

        self.mic_stream.start_stream()
        self.spk_stream.start_stream()

    def stop(self):
        try:
            if self.mic_stream is not None:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
        except Exception:
            pass
        try:
            if self.spk_stream is not None:
                self.spk_stream.stop_stream()
                self.spk_stream.close()
        except Exception:
            pass
        try:
            self.pa.terminate()
        except Exception:
            pass

    def read_mic_chunk(self) -> Optional[bytes]:
        try:
            data = self.mic_stream.read(CHUNK_FRAMES, exception_on_overflow=False)
            return data
        except Exception:
            return None

    def append_playback(self, data: bytes):
        with self.playback_lock:
            self.playback_buffer.extend(data)


class InteractiveVoiceClient:
    def __init__(self, base_url: str, user_id: str, session_id: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.user_id = user_id
        self.session_id = session_id

        self.ws_app: Optional[websocket.WebSocketApp] = None
        self.ws_thread: Optional[threading.Thread] = None
        self.audio = AudioIO()

        # Control state
        self.state = AudioState(
            stop_event=threading.Event(),
            playback_muted=threading.Event(),
            send_mic_enabled=threading.Event(),
        )
        self.state.send_mic_enabled.set()  # default: send mic

        # Half-duplex gating to prevent echo/self-interruption
        # When TTS audio is playing, temporarily pause sending mic audio upstream.
        self._tts_active = threading.Event()
        self._tts_last_audio_ts = 0.0
        # How long (ms) to keep the mic paused after the last TTS audio frame
        self.duck_ms = 500

        # Track whether the server is currently producing a response (TTS in progress)
        self._response_in_progress = threading.Event()

        # Track how much mic audio has been sent since the last commit (to avoid empty commits)
        self._mic_bytes_since_commit = 0
        # Require at least this much audio before committing (>=100ms required by server)
        self.min_commit_ms = 150
        self._min_commit_bytes = int(SAMPLE_RATE * BYTES_PER_SAMPLE * (self.min_commit_ms / 1000.0))

        # WebSocket state
        self.ws_open_event = threading.Event()

        # Sender/reader threads
        self.mic_capture_thread: Optional[threading.Thread] = None
        self.mic_sender_thread: Optional[threading.Thread] = None
        self.input_thread: Optional[threading.Thread] = None
        self.auto_commit_thread: Optional[threading.Thread] = None

        # Auto-commit state
        self._has_uncommitted_audio = False
        self._last_audio_send_ts = 0.0
        self._last_commit_ts = 0.0
        # Commit after this silence (seconds)
        self.auto_commit_silence = 1.0
        # Minimum spacing between commits (seconds)
        self.auto_commit_min_interval = 0.8
        # VAD parameters (RMS threshold out of 32767)
        self.vad_threshold = 600
        # Silence duration after speech to trigger commit (ms)
        self.vad_silence_ms = 700
        # Derived: number of chunks constituting silence
        self._chunk_ms = (CHUNK_FRAMES / float(SAMPLE_RATE)) * 1000.0
        self._silence_chunks_needed = max(1, int(self.vad_silence_ms / self._chunk_ms))
        self._silence_chunks = 0
        self._currently_speaking = False

    def run(self):
        # 1) Ensure session
        if not self.session_id:
            print("[HTTP] Starting new conversation session...")
            start = start_conversation(self.base_url, self.user_id)
            self.session_id = start.get("session_id")
            if not self.session_id:
                print("[ERR] No session_id returned by start endpoint.")
                sys.exit(1)
            print(f"[HTTP] session_id: {self.session_id}")
        else:
            print(f"[HTTP] Reusing session_id: {self.session_id}")

        # 2) Open WS
        ws_url = to_ws_url(self.base_url)
        ws_endpoint = f"{ws_url}/api/v1/conversations/{self.session_id}/realtime"
        print(f"[WS] Connecting to: {ws_endpoint}")

        def on_open(ws):
            print("[WS] Opened. Streaming microphone audio.")
            print("Commands: /commit, /end, /mute, /unmute, /help. You can also type text to send.")
            self.ws_open_event.set()

        def on_message(ws, message):
            # Treat on_message as TEXT-only to avoid double-appending audio.
            if isinstance(message, (bytes, bytearray)):
                # Binary frames are handled in on_data()
                return

            try:
                data = json.loads(message)
            except Exception:
                # Non-JSON text; avoid dumping large content
                preview = str(message)
                if len(preview) > 200:
                    preview = preview[:200] + "…"
                print(f"[WS] << {preview}")
                return

            t = data.get("type")
            if t == "session.created":
                print("[WS] << session.created")
            elif t == "ai_transcript.delta":
                delta = data.get("delta", "")
                print(f"AI… {delta}", end="", flush=True)
            elif t == "ai_transcript.completed":
                transcript = data.get("transcript", "")
                print()  # newline after streaming
                print(f"AI> {transcript}")
            elif t == "user_transcript.completed":
                transcript = data.get("transcript", "")
                print(f"You (VAD)> {transcript}")
            elif t in {"response.output_item.added"}:
                # TTS likely started
                self._tts_active.set()
                self._response_in_progress.set()
            elif t in {"response.output_item.done", "response.done"}:
                # TTS likely finished; mark last activity to allow a short duck window
                self._tts_last_audio_ts = time.time()
                self._response_in_progress.clear()
            elif t == "function_call.handled":
                print(f"[WS] << function_call.handled: call_id={data.get('call_id')}")
            elif t == "ended":
                print(f"[WS] << ended: {data}")
                self.state.stop_event.set()
            elif t == "error":
                payload = data.get("payload") or {}
                print(f"[WS] << error: {payload}")
                # Adjust state to avoid repeated empty commits or competing with active responses
                code = payload.get("code")
                if code == "input_audio_buffer_commit_empty":
                    self._has_uncommitted_audio = False
                    self._mic_bytes_since_commit = 0
                elif code == "conversation_already_has_active_response":
                    self._response_in_progress.set()
            else:
                evt = data.get("event")
                if evt:
                    print(f"[WS] << upstream: {evt}")
                    # Mirror response state updates from upstream events
                    if evt in {"response.created", "response.output_item.added", "response.content_part.added"}:
                        self._response_in_progress.set()
                    elif evt in {"response.output_item.done", "response.audio.done", "response.done"}:
                        self._response_in_progress.clear()
                else:
                    print(f"[WS] << event: {t}")

        def on_data(ws, data, data_type, cont):
            # Binary frames are AI audio in pcm16@24kHz
            if isinstance(data, (bytes, bytearray)):
                # Mark TTS as active and record last audio time
                self._tts_active.set()
                self._tts_last_audio_ts = time.time()
                # Avoid auto-committing stale or empty buffers while TTS is playing
                self._has_uncommitted_audio = False
                self._mic_bytes_since_commit = 0
                if not self.state.playback_muted.is_set():
                    self.audio.append_playback(bytes(data))
            else:
                s = str(data)
                print(f"[WS] << data: {s[:120]}")

        def on_error(ws, error):
            print(f"[WS] Error: {error}")

        def on_close(ws, status_code, msg):
            print(f"[WS] Closed: code={status_code}, msg={msg}")
            self.state.stop_event.set()
            self.ws_open_event.clear()

        self.ws_app = websocket.WebSocketApp(
            ws_endpoint,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_data=on_data,
        )

        # 3) Start audio IO
        try:
            self.audio.start()
        except Exception as e:
            print(f"[ERR] Failed to start audio IO (check 24kHz support): {e}")
            sys.exit(2)

        # 4) Start WS thread
        self.ws_thread = threading.Thread(
            target=self.ws_app.run_forever,
            kwargs={"ping_interval": 20, "ping_timeout": 10},
            daemon=True,
        )
        self.ws_thread.start()

        # 5) Mic capture + sender threads
        self.mic_capture_thread = threading.Thread(target=self._mic_capture_loop, daemon=True)
        self.mic_sender_thread = threading.Thread(target=self._mic_sender_loop, daemon=True)
        self.mic_capture_thread.start()
        self.mic_sender_thread.start()

        # 6) Input thread for commands / text
        self.input_thread = threading.Thread(target=self._input_loop, daemon=True)
        self.input_thread.start()

        # 6b) Auto-commit thread (silence-based)
        self.auto_commit_thread = threading.Thread(target=self._auto_commit_loop, daemon=True)
        self.auto_commit_thread.start()

        # 7) Wait for stop
        try:
            while not self.state.stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n[CTRL-C] Stopping…")
        finally:
            self.shutdown()

    def _mic_capture_loop(self):
        while not self.state.stop_event.is_set():
            chunk = self.audio.read_mic_chunk()
            if not chunk:
                continue
            try:
                self.audio.mic_queue.put(chunk, timeout=0.1)
            except queue.Full:
                # Drop if queue is full to avoid latency build-up
                pass

    def _mic_sender_loop(self):
        # Send mic chunks as binary frames
        while not self.state.stop_event.is_set():
            # Ensure the WS is open before trying to send
            if not self.ws_open_event.wait(timeout=0.2):
                continue
            try:
                chunk = self.audio.mic_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            if not self.state.send_mic_enabled.is_set():
                continue
            # Half-duplex gating: don't send mic while TTS is playing or just finished
            if self._tts_active.is_set():
                # Keep mic paused for a short window after the last TTS frame
                if (time.time() - self._tts_last_audio_ts) < (self.duck_ms / 1000.0):
                    continue
                else:
                    self._tts_active.clear()
            try:
                if self.ws_app:
                    # Send explicitly as binary to avoid UTF-8 validation issues
                    self.ws_app.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
                    # Mark that there is new uncommitted audio
                    self._has_uncommitted_audio = True
                    self._last_audio_send_ts = time.time()
                    # Track how many bytes have been sent since last commit
                    self._mic_bytes_since_commit += len(chunk)

                    # Simple RMS-based VAD to detect end of speech
                    try:
                        rms = audioop.rms(chunk, 2)
                    except Exception:
                        rms = 0

                    if rms >= self.vad_threshold:
                        # Speaking
                        self._currently_speaking = True
                        self._silence_chunks = 0
                    else:
                        # Silence frame
                        if self._currently_speaking:
                            self._silence_chunks += 1
                            if (
                                self._silence_chunks >= self._silence_chunks_needed
                                and self._has_uncommitted_audio
                                and (time.time() - self._last_commit_ts) >= self.auto_commit_min_interval
                                and not self._tts_active.is_set()
                                and not self._response_in_progress.is_set()
                                and self._mic_bytes_since_commit >= self._min_commit_bytes
                            ):
                                try:
                                    self.ws_app.send(json.dumps({"type": "audio_commit"}))
                                    print("[WS] >> audio_commit (vad)")
                                    self._last_commit_ts = time.time()
                                    self._has_uncommitted_audio = False
                                    self._mic_bytes_since_commit = 0
                                except Exception:
                                    pass
                                finally:
                                    # Reset state after commit
                                    self._currently_speaking = False
                                    self._silence_chunks = 0
            except Exception:
                # Ignore occasional send failures while reconnecting/closing
                pass

    def _auto_commit_loop(self):
        """Automatically send an audio_commit after a short silence.
        This triggers OpenAI to transcribe and respond without manual /commit.
        """
        while not self.state.stop_event.is_set():
            # Check every 100ms
            time.sleep(0.1)
            if not self.ws_open_event.is_set():
                continue
            # Do not auto-commit if the server is already speaking or if TTS is active/recent
            if self._response_in_progress.is_set():
                continue
            now = time.time()
            if self._tts_active.is_set() and (now - self._tts_last_audio_ts) < (self.duck_ms / 1000.0):
                continue
            if not self._has_uncommitted_audio:
                continue
            # Ensure we have enough audio to satisfy server minimums
            if self._mic_bytes_since_commit < self._min_commit_bytes:
                continue
            # Respect a minimum interval between commits
            if (now - self._last_audio_send_ts) >= self.auto_commit_silence and (now - self._last_commit_ts) >= self.auto_commit_min_interval:
                try:
                    if self.ws_app:
                        self.ws_app.send(json.dumps({"type": "audio_commit"}))
                        print("[WS] >> audio_commit (auto)")
                        self._last_commit_ts = now
                        self._has_uncommitted_audio = False
                        self._mic_bytes_since_commit = 0
                except Exception:
                    # Ignore send failures; next loop may succeed
                    pass

    def _input_loop(self):
        print("You can type commands while speaking.")
        print("- /commit: manually commit current audio buffer (optional with server VAD)")
        print("- /end: end the conversation")
        print("- /mute | /unmute: mute or unmute AI audio playback")
        print("- /help: show commands")
        print("- Any other text will be sent as a user message")
        while not self.state.stop_event.is_set():
            try:
                line = input("You> ").strip()
            except EOFError:
                line = "/end"
            if not line:
                continue
            if line in {"/help", "help"}:
                print("Commands: /commit, /end, /mute, /unmute, /help")
                continue
            if line in {"/mute", "mute"}:
                self.state.playback_muted.set()
                print("[Audio] AI playback muted")
                continue
            if line in {"/unmute", "unmute"}:
                self.state.playback_muted.clear()
                print("[Audio] AI playback unmuted")
                continue
            if line in {"/end", "end", ":q", "/quit", "quit"}:
                try:
                    if self.ws_app:
                        self.ws_app.send(json.dumps({"type": "end"}))
                except Exception:
                    pass
                self.state.stop_event.set()
                break
            if line in {"/commit", "commit"}:
                try:
                    if self.ws_app:
                        self.ws_app.send(json.dumps({"type": "audio_commit"}))
                        print("[WS] >> audio_commit")
                        self._has_uncommitted_audio = False
                        self._last_commit_ts = time.time()
                except Exception as e:
                    print(f"[WS] send error: {e}")
                continue
            # Otherwise, treat as text message
            msg = {"type": "input_text", "text": line}
            try:
                if self.ws_app:
                    self.ws_app.send(json.dumps(msg))
            except Exception as e:
                print(f"[WS] send error: {e}")
                self.state.stop_event.set()
                break

    def shutdown(self):
        # Stop threads
        self.state.stop_event.set()

        # Close WS
        try:
            if self.ws_app:
                self.ws_app.close()
        except Exception:
            pass
        if self.ws_thread and self.ws_thread.is_alive():
            try:
                self.ws_thread.join(timeout=2)
            except Exception:
                pass

        # Stop audio
        try:
            self.audio.stop()
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="Interactive Talktor WS client (voice)")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL, e.g. http://127.0.0.1:8000")
    parser.add_argument("--user-id", required=True, help="User ID for the session")
    parser.add_argument("--session-id", default=None, help="Optional session ID to reuse")

    args = parser.parse_args()

    client = InteractiveVoiceClient(args.base_url, args.user_id, args.session_id)

    # Handle Ctrl+C cleanly
    def handle_sigint(signum, frame):
        client.state.stop_event.set()
    try:
        signal.signal(signal.SIGINT, handle_sigint)
    except Exception:
        pass

    try:
        client.run()
    except requests.HTTPError as http_err:
        print(f"HTTP error: {http_err}")
        if http_err.response is not None:
            print(f"Response: {http_err.response.text}")
        sys.exit(2)
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(3)


if __name__ == "__main__":
    main()
