"use client";

import React, { useEffect, useState, useCallback } from "react";
import { api, type BranchInfo } from "@/lib/api";
import { GitBranch, Plus, ChevronDown, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const BRANCH_COLORS = [
    'bg-blue-500',
    'bg-emerald-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-amber-500',
    'bg-cyan-500',
    'bg-rose-500',
    'bg-indigo-500',
];

interface BranchListProps {
    onCompare: (branchA: string, branchB: string) => void;
    onSelectBranch?: (branchId: string) => void;
}

export function BranchList({ onCompare, onSelectBranch }: BranchListProps) {
    const [branches, setBranches] = useState<BranchInfo[]>([]);
    const [loading, setLoading] = useState(true);
    const [activeBranch, setActiveBranch] = useState("main");

    const loadBranches = useCallback(async () => {
        try {
            setLoading(true);
            const data = await api.getBranches();
            setBranches(data);
        } catch (err: any) {
            toast.error("Failed to load branches");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadBranches();
    }, [loadBranches]);

    const handleCompare = (branchB: string) => {
        if (activeBranch === branchB) return;
        onCompare(activeBranch, branchB);
    };

    if (loading && branches.length === 0) {
        return <div className="p-4 text-xs text-slate-500">Loading branches...</div>;
    }

    return (
        <div className="flex flex-col h-1/3 min-h-[250px] bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800">
            <div className="flex items-center justify-between p-4 pb-2 border-b border-slate-200 dark:border-slate-800">
                <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider">Branches</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-2 override-scrollbar">
                {branches.map((b, i) => {
                    const colorClass = BRANCH_COLORS[i % BRANCH_COLORS.length];
                    const isActive = b.id === activeBranch;
                    return (
                        <div
                            key={b.id}
                            className={`flex items-center justify-between p-2 rounded-md mb-1 cursor-pointer transition-colors group ${isActive ? 'bg-slate-200 dark:bg-slate-800' : 'hover:bg-slate-100 dark:hover:bg-slate-800/50'}`}
                            onClick={() => {
                                setActiveBranch(b.id);
                                if (onSelectBranch) onSelectBranch(b.id);
                            }}
                        >
                            <div className="flex items-center gap-2">
                                <span className={`w-2.5 h-2.5 rounded-full ${colorClass} ${isActive ? 'ring-2 ring-offset-1 ring-slate-400 dark:ring-offset-slate-900' : ''}`} />
                                <span className={`text-sm ${isActive ? 'font-semibold text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`}>
                                    {b.id}
                                </span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-200/50 dark:bg-slate-950/50 text-slate-500 dark:text-slate-400 font-medium">
                                    {b.event_count}
                                </span>
                            </div>

                            <div className="flex items-center">
                                {isActive ? (
                                    <CheckCircle2 className="w-4 h-4 text-slate-400" />
                                ) : (
                                    <button
                                        onClick={(e) => { e.stopPropagation(); handleCompare(b.id); }}
                                        className="text-[10px] font-medium text-blue-600 hover:text-blue-700 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/30 dark:text-blue-400 dark:hover:bg-blue-900/50 px-2 py-1 rounded transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                        Compare
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
