"use client";

import { cn } from "@/lib/cn";
import type { DirectorResult } from "@/lib/api";

interface DirectorControlsProps {
  acting: boolean;
  lastResult: DirectorResult | null;
  onAct: () => void;
}

export function DirectorControls({ acting, lastResult, onAct }: DirectorControlsProps) {
  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onAct}
        disabled={acting}
        className={cn(
          "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
          acting
            ? "bg-purple-900/50 cursor-not-allowed text-purple-300"
            : "bg-purple-600 hover:bg-purple-500 text-white"
        )}
      >
        {acting ? "Director Acting..." : "Director Act"}
      </button>

      {lastResult && (
        <div
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs max-w-xs truncate",
            lastResult.status === "success"
              ? "bg-green-900/30 border border-green-800 text-green-300"
              : "bg-yellow-900/30 border border-yellow-800 text-yellow-300"
          )}
        >
          {lastResult.step_executed}: {lastResult.message}
        </div>
      )}
    </div>
  );
}
