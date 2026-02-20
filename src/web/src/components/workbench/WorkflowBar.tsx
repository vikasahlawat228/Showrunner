"use client";

import React from "react";
import { cn } from "@/lib/cn";
import type { WorkflowResponse } from "@/lib/api";

const STEP_LABELS: Record<string, string> = {
  world_building: "World",
  character_creation: "Characters",
  story_structure: "Story",
  scene_writing: "Scenes",
  screenplay_writing: "Screenplay",
  panel_division: "Panels",
  image_prompt_generation: "Images",
};

interface WorkflowBarProps {
  workflow: WorkflowResponse;
}

export function WorkflowBar({ workflow }: WorkflowBarProps) {
  return (
    <div className="flex items-center gap-1 overflow-x-auto pb-2">
      {workflow.steps.map((step, i) => {
        const isCurrent = step.step === workflow.current_step;
        const label = STEP_LABELS[step.step] || step.label;
        return (
          <React.Fragment key={step.step}>
            {i > 0 && <div className="w-4 h-px bg-gray-700 shrink-0" />}
            <div
              className={cn(
                "px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-colors",
                isCurrent
                  ? "bg-blue-600 text-white"
                  : step.status === "completed"
                    ? "bg-green-900/50 text-green-400"
                    : "bg-gray-800 text-gray-500"
              )}
            >
              {label}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}
