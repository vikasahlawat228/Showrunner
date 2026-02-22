"use client";

import React, { useEffect, useRef, useCallback } from "react";
import { useStudioStore } from "../../lib/store";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TokenIndicator } from "./TokenIndicator";
import { ApprovalBanner, ApprovalData } from "./ApprovalBanner";
import { useChatStream } from "../../hooks/useChatStream";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useZenStore } from "../../lib/store/zenSlice";
import { PlanViewer } from "./PlanViewer";

interface ChatSidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

export function ChatSidebar({ isOpen, onClose }: ChatSidebarProps) {
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const {
        chatSessions,
        activeSessionId,
        chatMessages,
        isStreaming,
        streamingContent,
        chatError,
        fetchChatSessions,
        createChatSession,
        setActiveSession,
        loadMessages,
        appendToken,
        addActionTrace,
        addArtifact,
        completeMessage,
        setStreaming,
        clearStreamingContent,
        setChatError,
        deleteSession,
        pendingApproval,
        setPendingApproval,
        backgroundStatus,
        setBackgroundStatus,
    } = useStudioStore();

    // Fetch sessions on mount
    useEffect(() => {
        if (isOpen) {
            fetchChatSessions();
        }
    }, [isOpen, fetchChatSessions]);

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [chatMessages, streamingContent]);

    // SSE stream hook
    const { sendMessage, abort } = useChatStream({
        onToken: (text) => {
            appendToken(text);
        },
        onActionTrace: (trace) => {
            addActionTrace(trace);
        },
        onArtifact: (artifact) => {
            addArtifact(artifact);
        },
        onApprovalNeeded: (data) => {
            setPendingApproval(data);
        },
        onBackgroundUpdate: (data) => {
            let msg = "Running...";
            if (data.step && data.status) {
                msg = `Step ${data.step}: ${data.status}`;
            } else if (data.status) {
                msg = String(data.status);
            }
            setBackgroundStatus(msg);
        },
        onComplete: (data) => {
            // Add the completed assistant message to the list
            const assistantMessage = {
                id: data.message_id,
                session_id: data.session_id,
                role: "assistant" as const,
                content: streamingContent,
                action_traces: [],
                artifacts: [],
                mentioned_entity_ids: [],
                created_at: new Date().toISOString(),
            };
            completeMessage(assistantMessage);
            setStreaming(false);
            setBackgroundStatus(null);

            // Reload messages from server for accuracy
            if (activeSessionId) {
                loadMessages(activeSessionId);
            }
        },
        onError: (error) => {
            setChatError(error);
            setStreaming(false);
        },
    });

    const handleSend = useCallback(
        async (content: string, mentionedEntityIds: string[]) => {
            // Build context payload if in Zen Mode
            const { editorContent } = useZenStore.getState();
            const contextPayload = window.location.pathname.startsWith('/zen') && editorContent
                ? { current_text_buffer: editorContent }
                : undefined;

            if (!activeSessionId) {
                // Create a new session first
                const newId = await createChatSession();
                if (!newId) return;
                // Add user message locally
                const userMsg = {
                    id: crypto.randomUUID(),
                    session_id: newId,
                    role: "user" as const,
                    content,
                    action_traces: [],
                    artifacts: [],
                    mentioned_entity_ids: mentionedEntityIds,
                    created_at: new Date().toISOString(),
                };
                completeMessage(userMsg);
                setStreaming(true);
                clearStreamingContent();
                sendMessage(newId, content, mentionedEntityIds, contextPayload);
                return;
            }

            // Add user message locally
            const userMsg = {
                id: crypto.randomUUID(),
                session_id: activeSessionId,
                role: "user" as const,
                content,
                action_traces: [],
                artifacts: [],
                mentioned_entity_ids: mentionedEntityIds,
                created_at: new Date().toISOString(),
            };
            completeMessage(userMsg);
            setStreaming(true);
            clearStreamingContent();
            sendMessage(activeSessionId, content, mentionedEntityIds, contextPayload);
        },
        [activeSessionId, createChatSession, completeMessage, setStreaming, clearStreamingContent, sendMessage]
    );

    if (!isOpen) return null;

    return (
        <div className="fixed right-0 top-0 h-full w-96 bg-gray-900 border-l border-gray-700 flex flex-col z-50 shadow-xl">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700">
                <div className="flex flex-col gap-1 w-2/3">
                    <div className="flex items-center gap-2">
                        <h2 className="text-sm font-semibold text-gray-100">Chat</h2>
                        {activeSessionId && (
                            <span className="text-xs text-gray-400 truncate">
                                {chatSessions.find((s) => s.id === activeSessionId)?.name || ""}
                            </span>
                        )}
                    </div>
                    {activeSessionId && (
                        <TokenIndicator session={chatSessions.find((s) => s.id === activeSessionId)!} />
                    )}
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={() => createChatSession()}
                        className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded transition-colors"
                        title="New chat"
                    >
                        +
                    </button>
                    <button
                        onClick={onClose}
                        className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded transition-colors"
                    >
                        ✕
                    </button>
                </div>
            </div>

            {/* Session picker (when no active session) */}
            {!activeSessionId && chatSessions.length > 0 && (
                <div className="flex-1 overflow-y-auto p-3 space-y-2">
                    <p className="text-xs text-gray-400 mb-2">Select a conversation or start a new one</p>
                    {chatSessions.map((session) => (
                        <button
                            key={session.id}
                            onClick={() => setActiveSession(session.id)}
                            className="w-full text-left p-3 bg-gray-800 hover:bg-gray-750 rounded-lg transition-colors"
                        >
                            <div className="text-sm font-medium text-gray-100">{session.name}</div>
                            <div className="text-xs text-gray-400 mt-1">
                                {session.message_count} messages · {session.state}
                            </div>
                            {session.last_message_preview && (
                                <div className="text-xs text-gray-500 mt-1 truncate">
                                    {session.last_message_preview}
                                </div>
                            )}
                        </button>
                    ))}
                </div>
            )}

            {/* Messages */}
            {(activeSessionId || chatSessions.length === 0) && (
                <>
                    <div className="flex-1 overflow-y-auto p-3">
                        {chatMessages.length === 0 && !isStreaming && (
                            <div className="text-center text-gray-500 text-sm mt-8">
                                Start a conversation about your project.
                                <br />
                                Use @mentions to reference entities.
                            </div>
                        )}

                        {chatMessages.map((msg) => (
                            <ChatMessage key={msg.id} message={msg} onSend={(text) => handleSend(text, [])} />
                        ))}

                        {/* Streaming content */}
                        {isStreaming && streamingContent && (
                            <div className="flex justify-start mb-3">
                                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-800 text-gray-100">
                                    {streamingContent.includes("## Plan:") ? (
                                        <PlanViewer content={streamingContent} onSend={(text) => handleSend(text, [])} />
                                    ) : (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {streamingContent + " ▊"}
                                            </ReactMarkdown>
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Error display */}
                        {chatError && (
                            <div className="p-2 bg-red-900/30 border border-red-700 rounded text-red-300 text-xs mb-2">
                                {chatError}
                                <button
                                    onClick={() => setChatError(null)}
                                    className="ml-2 text-red-400 hover:text-red-200"
                                >
                                    ✕
                                </button>
                            </div>
                        )}

                        <div ref={messagesEndRef} />
                    </div>

                    {/* Pending Approval Banner */}
                    {pendingApproval && (
                        <div className="px-3 pb-2 flex-shrink-0">
                            <ApprovalBanner
                                data={pendingApproval}
                                onApprove={() => {
                                    setPendingApproval(null);
                                    handleSend(`Approve action ${pendingApproval.intent}`, []);
                                }}
                                onReject={() => {
                                    setPendingApproval(null);
                                    handleSend("Reject action", []);
                                }}
                            />
                        </div>
                    )}

                    {/* Background Progress Indicator */}
                    {backgroundStatus && (
                        <div className="px-3 pb-2 flex-shrink-0">
                            <div className="flex items-center gap-2 bg-indigo-900/30 border border-indigo-700/50 rounded-lg p-2 shadow-inner">
                                <span className="flex h-2 w-2 relative">
                                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                                    <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                                </span>
                                <span className="text-xs font-mono text-indigo-300 truncate">
                                    {backgroundStatus}
                                </span>
                            </div>
                        </div>
                    )}

                    {/* Input */}
                    <ChatInput
                        onSend={handleSend}
                        disabled={!activeSessionId && chatSessions.length > 0}
                        isStreaming={isStreaming}
                        onAbort={abort}
                    />
                </>
            )}
        </div>
    );
}
