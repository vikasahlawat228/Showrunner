"use client";

import React, { useState } from "react";
import { StoryStructureTree } from "@/components/timeline/StoryStructureTree";
import { TimelineView } from "@/components/timeline/TimelineView";
import { EmotionalArcChart } from "@/components/timeline/EmotionalArcChart";
import { BranchList } from "@/components/timeline/BranchList";
import { BranchComparison } from "@/components/timeline/BranchComparison";
import { GitBranchPlus, X, Loader2, Minimize2 } from "lucide-react";
import { useZenStore } from "@/lib/store/zenSlice";
import { ZenEditor } from "@/components/zen/ZenEditor";
import { api } from "@/lib/api";

export default function TimelinePage() {
    const [activeEventId, setActiveEventId] = useState<string | null>(null);
    const [isBranchModalOpen, setIsBranchModalOpen] = useState(false);
    const [branchName, setBranchName] = useState("");
    const [isCreatingBranch, setIsCreatingBranch] = useState(false);
    const [branchError, setBranchError] = useState<string | null>(null);
    const [compareBranchA, setCompareBranchA] = useState<string | null>(null);
    const [compareBranchB, setCompareBranchB] = useState<string | null>(null);
    type ZoomLevel = "arc" | "chapter" | "scene" | "zen";
    const [zoomLevel, setZoomLevel] = useState<ZoomLevel>("scene");
    const zoomAccumulator = React.useRef(0);

    const handleWheel = (e: React.WheelEvent) => {
        // Accumulate scroll for semantic zooming
        zoomAccumulator.current += e.deltaY;

        // Zoom In (Scroll Down)
        if (e.deltaY > 0) {
            if (zoomLevel === "arc" && zoomAccumulator.current > 300) {
                setZoomLevel("chapter");
                zoomAccumulator.current = 0;
            } else if (zoomLevel === "chapter" && zoomAccumulator.current > 300) {
                setZoomLevel("scene");
                zoomAccumulator.current = 0;
            } else if (zoomLevel === "scene" && zoomAccumulator.current > 400 && activeEventId) {
                setZoomLevel("zen");
                zoomAccumulator.current = 0;
            }
        }
        // Zoom Out (Scroll Up)
        else if (e.deltaY < 0) {
            if (zoomLevel === "zen" && zoomAccumulator.current < -600) {
                setZoomLevel("scene");
                zoomAccumulator.current = 0;
            } else if (zoomLevel === "scene" && zoomAccumulator.current < -400) {
                setZoomLevel("chapter");
                zoomAccumulator.current = 0;
            } else if (zoomLevel === "chapter" && zoomAccumulator.current < -300) {
                setZoomLevel("arc");
                zoomAccumulator.current = 0;
            }
        }

        // Cap accumulator to prevent massive jumps
        if (Math.abs(zoomAccumulator.current) > 1000) {
            zoomAccumulator.current = Math.sign(zoomAccumulator.current) * 1000;
        }
    };

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
                <BranchList
                    onCompare={(a, b) => { setCompareBranchA(a); setCompareBranchB(b); }}
                    onSelectBranch={(branchId) => useZenStore.getState().setActiveBranch(branchId)}
                />
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
                <div
                    className="flex-1 relative overflow-hidden bg-slate-100 dark:bg-slate-950 perspective-1000"
                    onWheel={handleWheel}
                >
                    {/* Vignette effect during zoom */}
                    <div className={`absolute inset-0 z-50 transition-opacity duration-700 pointer-events-none zoom-vignette ${zoomLevel === "zen" ? "opacity-100" : "opacity-0"}`} />

                    {/* Level Label Overlay */}
                    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-40 px-3 py-1 bg-gray-900/60 backdrop-blur-md border border-white/10 rounded-full text-[10px] font-bold uppercase tracking-[0.2em] text-gray-400 pointer-events-none transition-all duration-300">
                        {zoomLevel === "arc" && "World Arc View"}
                        {zoomLevel === "chapter" && "Chapter Structure"}
                        {zoomLevel === "scene" && "Event Stream"}
                        {zoomLevel === "zen" && "Zen Editor"}
                    </div>

                    <div
                        className={`absolute inset-0 transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] flex flex-col ${zoomLevel === "zen" ? "scale-110 opacity-0 pointer-events-none blur-sm translate-z-[100px]" : "scale-100 opacity-100 translate-z-0"
                            } ${zoomLevel === "arc" ? "bg-slate-50 dark:bg-slate-950" : ""}`}
                    >
                        <div className={`transition-all duration-500 transform ${zoomLevel === "arc" ? "flex-1 overflow-hidden translate-z-0" : zoomLevel === "chapter" ? "opacity-30 blur-sm scale-95 pointer-events-none -translate-z-[100px]" : "hidden"}`}>
                            <div className="p-8 h-full">
                                <EmotionalArcChart />
                                <div className="mt-8 grid grid-cols-3 gap-6 opacity-60">
                                    <div className="h-40 bg-gray-800/20 rounded-xl border border-white/5" />
                                    <div className="h-40 bg-gray-800/20 rounded-xl border border-white/5" />
                                    <div className="h-40 bg-gray-800/20 rounded-xl border border-white/5" />
                                </div>
                            </div>
                        </div>

                        <div className={`transition-all duration-500 transform ${zoomLevel === "chapter" ? "flex-1 overflow-hidden translate-z-0" : (zoomLevel === "arc" || zoomLevel === "scene") ? "opacity-30 blur-sm scale-95 pointer-events-none" : "hidden"}`}>
                            <div className="max-w-2xl mx-auto py-12">
                                <StoryStructureTree />
                            </div>
                        </div>

                        <div className={`transition-all duration-500 transform ${zoomLevel === "scene" ? "flex-1 translate-z-0" : zoomLevel === "chapter" ? "opacity-30 blur-sm scale-110 pointer-events-none translate-z-[100px]" : "hidden"}`}>
                            <TimelineView
                                onActiveEventChange={setActiveEventId}
                                onZoom={(eventId) => {
                                    setActiveEventId(eventId);
                                    setZoomLevel("zen");
                                }}
                            />
                        </div>
                    </div>

                    {compareBranchA && compareBranchB && zoomLevel !== "zen" && (
                        <BranchComparison
                            branchA={compareBranchA}
                            branchB={compareBranchB}
                            onClose={() => { setCompareBranchA(null); setCompareBranchB(null); }}
                        />
                    )}

                    {/* Zen Editor Overlay */}
                    <div
                        className={`absolute inset-0 z-30 transition-all duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] bg-gray-950 flex flex-col ${zoomLevel === "zen" ? "scale-100 opacity-100 translate-z-0" : "scale-90 opacity-0 pointer-events-none -translate-z-[100px]"
                            }`}
                    >
                        <div className="flex items-center justify-between px-6 py-2 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-sm shrink-0">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-semibold text-gray-200">Focused Scene Edit</span>
                                <span className="text-xs text-gray-500 font-mono ml-2">{activeEventId}</span>
                            </div>
                            <button
                                onClick={() => setZoomLevel("scene")}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-gray-800 hover:bg-gray-700 text-gray-300 transition-colors text-xs font-medium"
                            >
                                <Minimize2 className="w-3.5 h-3.5" />
                                Zoom Out
                            </button>
                        </div>
                        <div className="flex-1 overflow-hidden">
                            <ZenEditor />
                        </div>
                    </div>
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
