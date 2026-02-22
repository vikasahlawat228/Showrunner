"use client";

import React, { useEffect, useState } from "react";
import { useStudioStore } from "../../lib/store";
import type { ChatSessionSummary } from "../../lib/store/chatSlice";

interface SessionPickerProps {
    isOpen: boolean;
    onClose: () => void;
    onSelect: (sessionId: string) => void;
}

export function SessionPicker({ isOpen, onClose, onSelect }: SessionPickerProps) {
    const {
        chatSessions,
        activeSessionId,
        fetchChatSessions,
        createChatSession,
        deleteSession,
    } = useStudioStore();

    const [filter, setFilter] = useState<"all" | "active" | "ended">("all");

    useEffect(() => {
        if (isOpen) {
            fetchChatSessions();
        }
    }, [isOpen, fetchChatSessions]);

    if (!isOpen) return null;

    const filtered = chatSessions.filter((s) => {
        if (filter === "all") return true;
        return s.state === filter;
    });

    const handleNewSession = async () => {
        const id = await createChatSession();
        if (id) {
            onSelect(id);
            onClose();
        }
    };

    const handleDelete = async (e: React.MouseEvent, sessionId: string) => {
        e.stopPropagation();
        if (confirm("Delete this session and all its messages?")) {
            await deleteSession(sessionId);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
            <div className="bg-gray-900 rounded-lg border border-gray-700 w-[480px] max-h-[600px] flex flex-col shadow-xl">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
                    <h2 className="text-sm font-semibold text-gray-100">Chat Sessions</h2>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleNewSession}
                            className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs rounded transition-colors"
                        >
                            New Session
                        </button>
                        <button
                            onClick={onClose}
                            className="p-1.5 text-gray-400 hover:text-gray-200 rounded hover:bg-gray-800"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                {/* Filter tabs */}
                <div className="flex gap-1 px-4 py-2 border-b border-gray-800">
                    {(["all", "active", "ended"] as const).map((f) => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`px-2 py-1 text-xs rounded transition-colors ${filter === f
                                    ? "bg-blue-600 text-white"
                                    : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
                                }`}
                        >
                            {f.charAt(0).toUpperCase() + f.slice(1)}
                        </button>
                    ))}
                </div>

                {/* Session list */}
                <div className="flex-1 overflow-y-auto p-2">
                    {filtered.length === 0 ? (
                        <div className="text-center text-gray-500 text-sm py-8">
                            No sessions found
                        </div>
                    ) : (
                        <div className="space-y-1">
                            {filtered.map((session) => (
                                <SessionRow
                                    key={session.id}
                                    session={session}
                                    isActive={session.id === activeSessionId}
                                    onSelect={() => {
                                        onSelect(session.id);
                                        onClose();
                                    }}
                                    onDelete={(e) => handleDelete(e, session.id)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function SessionRow({
    session,
    isActive,
    onSelect,
    onDelete,
}: {
    session: ChatSessionSummary;
    isActive: boolean;
    onSelect: () => void;
    onDelete: (e: React.MouseEvent) => void;
}) {
    const stateColors: Record<string, string> = {
        active: "text-green-400",
        compacted: "text-yellow-400",
        ended: "text-gray-500",
    };

    return (
        <button
            onClick={onSelect}
            className={`w-full text-left p-3 rounded-lg transition-colors group ${isActive
                    ? "bg-blue-600/20 border border-blue-600/40"
                    : "hover:bg-gray-800 border border-transparent"
                }`}
        >
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-100">{session.name}</span>
                    <span className={`text-xs ${stateColors[session.state] || "text-gray-400"}`}>
                        {session.state}
                    </span>
                </div>
                <button
                    onClick={onDelete}
                    className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 text-xs transition-opacity"
                    title="Delete session"
                >
                    ✕
                </button>
            </div>

            <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                <span>{session.message_count} messages</span>
                <span>{new Date(session.updated_at).toLocaleDateString()}</span>
            </div>

            {session.last_message_preview && (
                <div className="text-xs text-gray-500 mt-1 truncate">
                    {session.last_message_preview}
                </div>
            )}

            {session.tags.length > 0 && (
                <div className="flex gap-1 mt-1.5">
                    {session.tags.map((tag) => (
                        <span
                            key={tag}
                            className="text-xs bg-gray-700 text-gray-300 px-1.5 py-0.5 rounded"
                        >
                            {tag}
                        </span>
                    ))}
                </div>
            )}
        </button>
    );
}
