import { useCallback, useRef } from "react";
import type { ChatEvent, ChatMessage, ChatActionTrace, ChatArtifact } from "../lib/store/chatSlice";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

interface UseChatStreamOptions {
    onToken: (text: string) => void;
    onActionTrace: (trace: ChatActionTrace) => void;
    onArtifact: (artifact: ChatArtifact) => void;
    onComplete: (data: { message_id: string; session_id: string; duration_ms: number }) => void;
    onError: (error: string) => void;
    onApprovalNeeded?: (data: any) => void;
    onBackgroundUpdate?: (data: any) => void;
}

export function useChatStream(options: UseChatStreamOptions) {
    const abortRef = useRef<AbortController | null>(null);

    const sendMessage = useCallback(
        async (
            sessionId: string,
            content: string,
            mentionedEntityIds: string[] = [],
            contextPayload?: Record<string, any>
        ) => {
            // Abort any in-flight request
            abortRef.current?.abort();
            const controller = new AbortController();
            abortRef.current = controller;

            try {
                const res = await fetch(
                    `${API_BASE}/api/v1/chat/sessions/${encodeURIComponent(sessionId)}/messages`,
                    {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            content,
                            mentioned_entity_ids: mentionedEntityIds,
                            context_payload: contextPayload,
                        }),
                        signal: controller.signal,
                    }
                );

                if (!res.ok) {
                    const body = await res.json().catch(() => null);
                    throw new Error(body?.detail || `HTTP ${res.status}`);
                }

                const reader = res.body?.getReader();
                if (!reader) throw new Error("No response body");

                const decoder = new TextDecoder();
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    // Parse SSE lines
                    const lines = buffer.split("\n");
                    buffer = lines.pop() || "";

                    for (const line of lines) {
                        if (!line.startsWith("data: ")) continue;
                        const jsonStr = line.slice(6).trim();
                        if (!jsonStr) continue;

                        try {
                            const event: ChatEvent = JSON.parse(jsonStr);

                            switch (event.event_type) {
                                case "token":
                                    options.onToken(event.data.text || "");
                                    break;
                                case "action_trace":
                                    options.onActionTrace(event.data as ChatActionTrace);
                                    break;
                                case "artifact":
                                    options.onArtifact(event.data as ChatArtifact);
                                    break;
                                case "approval_needed":
                                    options.onApprovalNeeded?.(event.data);
                                    break;
                                case "background_update":
                                    options.onBackgroundUpdate?.(event.data);
                                    break;
                                case "complete":
                                    options.onComplete(event.data as any);
                                    break;
                                case "error":
                                    options.onError(event.data.error || "Unknown error");
                                    break;
                            }
                        } catch {
                            // Ignore malformed SSE lines
                        }
                    }
                }
            } catch (err: any) {
                if (err.name !== "AbortError") {
                    options.onError(err.message || "Stream failed");
                }
            }
        },
        [options]
    );

    const abort = useCallback(() => {
        abortRef.current?.abort();
    }, []);

    return { sendMessage, abort };
}
