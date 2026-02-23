"use client";

import React, { useState, useEffect, useCallback } from "react";
import { GitBranch, Plus, ChevronDown, Merge, ArrowRightLeft, Check, X, Loader2 } from "lucide-react";
import { api, type BranchInfo, type BranchComparison } from "@/lib/api";
import { useZenStore } from "@/lib/store/zenSlice";
import { toast } from "sonner";

export function BranchRibbon() {
    const { activeBranch, setActiveBranch, checkoutBranch } = useZenStore();
    const [branches, setBranches] = useState<BranchInfo[]>([]);
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [isCreating, setIsCreating] = useState(false);
    const [newBranchName, setNewBranchName] = useState("");
    const [comparison, setComparison] = useState<BranchComparison | null>(null);
    const [isComparing, setIsComparing] = useState(false);
    const [compareBranch, setCompareBranch] = useState<string | null>(null);

    const fetchBranches = useCallback(async () => {
        try {
            const data = await api.getBranches();
            setBranches(data);
        } catch {
            /* silent — branches may not be populated yet */
        }
    }, []);

    useEffect(() => {
        fetchBranches();
    }, [fetchBranches]);

    const handleCreateBranch = async () => {
        if (!newBranchName.trim()) return;
        setIsCreating(true);
        try {
            await api.createBranch({
                branch_name: newBranchName.trim(),
                parent_event_id: branches.find(b => b.id === activeBranch)?.head_event_id || "",
                source_branch_id: activeBranch || "main",
            });
            toast.success(`Branch "${newBranchName}" created`);
            setNewBranchName("");
            setDropdownOpen(false);
            await fetchBranches();
            await checkoutBranch(newBranchName.trim());
        } catch (err: any) {
            toast.error(err.message || "Failed to create branch");
        } finally {
            setIsCreating(false);
        }
    };

    const handleSwitchBranch = async (branchId: string) => {
        setDropdownOpen(false);
        setComparison(null);
        setCompareBranch(null);
        await checkoutBranch(branchId);
        toast.success(`Switched to branch: ${branchId}`);
    };

    const handleCompare = async (otherBranchId: string) => {
        if (!activeBranch) return;
        setIsComparing(true);
        setCompareBranch(otherBranchId);
        try {
            const result = await api.compareBranches(activeBranch, otherBranchId);
            setComparison(result);
        } catch (err: any) {
            toast.error(err.message || "Branch comparison failed");
        } finally {
            setIsComparing(false);
        }
    };

    const otherBranches = branches.filter(b => b.id !== activeBranch);

    return (
        <div className="relative">
            {/* Ribbon Bar */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-900/80 border-b border-gray-800 text-xs">
                <GitBranch className="w-3.5 h-3.5 text-indigo-400" />

                {/* Branch selector */}
                <button
                    onClick={() => setDropdownOpen(!dropdownOpen)}
                    className="flex items-center gap-1 px-2 py-0.5 rounded bg-gray-800 hover:bg-gray-700 border border-gray-700 text-gray-200 transition-colors font-mono"
                >
                    {activeBranch || "main"}
                    <ChevronDown className="w-3 h-3 text-gray-500" />
                </button>

                {/* Quick actions */}
                <button
                    onClick={() => {
                        setNewBranchName("");
                        setDropdownOpen(true);
                    }}
                    className="p-1 hover:bg-gray-800 rounded transition-colors text-gray-500 hover:text-gray-300"
                    title="Create branch"
                >
                    <Plus className="w-3.5 h-3.5" />
                </button>

                {otherBranches.length > 0 && (
                    <button
                        onClick={() => handleCompare(otherBranches[0].id)}
                        className="flex items-center gap-1 px-2 py-0.5 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
                        title={`Compare with ${otherBranches[0].id}`}
                    >
                        <ArrowRightLeft className="w-3 h-3" />
                        <span className="hidden sm:inline">Compare</span>
                    </button>
                )}

                {/* Active branch label */}
                <span className="ml-auto text-[10px] text-gray-600 font-mono tracking-wider uppercase">
                    {branches.find(b => b.id === activeBranch)?.event_count ?? 0} events
                </span>
            </div>

            {/* Dropdown */}
            {dropdownOpen && (
                <div className="absolute left-3 top-full mt-1 z-50 w-64 bg-gray-900 border border-gray-700 rounded-lg shadow-2xl overflow-hidden animate-in slide-in-from-top-2 fade-in duration-150">
                    {/* Branch list */}
                    <div className="max-h-40 overflow-y-auto">
                        {branches.map(b => (
                            <button
                                key={b.id}
                                onClick={() => handleSwitchBranch(b.id)}
                                className={`w-full flex items-center gap-2 px-3 py-2 text-left text-xs hover:bg-gray-800 transition-colors ${b.id === activeBranch ? "text-indigo-300 bg-gray-800/50" : "text-gray-300"
                                    }`}
                            >
                                <GitBranch className="w-3 h-3 shrink-0" />
                                <span className="font-mono truncate flex-1">{b.id}</span>
                                <span className="text-gray-600 text-[10px]">{b.event_count} events</span>
                                {b.id === activeBranch && <Check className="w-3 h-3 text-indigo-400" />}
                            </button>
                        ))}
                        {branches.length === 0 && (
                            <div className="px-3 py-2 text-xs text-gray-500">No branches yet</div>
                        )}
                    </div>

                    {/* Create new branch */}
                    <div className="border-t border-gray-800 p-2">
                        <div className="flex gap-1">
                            <input
                                type="text"
                                value={newBranchName}
                                onChange={(e) => setNewBranchName(e.target.value)}
                                placeholder="new_branch_name"
                                className="flex-1 bg-gray-950 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 font-mono focus:outline-none focus:border-indigo-500"
                                onKeyDown={(e) => e.key === "Enter" && handleCreateBranch()}
                            />
                            <button
                                onClick={handleCreateBranch}
                                disabled={!newBranchName.trim() || isCreating}
                                className="px-2 py-1 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 rounded text-white text-xs transition-colors"
                            >
                                {isCreating ? <Loader2 className="w-3 h-3 animate-spin" /> : <Plus className="w-3 h-3" />}
                            </button>
                        </div>
                    </div>

                    <button
                        onClick={() => setDropdownOpen(false)}
                        className="w-full text-center py-1.5 text-[10px] text-gray-600 hover:text-gray-400 hover:bg-gray-800/50 transition-colors"
                    >
                        Close
                    </button>
                </div>
            )}

            {/* Comparison panel */}
            {comparison && compareBranch && (
                <div className="border-b border-gray-800 bg-gray-950/80 px-4 py-3 animate-in slide-in-from-top-2 fade-in duration-200">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2 text-xs">
                            <Merge className="w-3.5 h-3.5 text-purple-400" />
                            <span className="text-gray-300">
                                <span className="font-mono text-indigo-300">{activeBranch}</span>
                                {" "}vs{" "}
                                <span className="font-mono text-purple-300">{compareBranch}</span>
                            </span>
                        </div>
                        <button
                            onClick={() => { setComparison(null); setCompareBranch(null); }}
                            className="p-0.5 hover:bg-gray-800 rounded transition-colors"
                        >
                            <X className="w-3.5 h-3.5 text-gray-500" />
                        </button>
                    </div>

                    <div className="grid grid-cols-3 gap-3 text-center text-[11px]">
                        <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-2">
                            <div className="text-green-300 font-bold text-sm">{comparison.only_in_a.length}</div>
                            <div className="text-green-400/70">Only in {activeBranch}</div>
                        </div>
                        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2">
                            <div className="text-yellow-300 font-bold text-sm">{comparison.different.length}</div>
                            <div className="text-yellow-400/70">Different</div>
                        </div>
                        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-2">
                            <div className="text-purple-300 font-bold text-sm">{comparison.only_in_b.length}</div>
                            <div className="text-purple-400/70">Only in {compareBranch}</div>
                        </div>
                    </div>

                    {comparison.different.length > 0 && (
                        <div className="mt-2 space-y-1 max-h-32 overflow-y-auto">
                            {comparison.different.slice(0, 5).map((d, i) => (
                                <div key={i} className="flex items-center gap-2 text-[10px] text-gray-400 bg-gray-900/50 rounded px-2 py-1">
                                    <ArrowRightLeft className="w-2.5 h-2.5 text-yellow-500 shrink-0" />
                                    <span className="truncate">{d.container_id}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}

            {isComparing && (
                <div className="border-b border-gray-800 bg-gray-950/80 px-4 py-3 flex items-center justify-center gap-2 text-xs text-gray-500">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Comparing branches...
                </div>
            )}
        </div>
    );
}
