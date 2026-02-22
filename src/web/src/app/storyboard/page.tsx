"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { ArrowLeft, Film, LayoutList, Map, Plus } from "lucide-react";
import { useStoryboardStore } from "@/lib/store/storyboardSlice";
import { SceneStrip } from "@/components/storyboard/SceneStrip";
import { PanelEditor } from "@/components/storyboard/PanelEditor";
import { SemanticCanvas } from "@/components/storyboard/SemanticCanvas";
import { VoiceToSceneButton } from "@/components/storyboard/VoiceToSceneButton";
import { api } from "@/lib/api";
import { toast } from "sonner";
import { useCallback, useState } from "react";

export default function StoryboardPage() {
    const [scenes, setScenes] = useState<any[]>([]);
    const [viewMode, setViewMode] = useState<"strip" | "canvas">("strip");
    const { selectedPanelId } = useStoryboardStore();

    const loadScenes = useCallback(async () => {
        try {
            const graph = await api.getGraph();
            const sceneNodes = graph.nodes
                .filter((n: any) => n.data?.containerType === "scene")
                .map((n: any) => ({
                    id: n.id,
                    name: n.data?.label || n.id,
                }));
            setScenes(sceneNodes);
        } catch (err) {
            console.error("Failed to load scenes:", err);
            // Provide demo scenes as fallback
            setScenes([
                { id: "demo-scene-1", name: "Opening Scene" },
                { id: "demo-scene-2", name: "The Confrontation" },
                { id: "demo-scene-3", name: "Resolution" },
            ]);
        }
    }, [setScenes]);

    // Load scenes from the graph API on mount
    useEffect(() => {
        loadScenes();
    }, [loadScenes]);

    // Refresh scenes when a new one is quickly added
    useEffect(() => {
        const handleRefresh = () => loadScenes();
        // Hook into the store fetchAll which is called from QuickAddModal
        window.addEventListener("focus", handleRefresh);
        return () => window.removeEventListener("focus", handleRefresh);
    }, [loadScenes]);

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white">
            {/* Top bar */}
            <header className="flex items-center justify-between px-4 py-2 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-sm shrink-0">
                <div className="flex items-center gap-3">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-300 transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <div className="w-px h-4 bg-gray-800" />
                    <div className="flex items-center gap-2">
                        <Film className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm font-semibold text-gray-200">
                            Storyboard
                        </span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <VoiceToSceneButton
                        onPanelsGenerated={(sceneId, panels) => {
                            toast.success(`Generated ${panels.length} panels from voice input`);
                            window.location.reload(); // Refresh to catch new panels in store
                        }}
                    />

                    {/* View toggle */}
                    <div className="flex items-center bg-gray-900 rounded-lg p-1 border border-gray-800">
                        <button
                            onClick={() => setViewMode("strip")}
                            className={`flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-md transition-colors ${viewMode === "strip"
                                ? "bg-gray-800 text-white shadow-sm"
                                : "text-gray-500 hover:text-gray-300"
                                }`}
                        >
                            <LayoutList className="w-3 h-3" />
                            Strips
                        </button>
                        <button
                            onClick={() => setViewMode("canvas")}
                            className={`flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-md transition-colors ${viewMode === "canvas"
                                ? "bg-gray-800 text-white shadow-sm"
                                : "text-gray-500 hover:text-gray-300"
                                }`}
                        >
                            <Map className="w-3 h-3" />
                            Canvas
                        </button>
                    </div>

                    {/* App navigation */}
                    <nav className="flex items-center gap-1 ml-2">
                        <Link href="/dashboard" className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">Canvas</Link>
                        <Link href="/zen" className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">Zen</Link>
                        <Link href="/pipelines" className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors">Pipelines</Link>
                        <span className="px-3 py-1.5 rounded text-xs text-emerald-400 bg-emerald-500/10">Storyboard</span>
                        <a href="/preview" className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-emerald-300 hover:bg-gray-800 transition-colors">📱 Sim</a>
                    </nav>
                </div>
            </header>

            {/* Content */}
            <div className="flex flex-1 overflow-hidden">
                {/* Main view */}
                <div className="flex-1 overflow-hidden">
                    {viewMode === "strip" ? (
                        <div className="h-full overflow-y-auto p-6 space-y-6">
                            {scenes.length === 0 ? (
                                <div className="text-center py-16 text-gray-600">
                                    <Film className="w-10 h-10 mx-auto mb-3 opacity-30" />
                                    <p>No scenes found.</p>
                                    <p className="text-xs mt-1 mb-4">Create scenes to start storyboarding.</p>
                                    <button
                                        onClick={() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'scene' } }))}
                                        className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-md transition-colors shadow-sm"
                                    >
                                        <Plus className="w-4 h-4" />
                                        Add Scene
                                    </button>
                                </div>
                            ) : (
                                <>
                                    {scenes.map((scene) => (
                                        <SceneStrip key={scene.id} scene={scene} />
                                    ))}
                                    <div className="flex justify-center pt-4 pb-8 border-t border-gray-800/60 mt-8">
                                        <button
                                            onClick={() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'scene' } }))}
                                            className="flex items-center gap-2 px-4 py-2 border border-dashed border-gray-700 hover:border-indigo-500 text-gray-400 hover:text-indigo-400 text-sm font-medium rounded-xl transition-colors bg-gray-900/50 hover:bg-gray-900"
                                        >
                                            <Plus className="w-4 h-4" />
                                            Add Another Scene
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    ) : (
                        <SemanticCanvas />
                    )}
                </div>

                {/* Editor sidebar (visible when a panel is selected) */}
                {selectedPanelId && (
                    <aside className="w-72 border-l border-gray-800 bg-gray-950/80 shrink-0 overflow-hidden flex flex-col">
                        <PanelEditor />
                    </aside>
                )}
            </div>
        </div>
    );
}
