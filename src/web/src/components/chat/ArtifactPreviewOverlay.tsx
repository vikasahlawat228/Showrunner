"use client";

import { useStudioStore } from "@/lib/store";
import { X, Copy, Check, Download, MousePointerSquareDashed } from "lucide-react";
import { useState } from "react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export function ArtifactPreviewOverlay() {
    const { activePreviewArtifact, setActivePreviewArtifact } = useStudioStore();
    const [copied, setCopied] = useState(false);

    if (!activePreviewArtifact) return null;

    const handleCopy = () => {
        navigator.clipboard.writeText(activePreviewArtifact.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const isMarkdown = ["prose", "outline"].includes(activePreviewArtifact.artifact_type);
    const isCode = ["schema", "yaml"].includes(activePreviewArtifact.artifact_type);

    return (
        <div className="absolute inset-4 z-40 flex flex-col bg-gray-900 border border-gray-700 shadow-2xl rounded-xl overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300 pointer-events-auto">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700 shrink-0">
                <div className="flex items-center gap-3">
                    <div className="bg-indigo-500/20 p-1.5 rounded-lg border border-indigo-500/30">
                        <MousePointerSquareDashed className="w-4 h-4 text-indigo-400" />
                    </div>
                    <div>
                        <h3 className="font-semibold text-gray-100 leading-tight">
                            {activePreviewArtifact.title}
                        </h3>
                        <p className="text-xs text-gray-400 uppercase tracking-wider font-mono">
                            {activePreviewArtifact.artifact_type} generated
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={handleCopy}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-400 hover:text-gray-100 hover:bg-gray-700 rounded transition"
                    >
                        {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        {copied ? "Copied" : "Copy"}
                    </button>
                    {/* Future: Add 'Commit to Scene' functionality here */}
                    <div className="w-px h-4 bg-gray-600 mx-1"></div>
                    <button
                        onClick={() => setActivePreviewArtifact(null)}
                        className="p-1.5 text-gray-400 hover:text-white hover:bg-red-500/20 rounded transition"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 bg-gray-950/50">
                {isCode ? (
                    <pre className="text-sm text-gray-300 font-mono whitespace-pre-wrap">
                        {activePreviewArtifact.content}
                    </pre>
                ) : isMarkdown ? (
                    <div className="prose prose-invert prose-indigo max-w-3xl mx-auto">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {activePreviewArtifact.content}
                        </ReactMarkdown>
                    </div>
                ) : (
                    <div className="text-gray-300 whitespace-pre-wrap">
                        {activePreviewArtifact.content}
                    </div>
                )}
            </div>
        </div>
    );
}
