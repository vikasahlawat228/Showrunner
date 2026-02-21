"use client";

import React, { useState, useEffect } from "react";
import { ResearchResult, api, SceneSummary } from "@/lib/api";
import { Star, Link as LinkIcon, Trash2, ChevronDown, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";

interface ResearchDetailPanelProps {
    topic: ResearchResult;
    onDeleted: () => void;
}

export function ResearchDetailPanel({ topic, onDeleted }: ResearchDetailPanelProps) {
    const [scenes, setScenes] = useState<SceneSummary[]>([]);
    const [isLinking, setIsLinking] = useState(false);
    const [showLinkMenu, setShowLinkMenu] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const [isDeleting, setIsDeleting] = useState(false);

    // Fetch available scenes for linking (using chapter 1 as default for now, could be expanded)
    useEffect(() => {
        const fetchScenes = async () => {
            try {
                const data = await api.getScenes(1);
                setScenes(data);
            } catch (err) {
                console.error("Failed to fetch scenes for linking", err);
            }
        };
        fetchScenes();
    }, []);

    const handleLinkToScene = async (sceneId: string) => {
        setIsLinking(true);
        setShowLinkMenu(false);
        try {
            // Connect ResearchTopic to Scene using updateContainer with relationships update
            await api.updateContainer(topic.id, {
                relationships: [{ target_id: sceneId, type: "references" }]
            });
            toast.success("Linked research to scene successfully");
        } catch (err: any) {
            toast.error(err.message || "Failed to link scene");
        } finally {
            setIsLinking(false);
        }
    };

    const handleDelete = async () => {
        setIsDeleting(true);
        try {
            // The topic entity is technically a container, delete it natively via schema routes
            // Assuming a generic delete container endpoint here
            await fetch(`/api/v1/containers/${topic.id}`, { method: 'DELETE' });
            toast.success("Research topic deleted");
            onDeleted();
        } catch (err: any) {
            toast.error("Failed to delete topic: " + err.message);
        } finally {
            setIsDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const getStars = (score: string) => {
        switch (score?.toLowerCase()) {
            case "high":
            case "★★★★★":
            case "★★★★☆":
                return 5;
            case "medium":
            case "★★★☆☆":
                return 3;
            case "low":
            case "★★☆☆☆":
            case "★☆☆☆☆":
                return 1;
            default:
                return 0;
        }
    };

    return (
        <div className="flex-1 flex flex-col overflow-hidden bg-gray-900/50">
            {/* Header */}
            <div className="px-6 py-5 border-b border-gray-800 flex items-start justify-between bg-gray-900/80">
                <div className="flex-1 mr-4">
                    <div className="flex items-center gap-3 mb-2">
                        <h2 className="text-xl font-bold text-white tracking-tight">{topic.name}</h2>
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-800 border border-gray-700">
                            <span className="text-xs font-medium text-gray-300">Confidence:</span>
                            <div className="flex gap-0.5 text-amber-400">
                                {Array.from({ length: 5 }).map((_, i) => (
                                    <Star key={i} className={`w-3.5 h-3.5 ${i < getStars(topic.confidence_score) ? "fill-current" : "text-gray-600"}`} />
                                ))}
                            </div>
                        </div>
                    </div>
                    <p className="text-sm text-gray-500 italic">Query: &quot;{topic.original_query}&quot;</p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                    <div className="relative">
                        <button
                            onClick={() => setShowLinkMenu(!showLinkMenu)}
                            disabled={isLinking}
                            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 hover:bg-indigo-500/20 transition-colors"
                        >
                            <LinkIcon className="w-4 h-4" />
                            Link to Scene
                            <ChevronDown className="w-4 h-4" />
                        </button>
                        {showLinkMenu && (
                            <>
                                <div className="fixed inset-0 z-10" onClick={() => setShowLinkMenu(false)} />
                                <div className="absolute right-0 mt-2 w-56 rounded-lg bg-gray-900 border border-gray-700 shadow-xl overflow-hidden z-20">
                                    <div className="px-3 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider bg-gray-800/50 border-b border-gray-700">
                                        Select Scene
                                    </div>
                                    <div className="max-h-64 overflow-y-auto py-1">
                                        {scenes.length === 0 ? (
                                            <div className="px-4 py-3 text-sm text-gray-500 text-center">No scenes available</div>
                                        ) : (
                                            scenes.map(scene => (
                                                <button
                                                    key={scene.id}
                                                    onClick={() => handleLinkToScene(scene.id)}
                                                    className="w-full text-left px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 hover:text-white transition-colors"
                                                >
                                                    Chap {scene.chapter}, Scene {scene.scene_number}<br />
                                                    <span className="text-xs text-gray-500">{scene.title || "Untitled Scene"}</span>
                                                </button>
                                            ))
                                        )}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                    <button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"
                        title="Delete Topic"
                    >
                        <Trash2 className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Content Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">

                {/* Summary */}
                <section>
                    <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        Executive Summary
                    </h3>
                    <div className="bg-gray-800/30 border border-gray-700/50 rounded-xl p-4">
                        <p className="text-gray-300 leading-relaxed text-sm">{topic.summary}</p>
                    </div>
                </section>

                {/* Key Facts */}
                {topic.key_facts && topic.key_facts.length > 0 && (
                    <section>
                        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                            Key Facts
                        </h3>
                        <ul className="grid gap-2">
                            {topic.key_facts.map((fact, i) => (
                                <li key={i} className="flex items-start gap-3 text-sm text-gray-300 bg-gray-800/20 p-3 rounded-lg border border-gray-800/80">
                                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                                    <span className="leading-relaxed">{fact}</span>
                                </li>
                            ))}
                        </ul>
                    </section>
                )}

                {/* Constraints */}
                {topic.constraints && topic.constraints.length > 0 && (
                    <section>
                        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                            Constraints & Rules
                        </h3>
                        <div className="bg-amber-950/10 border border-amber-900/20 rounded-xl overflow-hidden p-4">
                            <ul className="space-y-3">
                                {topic.constraints.map((constraint, i) => (
                                    <li key={i} className="flex gap-3 text-sm text-amber-200/80">
                                        <span className="text-amber-500/50 -ml-1">•</span>
                                        {constraint}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </section>
                )}

                {/* Story Implications */}
                {topic.story_implications && topic.story_implications.length > 0 && (
                    <section>
                        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-purple-500" />
                            Story Implications
                        </h3>
                        <div className="bg-purple-950/20 border border-purple-900/30 rounded-xl p-5">
                            <ul className="space-y-4">
                                {topic.story_implications.map((imp, i) => (
                                    <li key={i} className="flex flex-col gap-1 text-sm text-purple-200">
                                        <span className="font-semibold text-purple-300">Application {i + 1}</span>
                                        <span className="text-purple-200/80 leading-relaxed">{imp}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </section>
                )}

                {/* Sources */}
                {topic.sources && topic.sources.length > 0 && (
                    <section>
                        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Sources</h3>
                        <div className="flex flex-wrap gap-2">
                            {topic.sources.map((src, i) => (
                                <span key={i} className="px-2 py-1 bg-gray-800 text-gray-400 rounded text-xs">
                                    {src}
                                </span>
                            ))}
                        </div>
                    </section>
                )}

                <div className="h-8" />
            </div>

            <ConfirmDialog
                isOpen={showDeleteConfirm}
                title="Delete Research Topic"
                message="Are you sure you want to delete this research topic? This will not remove associations from scenes and may cause broken links."
                confirmLabel="Delete Topic"
                cancelLabel="Cancel"
                onConfirm={handleDelete}
                onCancel={() => setShowDeleteConfirm(false)}
                variant="danger"
            />
        </div>
    );
}
