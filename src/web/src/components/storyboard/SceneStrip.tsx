"use client";

import React, { useEffect, useState } from "react";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
} from "@dnd-kit/core";
import {
    SortableContext,
    horizontalListSortingStrategy,
    arrayMove,
} from "@dnd-kit/sortable";
import { useStoryboardStore, type SceneInfo } from "@/lib/store/storyboardSlice";
import { PanelCard } from "./PanelCard";
import { Plus, Sparkles, Loader2, ChevronRight, Wand2 } from "lucide-react";
import { type LayoutSuggestion, api } from "@/lib/api";
import { toast } from "sonner";
import { LayoutSuggestionPanel } from "./LayoutSuggestionPanel";

interface SceneStripProps {
    scene: SceneInfo;
}

export function SceneStrip({ scene }: SceneStripProps) {
    const {
        panelsByScene,
        loadPanelsForScene,
        reorderPanels,
        createPanel,
        generatePanels,
        isGenerating,
        isLoadingPanels,
    } = useStoryboardStore();

    const [isSuggesting, setIsSuggesting] = useState(false);
    const [suggestion, setSuggestion] = useState<LayoutSuggestion | null>(null);

    const handleSuggestLayout = async () => {
        try {
            setIsSuggesting(true);
            const res = await api.suggestLayout(scene.id);
            setSuggestion(res);
        } catch (err: any) {
            toast.error("Failed to suggest layout: " + err.message);
        } finally {
            setIsSuggesting(false);
        }
    };

    const handleApplyLayout = () => {
        if (!suggestion) return;
        generatePanels(scene.id, suggestion.suggested_panel_count);
        setSuggestion(null);
    };

    const panels = panelsByScene[scene.id] || [];

    useEffect(() => {
        loadPanelsForScene(scene.id);
    }, [scene.id, loadPanelsForScene]);

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over || active.id === over.id) return;

        const ids = panels.map((p) => p.id);
        const oldIndex = ids.indexOf(active.id as string);
        const newIndex = ids.indexOf(over.id as string);
        const newOrder = arrayMove(ids, oldIndex, newIndex);
        reorderPanels(scene.id, newOrder);
    };

    return (
        <div className="border border-gray-800 rounded-xl bg-gray-950/50 overflow-hidden">
            {/* Scene header */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-800/60 bg-gray-900/30">
                <div className="flex items-center gap-2">
                    <span className="text-base">🎬</span>
                    <h3 className="text-sm font-semibold text-white">{scene.name}</h3>
                    <span className="text-[10px] text-gray-600 bg-gray-800 px-1.5 py-0.5 rounded">
                        {panels.length} panels
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <button
                        onClick={handleSuggestLayout}
                        disabled={isSuggesting || isGenerating}
                        className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg bg-emerald-600/20 text-emerald-300 hover:bg-emerald-600/30 transition-colors disabled:opacity-50"
                    >
                        {isSuggesting ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                            <Wand2 className="w-3 h-3" />
                        )}
                        Suggest Layout
                    </button>
                    <button
                        onClick={() => generatePanels(scene.id, 6)}
                        disabled={isGenerating || isSuggesting}
                        className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-medium rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 transition-colors disabled:opacity-50"
                    >
                        {isGenerating ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                        ) : (
                            <Sparkles className="w-3 h-3" />
                        )}
                        Generate Panels
                    </button>
                    <button
                        onClick={() => createPanel(scene.id)}
                        className="flex items-center gap-1 px-2 py-1 text-[11px] text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800 transition-colors"
                    >
                        <Plus className="w-3 h-3" />
                        Add
                    </button>
                </div>
            </div>

            {/* Layout Suggestion Panel */}
            {suggestion && (
                <LayoutSuggestionPanel
                    suggestion={suggestion}
                    sceneName={scene.name}
                    onApply={handleApplyLayout}
                    onDiscard={() => setSuggestion(null)}
                />
            )}

            {/* Panel strip */}
            <div className="p-3 overflow-x-auto">
                {isLoadingPanels && panels.length === 0 ? (
                    <div className="flex items-center gap-2 text-gray-600 text-sm py-6 px-4">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Loading panels…
                    </div>
                ) : panels.length === 0 ? (
                    <div className="text-center py-8 text-gray-600 text-sm">
                        <p>No panels yet.</p>
                        <p className="text-xs mt-1">Click &quot;Generate Panels&quot; to auto-create from the scene, or add manually.</p>
                    </div>
                ) : (
                    <DndContext
                        sensors={sensors}
                        collisionDetection={closestCenter}
                        onDragEnd={handleDragEnd}
                    >
                        <SortableContext
                            items={panels.map((p) => p.id)}
                            strategy={horizontalListSortingStrategy}
                        >
                            <div className="flex gap-3">
                                {panels.map((panel) => (
                                    <PanelCard key={panel.id} panel={panel} />
                                ))}

                                {/* Add panel button at the end */}
                                <button
                                    onClick={() => createPanel(scene.id)}
                                    className="w-48 h-[200px] rounded-xl border-2 border-dashed border-gray-800 flex flex-col items-center justify-center text-gray-700 hover:text-gray-500 hover:border-gray-700 transition-colors shrink-0"
                                >
                                    <Plus className="w-6 h-6 mb-1" />
                                    <span className="text-xs">Add Panel</span>
                                </button>
                            </div>
                        </SortableContext>
                    </DndContext>
                )}
            </div>
        </div>
    );
}
