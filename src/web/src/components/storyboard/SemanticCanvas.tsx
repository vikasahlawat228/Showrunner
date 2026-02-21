"use client";

import React, { useMemo, useCallback } from "react";
import {
    ReactFlow,
    Background,
    Controls,
    Handle,
    Position,
    useViewport,
    type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useStoryboardStore, type SceneInfo } from "@/lib/store/storyboardSlice";
import { ImageIcon } from "lucide-react";

// ── Scene Node with Semantic Zoom ─────────────────────────

interface SceneNodeData {
    scene: SceneInfo;
    panelCount: number;
    panels: { id: string; description: string; panel_type: string }[];
    [key: string]: unknown;
}

function SceneNodeComponent({ data }: NodeProps) {
    const nodeData = data as unknown as SceneNodeData;
    const { zoom } = useViewport();

    const isZoomedIn = zoom > 0.6;

    return (
        <div
            className={`rounded-xl border-2 border-emerald-700/50 bg-emerald-950 shadow-lg transition-all ${isZoomedIn ? "min-w-[400px]" : "min-w-[180px]"
                }`}
        >
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-3 !bg-emerald-500"
            />

            {/* Header */}
            <div className="px-3 py-2 border-b border-emerald-800/60">
                <div className="flex items-center gap-2">
                    <span className="text-sm">🎬</span>
                    <span className="text-sm font-semibold text-white">
                        {nodeData.scene.name}
                    </span>
                    <span className="text-[10px] text-emerald-400 bg-emerald-500/20 px-1.5 py-0.5 rounded">
                        {nodeData.panelCount} panels
                    </span>
                </div>
            </div>

            {/* Semantic content */}
            {isZoomedIn ? (
                // Zoomed in: show panel thumbnails grid
                <div className="p-2 grid grid-cols-3 gap-1.5">
                    {nodeData.panels.slice(0, 9).map((p, i) => (
                        <div
                            key={p.id}
                            className="h-16 rounded bg-gray-900 border border-gray-800 flex flex-col items-center justify-center text-[8px] text-gray-600 overflow-hidden"
                        >
                            <ImageIcon className="w-3 h-3 mb-0.5" />
                            <span className="px-1 text-center truncate w-full">
                                {p.description.slice(0, 20) || `Panel ${i + 1}`}
                            </span>
                        </div>
                    ))}
                    {nodeData.panelCount > 9 && (
                        <div className="h-16 rounded bg-gray-900 border border-gray-800 flex items-center justify-center text-[10px] text-gray-500">
                            +{nodeData.panelCount - 9} more
                        </div>
                    )}
                </div>
            ) : (
                // Zoomed out: compact summary
                <div className="px-3 py-2 text-xs text-emerald-400/60">
                    {nodeData.panelCount > 0
                        ? `${nodeData.panelCount} panels`
                        : "Empty"}
                </div>
            )}

            <Handle
                type="source"
                position={Position.Right}
                className="!w-3 !h-3 !bg-emerald-500"
            />
        </div>
    );
}

const nodeTypes = {
    sceneNode: SceneNodeComponent,
};

// ── Main Canvas Component ─────────────────────────────────

export function SemanticCanvas() {
    const { scenes, panelsByScene } = useStoryboardStore();

    const nodes = useMemo(
        () =>
            scenes.map((scene, i) => {
                const panels = panelsByScene[scene.id] || [];
                return {
                    id: scene.id,
                    type: "sceneNode" as const,
                    position: { x: i * 450, y: 50 + (i % 2) * 120 },
                    data: {
                        scene,
                        panelCount: panels.length,
                        panels: panels.map((p) => ({
                            id: p.id,
                            description: p.description,
                            panel_type: p.panel_type,
                        })),
                    },
                };
            }),
        [scenes, panelsByScene]
    );

    const edges = useMemo(
        () =>
            scenes.slice(0, -1).map((scene, i) => ({
                id: `e-${scene.id}-${scenes[i + 1].id}`,
                source: scene.id,
                target: scenes[i + 1].id,
                animated: true,
                style: { stroke: "#10b981", strokeWidth: 2 },
            })),
        [scenes]
    );

    if (scenes.length === 0) {
        return (
            <div className="flex items-center justify-center h-full text-gray-600 text-sm">
                No scenes available. Add scenes from the Dashboard first.
            </div>
        );
    }

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
        >
            <Background color="#1a1a1a" gap={20} />
            <Controls
                position="bottom-right"
                className="!bg-gray-900 !border-gray-700 [&_button]:!bg-gray-800 [&_button]:!border-gray-700"
            />
        </ReactFlow>
    );
}
