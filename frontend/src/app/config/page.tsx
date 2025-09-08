"use client";

import React, { useEffect, useState } from "react";
import { getApiBaseUrl } from "@/lib/api";

export default function ConfigPage() {
  const [userId, setUserId] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = typeof window !== "undefined" ? localStorage.getItem("userId") : null;
    setUserId(stored || "default_user");
  }, []);

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem("userId", userId.trim() || "default_user");
      setSaved(true);
      setTimeout(() => setSaved(false), 1500);
    }
  };

  const handleReset = () => {
    setUserId("default_user");
  };

  return (
    <div className="space-y-6">
      <div className="inline-flex items-center gap-2 rounded-full bg-black/5 dark:bg-white/10 px-2.5 py-1 text-[11px] md:text-xs font-medium uppercase tracking-wide text-gray-700 dark:text-gray-200">
        <span className="h-1.5 w-1.5 rounded-full bg-gray-500/60 dark:bg-gray-300/60" />
        <span>Config</span>
      </div>

      <section className="rounded-xl border border-black/10 dark:border-white/10 p-4 md:p-5 bg-white/50 dark:bg-black/30 backdrop-blur supports-[backdrop-filter]:bg-white/30">
        <div className="space-y-4">
          <div className="text-sm text-black/70 dark:text-white/70">
            API base URL: <span className="font-mono text-xs md:text-sm">{getApiBaseUrl()}</span>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium" htmlFor="userId">User ID</label>
            <div className="flex gap-2">
              <input
                id="userId"
                className="flex-1 px-3 py-2 rounded-md border border-black/10 dark:border-white/10 bg-transparent focus:outline-none focus:ring-2 focus:ring-black/10 dark:focus:ring-white/10"
                placeholder="Enter a user id"
                value={userId}
                onChange={(e) => setUserId(e.target.value)}
              />
              <button className="px-3 py-2 rounded-full text-sm border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors" onClick={handleSave}>Save</button>
              <button className="px-3 py-2 rounded-full text-sm border border-black/10 dark:border-white/10 hover:bg-black/5 dark:hover:bg-white/10 transition-colors" onClick={handleReset}>Reset</button>
            </div>
            {saved && <div className="text-xs text-emerald-600" aria-live="polite">Saved</div>}
            <div className="text-xs text-black/60 dark:text-white/60">Used as <code className="px-1 py-0.5 rounded bg-black/5 dark:bg-white/10">X-User-Id</code> header for API requests.</div>
          </div>
        </div>
      </section>
    </div>
  );
}
