import { useState, useEffect, useRef } from 'react';

export type SyncStatus = 'idle' | 'syncing' | 'error' | 'offline';

export function useCloudSync() {
    const [status, setStatus] = useState<SyncStatus>('offline');
    const [lastSync, setLastSync] = useState<string | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        const checkStatus = async () => {
            try {
                const response = await fetch('/api/v1/sync/status');
                if (response.ok) {
                    const data = await response.json();
                    setStatus(data.status as SyncStatus);
                    if (data.status === 'idle' || data.status === 'syncing') {
                        setLastSync(new Date().toISOString());
                    }
                } else {
                    setStatus('error');
                }
            } catch (error) {
                setStatus('offline');
            }
        };

        checkStatus(); // Initial check

        // Adaptive polling: 5s when syncing, 15s when idle/offline
        const startPolling = () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
            const delay = status === 'syncing' ? 5000 : 15000;
            intervalRef.current = setInterval(checkStatus, delay);
        };

        startPolling();

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [status]);

    return { status, lastSync };
}
