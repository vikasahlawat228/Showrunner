"use client";

import { useEffect, useState } from "react";
import { Cpu, Save, Plus, Trash2, Loader2 } from "lucide-react";
import { useStudioStore } from "@/lib/store";
import type { ModelConfigEntry, ProjectModelConfig } from "@/lib/api";

interface OverrideRow {
    agentId: string;
    config: ModelConfigEntry;
}

export function ModelConfigPanel() {
    const modelConfig = useStudioStore((s) => s.modelConfig);
    const availableModels = useStudioStore((s) => s.availableModels);
    const modelConfigLoading = useStudioStore((s) => s.modelConfigLoading);
    const modelConfigSaving = useStudioStore((s) => s.modelConfigSaving);
    const fetchModelConfig = useStudioStore((s) => s.fetchModelConfig);
    const fetchAvailableModels = useStudioStore((s) => s.fetchAvailableModels);
    const updateModelConfig = useStudioStore((s) => s.updateModelConfig);

    const [defaultModel, setDefaultModel] = useState("");
    const [overrides, setOverrides] = useState<OverrideRow[]>([]);
    const [dirty, setDirty] = useState(false);

    useEffect(() => {
        fetchModelConfig();
        fetchAvailableModels();
    }, [fetchModelConfig, fetchAvailableModels]);

    // Sync form state from store
    useEffect(() => {
        if (modelConfig) {
            setDefaultModel(modelConfig.default_model);
            setOverrides(
                Object.entries(modelConfig.model_overrides).map(([agentId, config]) => ({
                    agentId,
                    config: { ...config },
                }))
            );
            setDirty(false);
        }
    }, [modelConfig]);

    const handleSave = () => {
        const overridesMap: Record<string, ModelConfigEntry> = {};
        for (const row of overrides) {
            if (row.agentId.trim()) {
                overridesMap[row.agentId.trim()] = row.config;
            }
        }
        const payload: ProjectModelConfig = {
            default_model: defaultModel,
            model_overrides: overridesMap,
        };
        updateModelConfig(payload);
    };

    const addOverride = () => {
        setOverrides((prev) => [
            ...prev,
            {
                agentId: "",
                config: { model: defaultModel || "gemini/gemini-2.0-flash", temperature: 0.7, max_tokens: 2048 },
            },
        ]);
        setDirty(true);
    };

    const removeOverride = (idx: number) => {
        setOverrides((prev) => prev.filter((_, i) => i !== idx));
        setDirty(true);
    };

    const updateOverride = (idx: number, field: string, value: string | number) => {
        setOverrides((prev) =>
            prev.map((row, i) => {
                if (i !== idx) return row;
                if (field === "agentId") return { ...row, agentId: value as string };
                return { ...row, config: { ...row.config, [field]: value } };
            })
        );
        setDirty(true);
    };

    if (modelConfigLoading) {
        return (
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm p-4">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600 border-t-purple-400 animate-spin" />
                    Loading model config…
                </div>
            </div>
        );
    }

    const modelOptions = availableModels.length > 0 ? availableModels : [defaultModel].filter(Boolean);

    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-purple-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Model Config
                    </span>
                </div>
                <button
                    onClick={handleSave}
                    disabled={!dirty || modelConfigSaving}
                    className={`px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1 transition-all ${dirty && !modelConfigSaving
                            ? "bg-purple-500/20 text-purple-400 hover:bg-purple-500/30"
                            : "bg-gray-800 text-gray-600 cursor-not-allowed"
                        }`}
                >
                    {modelConfigSaving ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                    ) : (
                        <Save className="w-3 h-3" />
                    )}
                    {modelConfigSaving ? "Saving…" : "Save"}
                </button>
            </div>

            {/* Default Model */}
            <div className="p-4 space-y-3">
                <div>
                    <label className="block text-[10px] uppercase tracking-wider text-gray-500 mb-1.5">
                        Default Model
                    </label>
                    <select
                        value={defaultModel}
                        onChange={(e) => {
                            setDefaultModel(e.target.value);
                            setDirty(true);
                        }}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-purple-500/50 focus:border-purple-500/50 transition-colors appearance-none"
                    >
                        {modelOptions.map((m) => (
                            <option key={m} value={m}>
                                {m}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Agent Overrides */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <label className="text-[10px] uppercase tracking-wider text-gray-500">
                            Agent Overrides
                        </label>
                        <button
                            onClick={addOverride}
                            className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
                        >
                            <Plus className="w-3.5 h-3.5" />
                        </button>
                    </div>

                    {overrides.length === 0 ? (
                        <p className="text-xs text-gray-600 italic">
                            No per-agent overrides set.
                        </p>
                    ) : (
                        <div className="space-y-2">
                            {overrides.map((row, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center gap-2 p-2 rounded-lg bg-gray-800/40 border border-gray-800"
                                >
                                    <input
                                        value={row.agentId}
                                        onChange={(e) => updateOverride(idx, "agentId", e.target.value)}
                                        placeholder="agent_id"
                                        className="flex-1 bg-transparent text-sm text-white placeholder:text-gray-600 focus:outline-none min-w-0"
                                    />
                                    <select
                                        value={row.config.model}
                                        onChange={(e) => updateOverride(idx, "model", e.target.value)}
                                        className="bg-gray-700 border-none rounded px-2 py-1 text-xs text-gray-300 focus:outline-none appearance-none"
                                    >
                                        {modelOptions.map((m) => (
                                            <option key={m} value={m}>
                                                {m}
                                            </option>
                                        ))}
                                    </select>
                                    <button
                                        onClick={() => removeOverride(idx)}
                                        className="p-1 text-gray-600 hover:text-red-400 transition-colors"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
