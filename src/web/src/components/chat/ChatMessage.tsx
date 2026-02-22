"use client";

import React, { useState } from "react";
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
                    <div className="mt-2 border-t border-gray-600 pt-2">
                        {message.action_traces.map((trace, i) => (
                            <ActionTraceBlock key={i} trace={trace} />
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

function ActionTraceBlock({ trace }: { trace: ChatActionTrace }) {
    const [expanded, setExpanded] = useState(false);

    return (
        <div className="text-xs text-gray-400">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-1 hover:text-gray-200 transition-colors"
            >
                <span className={`transform ${expanded ? "rotate-90" : ""} transition-transform`}>
                    ▶
                </span>
                <span className="font-mono">{trace.tool_name}</span>
                {trace.duration_ms > 0 && (
                    <span className="text-gray-500">({trace.duration_ms}ms)</span>
                )}
            </button>
            {expanded && (
                <div className="ml-4 mt-1 space-y-0.5">
                    {trace.context_summary && <div>{trace.context_summary}</div>}
                    {trace.containers_used.length > 0 && (
                        <div>Containers: {trace.containers_used.join(", ")}</div>
                    )}
                    {trace.result_preview && (
                        <div className="text-gray-500 truncate">{trace.result_preview}</div>
                    )}
                </div>
            )}
        </div>
    );
}

function ArtifactCard({ artifact }: { artifact: ChatArtifact }) {
    const [expanded, setExpanded] = useState(false);

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
        <div className="border border-gray-600 rounded p-2 bg-gray-900">
            <button
                onClick={() => setExpanded(!expanded)}
                className="flex items-center gap-2 w-full text-left hover:text-gray-200"
            >
                <span>{typeIcons[artifact.artifact_type] || "📄"}</span>
                <span className="text-sm font-medium">{artifact.title}</span>
                {artifact.is_saved && (
                    <span className="text-green-400 text-xs">✓ saved</span>
                )}
            </button>
            {expanded && (
                <pre className="mt-2 text-xs text-gray-300 overflow-auto max-h-48 bg-gray-950 p-2 rounded">
                    {artifact.content}
                </pre>
            )}
        </div>
    );
}
