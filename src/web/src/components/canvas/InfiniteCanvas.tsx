"use client";

import React, { useEffect, useMemo, useCallback, useState } from "react";
import {
    ReactFlow,
    MiniMap,
    Controls,
    Background,
    BackgroundVariant,
    Panel,
    ConnectionMode,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { useStudioStore } from "@/lib/store";
import GenericNode from "./nodes/GenericNode";

const InfiniteCanvas = () => {
    const {
        nodes,
        edges,
        onNodesChange,
        onEdgesChange,
        onConnect,
        buildGraph,
        characters,
        scenes,
        world,
        loading,
    } = useStudioStore();

    const nodeTypes = useMemo(() => ({ genericContainer: GenericNode }), []);

    const [mounted, setMounted] = useState(false);

    // Rebuild graph whenever underlying semantic data changes or loading finishes
    useEffect(() => {
        setMounted(true);
        if (!loading) {
            buildGraph();
        }
    }, [loading, characters, scenes, world, buildGraph]);

    if (!mounted) return null;

    return (
        <div className="w-full h-full bg-slate-950">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                connectionMode={ConnectionMode.Loose}
                fitView
                className="react-flow-dark"
            >
                <Background variant={BackgroundVariant.Dots} gap={24} size={2} color="#334155" />

                <Controls className="fill-slate-400 border-none bg-slate-900 shadow-xl" />
                <MiniMap
                    nodeColor={(node) => {
                        switch (node.data?.containerType) {
                            case 'character': return '#1e3a8a';
                            case 'scene': return '#064e3b';
                            case 'world': return '#78350f';
                            default: return '#1e293b';
                        }
                    }}
                    maskColor="rgba(15, 23, 42, 0.7)"
                    className="!bg-slate-900 !border-slate-800 rounded-lg shadow-xl"
                    style={{ backgroundColor: '#0f172a' }}
                />

                <Panel position="top-left" className="bg-slate-900/80 backdrop-blur-sm p-3 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <h1 className="text-sm font-bold text-slate-200">Showrunner Graph</h1>
                    <p className="text-xs text-slate-400">Containers: {nodes.length} | Links: {edges.length}</p>
                </Panel>

                {/* Empty Canvas Onboarding CTA */}
                {!loading && nodes.length === 0 && (
                    <Panel position="top-center" className="mt-[30vh]">
                        <div className="text-center bg-slate-900/60 backdrop-blur-sm border border-slate-800/50 rounded-xl px-8 py-6 max-w-md">
                            <p className="text-lg font-semibold text-slate-300 mb-2">Your story canvas is empty</p>
                            <p className="text-sm text-slate-500 leading-relaxed">
                                Create Characters, Scenes, or World entries from the Assets panel, then they will appear here as interactive nodes you can connect.
                            </p>
                        </div>
                    </Panel>
                )}
            </ReactFlow>
        </div>
    );
};

export default InfiniteCanvas;
