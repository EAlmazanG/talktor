"use client";

import React from "react";

export type VoicePulseProps = {
  level: number; // 0..1 from AI playback
  size?: number; // outer square size in px
  className?: string;
};

// Single big dot with soft glow and ring, driven by AI playback level.
// Slower transitions for a smoother, more elegant feel.
export default function VoicePulse({ level, size = 200, className = "" }: VoicePulseProps) {
  const clamped = Math.max(0, Math.min(1, level));
  const amp = Math.min(1, clamped * 1.6); // boost a bit to feel responsive

  const baseDot = Math.round(size * 0.68); // base diameter of the dot
  const scale = 1 + amp * 0.35;
  const glowPx = 12 + amp * 26; // outer glow
  const innerGlowPx = 6 + amp * 14; // inner glow
  const ringScale = 1 + amp * 0.45;
  const ringOpacity = 0.12 + amp * 0.38;
  const blurPx = amp * 1.2;

  return (
    <div
      className={"relative flex items-center justify-center " + className}
      style={{ width: size, height: size }}
    >
      {/* Main dot */}
      <div
        className="absolute rounded-full"
        style={{
          width: baseDot,
          height: baseDot,
          transform: `translateZ(0) scale(${scale})`,
          background:
            "radial-gradient(75% 75% at 30% 30%, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.35) 26%, rgba(16,185,129,1) 100%)",
          boxShadow: `0 0 ${glowPx}px rgba(16,185,129,0.45), inset 0 0 ${innerGlowPx}px rgba(255,255,255,0.8)`,
          filter: `blur(${blurPx}px)`,
          transition: "transform 260ms ease, box-shadow 320ms ease, filter 260ms ease",
        }}
      />

      {/* Soft ring */}
      <div
        className="absolute rounded-full border"
        style={{
          width: baseDot,
          height: baseDot,
          borderColor: "rgba(16,185,129,0.35)",
          transform: `translateZ(0) scale(${ringScale})`,
          opacity: ringOpacity,
          transition: "transform 360ms ease, opacity 360ms ease",
        }}
      />
    </div>
  );
}
