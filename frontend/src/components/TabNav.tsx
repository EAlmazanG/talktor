"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import React from "react";
import Image from "next/image";

const tabs = [
  { href: "/practice", label: "Practice", emoji: "🟢" },
  { href: "/learn", label: "Learn", emoji: "🔵" },
  { href: "/progress", label: "Progress", emoji: "🟣" },
  { href: "/config", label: "Config", emoji: "⚙️" },
];

export function TabNav() {
  const pathname = usePathname();

  return (
    <nav className="w-full border-b border-black/10 dark:border-white/15 bg-white/80 dark:bg-black/50 backdrop-blur supports-[backdrop-filter]:bg-white/60 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4">
        <div className="flex items-center gap-2 h-14">
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
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${
                    active
                      ? "bg-foreground text-background"
                      : "hover:bg-black/5 dark:hover:bg-white/10"
                  }`}
                >
                  <span className="mr-1" aria-hidden>
                    {t.emoji}
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
