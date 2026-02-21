"use client";

import React, { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { StepNodeData } from "@/lib/store/pipelineBuilderSlice";
import { usePipelineBuilderStore } from "@/lib/store/pipelineBuilderSlice";
import { X } from "lucide-react";

const CATEGORY_COLORS: Record<string, { bg: string; border: string; badge: string }> = {
    context: {
        bg: "bg-emerald-950",
        border: "border-emerald-600/50",
        badge: "bg-emerald-500/20 text-emerald-300",
    },
    transform: {
        bg: "bg-yellow-950",
        border: "border-yellow-600/50",
        badge: "bg-yellow-500/20 text-yellow-300",
    },
    human: {
        bg: "bg-orange-950",
        border: "border-orange-500/50",
        badge: "bg-orange-500/20 text-orange-300",
    },
    execute: {
        bg: "bg-blue-950",
        border: "border-blue-600/50",
        badge: "bg-blue-500/20 text-blue-300",
    },
};

function StepNodeComponent({ data, id, selected }: NodeProps) {
    const nodeData = data as unknown as StepNodeData;
    const selectStep = usePipelineBuilderStore((s) => s.selectStep);
    const removeStep = usePipelineBuilderStore((s) => s.removeStep);
    const colors = CATEGORY_COLORS[nodeData.category] ?? CATEGORY_COLORS.execute;

    return (
        <div
            onClick={() => selectStep(id)}
            className={`relative rounded-xl shadow-lg border-2 transition-all cursor-pointer min-w-[200px]
        ${selected ? "ring-2 ring-indigo-400/60 border-indigo-400" : colors.border}
        ${colors.bg}`}
        >
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-3 !bg-gray-400 !border-gray-600"
            />

            {/* Delete button */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    removeStep(id);
                }}
                className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-gray-800 border border-gray-600 flex items-center justify-center text-gray-400 hover:text-red-400 hover:bg-red-900/30 transition-colors z-10"
            >
                <X className="w-3 h-3" />
            </button>

            <div className="p-3">
                <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-lg">{nodeData.icon}</span>
                    <span className="text-sm font-semibold text-white truncate">
                        {nodeData.label}
                    </span>
                </div>
                <span
                    className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${colors.badge}`}
                >
                    {nodeData.category}
                </span>
            </div>

            <Handle
                type="source"
                position={Position.Right}
                className="!w-3 !h-3 !bg-gray-400 !border-gray-600"
            />
        </div>
    );
}

export const StepNode = memo(StepNodeComponent);
