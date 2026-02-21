"use client";

import React, { useEffect, useState } from "react";
import { Loader2, Zap, BrainCircuit, PenTool, LayoutTemplate, Settings2 } from "lucide-react";
import { useZenStore } from "@/lib/store/zenSlice";
import { useStoryboardStore } from "@/lib/store/storyboardSlice";

export function GlobalActivityBar() {
    const { isDetecting, isSaving, isSearching } = useZenStore();
    const { isGenerating, isLoadingPanels } = useStoryboardStore();

    const [isVisible, setIsVisible] = useState(false);
    const [activityText, setActivityText] = useState("");
    const [Icon, setIcon] = useState<React.ElementType>(BrainCircuit);

    useEffect(() => {
        if (isDetecting) {
            setActivityText("Continuity Analyst: Deep checking scene context...");
            setIcon(() => BrainCircuit);
            setIsVisible(true);
        } else if (isGenerating) {
            setActivityText("Director Agent: Generating panel layouts...");
            setIcon(() => LayoutTemplate);
            setIsVisible(true);
        } else if (isSaving) {
            setActivityText("Syncing to Knowledge Graph...");
            setIcon(() => PenTool);
            setIsVisible(true);
        } else if (isSearching) {
            setActivityText("Librarian Agent: Searching archives...");
            setIcon(() => Settings2);
            setIsVisible(true);
        } else if (isLoadingPanels) {
            setActivityText("Loading Storyboard...");
            setIcon(() => Loader2);
            setIsVisible(true);
        } else {
            // Add a small delay before hiding to prevent flickering on fast operations
            const timer = setTimeout(() => setIsVisible(false), 500);
            return () => clearTimeout(timer);
        }
    }, [isDetecting, isGenerating, isSaving, isSearching, isLoadingPanels]);

    if (!isVisible) return null;

    return (
        <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-5 fade-in duration-300">
            <div className="flex items-center gap-3 px-4 py-2.5 bg-gray-900/95 backdrop-blur-md border border-indigo-500/30 shadow-2xl shadow-indigo-500/10 rounded-full">
                <div className="relative flex items-center justify-center">
                    <Loader2 className="w-4 h-4 text-indigo-400 animate-spin absolute" />
                    <Icon className="w-3 h-3 text-indigo-300 shadow-inner" aria-hidden="true" />
                </div>
                <span className="text-xs font-medium text-indigo-100 tracking-wide pr-1">
                    {activityText}
                </span>
            </div>
        </div>
    );
}
