"use client";

import React from "react";
import Link from "next/link";
import { ZenEditor } from "@/components/zen/ZenEditor";
import { ContextSidebar } from "@/components/zen/ContextSidebar";
import { StoryboardStrip } from "@/components/zen/StoryboardStrip";
import { InlineTranslation } from "@/components/zen/InlineTranslation";
import { LiveStoryboardSidebar } from "@/components/zen/LiveStoryboardSidebar";
import { TimelineRibbon } from "@/components/zen/TimelineRibbon";
import { useZenStore } from "@/lib/store/zenSlice";
import { ArrowLeft, Feather } from "lucide-react";

export default function ZenPage() {
    const { showTranslation, translationSource, setShowTranslation, isFocusTyping } = useZenStore();

    const handleReplace = (text: string) => {
        window.dispatchEvent(new CustomEvent("zen:replace", { detail: text }));
        setShowTranslation(false);
    };

    const handleInsertBelow = (text: string) => {
        window.dispatchEvent(new CustomEvent("zen:insertBelow", { detail: text }));
        setShowTranslation(false);
    };

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white">
            {/* Top bar */}
            <header className={`flex items-center justify-between px-4 py-2 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-sm shrink-0 transition-opacity duration-700 ${isFocusTyping ? "opacity-0 pointer-events-none" : "opacity-100"}`}>
                <div className="flex items-center gap-2">
                    <Feather className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-semibold text-gray-200">Zen Mode</span>
                </div>
            </header>

            {/* Main content area */}
            <div className="flex flex-1 overflow-hidden relative">
                <div className="flex-1 flex flex-col relative overflow-hidden">
                    <TimelineRibbon />
                    <ZenEditor />
                    {showTranslation && (
                        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 w-full max-w-2xl shadow-2xl z-40 animate-in slide-in-from-bottom-4 fade-in duration-200">
                            <InlineTranslation
                                sourceText={translationSource}
                                onReplace={handleReplace}
                                onInsertBelow={handleInsertBelow}
                                onClose={() => setShowTranslation(false)}
                            />
                        </div>
                    )}
                </div>
                <div className={`flex flex-row shrink-0 transition-opacity duration-700 ${isFocusTyping ? "opacity-0 pointer-events-none w-0" : "opacity-100"}`}>
                    <LiveStoryboardSidebar />
                    <ContextSidebar />
                </div>
            </div>

            {/* Storyboard strip */}
            <div className={`transition-opacity duration-700 ${isFocusTyping ? "opacity-0 pointer-events-none h-0" : "opacity-100"}`}>
                <StoryboardStrip />
            </div>
        </div>
    );
}
