import { useState, useEffect } from 'react';

export type PipelineState =
    | 'IDLE'
    | 'CONTEXT_GATHERING'
    | 'PROMPT_ASSEMBLY'
    | 'PAUSED_FOR_USER'
    | 'EXECUTING'
    | 'COMPLETED'
    | 'FAILED';

export interface PipelinePayload {
    prompt_text?: string;
    step_name?: string;
    [key: string]: any;
}

export function usePipelineStream(runId: string | undefined) {
    const [state, setState] = useState<PipelineState>('IDLE');
    const [payload, setPayload] = useState<PipelinePayload | undefined>(undefined);
    const [stepName, setStepName] = useState<string | undefined>(undefined);
    const [agentId, setAgentId] = useState<string | undefined>(undefined);
    const [error, setError] = useState<string | null>(null);
    const [isConnecting, setIsConnecting] = useState(false);

    useEffect(() => {
        if (!runId) return;

        setIsConnecting(true);
        const eventSource = new EventSource(`/api/v1/pipeline/${runId}/stream`);

        eventSource.onmessage = (event) => {
            try {
                // Backend sends PipelineRun.model_dump_json() with fields:
                // { id, current_state, current_agent_id, payload, created_at, error }
                const data = JSON.parse(event.data);

                if (data.current_state) {
                    setState(data.current_state as PipelineState);
                    setStepName(data.current_state);
                }
                if (data.current_agent_id !== undefined) {
                    setAgentId(data.current_agent_id || undefined);
                }
                if (data.payload) {
                    setPayload(data.payload);
                    if (data.payload.step_name) {
                        setStepName(data.payload.step_name);
                    }
                }
                if (data.error) {
                    setError(data.error);
                }
            } catch (err) {
                console.error('Failed to parse SSE message:', err);
            }
        };

        eventSource.onerror = () => {
            setError('Connection to stream lost or failed.');
            eventSource.close();
            setState('FAILED');
            setIsConnecting(false);
        };

        eventSource.onopen = () => {
            setIsConnecting(false);
            setError(null);
        };

        return () => {
            eventSource.close();
        };
    }, [runId]);

    return { state, payload, stepName, agentId, error, isConnecting };
}
