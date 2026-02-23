'use client';

import React from 'react';
import { usePipelineStream } from '@/components/pipeline/usePipelineStream';
import { InlinePromptReview } from './InlinePromptReview';
import { PipelineAuditFeed } from './PipelineAuditFeed';
import { api } from '@/lib/api';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';

interface PipelineRunViewerProps {
    runId: string;
    title?: string;
}

export function PipelineRunViewer({ runId, title }: PipelineRunViewerProps) {
    const { state, payload, stepName, agentId, error, isConnecting } = usePipelineStream(runId);

    const handleResume = async (resumePayload: any) => {
        try {
            await api.resumePipeline(runId, resumePayload);
        } catch (e) {
            console.error("Failed to resume pipeline", e);
        }
    };

    const handleReverse = async (stepId: string) => {
        // Requires Event Sourcing branch/rollback API
        console.log("Reverse triggered for step", stepId, "Not fully implemented on backend yet");
        alert("Event timeline reversed (Stubbed)");
    };

    const handleEditRetry = async (stepId: string, newPrompt: string) => {
        // Requires Pipeline rewind tracking or new run kickoff via Event Sourcing branch
        console.log("Edit retry for step", stepId, newPrompt);
        alert("Pipeline retry triggered (Stubbed)");
    };

    if (isConnecting && state === 'IDLE') {
        return (
            <div className="p-3 bg-gray-900 border border-gray-700 rounded-lg flex items-center gap-2 mt-2">
                <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                <span className="text-xs text-gray-400">Connecting to pipeline {title}...</span>
            </div>
        );
    }

    if (state === 'FAILED') {
        return (
            <div className="p-3 bg-red-900/20 border border-red-500/30 rounded-lg flex flex-col gap-1 mt-2">
                <div className="flex items-center gap-2">
                    <XCircle className="w-4 h-4 text-red-500" />
                    <span className="text-sm font-medium text-red-200">Pipeline Failed</span>
                </div>
                <div className="text-xs text-red-300 ml-6 break-words">{error || 'Unknown error'}</div>
            </div>
        );
    }

    if (state === 'COMPLETED') {
        return (
            <div className="p-3 bg-emerald-900/20 border border-emerald-500/30 rounded-lg flex flex-col gap-1 mt-2">
                <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-emerald-500" />
                    <span className="text-sm font-medium text-emerald-200">Pipeline Completed: {title}</span>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-gray-900 border border-gray-700 rounded-lg overflow-hidden mt-2">
            <div className="px-3 py-2 bg-gray-800/50 flex items-center justify-between border-b border-gray-700">
                <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-indigo-500" />
                    <span className="text-sm font-medium text-gray-200">{title || 'Running Pipeline'}</span>
                </div>
                <span className="text-[10px] uppercase font-bold tracking-wider text-gray-500 bg-gray-800 px-2 py-0.5 rounded-full">{state}</span>
            </div>

            <div className="p-3 border-b border-gray-800 flex items-center justify-between">
                <div className="text-xs text-gray-400">
                    Current Step: <span className="text-gray-200 font-medium ml-1">{stepName || '...'}</span>
                </div>
                {agentId && (
                    <div className="text-[10px] text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded font-mono">
                        {agentId}
                    </div>
                )}
            </div>

            {state === 'PAUSED_FOR_USER' && payload?.prompt_text !== undefined ? (
                <div className="px-3 pb-3">
                    <InlinePromptReview
                        initialPrompt={payload.prompt_text}
                        stepName={stepName || 'Approval'}
                        agentId={agentId}
                        onResume={handleResume}
                    />
                </div>
            ) : state !== 'IDLE' && (
                <div className="px-3 py-4 flex flex-col items-center justify-center text-gray-500">
                    <div className="flex gap-1 mb-2">
                        <span className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                        <span className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                        <span className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce"></span>
                    </div>
                    <span className="text-[10px] uppercase font-medium tracking-wide">Executing Background Task</span>
                </div>
            )}

            {payload?.auto_approved_steps && payload.auto_approved_steps.length > 0 && (
                <div className="px-3 pb-3">
                    <PipelineAuditFeed
                        steps={payload.auto_approved_steps}
                        onReverse={handleReverse}
                        onEditRetry={handleEditRetry}
                    />
                </div>
            )}
        </div>
    );
}
