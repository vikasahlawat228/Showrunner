import { useEffect, useRef } from "react";

/**
 * A declarative `setInterval` hook.
 * Fires `callback` every `delayMs` milliseconds.
 * Pass `null` for `delayMs` to pause the interval.
 */
export function useInterval(callback: () => void, delayMs: number | null) {
    const savedCallback = useRef<() => void>(callback);

    // Remember the latest callback without re-registering the interval.
    useEffect(() => {
        savedCallback.current = callback;
    }, [callback]);

    useEffect(() => {
        if (delayMs === null) return;

        const id = setInterval(() => savedCallback.current(), delayMs);
        return () => clearInterval(id);
    }, [delayMs]);
}
