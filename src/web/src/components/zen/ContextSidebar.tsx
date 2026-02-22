"use client";

import React, { useState, useEffect } from "react";
import { useZenStore, type ContextEntry } from "@/lib/store/zenSlice";
import { ContextInspector } from "@/components/ui/ContextInspector";
import { ContinuityPanel } from "./ContinuityPanel";
import { StyleScorecard } from "./StyleScorecard";
import { api } from "@/lib/api";
import {
    PanelRightClose,
    PanelRightOpen,
    Users,
    MapPin,
    Globe,
    FileText,
    Link2,
    Loader2,
    X,
    ChevronDown,
    Clock,
} from "lucide-react";
import { InlineTranslation } from "./InlineTranslation";

const TYPE_ICONS: Record<string, React.ReactNode> = {
    character: <Users className="w-3.5 h-3.5" />,
    scene: <FileText className="w-3.5 h-3.5" />,
    location: <MapPin className="w-3.5 h-3.5" />,
    world: <Globe className="w-3.5 h-3.5" />,
};

const TYPE_COLORS: Record<string, string> = {
    character: "border-violet-500/40 bg-violet-500/5",
    scene: "border-blue-500/40 bg-blue-500/5",
    location: "border-emerald-500/40 bg-emerald-500/5",
    world: "border-amber-500/40 bg-amber-500/5",
    fragment: "border-gray-600/40 bg-gray-500/5",
};

const TYPE_BADGE_COLORS: Record<string, string> = {
    character: "bg-violet-500/20 text-violet-300",
    scene: "bg-blue-500/20 text-blue-300",
    location: "bg-emerald-500/20 text-emerald-300",
    world: "bg-amber-500/20 text-amber-300",
};

function ContextCard({ entry }: { entry: ContextEntry }) {
    const colorClass = TYPE_COLORS[entry.containerType] ?? "border-gray-700 bg-gray-800/50";
    const badgeClass = TYPE_BADGE_COLORS[entry.containerType] ?? "bg-gray-600/20 text-gray-400";

    if (entry.loading) {
        return (
            <div className={`rounded-lg border p-3 ${colorClass} animate-pulse`}>
                <div className="flex items-center gap-2">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-500" />
                    <span className="text-sm text-gray-500">Loading context…</span>
                </div>
            </div>
        );
    }

    return (
        <div className={`rounded-lg border p-3 ${colorClass} transition-all hover:border-opacity-80`}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    {TYPE_ICONS[entry.containerType] ?? <FileText className="w-3.5 h-3.5" />}
                    <span className="font-medium text-sm text-white">{entry.name}</span>
                </div>
                <span className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${badgeClass}`}>
                    {entry.containerType}
                </span>
            </div>

            {/* Context text preview */}
            <div className="text-xs text-gray-400 leading-relaxed whitespace-pre-line line-clamp-6">
                {entry.contextText}
            </div>

            {entry.relatedCount > 0 && (
                <div className="flex items-center gap-1 mt-2 text-[11px] text-gray-500">
                    <Link2 className="w-3 h-3" />
                    <span>{entry.relatedCount} related</span>
                </div>
            )}
        </div>
    );
}

function PreviouslySection() {
    const [open, setOpen] = useState(true);
    const [sessions, setSessions] = useState<Array<{ id: string; name: string; updated_at: string; message_count: number }>>([]);
    const [show, setShow] = useState(false);

    useEffect(() => {
        let cancelled = false;
        api.getChatSessions().then((data) => {
            if (cancelled) return;
            if (!data || data.length === 0) return;
            // Check if most recent session is > 4h old
            const latest = data[0];
            const hoursAgo = (Date.now() - new Date(latest.updated_at).getTime()) / (1000 * 60 * 60);
            if (hoursAgo > 4) {
                setSessions(data.slice(0, 3));
                setShow(true);
            }
        }).catch(() => { /* ignore */ });
        return () => { cancelled = true; };
    }, []);

    if (!show || sessions.length === 0) return null;

    return (
        <div className="px-4 py-2 border-b border-gray-800/60 shrink-0">
            <button
                onClick={() => setOpen(!open)}
                className="flex items-center gap-1.5 w-full text-left group"
            >
                <ChevronDown className={`w-3 h-3 text-gray-500 transition-transform duration-200 ${open ? "" : "-rotate-90"}`} />
                <span className="text-[10px] uppercase text-gray-500 font-semibold tracking-wider group-hover:text-gray-300 transition-colors">
                    Previously…
                </span>
            </button>
            {open && (
                <div className="mt-2 space-y-1.5 animate-in fade-in duration-200">
                    {sessions.map((s) => {
                        const h = Math.floor((Date.now() - new Date(s.updated_at).getTime()) / (1000 * 60 * 60));
                        const ago = h < 24 ? `${h}h ago` : `${Math.floor(h / 24)}d ago`;
                        return (
                            <div key={s.id} className="flex items-center gap-2 rounded-md bg-gray-900/50 px-2.5 py-1.5 border border-gray-800/50">
                                <Clock className="w-3 h-3 text-indigo-400 shrink-0" />
                                <span className="text-xs text-gray-300 truncate flex-1">{s.name}</span>
                                <span className="text-[10px] text-gray-600 shrink-0">{ago}</span>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}

export function ContextSidebar() {
    const {
        sidebarVisible,
        toggleSidebar,
        contextEntries,
        detectedEntities,
        isDetecting,
        clearDetections,
        lastAIOperation,
        translationSource,
        activeSidebarTab,
        setActiveSidebarTab,
    } = useZenStore();

    // Use effects to sync any legacy state if necessary, but we rely on activeSidebarTab now.

    if (!sidebarVisible) {
        return (
            <button
                onClick={toggleSidebar}
                className="fixed right-4 top-4 p-2 rounded-lg bg-gray-800 border border-gray-700 text-gray-400 hover:text-white hover:bg-gray-700 transition-colors z-50"
                title="Open context sidebar"
            >
                <PanelRightOpen className="w-4 h-4" />
            </button>
        );
    }

    return (
        <aside className="w-80 border-l border-gray-800 bg-gray-950/80 backdrop-blur-sm flex flex-col shrink-0 overflow-hidden">
            {/* Header */}
            <div className="flex flex-col border-b border-gray-800">
                <div className="flex items-center justify-between px-4 py-3">
                    <h2 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                        {activeSidebarTab === "context" && "📎 Sidebar"}
                        {activeSidebarTab === "translation" && "🌐 Translation"}
                        {activeSidebarTab === "continuity" && "🔄 Continuity"}
                        {activeSidebarTab === "style" && "✨ Style"}
                        {isDetecting && activeSidebarTab === "context" && (
                            <Loader2 className="w-3 h-3 animate-spin text-indigo-400" />
                        )}
                    </h2>
                    <div className="flex items-center gap-1">
                        {activeSidebarTab === "context" && contextEntries.length > 0 && (
                            <button
                                onClick={clearDetections}
                                className="p-1 rounded text-gray-500 hover:text-gray-300 transition-colors"
                                title="Clear all"
                            >
                                <X className="w-3.5 h-3.5" />
                            </button>
                        )}
                        <button
                            onClick={toggleSidebar}
                            className="p-1 rounded text-gray-500 hover:text-gray-300 transition-colors"
                            title="Close sidebar"
                        >
                            <PanelRightClose className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex items-center gap-1 px-2 py-2 border-b border-gray-800/60 bg-gray-950/50 overflow-x-auto no-scrollbar">
                <button
                    onClick={() => setActiveSidebarTab("context")}
                    className={`flex-none px-2 py-1.5 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1.5 ${activeSidebarTab === "context" ? "bg-indigo-600/30 text-indigo-300" : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                        }`}
                >
                    Context
                </button>
                <button
                    onClick={() => setActiveSidebarTab("continuity")}
                    className={`flex-none px-2 py-1.5 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1.5 ${activeSidebarTab === "continuity" ? "bg-indigo-600/30 text-indigo-300" : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                        }`}
                >
                    Continuity
                </button>
                <button
                    onClick={() => setActiveSidebarTab("style")}
                    className={`flex-none px-2 py-1.5 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1.5 ${activeSidebarTab === "style" ? "bg-indigo-600/30 text-indigo-300" : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                        }`}
                >
                    Style
                </button>
                <button
                    onClick={() => setActiveSidebarTab("translation")}
                    className={`flex-none px-2 py-1.5 text-xs font-medium rounded transition-colors flex items-center justify-center gap-1.5 ${activeSidebarTab === "translation" ? "bg-indigo-600/30 text-indigo-300" : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50"
                        }`}
                >
                    <Globe className="w-3.5 h-3.5" /> Translate
                </button>
            </div>

            {activeSidebarTab === "context" && (
                <>
                    {/* "Previously…" section for returning users */}
                    <PreviouslySection />

                    {/* Entity tags */}
                    {detectedEntities.length > 0 && (
                        <div className="px-4 py-2 border-b border-gray-800/60 shrink-0">
                            <div className="text-[10px] uppercase text-gray-600 font-semibold mb-1.5">
                                Detected Entities
                            </div>
                            <div className="flex flex-wrap gap-1">
                                {detectedEntities.map((entity) => {
                                    const badgeClass =
                                        TYPE_BADGE_COLORS[entity.container_type] ??
                                        "bg-gray-600/20 text-gray-400";
                                    return (
                                        <span
                                            key={entity.container_id}
                                            className={`text-[11px] px-2 py-0.5 rounded-full ${badgeClass}`}
                                            title={`${entity.mention} (${(entity.confidence * 100).toFixed(0)}%)`}
                                        >
                                            {entity.container_name}
                                        </span>
                                    );
                                })}
                            </div>
                        </div>
                    )}

                    {/* Glass Box — Last AI Operation */}
                    {lastAIOperation && (
                        <div className="px-3 py-2 border-b border-gray-800/60 shrink-0">
                            <ContextInspector operation={lastAIOperation} />
                        </div>
                    )}

                    {/* Context cards */}
                    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
                        {contextEntries.length === 0 && !isDetecting && !lastAIOperation && (
                            <div className="text-center text-gray-600 text-sm py-8">
                                <p className="mb-1">No entities detected yet.</p>
                                <p className="text-xs">
                                    Start writing and mention characters,
                                    <br />
                                    locations, or scenes to see context here.
                                </p>
                            </div>
                        )}

                        {contextEntries.map((entry) => (
                            <ContextCard key={entry.containerId} entry={entry} />
                        ))}
                    </div>
                </>
            )}

            {activeSidebarTab === "translation" && (
                <div className="flex-1 overflow-y-auto p-3">
                    <InlineTranslation
                        sourceText={translationSource}
                        onReplace={(text) => {
                            window.dispatchEvent(new CustomEvent("zen:replace", { detail: text }));
                        }}
                        onInsertBelow={(text) => {
                            window.dispatchEvent(new CustomEvent("zen:insertBelow", { detail: text }));
                        }}
                        onClose={() => setActiveSidebarTab("context")}
                    />
                </div>
            )}

            {activeSidebarTab === "continuity" && (
                <div className="flex-1 overflow-hidden">
                    <ContinuityPanel />
                </div>
            )}

            {activeSidebarTab === "style" && (
                <div className="flex-1 overflow-hidden">
                    <StyleScorecard />
                </div>
            )}
        </aside>
    );
}
