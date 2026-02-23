"use client";

import React, { useEffect, useState } from "react";
import { GitBranch, Plus, ArrowLeftRight, Check, X } from "lucide-react";
import { useZenStore } from "@/lib/store/zenSlice";
import { api, type BranchInfo } from "@/lib/api";
import { toast } from "sonner";

export function TimelineRibbon() {
    const { activeBranch, setActiveBranch, checkoutBranch } = useZenStore();
    const [branches, setBranches] = useState<BranchInfo[]>([]);
    const [isCreating, setIsCreating] = useState(false);
    const [newBranchName, setNewBranchName] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const loadBranches = async () => {
        try {
            const data = await api.getBranches();
            setBranches(data);
        } catch (err) {
            console.error("Failed to load branches:", err);
        }
    };

    useEffect(() => {
        loadBranches();
    }, []);

    const handleBranchSelect = async (branchId: string) => {
        setIsLoading(true);
        try {
            await checkoutBranch(branchId);
        } catch (err) {
            toast.error("Failed to checkout branch");
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateBranch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newBranchName.trim()) return;

        setIsCreating(false);
        setIsLoading(true);

        try {
            // Usually we'd branch off a specific event, but for simplicity we branch from latest
            // The backend handles appending timeline events. We'll find an event to branch from.
            const eventsData = await api.getTimelineEvents();
            const parentEvent = eventsData.length > 0 ? eventsData[eventsData.length - 1].id : "root";

            await api.createBranch({
                branch_name: newBranchName,
                parent_event_id: parentEvent,
                source_branch_id: activeBranch || "main",
            });

            await loadBranches();
            toast.success(`Created branch: ${newBranchName}`);
            await handleBranchSelect(newBranchName);
            setNewBranchName("");
        } catch (err: any) {
            toast.error(`Failed to create branch: ${err.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Make sure we always show 'main'
    const displayBranches = branches.length > 0 ? branches : [{ id: "main", head_event_id: null, event_count: 0 }];

    return (
        <div className="flex items-center w-full bg-gray-950 border-b border-gray-800/60 px-4 py-1.5 shrink-0 z-50 overflow-x-auto relative mt-12 mb-0">
            <div className="flex items-center gap-2 mr-4 text-gray-400">
                <GitBranch className="w-4 h-4" />
                <span className="text-xs font-semibold uppercase tracking-wider">Branches</span>
            </div>

            <div className="flex items-center gap-1.5 flex-1 h-8">
                {displayBranches.map((b) => (
                    <button
                        key={b.id}
                        onClick={() => handleBranchSelect(b.id)}
                        disabled={isLoading}
                        className={`px-3 py-1 rounded-full text-xs font-medium transition-colors border ${activeBranch === b.id
                            ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/30"
                            : "bg-gray-900 border-gray-800 text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                            }`}
                    >
                        {b.id}
                        {b.event_count > 0 && <span className="ml-1.5 opacity-50 text-[10px]">({b.event_count})</span>}
                    </button>
                ))}

                {isCreating ? (
                    <form onSubmit={handleCreateBranch} className="flex items-center ml-2 border border-gray-700 bg-gray-900 rounded-full pr-1 overflow-hidden h-6">
                        <input
                            type="text"
                            value={newBranchName}
                            onChange={(e) => setNewBranchName(e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-'))}
                            placeholder="branch-name"
                            className="bg-transparent text-xs text-white px-3 py-1 outline-none w-28 placeholder:text-gray-600"
                            autoFocus
                        />
                        <button type="submit" className="p-1 hover:bg-gray-800 rounded-full text-emerald-400 transition-colors">
                            <Check className="w-3 h-3" />
                        </button>
                        <button type="button" onClick={() => setIsCreating(false)} className="p-1 hover:bg-gray-800 rounded-full text-rose-400 transition-colors">
                            <X className="w-3 h-3" />
                        </button>
                    </form>
                ) : (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="ml-2 p-1.5 rounded-full text-gray-500 hover:text-indigo-400 hover:bg-indigo-500/10 transition-colors border border-dashed border-gray-700 hover:border-indigo-500/30"
                        title="Create New Branch"
                    >
                        <Plus className="w-3.5 h-3.5" />
                    </button>
                )}
            </div>

            {activeBranch !== "main" && (
                <div className="flex items-center gap-2 ml-4">
                    <button
                        onClick={async () => {
                            try {
                                const currentText = useZenStore.getState().editorContent;
                                await checkoutBranch("main");
                                // After switching to main, we overwrite main with current text
                                useZenStore.getState().saveFragment(currentText, "Merged from " + activeBranch);
                                toast.success(`Merged ${activeBranch} into main`);
                            } catch (err) {
                                toast.error("Merge failed");
                            }
                        }}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
                    >
                        <Check className="w-3.5 h-3.5" />
                        Merge to Main
                    </button>
                    <button
                        onClick={async () => {
                            try {
                                await checkoutBranch("main");
                                toast.success(`Discarded ${activeBranch}`);
                            } catch (err) {
                                toast.error("Failed to discard");
                            }
                        }}
                        className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20 hover:bg-rose-500/20 transition-colors"
                    >
                        <X className="w-3.5 h-3.5" />
                        Discard
                    </button>
                </div>
            )}
        </div>
    );
}
