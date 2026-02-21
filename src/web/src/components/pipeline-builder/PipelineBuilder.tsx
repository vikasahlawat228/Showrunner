"use client";

import React, { useCallback, useEffect } from "react";
import {
    ReactFlow,
    Background,
    Controls,
    type OnNodesChange,
    type OnEdgesChange,
    type OnConnect,
    applyNodeChanges,
    applyEdgeChanges,
    type Node,
    type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { StepNode } from "./StepNode";
import { StepLibrary } from "./StepLibrary";
import { StepConfigPanel } from "./StepConfigPanel";
import { usePipelineBuilderStore, type StepNodeData } from "@/lib/store/pipelineBuilderSlice";
import { Save, Play, Plus, Loader2 } from "lucide-react";

const nodeTypes = {
    stepNode: StepNode,
};

export function PipelineBuilder() {
    const {
        nodes,
        edges,
        setNodes,
        setEdges,
        onConnect,
        pipelineName,
        pipelineDescription,
        setPipelineName,
        setPipelineDescription,
        saveDefinition,
        runPipeline,
        resetBuilder,
        isSaving,
        isRunning,
        currentDefinitionId,
        selectStep,
    } = usePipelineBuilderStore();

    const handleNodesChange: OnNodesChange<Node<StepNodeData>> = useCallback(
        (changes) => setNodes(applyNodeChanges(changes, nodes) as Node<StepNodeData>[]),
        [nodes, setNodes]
    );

    const handleEdgesChange: OnEdgesChange = useCallback(
        (changes) => setEdges(applyEdgeChanges(changes, edges)),
        [edges, setEdges]
    );

    const handleConnect: OnConnect = useCallback(
        (params) => {
            if (params.source && params.target) {
                onConnect({ source: params.source, target: params.target });
            }
        },
        [onConnect]
    );

    return (
        <div className="flex h-full">
            {/* Left: Step Library */}
            <aside className="w-56 border-r border-gray-800 bg-gray-950/80 shrink-0 overflow-hidden flex flex-col">
                <StepLibrary />
            </aside>

            {/* Center: Canvas */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-2 border-b border-gray-800/60 bg-gray-950/90 shrink-0">
                    <div className="flex items-center gap-3">
                        <input
                            type="text"
                            value={pipelineName}
                            onChange={(e) => setPipelineName(e.target.value)}
                            className="bg-transparent text-sm font-semibold text-white border-b border-transparent hover:border-gray-600 focus:border-indigo-400 focus:outline-none px-1 py-0.5"
                            placeholder="Pipeline Name"
                        />
                        {currentDefinitionId && (
                            <span className="text-[10px] text-gray-600 font-mono">
                                {currentDefinitionId.slice(0, 8)}
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={resetBuilder}
                            className="px-2.5 py-1 text-xs text-gray-500 hover:text-gray-300 rounded hover:bg-gray-800 transition-colors"
                        >
                            <Plus className="w-3 h-3 inline mr-1" />
                            New
                        </button>
                        <button
                            onClick={() => saveDefinition()}
                            disabled={isSaving}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 hover:text-white transition-colors disabled:opacity-50"
                        >
                            {isSaving ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                                <Save className="w-3 h-3" />
                            )}
                            Save
                        </button>
                        <button
                            onClick={() => runPipeline()}
                            disabled={isRunning || nodes.length === 0}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
                        >
                            {isRunning ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                                <Play className="w-3 h-3" />
                            )}
                            Run
                        </button>
                    </div>
                </div>

                {/* React Flow Canvas */}
                <div className="flex-1">
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={handleNodesChange}
                        onEdgesChange={handleEdgesChange}
                        onConnect={handleConnect}
                        nodeTypes={nodeTypes}
                        onPaneClick={() => selectStep(null)}
                        fitView
                        proOptions={{ hideAttribution: true }}
                        defaultEdgeOptions={{
                            animated: true,
                            style: { stroke: "#6366f1", strokeWidth: 2 },
                        }}
                    >
                        <Background color="#1e1e1e" gap={20} />
                        <Controls
                            position="bottom-right"
                            className="!bg-gray-900 !border-gray-700 !text-gray-400 [&_button]:!bg-gray-800 [&_button]:!border-gray-700 [&_button:hover]:!bg-gray-700"
                        />
                    </ReactFlow>
                </div>
            </div>

            {/* Right: Config Panel */}
            <aside className="w-64 border-l border-gray-800 bg-gray-950/80 shrink-0 overflow-hidden flex flex-col">
                <StepConfigPanel />
            </aside>
        </div>
    );
}
