"use client";

import React, { useEffect } from "react";
import { usePipelineBuilderStore, type StepRegistryEntry } from "@/lib/store/pipelineBuilderSlice";

const CATEGORY_COLORS: Record<string, string> = {
    context: "border-emerald-700/40 hover:border-emerald-600",
    transform: "border-yellow-700/40 hover:border-yellow-600",
    human: "border-orange-700/40 hover:border-orange-600",
    execute: "border-blue-700/40 hover:border-blue-600",
};

const CATEGORY_LABELS: Record<string, string> = {
    context: "🟢 Context",
    transform: "🟡 Transform",
    human: "🟠 Human",
    execute: "🔵 Execute",
};

export function StepLibrary() {
    const { stepRegistry, registryLoaded, loadRegistry, addStep } =
        usePipelineBuilderStore();

    useEffect(() => {
        loadRegistry();
    }, [loadRegistry]);

    if (!registryLoaded) {
        return (
            <div className="p-4 text-gray-500 text-sm">Loading step library…</div>
        );
    }

    // Group by category
    const grouped = stepRegistry.reduce<Record<string, StepRegistryEntry[]>>(
        (acc, entry) => {
            const cat = entry.category;
            if (!acc[cat]) acc[cat] = [];
            acc[cat].push(entry);
            return acc;
        },
        {}
    );

    const categoryOrder = ["context", "transform", "human", "execute"];

    return (
        <div className="flex flex-col h-full">
            <div className="px-4 py-3 border-b border-gray-800">
                <h3 className="text-sm font-semibold text-gray-300">Step Library</h3>
                <p className="text-[10px] text-gray-600 mt-0.5">
                    Click a step to add it to the canvas
                </p>
            </div>

            <div className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
                {categoryOrder.map((cat) => {
                    const steps = grouped[cat];
                    if (!steps) return null;
                    return (
                        <div key={cat}>
                            <div className="text-[10px] uppercase font-bold text-gray-600 mb-1.5 px-1">
                                {CATEGORY_LABELS[cat] ?? cat}
                            </div>
                            <div className="space-y-1">
                                {steps.map((entry) => (
                                    <button
                                        key={entry.step_type}
                                        onClick={() =>
                                            addStep(entry.step_type, {
                                                x: 250 + Math.random() * 200,
                                                y: 100 + Math.random() * 300,
                                            })
                                        }
                                        className={`w-full text-left px-3 py-2 rounded-lg border bg-gray-900/50 transition-all cursor-pointer ${CATEGORY_COLORS[cat] ?? "border-gray-700"
                                            } hover:bg-gray-800`}
                                    >
                                        <div className="flex items-center gap-2">
                                            <span className="text-base">{entry.icon}</span>
                                            <div>
                                                <div className="text-xs font-medium text-gray-200">
                                                    {entry.label}
                                                </div>
                                                <div className="text-[10px] text-gray-500 leading-tight">
                                                    {entry.description}
                                                </div>
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
