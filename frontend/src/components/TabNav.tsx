"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import Image from "next/image";

// Minimal inline SVG icons (stroke-current so they inherit text color)
function IconMic() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="h-[18px] w-[18px] md:h-5 md:w-5">
      <rect x="9" y="3" width="6" height="10" rx="3"/>
      <path d="M5 10v1a7 7 0 0 0 14 0v-1"/>
      <line x1="12" y1="17" x2="12" y2="21"/>
      <line x1="8" y1="21" x2="16" y2="21"/>
    </svg>
  );
}

function IconBook() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="h-[18px] w-[18px] md:h-5 md:w-5">
      {/* Lightbulb: simple and legible at small sizes */}
      <path d="M12 5 L2 10 L12 15 L22 10 L12 5 Z"/>
      <path d="M6 12 v4 c3 2 9 2 12 0 v-4"/>
    </svg>
  );
}

function IconTrendUp() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="h-[18px] w-[18px] md:h-5 md:w-5">
      <path d="M3 17l6-6 4 4 8-8"/>
    </svg>
  );
}

function IconSliders() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className="h-[18px] w-[18px] md:h-5 md:w-5">
      <line x1="4" y1="6" x2="20" y2="6"/>
      <line x1="4" y1="12" x2="14" y2="12"/>
      <line x1="4" y1="18" x2="18" y2="18"/>
      <circle cx="16" cy="6" r="2"/>
      <circle cx="10" cy="12" r="2"/>
      <circle cx="20" cy="18" r="2"/>
    </svg>
  );
}

const tabs = [
  { href: "/practice", label: "Practice", Icon: IconMic },
  { href: "/learn", label: "Learn", Icon: IconBook },
  { href: "/progress", label: "Progress", Icon: IconTrendUp },
  { href: "/config", label: "Config", Icon: IconSliders },
];

export function TabNav() {
  const pathname = usePathname();

  return (
    <nav className="w-full border-b border-black/10 dark:border-white/15 bg-white/80 dark:bg-black/50 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4">
        <div className="flex items-center gap-2 h-16">
          <div className="flex items-center gap-2">
            <Image
              src="/assets/icons/talktor.svg"
              alt="Talktor logo"
              width={40}
              height={40}
              className="rounded-sm"
              priority
            />
            <div className="font-semibold tracking-tight">Talktor</div>
          </div>
          <div className="ml-auto flex items-center gap-1">
            {tabs.map((t) => {
              const active = pathname === t.href || pathname.startsWith(`${t.href}/`);
              return (
                <Link
                  key={t.href}
                  href={t.href}
                  className={`inline-flex items-center gap-2 px-3.5 py-2 rounded-full text-sm leading-none transition-colors ${
                    active
                      ? "bg-foreground text-background"
                      : "hover:bg-black/5 dark:hover:bg-white/10"
                  }`}
                >
                  <span className="inline-flex" aria-hidden>
                    {React.createElement(t.Icon)}
                  </span>
                  {t.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
}
