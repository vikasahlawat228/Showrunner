"use client";

import { cn } from "@/lib/cn";
import type { PipelineState } from "@/components/pipeline/usePipelineStream";

interface DirectorControlsProps {
  pipelineState: PipelineState;
  isStarting?: boolean;
  onStartPipeline: () => void;
}

export function DirectorControls({ pipelineState, isStarting, onStartPipeline }: DirectorControlsProps) {
  const isActing = isStarting || ['CONTEXT_GATHERING', 'PROMPT_ASSEMBLY', 'EXECUTING', 'PAUSED_FOR_USER'].includes(pipelineState);

  return (
    <div className="flex items-center gap-3">
      <button
        onClick={onStartPipeline}
        disabled={isActing}
        className={cn(
          "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
          isActing
            ? "bg-purple-900/50 cursor-not-allowed text-purple-300"
            : "bg-purple-600 hover:bg-purple-500 text-white"
        )}
      >
        {isStarting ? "Starting..." : isActing ? "Pipeline Running..." : "Start Director Pipeline"}
      </button>

      {pipelineState !== 'IDLE' && (
        <div
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs max-w-xs truncate",
            pipelineState === "COMPLETED"
              ? "bg-green-900/30 border border-green-800 text-green-300"
              : pipelineState === "FAILED"
                ? "bg-red-900/30 border border-red-800 text-red-300"
                : "bg-blue-900/30 border border-blue-800 text-blue-300"
          )}
        >
          Status: {pipelineState}
        </div>
      )}
    </div>
  );
}
