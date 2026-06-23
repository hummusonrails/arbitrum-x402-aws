"use client";

import { useEffect, useState } from "react";

/**
 * Polls /api/sync (which reads the CLI's .demo-sync.json) and returns the
 * current step id. Best-effort: network errors are ignored so the companion
 * simply holds the last screen if the CLI/server hiccups.
 */
export function useSync(pollMs = 250): string {
  const [step, setStep] = useState<string>("idle");

  useEffect(() => {
    let alive = true;
    const tick = async () => {
      try {
        const res = await fetch("/api/sync", { cache: "no-store" });
        const json = await res.json();
        if (alive && typeof json.step === "string") setStep(json.step);
      } catch {
        /* keep last screen */
      }
    };
    tick();
    const id = setInterval(tick, pollMs);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, [pollMs]);

  return step;
}
