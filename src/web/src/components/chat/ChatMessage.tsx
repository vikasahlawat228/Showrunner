"use client";

import React, { useState } from "react";
import { useStudioStore } from "@/lib/store";
import type { ChatMessage as ChatMessageType, ChatActionTrace, ChatArtifact } from "../../lib/store/chatSlice";
import { PlanViewer } from "./PlanViewer";
import { PipelineRunViewer } from "./PipelineRunViewer";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
    message: ChatMessageType;
    onSend?: (message: string) => void;
}

export function ChatMessage({ message, onSend }: ChatMessageProps) {
    const isUser = message.role === "user";
    const isSystem = message.role === "system";

    return (
        <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-3`}>
            <div
                className={`max-w-[80%] rounded-lg px-4 py-2 ${isUser
                    ? "bg-blue-600 text-white"
                    : isSystem
                        ? "bg-gray-700 text-gray-300 text-sm italic"
                        : "bg-gray-800 text-gray-100"
                    }`}
            >
                {/* Message content */}
                {message.content.includes("## Plan:") ? (
                    <PlanViewer content={message.content} onSend={onSend} />
                ) : isUser ? (
                    <div className="whitespace-pre-wrap text-sm">{message.content}</div>
                ) : (
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                )}

                {/* Action traces (Glass Box) */}
                {message.action_traces.length > 0 && (
                    <div className="mt-2 border-t border-gray-600 pt-2 space-y-1">
                        {message.action_traces.filter(t => !t.parent_id).map((trace, i) => (
                            <ActionTraceBlock key={trace.id || i} trace={trace} allTraces={message.action_traces} depth={0} />
                        ))}
                    </div>
                )}

                {/* Artifacts */}
                {message.artifacts.length > 0 && (
                    <div className="mt-2 space-y-1 w-full">
                        {message.artifacts.map((artifact, i) => (
                            <ArtifactCard key={i} artifact={artifact} />
                        ))}
                    </div>
                )}

                {/* Timestamp */}
                <div className="mt-1 text-xs opacity-50">
                    {new Date(message.created_at).toLocaleTimeString()}
                </div>
            </div>
        </div>
    );
}

export function ActionTraceBlock({ trace, allTraces = [], depth = 0 }: { trace: ChatActionTrace; allTraces?: ChatActionTrace[]; depth?: number }) {
    const [expanded, setExpanded] = useState(false);
    const [showPrompt, setShowPrompt] = useState(false);
    const [showRawJson, setShowRawJson] = useState(false);

    // Filter children 
    const children = allTraces.filter(t => t.parent_id === trace.id && t.parent_id != null);

    return (
        <div className="text-xs text-gray-400" style={{ marginLeft: `${depth * 8}px` }}>
            <div className="flex items-center gap-1 group">
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex flex-1 items-center gap-1 hover:text-gray-200 transition-colors text-left"
                >
                    <span className={`transform ${expanded ? "rotate-90" : ""} transition-transform w-3 inline-block text-center`}>
                        ▶
                    </span>
                    <span className="font-mono">{trace.tool_name}</span>
                    {trace.duration_ms > 0 && (
                        <span className="text-gray-500">({trace.duration_ms}ms)</span>
                    )}
                </button>
            </div>
            {expanded && (
                <div className="ml-4 mt-1 mb-2 space-y-1 border-l border-gray-700 pl-2">
                    {trace.context_summary && <div>{trace.context_summary}</div>}
                    {trace.containers_used?.length > 0 && (
                        <div>Containers: {trace.containers_used.join(", ")}</div>
                    )}
                    {trace.result_preview && (
                        <div className="text-gray-500 truncate">{trace.result_preview}</div>
                    )}

                    {/* Glass Box Detail Toggles */}
                    <div className="flex gap-2 mt-2 mb-1">
                        {trace.prompt && (
                            <button onClick={() => setShowPrompt(!showPrompt)} className="px-2 py-0.5 bg-gray-800 rounded border border-gray-600 hover:bg-gray-700 transition">
                                {showPrompt ? "Hide Prompt" : "Show Prompt"}
                            </button>
                        )}
                        {trace.raw_json && (
                            <button onClick={() => setShowRawJson(!showRawJson)} className="px-2 py-0.5 bg-gray-800 rounded border border-gray-600 hover:bg-gray-700 transition">
                                {showRawJson ? "Hide Payload" : "Show Payload"}
                            </button>
                        )}
                    </div>

                    {showPrompt && trace.prompt && (
                        <div className="mt-1 p-2 bg-gray-900 rounded border border-gray-700 font-mono text-[10px] whitespace-pre-wrap overflow-x-auto text-gray-300">
                            {trace.prompt}
                        </div>
                    )}
                    {showRawJson && trace.raw_json && (
                        <div className="mt-1 p-2 bg-gray-900 rounded border border-gray-700 font-mono text-[10px] whitespace-pre-wrap overflow-x-auto text-green-400">
                            {trace.raw_json}
                        </div>
                    )}

                    {/* Render Children Recursively */}
                    {children.length > 0 && (
                        <div className="mt-2 space-y-1 pt-1 border-t border-gray-800">
                            {children.map((child, i) => (
                                <ActionTraceBlock key={child.id || i} trace={child} allTraces={allTraces} depth={0} />
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export function ArtifactCard({ artifact }: { artifact: ChatArtifact }) {
    const { setActivePreviewArtifact } = useStudioStore();

    if (artifact.artifact_type === 'pipeline_run') {
        let runId = "";
        try {
            runId = JSON.parse(artifact.content).run_id;
        } catch {
            runId = artifact.content;
        }
        return <PipelineRunViewer runId={runId} title={artifact.title} />;
    }

    const typeIcons: Record<string, string> = {
        prose: "📝",
        outline: "📋",
        schema: "🗂️",
        panel: "🖼️",
        diff: "📊",
        table: "📊",
        yaml: "📄",
    };

    return (
        <div className="border border-gray-600 rounded p-2 bg-gray-900 group transition-colors hover:border-indigo-500/50">
            <button
                onClick={() => setActivePreviewArtifact(artifact)}
                className="flex items-center gap-2 w-full text-left hover:text-white"
            >
                <span>{typeIcons[artifact.artifact_type] || "📄"}</span>
                <span className="text-sm font-medium transition-colors group-hover:text-indigo-300 pointer-events-none truncate">{artifact.title}</span>
                {artifact.is_saved && (
                    <span className="text-green-400 text-xs ml-auto shrink-0">✓ saved</span>
                )}
            </button>
        </div>
    );
}
