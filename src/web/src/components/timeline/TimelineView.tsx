import React, { useCallback, useEffect, useRef, useState } from "react";
import { TimelinePanel, type TimelineEvent } from "./TimelinePanel";
import { api } from "@/lib/api";
import { useStudioStore } from "@/lib/store";
import { useInterval } from "./useInterval";
import { EmotionalArcChart } from "./EmotionalArcChart";
import { StoryRibbons } from "./StoryRibbons";
import { ChevronDown, ChevronRight } from "lucide-react";

const POLL_INTERVAL_MS = 2000;

export interface TimelineViewProps {
    onActiveEventChange?: (eventId: string | null) => void;
}

function CollapsibleSection({ title, defaultOpen = false, children }: { title: string, defaultOpen?: boolean, children: React.ReactNode }) {
    const [isOpen, setIsOpen] = useState(defaultOpen);
    return (
        <div className="flex flex-col gap-2 mt-4">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 text-gray-400 hover:text-gray-200 transition-colors w-fit"
            >
                {isOpen ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                <span className="text-sm font-semibold uppercase tracking-wider">{title}</span>
            </button>
            {isOpen && <div className="animate-in fade-in slide-in-from-top-2 duration-200">{children}</div>}
        </div>
    );
}

export function TimelineView({ onActiveEventChange }: TimelineViewProps) {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeEventId, setActiveEventId] = useState<string | null>(null);

    // Track IDs we've already seen so we can flag newcomers.
    const knownIdsRef = useRef<Set<string>>(new Set());
    const [newEventIds, setNewEventIds] = useState<Set<string>>(new Set());

    // Sync activeEventId to parent
    useEffect(() => {
        if (onActiveEventChange) {
            onActiveEventChange(activeEventId);
        }
    }, [activeEventId, onActiveEventChange]);

    const loadEvents = useCallback(async (isInitial = false) => {
        try {
            if (isInitial) setLoading(true);

            const data: TimelineEvent[] = await api.getTimelineEvents();

            // Determine which events are new (not in the known set).
            const incoming = new Set<string>();
            if (!isInitial) {
                for (const evt of data) {
                    if (!knownIdsRef.current.has(evt.id)) {
                        incoming.add(evt.id);
                    }
                }
            }

            // Update known IDs.
            knownIdsRef.current = new Set(data.map((e) => e.id));

            // Merge new IDs — they'll be cleared after the pulse animation.
            if (incoming.size > 0) {
                setNewEventIds(incoming);
                // Auto-clear after the animation duration (3 × 1s = 3s).
                setTimeout(() => setNewEventIds(new Set()), 3200);
            }

            setEvents(data);

            // Set active event only on initial load (preserve user selection).
            if (isInitial && data.length > 0) {
                setActiveEventId(data[data.length - 1].id);
            }
        } catch (e) {
            if (isInitial) {
                setError(
                    `Failed to load timeline events: ${e instanceof Error ? e.message : e}`
                );
            }
            // Silently ignore poll failures to avoid flashing error state.
        } finally {
            if (isInitial) setLoading(false);
        }
    }, []);

    // Initial fetch.
    useEffect(() => {
        loadEvents(true);
    }, [loadEvents]);

    // SSE Integration
    useEffect(() => {
        let isSubscribed = true;
        const sseUrl = `${process.env.NEXT_PUBLIC_API_URL || ""}/api/v1/timeline/stream`;

        const source = new EventSource(sseUrl);
        source.onmessage = (e) => {
            if (!isSubscribed) return;
            try {
                const newEvent: TimelineEvent = JSON.parse(e.data);
                if (!knownIdsRef.current.has(newEvent.id)) {
                    // Update state with new event
                    setEvents(prev => {
                        // avoid duplicate if multiple SSEs arrive
                        if (prev.some(evt => evt.id === newEvent.id)) return prev;
                        return [...prev, newEvent];
                    });

                    knownIdsRef.current.add(newEvent.id);
                    setNewEventIds(prev => new Set(prev).add(newEvent.id));

                    // Clear pulse after 3s
                    setTimeout(() => {
                        if (isSubscribed) {
                            setNewEventIds(prev => {
                                const next = new Set(prev);
                                next.delete(newEvent.id);
                                return next;
                            });
                        }
                    }, 3200);
                }
            } catch (err) {
                console.error("Failed to parse SSE event", err);
            }
        };

        source.onerror = (err) => {
            console.error("SSE connection error", err);
            source.close(); // let polling take over if SSE is failing
        };

        return () => {
            isSubscribed = false;
            source.close();
        };
    }, []);

    // Poll every 2 seconds as fallback/sync mechanism.
    useInterval(() => {
        loadEvents(false);
    }, POLL_INTERVAL_MS);

    const handleCheckout = async (eventId: string) => {
        try {
            await api.checkoutEvent(eventId);
            setActiveEventId(eventId);

            // Refetch studio data to reflect the new state in the store.
            useStudioStore.getState().fetchAll();
        } catch (e) {
            setError(`Checkout failed: ${e instanceof Error ? e.message : e}`);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500 text-lg">
                Loading Timeline...
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center h-full text-red-500 text-lg">
                {error}
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full overflow-y-auto w-full pr-2 space-y-6 pb-20 scrollbar-thin scrollbar-thumb-gray-700">
            <div className="flex-shrink-0">
                <TimelinePanel
                    events={events}
                    onCheckout={handleCheckout}
                    activeEventId={activeEventId}
                    newEventIds={newEventIds}
                />
            </div>

            <CollapsibleSection title="Emotional Arc Analysis" defaultOpen={true}>
                <EmotionalArcChart />
            </CollapsibleSection>

            <CollapsibleSection title="Character Presence Ribbons" defaultOpen={true}>
                <StoryRibbons />
            </CollapsibleSection>
        </div>
    );
}
