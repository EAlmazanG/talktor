// Audio utilities for Talktor frontend
// - Microphone capture -> PCM16 24kHz mono -> WebSocket binary frames
// - AI audio playback from PCM16 24kHz binary frames
// All code and comments must be in English

import type { RealtimeClient } from "./ws";

export type MicStreamController = {
  stop: () => void;
};

export type AiAudioPlayer = {
  feedPcm16: (bytes: ArrayBuffer) => void; // expects PCM16 mono @ 24000 Hz
  clear: () => void;
  close: () => Promise<void>;
};

function floatToPcm16(float32: Float32Array): Int16Array {
  const out = new Int16Array(float32.length);
  for (let i = 0; i < float32.length; i++) {
    const s = Math.max(-1, Math.min(1, float32[i]));
    out[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }
  return out;
}

function pcm16ToFloat(bytes: ArrayBuffer): Float32Array {
  const view = new DataView(bytes);
  const len = bytes.byteLength / 2;
  const out = new Float32Array(len);
  for (let i = 0; i < len; i++) {
    const v = view.getInt16(i * 2, true);
    out[i] = v < 0 ? v / 0x8000 : v / 0x7fff;
  }
  return out;
}

function resampleLinear(input: Float32Array, fromRate: number, toRate: number): Float32Array {
  if (fromRate === toRate) return input;
  const ratio = toRate / fromRate;
  const outLen = Math.max(1, Math.floor(input.length * ratio));
  const out = new Float32Array(outLen);
  const step = 1 / ratio;
  let pos = 0;
  for (let i = 0; i < outLen; i++) {
    const idx = Math.floor(pos);
    const frac = pos - idx;
    const s0 = input[idx] || 0;
    const s1 = input[idx + 1] || s0;
    out[i] = s0 + (s1 - s0) * frac;
    pos += step;
  }
  return out;
}

// Start microphone streaming: capture audio, downsample to 24kHz PCM16 mono, send over WebSocket as binary frames.
export async function startMicStreaming(
  client: RealtimeClient,
  opts?: { targetRate?: number; frameMs?: number; commitIntervalMs?: number }
): Promise<MicStreamController> {
  const targetRate = opts?.targetRate ?? 24000;
  const frameMs = opts?.frameMs ?? 40; // 40ms per send (~960 samples @ 24k)
  const commitIntervalMs = opts?.commitIntervalMs ?? 250;

  // Request mic
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  // Create audio graph
  const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  // Some browsers will not match requested sample rate; we adapt via resampleLinear
  const source = audioCtx.createMediaStreamSource(stream);

  // ScriptProcessorNode is deprecated but still broadly supported and simpler for streaming
  const bufferSize = 2048; // small-ish for low latency
  const processor = audioCtx.createScriptProcessor(bufferSize, 1, 1);

  // Ensure the processor runs by connecting to destination through a zero-gain node
  const silentGain = audioCtx.createGain();
  silentGain.gain.value = 0;

  source.connect(processor);
  processor.connect(silentGain);
  silentGain.connect(audioCtx.destination);

  let running = true;
  let leftover: Float32Array | null = null;

  const samplesPerChunk = Math.floor((audioCtx.sampleRate * frameMs) / 1000);

  processor.onaudioprocess = (ev) => {
    if (!running) return;
    const input = ev.inputBuffer.getChannelData(0);

    // Concatenate with leftover
    let data: Float32Array;
    if (leftover && leftover.length > 0) {
      data = new Float32Array(leftover.length + input.length);
      data.set(leftover, 0);
      data.set(input, leftover.length);
    } else {
      data = new Float32Array(input.length);
      data.set(input, 0);
    }

    // Chop into chunks of samplesPerChunk
    let offset = 0;
    while (offset + samplesPerChunk <= data.length) {
      const slice = data.subarray(offset, offset + samplesPerChunk);
      // Downsample to targetRate and convert to PCM16
      const down = resampleLinear(slice, audioCtx.sampleRate, targetRate);
      const pcm16 = floatToPcm16(down);
      // Send as binary (raw PCM16 little-endian). Use Uint8Array to satisfy TS types.
      client.sendBinary(new Uint8Array(pcm16.buffer));
      offset += samplesPerChunk;
    }

    // Keep leftover
    leftover = offset < data.length ? data.subarray(offset) : null;
  };

  const commitTimer = window.setInterval(() => {
    client.sendJson({ type: "audio_commit" });
  }, commitIntervalMs);

  const stop = () => {
    running = false;
    window.clearInterval(commitTimer);
    try { processor.disconnect(); } catch {}
    try { source.disconnect(); } catch {}
    try { silentGain.disconnect(); } catch {}
    try { stream.getTracks().forEach((t) => t.stop()); } catch {}
    try { audioCtx.close(); } catch {}
  };

  return { stop };
}

export function createAiAudioPlayer(): AiAudioPlayer {
  const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  const bufferSize = 1024;
  const node = audioCtx.createScriptProcessor(bufferSize, 1, 1);
  const gain = audioCtx.createGain();
  gain.gain.value = 1.0;
  node.connect(gain);
  gain.connect(audioCtx.destination);

  // Simple FIFO queue of Float32 samples ready for playback at audioCtx.sampleRate
  let queue: Float32Array[] = [];
  let readOffset = 0; // index within the first buffer

  node.onaudioprocess = (ev) => {
    const out = ev.outputBuffer.getChannelData(0);
    let filled = 0;
    while (filled < out.length) {
      if (queue.length === 0) {
        // underrun: output silence
        out.fill(0, filled);
        break;
      }
      const buf = queue[0];
      const remaining = buf.length - readOffset;
      const need = out.length - filled;
      const toCopy = Math.min(remaining, need);
      out.set(buf.subarray(readOffset, readOffset + toCopy), filled);
      readOffset += toCopy;
      filled += toCopy;
      if (readOffset >= buf.length) {
        queue.shift();
        readOffset = 0;
      }
    }
  };

  const feedPcm16 = (bytes: ArrayBuffer) => {
    // Convert to float and resample to audioCtx.sampleRate from 24k
    const float24k = pcm16ToFloat(bytes);
    const floatCtx = resampleLinear(float24k, 24000, audioCtx.sampleRate);
    queue.push(floatCtx);
  };

  const clear = () => {
    queue = [];
    readOffset = 0;
  };

  const close = async () => {
    try { node.disconnect(); } catch {}
    try { gain.disconnect(); } catch {}
    try { await audioCtx.close(); } catch {}
  };

  return { feedPcm16, clear, close };
}
