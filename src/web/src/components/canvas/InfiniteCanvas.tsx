"use client";

import React, { useEffect, useMemo, useCallback } from "react";
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

    // Rebuild graph whenever underlying semantic data changes or loading finishes
    useEffect(() => {
        if (!loading) {
            buildGraph();
        }
    }, [loading, buildGraph]);

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
                    className="bg-slate-900 border-slate-800 rounded-lg shadow-xl"
                />

                <Panel position="top-left" className="bg-slate-900/80 backdrop-blur-sm p-3 rounded-lg border border-slate-800 flex flex-col gap-1">
                    <h1 className="text-sm font-bold text-slate-200">Showrunner Graph</h1>
                    <p className="text-xs text-slate-400">Containers: {nodes.length} | Links: {edges.length}</p>
                </Panel>
            </ReactFlow>
        </div>
    );
};

export default InfiniteCanvas;
