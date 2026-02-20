import React, { useEffect, useState } from "react";
import { TimelinePanel, type TimelineEvent } from "./TimelinePanel";
import { api } from "@/lib/api";
import { useStudioStore } from "@/lib/store";

export function TimelineView() {
    const [events, setEvents] = useState<TimelineEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeEventId, setActiveEventId] = useState<string | null>(null);

    const loadEvents = async () => {
        try {
            setLoading(true);
            const data = await api.getTimelineEvents();
            setEvents(data);

            // Assume the latest event on 'main' branch is active if available
            // In a real implementation this would come from a "current HEAD" status
            if (data.length > 0) {
                setActiveEventId(data[data.length - 1].id);
            }
        } catch (e) {
            setError(`Failed to load timeline events: ${e instanceof Error ? e.message : e}`);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadEvents();
    }, []);

    const handleCheckout = async (eventId: string) => {
        try {
            // Stub for full checkout implementation
            await api.checkoutEvent(eventId);
            setActiveEventId(eventId);

            // Refetch studio data to reflect the new state in the store
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
        <TimelinePanel
            events={events}
            onCheckout={handleCheckout}
            activeEventId={activeEventId}
        />
    );
}
