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
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Config</h1>

      <div className="rounded-md border p-3 space-y-3">
        <div className="text-sm text-black/70 dark:text-white/70">
          <div>API base URL: <span className="font-mono">{getApiBaseUrl()}</span></div>
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium" htmlFor="userId">User ID</label>
          <div className="flex gap-2">
            <input
              id="userId"
              className="flex-1 px-3 py-2 rounded-md border bg-transparent"
              placeholder="Enter a user id"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
            />
            <button className="px-3 py-2 rounded-md border" onClick={handleSave}>Save</button>
            <button className="px-3 py-2 rounded-md border" onClick={handleReset}>Reset</button>
          </div>
          {saved && <div className="text-xs text-emerald-600">Saved</div>}
        </div>
      </div>

      <div className="text-sm text-black/70 dark:text-white/70">
        - This user ID is sent as <code className="px-1 py-0.5 rounded bg-black/5 dark:bg-white/10">X-User-Id</code> on REST requests.
      </div>
    </div>
  );
}
