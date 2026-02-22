"use client";

import React, { useState } from "react";
import type { ChatArtifact } from "../../lib/store/chatSlice";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ArtifactPreviewProps {
    artifact: ChatArtifact;
    onAccept?: (artifact: ChatArtifact) => void;
    onReject?: (artifact: ChatArtifact) => void;
}

export function ArtifactPreview({ artifact, onAccept, onReject }: ArtifactPreviewProps) {
    const [viewMode, setViewMode] = useState<"preview" | "raw">("preview");

    return (
        <div className="border border-gray-600 rounded-lg bg-gray-900 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
                <div className="flex items-center gap-2">
                    <span className="text-sm">{getTypeIcon(artifact.artifact_type)}</span>
                    <span className="text-sm font-medium text-gray-100">{artifact.title}</span>
                    <span className="text-xs text-gray-400 bg-gray-700 px-1.5 py-0.5 rounded">
                        {artifact.artifact_type}
                    </span>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => setViewMode(viewMode === "preview" ? "raw" : "preview")}
                        className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-700"
                    >
                        {viewMode === "preview" ? "Raw" : "Preview"}
                    </button>
                </div>
            </div>

            {/* Content */}
            <div className="p-4 max-h-96 overflow-auto">
                {viewMode === "preview" ? (
                    <PreviewContent artifact={artifact} />
                ) : (
                    <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono">
                        {artifact.content}
                    </pre>
                )}
            </div>

            {/* Action buttons (approval gate) */}
            {!artifact.is_saved && (onAccept || onReject) && (
                <div className="flex items-center gap-2 px-4 py-2 border-t border-gray-700 bg-gray-850">
                    {onAccept && (
                        <button
                            onClick={() => onAccept(artifact)}
                            className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs rounded transition-colors"
                        >
                            Accept & Save
                        </button>
                    )}
                    {onReject && (
                        <button
                            onClick={() => onReject(artifact)}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition-colors"
                        >
                            Reject
                        </button>
                    )}
                    {artifact.container_id && (
                        <span className="text-xs text-gray-500 ml-auto">
                            Target: {artifact.container_id}
                        </span>
                    )}
                </div>
            )}

            {artifact.is_saved && (
                <div className="px-4 py-1.5 border-t border-gray-700 bg-gray-850">
                    <span className="text-xs text-green-400">Saved to project</span>
                </div>
            )}
        </div>
    );
}

function PreviewContent({ artifact }: { artifact: ChatArtifact }) {
    switch (artifact.artifact_type) {
        case "prose":
            return (
                <div className="text-sm text-gray-200 leading-relaxed min-h-[4rem]">
                    <div className="prose prose-invert prose-sm max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {artifact.content}
                        </ReactMarkdown>
                    </div>
                </div>
            );

        case "outline":
            return (
                <div className="text-sm text-gray-200 space-y-1">
                    {artifact.content.split("\n").map((line, i) => {
                        const indent = line.search(/\S/);
                        const isHeader = line.trim().startsWith("#");
                        return (
                            <div
                                key={i}
                                style={{ paddingLeft: `${Math.max(0, indent) * 8}px` }}
                                className={isHeader ? "font-semibold text-blue-300 mt-2" : ""}
                            >
                                {line.trim()}
                            </div>
                        );
                    })}
                </div>
            );

        case "diff":
            return (
                <pre className="text-xs font-mono">
                    {artifact.content.split("\n").map((line, i) => {
                        const color = line.startsWith("+")
                            ? "text-green-400"
                            : line.startsWith("-")
                                ? "text-red-400"
                                : line.startsWith("@")
                                    ? "text-blue-400"
                                    : "text-gray-300";
                        return (
                            <div key={i} className={color}>
                                {line}
                            </div>
                        );
                    })}
                </pre>
            );

        case "yaml":
        case "schema":
            return (
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono bg-gray-950 p-3 rounded">
                    {artifact.content}
                </pre>
            );

        case "table":
            return (
                <div className="text-xs text-gray-300 font-mono whitespace-pre">
                    {artifact.content}
                </div>
            );

        default:
            return <pre className="text-xs text-gray-300 whitespace-pre-wrap">{artifact.content}</pre>;
    }
}

function getTypeIcon(type: string): string {
    const icons: Record<string, string> = {
        prose: "📝",
        outline: "📋",
        schema: "🗂️",
        panel: "🖼️",
        diff: "📊",
        table: "📊",
        yaml: "📄",
    };
    return icons[type] || "📄";
}
