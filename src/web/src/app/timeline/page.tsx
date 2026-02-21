"use client";

import React, { useState } from "react";
import { StoryStructureTree } from "@/components/timeline/StoryStructureTree";
import { TimelineView } from "@/components/timeline/TimelineView";
import { BranchList } from "@/components/timeline/BranchList";
import { BranchComparison } from "@/components/timeline/BranchComparison";
import { api } from "@/lib/api";
import { GitBranchPlus, X, Loader2 } from "lucide-react";

export default function TimelinePage() {
    const [activeEventId, setActiveEventId] = useState<string | null>(null);
    const [isBranchModalOpen, setIsBranchModalOpen] = useState(false);
    const [branchName, setBranchName] = useState("");
    const [isCreatingBranch, setIsCreatingBranch] = useState(false);
    const [branchError, setBranchError] = useState<string | null>(null);
    const [compareBranchA, setCompareBranchA] = useState<string | null>(null);
    const [compareBranchB, setCompareBranchB] = useState<string | null>(null);

    const handleCreateBranch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!branchName.trim() || !activeEventId) return;

        try {
            setIsCreatingBranch(true);
            setBranchError(null);
            await api.createBranch({
                branch_name: branchName.trim(),
                parent_event_id: activeEventId
            });
            setIsBranchModalOpen(false);
            setBranchName("");

            // The TimelineView will automatically pick up the new branch
            // via its SSE stream or polling fallback.
        } catch (err: any) {
            setBranchError(err.message || "Failed to create branch");
        } finally {
            setIsCreatingBranch(false);
        }
    };

    return (
        <div className="flex h-screen w-full bg-slate-50 dark:bg-slate-950 overflow-hidden relative">
            {/* Split layout */}
            <div className="w-80 flex-shrink-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm z-10 flex flex-col h-full">
                <div className="flex-1 overflow-hidden">
                    <StoryStructureTree />
                </div>
                <BranchList onCompare={(a, b) => { setCompareBranchA(a); setCompareBranchB(b); }} />
            </div>

            <div className="flex-1 flex flex-col min-w-0 bg-slate-100 dark:bg-slate-950">
                {/* Header Action Bar for Right Panel */}
                <div className="flex items-center justify-between px-6 py-3 border-b border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 backdrop-blur z-20 shadow-sm relative">
                    <div className="flex flex-col">
                        <h1 className="text-base font-semibold text-slate-800 dark:text-slate-100">Event Knowledge Graph</h1>
                        <p className="text-xs text-slate-500 dark:text-slate-400">Live event-sourcing stream</p>
                    </div>

                    <button
                        onClick={() => setIsBranchModalOpen(true)}
                        disabled={!activeEventId}
                        title={!activeEventId ? "Select an event in the timeline first" : "Create new branch from selected event"}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:text-slate-500 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg shadow-sm shadow-blue-500/20 transition-all"
                    >
                        <GitBranchPlus className="w-4 h-4" />
                        Create Branch
                    </button>
                </div>

                {/* Timeline Canvas */}
                <div className="flex-1 relative overflow-hidden">
                    <TimelineView onActiveEventChange={setActiveEventId} />
                    {compareBranchA && compareBranchB && (
                        <BranchComparison
                            branchA={compareBranchA}
                            branchB={compareBranchB}
                            onClose={() => { setCompareBranchA(null); setCompareBranchB(null); }}
                        />
                    )}
                </div>
            </div>

            {/* Create Branch Modal */}
            {isBranchModalOpen && (
                <div className="absolute inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 dark:bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-sm bg-white dark:bg-slate-900 rounded-2xl shadow-2xl border border-slate-200 dark:border-slate-800 overflow-hidden animate-in fade-in zoom-in duration-200">
                        <div className="flex justify-between items-center px-5 py-4 border-b border-slate-200 dark:border-slate-800">
                            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Create New Branch</h2>
                            <button
                                onClick={() => setIsBranchModalOpen(false)}
                                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <form onSubmit={handleCreateBranch} className="p-5">
                            <div className="mb-4">
                                <label htmlFor="branchName" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1.5">
                                    Branch Name
                                </label>
                                <input
                                    id="branchName"
                                    type="text"
                                    autoFocus
                                    value={branchName}
                                    onChange={(e) => setBranchName(e.target.value)}
                                    placeholder="e.g., alt_ending_1"
                                    className="w-full px-3 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-700 rounded-lg text-sm text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                    required
                                />
                                <p className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">
                                    Branching from event: <span className="font-mono bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded text-slate-700 dark:text-slate-300">{activeEventId}</span>
                                </p>
                            </div>

                            {branchError && (
                                <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm rounded-lg border border-red-100 dark:border-red-900/30">
                                    {branchError}
                                </div>
                            )}

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsBranchModalOpen(false)}
                                    className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={!branchName.trim() || isCreatingBranch}
                                    className="flex items-center justify-center min-w-[120px] px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 dark:disabled:bg-blue-800 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
                                >
                                    {isCreatingBranch ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Branch"}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
