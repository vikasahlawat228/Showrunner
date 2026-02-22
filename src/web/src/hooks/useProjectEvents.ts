import { useEffect } from 'react';
import { useStudioStore } from '@/lib/store';
import { toast } from 'sonner';

export function useProjectEvents() {
    const { fetchCharacters, fetchScenes, fetchWorld, workflow } = useStudioStore();

    useEffect(() => {
        let eventSource: EventSource | null = null;
        let reconnectTimeout: ReturnType<typeof setTimeout>;

        const connect = () => {
            eventSource = new EventSource('/api/v1/project/events');

            eventSource.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'GRAPH_UPDATED') {
                        // A file was modified/created/deleted
                        // We refresh all assets to keep the sidebar in sync
                        fetchCharacters();
                        fetchWorld();
                        // Refresh scenes for the current chapter
                        if (workflow?.current_chapter) {
                            fetchScenes(workflow.current_chapter);
                        } else {
                            fetchScenes(1);
                        }
                    }
                } catch (err) {
                    console.error('Failed to parse project event:', err);
                }
            };

            eventSource.onerror = () => {
                eventSource?.close();
                // Attempt to reconnect after 5 seconds
                reconnectTimeout = setTimeout(connect, 5000);
            };
        };

        connect();

        return () => {
            if (eventSource) {
                eventSource.close();
            }
            clearTimeout(reconnectTimeout);
        };
    }, [fetchCharacters, fetchScenes, fetchWorld, workflow?.current_chapter]);
}
