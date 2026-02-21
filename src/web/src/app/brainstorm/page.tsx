"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ArrowLeft, Plus, Sparkles, Lightbulb } from "lucide-react";
import {
    ReactFlow,
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { IdeaCardNode, type IdeaCardNodeData } from "@/components/brainstorm/IdeaCardNode";
import { SuggestionPanel } from "@/components/brainstorm/SuggestionPanel";
import { api, BrainstormSuggestion } from "@/lib/api";
import { toast } from "sonner";

const nodeTypes = {
    ideaCard: IdeaCardNode,
};

export default function BrainstormPage() {
    const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

    // Suggestion Panel State
    const [suggestion, setSuggestion] = useState<BrainstormSuggestion | null>(null);
    const [isSuggesting, setIsSuggesting] = useState(false);

    // Load initial cards
    useEffect(() => {
        const loadCards = async () => {
            try {
                const cards = await api.getBrainstormCards();
                const initialNodes = cards.map((c: any) => ({
                    id: c.id,
                    type: "ideaCard",
                    position: { x: c.attributes?.position_x || 0, y: c.attributes?.position_y || 0 },
                    data: {
                        text: c.attributes?.text || "",
                        color: c.attributes?.color,
                        tags: c.tags || [],
                        syncState: "synced",
                        onDelete: handleDeleteCard,
                        onChange: handleCardChange,
                        onRetry: handleRetryCard, // Added onRetry
                    },
                }));
                setNodes(initialNodes);
            } catch (error) {
                console.error("Failed to load brainstorm cards:", error);
                toast.error("Failed to load cards. Using empty canvas.");
            }
        };

        loadCards();
    }, []);

    // Handlers
    const onConnect = useCallback(
        (params: Connection | Edge) => setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: "#64748b" } } as Edge, eds)),
        [setEdges]
    );

    const handleAddCard = async () => {
        const id = crypto.randomUUID();
        const x = window.innerWidth / 2 + (Math.random() * 100 - 50) - 200;
        const y = window.innerHeight / 2 + (Math.random() * 100 - 50) - 100;

        const newNode: Node = {
            id,
            type: "ideaCard",
            position: { x, y },
            data: {
                text: "New idea...",
                color: "#4F46E5",
                tags: [],
                syncState: "syncing",
                onDelete: handleDeleteCard,
                onChange: handleCardChange,
                onRetry: handleRetryCard,
            },
        };

        setNodes((nds) => [...nds, newNode]);

        try {
            await api.saveBrainstormCard({
                text: "New idea...",
                position_x: x,
                position_y: y,
                color: "#4F46E5",
                tags: [],
            });
            // Update sync state
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "synced" } } : n));
        } catch (error) {
            console.error(error);
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "error" } } : n));
        }
    };

    const handleRetryCard = async (id: string) => {
        const node = nodes.find(n => n.id === id);
        if (!node) return;

        setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "syncing" } } : n));
        try {
            await api.saveBrainstormCard({
                text: (node.data as unknown as IdeaCardNodeData).text,
                position_x: node.position.x,
                position_y: node.position.y,
                color: (node.data as unknown as IdeaCardNodeData).color,
                tags: (node.data as unknown as IdeaCardNodeData).tags,
            });
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "synced" } } : n));
        } catch (error) {
            console.error(error);
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "error" } } : n));
        }
    };

    const handleSuggest = async () => {
        if (nodes.length === 0) {
            toast.info("Add some cards first to get suggestions!");
            return;
        }

        setIsSuggesting(true);
        setSuggestion(null);

        try {
            const cardsPayload = nodes.map(n => ({
                id: n.id,
                text: (n.data as unknown as IdeaCardNodeData).text,
                x: n.position.x,
                y: n.position.y,
            }));

            const res = await api.suggestBrainstormConnections({ cards: cardsPayload });
            setSuggestion(res);
            toast.success("Suggestions ready!");
        } catch (error) {
            console.error(error);
            toast.error("Failed to get suggestions");
        } finally {
            setIsSuggesting(false);
        }
    };

    const handleCardChange = async (id: string, newText: string) => {
        setNodes((nds) =>
            nds.map((n) => {
                if (n.id === id) {
                    return { ...n, data: { ...n.data, text: newText, syncState: "syncing" } };
                }
                return n;
            })
        );

        const node = nodes.find(n => n.id === id);
        if (node) {
            try {
                await api.saveBrainstormCard({
                    text: newText,
                    position_x: node.position.x,
                    position_y: node.position.y,
                    color: (node.data as unknown as IdeaCardNodeData).color,
                    tags: (node.data as unknown as IdeaCardNodeData).tags,
                });
                setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "synced" } } : n));
            } catch (error) {
                console.error(error);
                setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "error" } } : n));
            }
        }
    };

    const handleDeleteCard = async (id: string) => {
        setNodes((nds) => nds.filter((n) => n.id !== id));
        setEdges((eds) => eds.filter((e) => e.source !== id && e.target !== id));
        try {
            await api.deleteBrainstormCard(id);
            toast.success("Card deleted");
        } catch (error) {
            console.error(error);
        }
    };

    const handleNodeDragStop = async (_: React.MouseEvent, node: Node) => {
        setNodes((nds) => nds.map(n => n.id === node.id ? { ...n, data: { ...n.data, syncState: "syncing" } } : n));
        try {
            const data = node.data as unknown as IdeaCardNodeData;
            await api.saveBrainstormCard({
                text: data.text,
                position_x: node.position.x,
                position_y: node.position.y,
                color: data.color,
                tags: data.tags,
            });
            setNodes((nds) => nds.map(n => n.id === node.id ? { ...n, data: { ...n.data, syncState: "synced" } } : n));
        } catch (error) {
            console.error(error);
            setNodes((nds) => nds.map(n => n.id === node.id ? { ...n, data: { ...n.data, syncState: "error" } } : n));
        }
    };

    // Applying AI Suggestions
    const onApplyEdge = (sourceId: string, targetId: string, label: string) => {
        const newEdge: Edge = {
            id: `suggested-e-${sourceId}-${targetId}`,
            source: sourceId,
            target: targetId,
            label,
            animated: true,
            style: { stroke: "#10b981", strokeWidth: 2, strokeDasharray: "5,5" },
            labelStyle: { fill: "#10b981", fontWeight: 700, fontSize: 12 },
            labelBgStyle: { fill: "#1f2937" },
        };
        setEdges((eds) => [...eds, newEdge]);
        toast.success("Connection added!");
    };

    const onApplyCard = async (text: string, nearCardId: string) => {
        const nearNode = nodes.find(n => n.id === nearCardId);
        const x = nearNode ? nearNode.position.x + 300 : window.innerWidth / 2;
        const y = nearNode ? nearNode.position.y + (Math.random() * 100 - 50) : window.innerHeight / 2;

        const id = crypto.randomUUID();
        const newNode: Node = {
            id,
            type: "ideaCard",
            position: { x, y },
            data: {
                text,
                color: "#10B981", // Emerald for new suggestions
                tags: ["ai-suggested"],
                syncState: "syncing",
                onDelete: handleDeleteCard,
                onChange: handleCardChange,
                onRetry: handleRetryCard,
            },
        };

        setNodes((nds) => [...nds, newNode]);

        if (nearNode) {
            onApplyEdge(nearNode.id, id, "leads to");
        }

        try {
            await api.saveBrainstormCard({
                text,
                position_x: x,
                position_y: y,
                color: "#10B981",
                tags: ["ai-suggested"],
            });
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "synced" } } : n));
            toast.success("Idea added to canvas!");
        } catch (error) {
            console.error(error);
            setNodes((nds) => nds.map(n => n.id === id ? { ...n, data: { ...n.data, syncState: "error" } } : n));
        }
    };

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white overflow-hidden">
            {/* Top Navigation */}
            <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/50 backdrop-blur-md relative z-10 shrink-0">
                <div className="flex items-center gap-3">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-300 transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <div className="w-px h-4 bg-gray-800" />
                    <div className="flex items-center gap-2 text-gray-200">
                        <Lightbulb className="w-4 h-4 text-emerald-400" />
                        <span className="font-semibold text-sm">Brainstorm Canvas</span>
                    </div>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleAddCard}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-gray-200 text-sm font-medium rounded-md transition-colors border border-gray-700"
                    >
                        <Plus className="w-4 h-4" />
                        Add Card
                    </button>
                    <button
                        onClick={handleSuggest}
                        disabled={isSuggesting}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-500 text-sm font-medium rounded-md transition-colors border border-amber-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <Sparkles className="w-4 h-4" />
                        Suggest
                    </button>
                </div>
            </header>

            {/* Canvas Area */}
            <div className="flex-1 relative">
                <ReactFlow
                    nodes={nodes}
                    edges={edges}
                    onNodesChange={onNodesChange}
                    onEdgesChange={onEdgesChange}
                    onConnect={onConnect}
                    onNodeDragStop={handleNodeDragStop}
                    nodeTypes={nodeTypes}
                    fitView
                    className="bg-gray-950"
                    proOptions={{ hideAttribution: true }}
                >
                    <Background color="#1f2937" gap={24} size={2} />
                    <Controls className="!bg-gray-900 !border-gray-800 [&>button]:!bg-gray-900 [&>button]:!border-gray-800 [&>button]:!text-gray-400 [&>button:hover]:!bg-gray-800" />
                    <MiniMap
                        nodeColor={(n) => {
                            const data = n.data as unknown as IdeaCardNodeData;
                            return data.color || "#4F46E5";
                        }}
                        maskColor="rgba(17, 24, 39, 0.8)"
                        className="!bg-gray-900 !border-gray-800 rounded-lg shadow-xl"
                    />
                </ReactFlow>

                <SuggestionPanel
                    suggestion={suggestion}
                    isLoading={isSuggesting}
                    onApplyEdge={onApplyEdge}
                    onApplyCard={onApplyCard}
                    onClose={() => setSuggestion(null)}
                />
            </div>
        </div>
    );
}
