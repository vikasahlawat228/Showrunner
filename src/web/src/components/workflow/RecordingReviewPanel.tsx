"use client";

import React, { useState } from "react";
import { useRecorderStore, type RecordedAction } from "@/lib/store/recorderSlice";
import { api } from "@/lib/api";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import {
    X,
    Trash2,
    Loader2,
    Workflow,
    Zap,
    MessageSquare,
    CheckCircle2,
    MousePointerClick,
    Save,
    AtSign,
    ListChecks,
    ArrowRight,
} from "lucide-react";

const ACTION_ICONS: Record<string, React.ReactNode> = {
    slash_command: <Zap className="w-4 h-4 text-yellow-400" />,
    chat_message: <MessageSquare className="w-4 h-4 text-blue-400" />,
    approval: <CheckCircle2 className="w-4 h-4 text-green-400" />,
    text_selection: <MousePointerClick className="w-4 h-4 text-purple-400" />,
    option_select: <ListChecks className="w-4 h-4 text-cyan-400" />,
    save: <Save className="w-4 h-4 text-emerald-400" />,
    entity_mention: <AtSign className="w-4 h-4 text-pink-400" />,
};

const ACTION_LABELS: Record<string, string> = {
    slash_command: "Slash Command",
    chat_message: "Chat Message",
    approval: "Approval",
    text_selection: "Text Selection",
    option_select: "Option Select",
    save: "Save",
    entity_mention: "Entity Mention",
};

function formatTimestamp(ts: number): string {
    return new Date(ts).toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

export function RecordingReviewPanel() {
    const router = useRouter();
    const {
        actions,
        recordingName,
        setRecordingName,
        removeAction,
        clearRecording,
        showReviewPanel,
        setShowReviewPanel,
        isCompiling,
        setIsCompiling,
    } = useRecorderStore();

    const handleDiscard = () => {
        clearRecording();
        setShowReviewPanel(false);
    };

    const handleCompile = async () => {
        if (actions.length === 0) {
            toast.error("No actions to compile");
            return;
        }

        setIsCompiling(true);
        toast.loading("Compiling pipeline from recorded actions...", { id: "distill" });

        try {
            const result = await api.distillRecordedActions({
                title: recordingName || `Recorded Workflow`,
                actions: actions.map((a) => ({
                    type: a.type,
                    description: a.description,
                    payload: a.payload,
                })),
            });

            toast.success("Pipeline compiled successfully!", { id: "distill" });
            clearRecording();
            setShowReviewPanel(false);

            // Navigate to pipeline builder with the new definition
            router.push(`/pipelines?def=${result.id}`);
        } catch (err: any) {
            toast.error("Failed to compile pipeline", {
                id: "distill",
                description: err.message || "Unknown error",
            });
        } finally {
            setIsCompiling(false);
        }
    };

    if (!showReviewPanel) return null;

    return (
        <div className="fixed inset-0 z-[60] bg-black/60 backdrop-blur-sm flex items-center justify-center">
            <div
                className="bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-lg mx-4 flex flex-col max-h-[80vh]"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-indigo-600/20">
                            <Workflow className="w-5 h-5 text-indigo-400" />
                        </div>
                        <div>
                            <h2 className="text-sm font-semibold text-white">Compile Recorded Workflow</h2>
                            <p className="text-xs text-gray-500 mt-0.5">
                                {actions.length} action{actions.length !== 1 ? "s" : ""} recorded
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setShowReviewPanel(false)}
                        className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-lg transition-colors"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>

                {/* Pipeline name */}
                <div className="px-6 py-3 border-b border-gray-800/60">
                    <label className="block text-xs text-gray-500 mb-1.5 font-medium">Pipeline Name</label>
                    <input
                        type="text"
                        value={recordingName}
                        onChange={(e) => setRecordingName(e.target.value)}
                        className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500/30 transition-colors"
                        placeholder="My Workflow Pipeline"
                    />
                </div>

                {/* Actions list */}
                <div className="flex-1 overflow-y-auto px-6 py-3 space-y-2">
                    {actions.length === 0 ? (
                        <div className="text-center text-gray-600 text-sm py-8">
                            No actions recorded. Start recording and use AI features to capture your workflow.
                        </div>
                    ) : (
                        actions.map((action, index) => (
                            <div
                                key={action.id}
                                className="group flex items-start gap-3 p-3 rounded-xl bg-gray-800/50 border border-gray-800 hover:border-gray-700 transition-colors"
                            >
                                {/* Step number + icon */}
                                <div className="flex flex-col items-center gap-1 pt-0.5">
                                    <span className="text-[10px] font-mono text-gray-600">{index + 1}</span>
                                    {ACTION_ICONS[action.type] || <Zap className="w-4 h-4 text-gray-500" />}
                                </div>

                                {/* Content */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs font-semibold text-gray-300">
                                            {ACTION_LABELS[action.type] || action.type}
                                        </span>
                                        <span className="text-[10px] text-gray-600 font-mono">
                                            {formatTimestamp(action.timestamp)}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-0.5 truncate">{action.description}</p>
                                    {action.payload.command && (
                                        <span className="inline-block mt-1 px-1.5 py-0.5 rounded bg-gray-700/50 text-[10px] font-mono text-indigo-300">
                                            /{action.payload.command}
                                        </span>
                                    )}
                                </div>

                                {/* Remove button */}
                                <button
                                    onClick={() => removeAction(action.id)}
                                    className="p-1 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all rounded hover:bg-gray-700"
                                    title="Remove action"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>

                                {/* Arrow connector (except last) */}
                                {index < actions.length - 1 && (
                                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2">
                                        <ArrowRight className="w-3 h-3 text-gray-700 rotate-90" />
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-gray-800">
                    <button
                        onClick={handleDiscard}
                        disabled={isCompiling}
                        className="px-4 py-2 text-xs font-medium text-gray-500 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                    >
                        Discard
                    </button>
                    <button
                        onClick={handleCompile}
                        disabled={isCompiling || actions.length === 0}
                        className="flex items-center gap-2 px-5 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50 disabled:hover:bg-indigo-600 shadow-lg shadow-indigo-600/20"
                    >
                        {isCompiling ? (
                            <>
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                Compiling...
                            </>
                        ) : (
                            <>
                                <Workflow className="w-3.5 h-3.5" />
                                Compile to Pipeline
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
