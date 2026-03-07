"use client";

import React, { useEffect, useRef, useCallback, useState } from "react";
import { useStudioStore } from "../../lib/store";
import { ChatMessage, ActionTraceBlock, ArtifactCard } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { TokenIndicator } from "./TokenIndicator";
import { ApprovalBanner, ApprovalData } from "./ApprovalBanner";
import { WelcomeBackBanner } from "./WelcomeBackBanner";
import { useChatStream } from "../../hooks/useChatStream";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useZenStore } from "@/lib/store/zenSlice";
import { Sparkles } from "lucide-react";

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
        streamingTraces,
        streamingArtifacts,
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

    // Welcome-back banner state
    const [welcomeBack, setWelcomeBack] = useState<{ daysSince: number; summary: string } | null>(null);

    // Detect stale sessions when switching active session
    useEffect(() => {
        if (!activeSessionId) {
            setWelcomeBack(null);
            return;
        }
        const session = chatSessions.find((s) => s.id === activeSessionId);
        if (!session) return;
        const updatedAt = new Date(session.updated_at).getTime();
        const hoursSince = (Date.now() - updatedAt) / (1000 * 60 * 60);
        if (hoursSince > 24) {
            setWelcomeBack({
                daysSince: Math.floor(hoursSince / 24),
                summary: session.last_message_preview || "",
            });
        } else {
            setWelcomeBack(null);
        }
    }, [activeSessionId, chatSessions]);

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
            const { editorContent, activeSceneId, activeChapterId, detectedEntities } = useZenStore.getState();
            const isZen = window.location.pathname.startsWith('/zen');

            const contextPayload = isZen
                ? {
                    zen_context: {
                        scene_id: activeSceneId,
                        chapter_id: activeChapterId,
                        current_text: editorContent?.slice(0, 2000),
                        entities: detectedEntities.map(e => e.container_name)
                    }
                }
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
            setWelcomeBack(null); // dismiss banner on send



            sendMessage(activeSessionId, content, mentionedEntityIds, contextPayload);
        },
        [activeSessionId, createChatSession, completeMessage, setStreaming, clearStreamingContent, sendMessage]
    );

    // Listen for custom external chat injections (e.g., from OnboardingWizard)
    useEffect(() => {
        const handleInject = (e: CustomEvent<{ message: string }>) => {
            useStudioStore.getState().setChatSidebarOpen(true);
            // Delay slightly to allow sidebar transition
            setTimeout(() => {
                handleSend(e.detail.message, []);
            }, 300);
        };
        window.addEventListener('chat:inject', handleInject as EventListener);
        return () => window.removeEventListener('chat:inject', handleInject as EventListener);
    }, [handleSend]);

    if (!isOpen) return null;

    return (
        <div className="w-[400px] flex-shrink-0 bg-gray-900 border-l border-gray-700 flex flex-col z-40 shadow-xl h-full">
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
                        {/* Welcome-back banner */}
                        {welcomeBack && (
                            <WelcomeBackBanner
                                daysSince={welcomeBack.daysSince}
                                summary={welcomeBack.summary}
                                onDismiss={() => setWelcomeBack(null)}
                                onCatchUp={() => {
                                    setWelcomeBack(null);
                                    handleSend("/plan catch-up", []);
                                }}
                            />
                        )}

                        {chatMessages.length === 0 && !isStreaming && !welcomeBack && (
                            <div className="flex flex-col items-center justify-center mt-12 mb-8 px-4 w-full">
                                <div className="w-12 h-12 bg-indigo-500/10 rounded-full flex items-center justify-center mb-4 border border-indigo-500/20">
                                    <Sparkles className="w-6 h-6 text-indigo-400" />
                                </div>
                                <h3 className="text-gray-200 font-medium mb-2">How can I help?</h3>
                                <p className="text-center text-gray-500 text-sm mb-6">
                                    Start a conversation or use one of these quick actions.
                                </p>
                                <div className="flex flex-col gap-2 w-full max-w-[280px]">
                                    {[
                                        { label: "Create a new Character", prompt: "/plan Create a new character" },
                                        { label: "Outline act 1", prompt: "/plan Outline act 1" },
                                        { label: "Review continuity", prompt: "/review Check recent scenes for continuity" }
                                    ].map((action, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleSend(action.prompt, [])}
                                            className="px-4 py-2.5 bg-gray-800/50 hover:bg-gray-700/80 text-gray-300 text-sm rounded-lg transition-all border border-gray-700/50 hover:border-indigo-500/30 flex items-center justify-between group shadow-sm bg-gradient-to-br from-gray-800/50 to-gray-900/50 hover:from-gray-700/50 hover:to-gray-800/50"
                                        >
                                            <span>{action.label}</span>
                                            <span className="opacity-0 group-hover:opacity-100 text-indigo-400 transition-opacity text-lg leading-none transform group-hover:translate-x-1 duration-200">→</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {chatMessages.map((msg) => (
                            <ChatMessage key={msg.id} message={msg} onSend={(text) => handleSend(text, [])} />
                        ))}

                        {/* Streaming content */}
                        {isStreaming && (streamingContent || streamingTraces.length > 0 || streamingArtifacts.length > 0) && (
                            <div className="flex justify-start mb-3">
                                <div className="max-w-[80%] rounded-lg px-4 py-2 bg-gray-800 text-gray-100 w-full">
                                    {streamingContent.includes("## Plan:") ? (
                                        <PlanViewer content={streamingContent} onSend={(text) => handleSend(text, [])} />
                                    ) : streamingContent ? (
                                        <div className="prose prose-invert prose-sm max-w-none">
                                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                {streamingContent + " ▊"}
                                            </ReactMarkdown>
                                        </div>
                                    ) : (
                                        <div className="text-gray-500 text-sm italic mb-2">Thinking... ▊</div>
                                    )}

                                    {/* Action traces (Glass Box) */}
                                    {streamingTraces.length > 0 && (
                                        <div className="mt-2 border-t border-gray-600 pt-2 space-y-1">
                                            {streamingTraces.map((trace: any, i: number) => (
                                                <ActionTraceBlock key={i} trace={trace} />
                                            ))}
                                        </div>
                                    )}

                                    {/* Artifacts */}
                                    {streamingArtifacts.length > 0 && (
                                        <div className="mt-2 space-y-1 w-full">
                                            {streamingArtifacts.map((artifact: any, i: number) => (
                                                <ArtifactCard key={i} artifact={artifact} />
                                            ))}
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

                    {/* Ambient AI Settings (Zen Mode Only Context) */}
                    {window.location.pathname.startsWith('/zen') && (
                        <div className="px-3 pb-2 flex-shrink-0">
                            <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-3">
                                <h3 className="text-xs font-semibold text-gray-300 mb-2 flex items-center justify-between">
                                    <span>Ambient AI Orchestration</span>
                                </h3>
                                <div className="space-y-3">
                                    <div>
                                        <label className="text-[10px] text-gray-400 block mb-1">Model Temperament</label>
                                        <select
                                            value={useZenStore.getState().ghostTextTemperament || "Default"}
                                            onChange={(e) => useZenStore.getState().setGhostTextTemperament(e.target.value)}
                                            className="w-full bg-gray-900 border border-gray-700 rounded p-1 text-xs text-gray-200 focus:outline-none focus:border-indigo-500/50"
                                        >
                                            <option value="Default">Default</option>
                                            <option value="Action-Heavy">Action-Heavy</option>
                                            <option value="Dialogue-Focused">Dialogue-Focused</option>
                                            <option value="Descriptive">Descriptive & Atmospheric</option>
                                            <option value="Terse">Terse & Punchy</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-[10px] text-gray-400 block mb-1">Constraints</label>
                                        <input
                                            type="text"
                                            value={useZenStore.getState().ghostTextConstraints}
                                            onChange={(e) => useZenStore.getState().setGhostTextConstraints(e.target.value)}
                                            placeholder="e.g. Focus on internal monologue..."
                                            className="w-full bg-gray-900 border border-gray-700 rounded p-1.5 text-xs text-gray-200 focus:outline-none focus:border-indigo-500/50"
                                        />
                                    </div>
                                </div>
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
