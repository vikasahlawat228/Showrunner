"use client";

import React, { useEffect, useState } from "react";
import { api, type BranchComparison as BranchComparisonType } from "@/lib/api";
import { X, ArrowRight, Loader2, FileText, LayoutTemplate, Layers, LayoutList } from "lucide-react";
import { toast } from "sonner";

interface BranchComparisonProps {
    branchA: string;
    branchB: string;
    onClose: () => void;
}

function getTypeIcon(type: string) {
    switch (type) {
        case "season": return <LayoutTemplate className="w-3.5 h-3.5" />;
        case "arc": return <Layers className="w-3.5 h-3.5" />;
        case "chapter": return <LayoutList className="w-3.5 h-3.5" />;
        case "scene": return <FileText className="w-3.5 h-3.5" />;
        default: return <FileText className="w-3.5 h-3.5" />;
    }
}

export function BranchComparison({ branchA, branchB, onClose }: BranchComparisonProps) {
    const [data, setData] = useState<BranchComparisonType | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchParams() {
            try {
                setLoading(true);
                const result = await api.compareBranches(branchA, branchB);
                setData(result);
            } catch (err: any) {
                toast.error(err.message || "Failed to compare branches");
                onClose();
            } finally {
                setLoading(false);
            }
        }
        fetchParams();
    }, [branchA, branchB, onClose]);

    if (loading) {
        return (
            <div className="absolute inset-x-0 bottom-0 top-1/2 md:top-auto md:h-[400px] z-40 bg-slate-900 border-t border-slate-800 shadow-2xl flex flex-col justify-center items-center animate-in slide-in-from-bottom-8 duration-300 transform -translate-y-0 text-slate-400">
                <Loader2 className="w-8 h-8 animate-spin mb-4" />
                <p>Computing diff between {branchA} and {branchB}...</p>
            </div>
        );
    }

    if (!data) return null;

    return (
        <div className="absolute inset-x-0 bottom-0 top-1/2 md:top-auto md:h-[400px] z-40 bg-slate-900 border-t border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-bottom-8 duration-300">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-950">
                <div className="flex items-center gap-4">
                    <h3 className="text-sm font-semibold text-slate-200">Branch Comparison</h3>
                    <div className="flex items-center gap-2 text-xs font-mono">
                        <span className="px-2 py-0.5 rounded bg-blue-900/40 text-blue-400">{data.branch_a}</span>
                        <ArrowRight className="w-3 h-3 text-slate-500" />
                        <span className="px-2 py-0.5 rounded bg-emerald-900/40 text-emerald-400">{data.branch_b}</span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <span className="text-xs text-slate-500">{data.same_count} identical containers</span>
                    <button onClick={onClose} className="p-1 text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6 override-scrollbar">

                {/* Only in A */}
                <div className="flex flex-col">
                    <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        Only in {data.branch_a} <span className="bg-red-900/30 text-red-400 px-1.5 rounded">{data.only_in_a.length}</span>
                    </h4>
                    <div className="flex-1 overflow-y-auto space-y-2 override-scrollbar p-1">
                        {data.only_in_a.map(item => (
                            <div key={item.container_id} className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-300">
                                <div className="flex items-center gap-2 mb-1.5 text-slate-400">
                                    {getTypeIcon((item.state.container_type as string) || "scene")}
                                    <span className="text-xs font-medium uppercase tracking-wider">{item.state.container_type as string}</span>
                                </div>
                                <div className="font-medium text-slate-200">{item.state.name as string}</div>
                            </div>
                        ))}
                        {data.only_in_a.length === 0 && <p className="text-xs text-slate-600 italic px-1">No exclusive containers</p>}
                    </div>
                </div>

                {/* Only in B */}
                <div className="flex flex-col">
                    <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        Only in {data.branch_b} <span className="bg-emerald-900/30 text-emerald-400 px-1.5 rounded">{data.only_in_b.length}</span>
                    </h4>
                    <div className="flex-1 overflow-y-auto space-y-2 override-scrollbar p-1">
                        {data.only_in_b.map(item => (
                            <div key={item.container_id} className="p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg text-sm text-slate-300">
                                <div className="flex items-center gap-2 mb-1.5 text-slate-400">
                                    {getTypeIcon((item.state.container_type as string) || "scene")}
                                    <span className="text-xs font-medium uppercase tracking-wider">{item.state.container_type as string}</span>
                                </div>
                                <div className="font-medium text-slate-200">{item.state.name as string}</div>
                            </div>
                        ))}
                        {data.only_in_b.length === 0 && <p className="text-xs text-slate-600 italic px-1">No exclusive containers</p>}
                    </div>
                </div>

                {/* Different */}
                <div className="flex flex-col">
                    <h4 className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                        Modified <span className="bg-amber-900/30 text-amber-400 px-1.5 rounded">{data.different.length}</span>
                    </h4>
                    <div className="flex-1 overflow-y-auto space-y-3 override-scrollbar p-1">
                        {data.different.map(item => {
                            // Simple diff view
                            const keysA = Object.keys(item.state_a);
                            const keysB = Object.keys(item.state_b);
                            const allKeys = Array.from(new Set([...keysA, ...keysB]));
                            const diffs = allKeys.filter(k => JSON.stringify(item.state_a[k]) !== JSON.stringify(item.state_b[k]));

                            return (
                                <div key={item.container_id} className="p-3 bg-slate-800 border border-slate-700 rounded-lg text-sm">
                                    <div className="flex items-center gap-2 mb-2 text-slate-300">
                                        {getTypeIcon((item.state_a.container_type as string) || "scene")}
                                        <span className="font-semibold text-slate-200">{item.state_a.name as string || item.state_b.name as string}</span>
                                    </div>
                                    <div className="space-y-1.5">
                                        {diffs.map(k => (
                                            <div key={k} className="text-xs bg-slate-900/50 rounded p-1.5 font-mono overflow-auto">
                                                <div className="text-slate-500 mb-0.5">{k}:</div>
                                                <div className="flex items-start gap-1 flex-wrap">
                                                    <span className="text-red-400 line-through bg-red-900/20 px-1 rounded max-w-[45%] break-words inline-block">
                                                        {JSON.stringify(item.state_a[k]) || "null"}
                                                    </span>
                                                    <ArrowRight className="w-3 h-3 text-slate-600 shrink-0 mt-0.5" />
                                                    <span className="text-emerald-400 bg-emerald-900/20 px-1 rounded max-w-[45%] break-words inline-block">
                                                        {JSON.stringify(item.state_b[k]) || "null"}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                        {data.different.length === 0 && <p className="text-xs text-slate-600 italic px-1">No modified containers</p>}
                    </div>
                </div>

            </div>
        </div>
    );
}
