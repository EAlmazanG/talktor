"use client";

import React, { useEffect, useRef } from "react";
import type { AiAudioPlayer } from "@/lib/audio";
import type AudioMotionAnalyzer from "audiomotion-analyzer";

export type AiRadialVisualizerProps = {
  player: AiAudioPlayer | null;
  size?: number; // canvas size in px (width=height)
  className?: string;
  level?: number; // optional AI level 0..1 to pulse central dot
};

// Radial spectrum visualizer using AudioMotion Analyzer.
// Connects to the AI player's output node and renders a dynamic circular spectrum
// around the center, with subtle spin for a modern 3D-like feel.
export default function AiRadialVisualizer({ player, size = 220, className = "", level = 0 }: AiRadialVisualizerProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const amRef = useRef<AudioMotionAnalyzer | null>(null);

  useEffect(() => {
    let destroyed = false;
    let localAnalyzer: AudioMotionAnalyzer | null = null;

    const setup = async () => {
      if (!containerRef.current || !player) return;

      const AudioMotionAnalyzer = (await import("audiomotion-analyzer")).default;
      if (destroyed) return;

      const audioCtx = player.getAudioContext();
      const outputNode = player.getOutputNode();

      // Create analyzer bound to the same AudioContext; do not connect to speakers to avoid double playback
      localAnalyzer = new AudioMotionAnalyzer(containerRef.current, {
        audioCtx,
        connectSpeakers: false,
        // Canvas + visual settings
        width: size,
        height: size,
        overlay: true,
        showBgColor: false,
        showScaleX: false,
        showScaleY: false,
        // Radial spectrum
        radial: true,
        radius: 0.24, // inner radius (0..1)
        spinSpeed: 0.8, // subtle spin for 3D-like motion
        // Bars/graph look
        mode: 2, // 1/12th octave bands for clean rings
        roundBars: true,
        lineWidth: 1.5,
        fillAlpha: 0.8,
        gradient: "prism",
        smoothing: 0.6,
        maxFPS: 60,
        start: true,
      });

      try {
        localAnalyzer.connectInput(outputNode);
      } catch {
        // ignore if already connected
      }

      amRef.current = localAnalyzer;
    };

    void setup();

    return () => {
      destroyed = true;
      const am = amRef.current;
      if (am) {
        try {
          am.destroy();
        } catch {}
        amRef.current = null;
      }
    };
  }, [player, size]);

  return (
    <div className={"relative flex items-center justify-center " + className} style={{ width: size, height: size }}>
      <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
    </div>
  );
}
