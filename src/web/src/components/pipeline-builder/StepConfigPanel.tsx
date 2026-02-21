"use client";

import React from "react";
import { usePipelineBuilderStore } from "@/lib/store/pipelineBuilderSlice";
import { X, Settings } from "lucide-react";

export function StepConfigPanel() {
    const { nodes, selectedStepId, selectStep, updateStepConfig, updateStepLabel } =
        usePipelineBuilderStore();

    const selectedNode = nodes.find((n) => n.id === selectedStepId);

    if (!selectedNode) {
        return (
            <div className="p-4 text-gray-600 text-sm text-center mt-8">
                <Settings className="w-6 h-6 mx-auto mb-2 opacity-40" />
                <p>Select a step to configure it</p>
            </div>
        );
    }

    const { data } = selectedNode;
    const configSchema = data.configSchema || {};
    const currentConfig = data.config || {};

    return (
        <div className="flex flex-col h-full">
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <span className="text-base">{data.icon}</span>
                    Configure Step
                </h3>
                <button
                    onClick={() => selectStep(null)}
                    className="p-1 rounded text-gray-500 hover:text-gray-300"
                >
                    <X className="w-3.5 h-3.5" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
                {/* Label */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Label
                    </label>
                    <input
                        type="text"
                        value={data.label}
                        onChange={(e) => updateStepLabel(selectedNode.id, e.target.value)}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    />
                </div>

                {/* Step Type (read-only) */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Step Type
                    </label>
                    <div className="text-xs text-gray-400 font-mono bg-gray-900 border border-gray-800 rounded-md px-3 py-1.5">
                        {data.stepType}
                    </div>
                </div>

                {/* Dynamic Config Fields */}
                {Object.entries(configSchema).map(([key, schema]: [string, any]) => (
                    <div key={key}>
                        <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                            {key.replace(/_/g, " ")}
                        </label>
                        {schema.type === "boolean" ? (
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={currentConfig[key] ?? schema.default ?? false}
                                    onChange={(e) =>
                                        updateStepConfig(selectedNode.id, { [key]: e.target.checked })
                                    }
                                    className="rounded bg-gray-800 border-gray-600 text-indigo-500 focus:ring-indigo-500"
                                />
                                <span className="text-xs text-gray-400">
                                    {currentConfig[key] ? "Enabled" : "Disabled"}
                                </span>
                            </label>
                        ) : schema.type === "integer" || schema.type === "float" ? (
                            <input
                                type="number"
                                value={currentConfig[key] ?? schema.default ?? 0}
                                onChange={(e) =>
                                    updateStepConfig(selectedNode.id, {
                                        [key]: schema.type === "integer"
                                            ? parseInt(e.target.value) || 0
                                            : parseFloat(e.target.value) || 0,
                                    })
                                }
                                step={schema.type === "float" ? 0.1 : 1}
                                className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                            />
                        ) : schema.type === "json" ? (
                            <textarea
                                value={JSON.stringify(currentConfig[key] ?? schema.default ?? {}, null, 2)}
                                onChange={(e) => {
                                    try {
                                        updateStepConfig(selectedNode.id, { [key]: JSON.parse(e.target.value) });
                                    } catch {
                                        // Invalid JSON, ignore
                                    }
                                }}
                                rows={3}
                                className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-xs font-mono text-white focus:border-indigo-500 focus:outline-none resize-none"
                            />
                        ) : (
                            <input
                                type="text"
                                value={currentConfig[key] ?? schema.default ?? ""}
                                onChange={(e) =>
                                    updateStepConfig(selectedNode.id, { [key]: e.target.value })
                                }
                                placeholder={String(schema.default || "")}
                                className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                            />
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
