"use client";

import React from "react";
import { usePathname } from "next/navigation";
import {
    BookOpen, Users, AlertTriangle, Target, X,
    FileText, Eye, Clock, Lightbulb, Loader2
} from "lucide-react";
import { useStoryContextStore } from "@/lib/store/storyContextSlice";
import { useZenStore } from "@/lib/store/zenSlice";

export function StoryContextSidebar() {
    const pathname = usePathname();
    const {
        isStoryContextOpen,
        setStoryContextOpen,
        currentSceneSummary,
        presentCharacters,
        previousSceneRecap,
        emotionalArcTarget,
        continuityFlags,
        writingGoals,
        isLoading,
    } = useStoryContextStore();

    const sessionWordsWritten = useZenStore((s) => s.sessionWordsWritten);

    if (!isStoryContextOpen) return null;

    // Determine context based on current route
    const getRouteContext = () => {
        if (pathname?.startsWith("/zen")) return "zen";
        if (pathname?.startsWith("/storyboard")) return "storyboard";
        if (pathname?.startsWith("/timeline")) return "timeline";
        if (pathname?.startsWith("/brainstorm")) return "brainstorm";
        if (pathname?.startsWith("/preview")) return "preview";
        return "general";
    };

    const context = getRouteContext();

    return (
        <aside className="w-72 shrink-0 bg-gray-950 border-r border-gray-800 flex flex-col overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
                <div className="flex items-center gap-2">
                    <BookOpen className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-semibold text-gray-200">Story Context</span>
                </div>
                <button
                    onClick={() => setStoryContextOpen(false)}
                    className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {isLoading && (
                    <div className="flex items-center justify-center py-8 text-gray-500">
                        <Loader2 className="w-5 h-5 animate-spin" />
                    </div>
                )}

                {/* ─── Zen Mode Context ─────────────────────────── */}
                {context === "zen" && (
                    <>
                        {/* Scene Summary */}
                        {currentSceneSummary && (
                            <ContextCard
                                icon={<FileText className="w-3.5 h-3.5" />}
                                title="Current Scene"
                                color="text-blue-400"
                            >
                                <p className="text-xs text-gray-400 leading-relaxed">
                                    {currentSceneSummary}
                                </p>
                            </ContextCard>
                        )}

                        {/* Characters Present */}
                        <ContextCard
                            icon={<Users className="w-3.5 h-3.5" />}
                            title="Characters Present"
                            color="text-violet-400"
                        >
                            {presentCharacters.length > 0 ? (
                                <div className="space-y-1.5">
                                    {presentCharacters.map((c) => (
                                        <div key={c.id} className="flex items-center justify-between">
                                            <span className="text-xs text-gray-300">{c.name}</span>
                                            <span className="text-[10px] text-gray-600 capitalize">{c.role}</span>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-xs text-gray-600 italic">No characters detected yet</p>
                            )}
                        </ContextCard>

                        {/* Previous Scene */}
                        {previousSceneRecap && (
                            <ContextCard
                                icon={<Clock className="w-3.5 h-3.5" />}
                                title="Previous Scene"
                                color="text-amber-400"
                            >
                                <p className="text-xs text-gray-400 leading-relaxed">{previousSceneRecap}</p>
                            </ContextCard>
                        )}

                        {/* Emotional Target */}
                        {emotionalArcTarget !== null && (
                            <ContextCard
                                icon={<Target className="w-3.5 h-3.5" />}
                                title="Emotional Intensity"
                                color="text-rose-400"
                            >
                                <div className="flex items-center gap-2">
                                    <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
                                        <div
                                            className="h-full bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 rounded-full transition-all"
                                            style={{ width: `${Math.min(100, emotionalArcTarget * 10)}%` }}
                                        />
                                    </div>
                                    <span className="text-xs text-gray-400 font-mono">{emotionalArcTarget}/10</span>
                                </div>
                            </ContextCard>
                        )}

                        {/* Writing Goals */}
                        <ContextCard
                            icon={<Target className="w-3.5 h-3.5" />}
                            title="Writing Goals"
                            color="text-emerald-400"
                        >
                            <div className="space-y-2">
                                <div className="flex justify-between text-xs">
                                    <span className="text-gray-400">Session words</span>
                                    <span className="text-gray-300 font-medium">{sessionWordsWritten}</span>
                                </div>
                                <div className="h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-emerald-500/50 rounded-full transition-all"
                                        style={{ width: `${Math.min(100, (sessionWordsWritten / writingGoals.targetWords) * 100)}%` }}
                                    />
                                </div>
                                <div className="text-[10px] text-gray-600 text-right">
                                    Target: {writingGoals.targetWords} words
                                </div>
                            </div>
                        </ContextCard>
                    </>
                )}

                {/* ─── Storyboard Context ───────────────────────── */}
                {context === "storyboard" && (
                    <>
                        <ContextCard
                            icon={<Eye className="w-3.5 h-3.5" />}
                            title="Visual Continuity"
                            color="text-cyan-400"
                        >
                            <p className="text-xs text-gray-400 leading-relaxed">
                                Keep character appearances consistent across panels. Check the scene ↔ panel mapping for alignment.
                            </p>
                        </ContextCard>
                        {presentCharacters.length > 0 && (
                            <ContextCard
                                icon={<Users className="w-3.5 h-3.5" />}
                                title="Characters in Scene"
                                color="text-violet-400"
                            >
                                <div className="space-y-1.5">
                                    {presentCharacters.map((c) => (
                                        <div key={c.id} className="text-xs text-gray-300">{c.name}</div>
                                    ))}
                                </div>
                            </ContextCard>
                        )}
                    </>
                )}

                {/* ─── Timeline Context ─────────────────────────── */}
                {context === "timeline" && (
                    <ContextCard
                        icon={<Clock className="w-3.5 h-3.5" />}
                        title="Structure Overview"
                        color="text-blue-400"
                    >
                        <p className="text-xs text-gray-400 leading-relaxed">
                            <strong className="text-gray-300">Emotional Intensity</strong> measures character conflict density, dialogue tension, and pacing variance per scene.
                        </p>
                        <p className="text-xs text-gray-500 mt-2">
                            Click any data point on the arc to jump to that scene in Zen Mode.
                        </p>
                    </ContextCard>
                )}

                {/* ─── Brainstorm Context ───────────────────────── */}
                {context === "brainstorm" && (
                    <ContextCard
                        icon={<Lightbulb className="w-3.5 h-3.5" />}
                        title="Idea Connections"
                        color="text-amber-400"
                    >
                        <p className="text-xs text-gray-400 leading-relaxed">
                            Select multiple cards to group them into themes, or use "Create Scene Outline" to turn ideas into structured scenes.
                        </p>
                    </ContextCard>
                )}

                {/* ─── Preview Context ──────────────────────────── */}
                {context === "preview" && (
                    <ContextCard
                        icon={<Eye className="w-3.5 h-3.5" />}
                        title="Pacing Guide"
                        color="text-emerald-400"
                    >
                        <p className="text-xs text-gray-400 leading-relaxed">
                            <strong className="text-gray-300">Green</strong> = fast pacing,{" "}
                            <strong className="text-gray-300">Gray</strong> = medium,{" "}
                            <strong className="text-gray-300">Red</strong> = slow. Look for consecutive slow panels (dead zones).
                        </p>
                    </ContextCard>
                )}

                {/* ─── Continuity Flags (always shown) ─────────── */}
                {continuityFlags.length > 0 && (
                    <ContextCard
                        icon={<AlertTriangle className="w-3.5 h-3.5" />}
                        title={`Continuity Issues (${continuityFlags.length})`}
                        color="text-amber-400"
                    >
                        <div className="space-y-2">
                            {continuityFlags.map((flag, i) => (
                                <div
                                    key={i}
                                    className={`text-xs px-2.5 py-1.5 rounded border ${flag.severity === "high"
                                        ? "bg-red-500/10 border-red-500/20 text-red-300"
                                        : "bg-amber-500/10 border-amber-500/20 text-amber-300"
                                        }`}
                                >
                                    {flag.message}
                                </div>
                            ))}
                        </div>
                    </ContextCard>
                )}

                {/* General fallback */}
                {context === "general" && !isLoading && (
                    <div className="text-center py-8 text-gray-600">
                        <BookOpen className="w-8 h-8 mx-auto mb-3 opacity-30" />
                        <p className="text-xs">Navigate to a page to see contextual information</p>
                    </div>
                )}
            </div>
        </aside>
    );
}

// ─── Reusable Card Component ──────────────────────────────

function ContextCard({
    icon,
    title,
    color,
    children,
}: {
    icon: React.ReactNode;
    title: string;
    color: string;
    children: React.ReactNode;
}) {
    return (
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3">
            <div className={`flex items-center gap-1.5 mb-2 ${color}`}>
                {icon}
                <span className="text-xs font-semibold uppercase tracking-wider">{title}</span>
            </div>
            {children}
        </div>
    );
}
