'use client';

import React, { useState, useEffect } from 'react';
import { History, RotateCcw, AlertCircle, Loader2 } from 'lucide-react';

export interface Revision {
    revision_id: string;
    modified_time: string;
    size: number;
    user_name: string;
}

interface HistoryPanelProps {
    yamlPath: string;
    onRevertSuccess?: () => void;
}

export function HistoryPanel({ yamlPath, onRevertSuccess }: HistoryPanelProps) {
    const [revisions, setRevisions] = useState<Revision[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [revertingId, setRevertingId] = useState<string | null>(null);

    useEffect(() => {
        async function loadRevisions() {
            if (!yamlPath) return;

            setLoading(true);
            setError(null);

            try {
                const res = await fetch(`/api/v1/sync/revisions?yaml_path=${encodeURIComponent(yamlPath)}`);
                if (!res.ok) {
                    throw new Error('Failed to load revisions');
                }
                const data = await res.json();
                setRevisions(data);
            } catch (err: any) {
                setError(err.message || 'Unknown error occurred');
            } finally {
                setLoading(false);
            }
        }

        loadRevisions();
    }, [yamlPath]);

    const handleRevert = async (revisionId: string) => {
        if (!confirm('Are you sure you want to revert to this version? Unsaved local changes will be lost.')) {
            return;
        }

        setRevertingId(revisionId);
        setError(null);

        try {
            const res = await fetch('/api/v1/sync/revert', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ yaml_path: yamlPath, revision_id: revisionId }),
            });

            if (!res.ok) {
                throw new Error('Failed to revert file');
            }

            if (onRevertSuccess) {
                onRevertSuccess();
            }
        } catch (err: any) {
            setError(err.message || 'Failed to revert');
        } finally {
            setRevertingId(null);
        }
    };

    return (
        <div className="flex flex-col h-full bg-surface border-l border-neutral-800 w-80">
            <div className="flex items-center gap-2 p-4 border-b border-neutral-800">
                <History className="h-4 w-4 text-neutral-400" />
                <h3 className="font-medium text-sm text-neutral-200">Version History</h3>
            </div>

            <div className="flex-1 overflow-y-auto p-4">
                {loading ? (
                    <div className="flex justify-center items-center py-8 text-neutral-500">
                        <Loader2 className="h-5 w-5 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="flex items-start gap-2 p-3 bg-red-950/30 text-red-400 rounded-md text-xs">
                        <AlertCircle className="h-4 w-4 shrink-0 mt-0.5" />
                        <p>{error}</p>
                    </div>
                ) : revisions.length === 0 ? (
                    <div className="text-center py-8 text-neutral-500 text-sm">
                        No history available for this file.
                    </div>
                ) : (
                    <div className="space-y-3">
                        {revisions.map((rev, idx) => {
                            const date = new Date(rev.modified_time);
                            const isLatest = idx === 0;

                            return (
                                <div
                                    key={rev.revision_id}
                                    className={`p-3 rounded-lg border ${isLatest ? 'bg-indigo-950/20 border-indigo-900/50' : 'bg-surface-elevated border-neutral-800'}`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        <div>
                                            <div className="text-sm font-medium text-neutral-200">
                                                {date.toLocaleDateString()} at {date.toLocaleTimeString()}
                                            </div>
                                            <div className="text-xs text-neutral-500 mt-0.5">
                                                {isLatest ? 'Current Version' : `by ${rev.user_name}`}
                                            </div>
                                        </div>
                                    </div>

                                    {!isLatest && (
                                        <button
                                            onClick={() => handleRevert(rev.revision_id)}
                                            disabled={revertingId !== null}
                                            className="flex items-center gap-1.5 w-full justify-center px-3 py-1.5 mt-3 text-xs font-medium text-indigo-300 bg-indigo-950/40 hover:bg-indigo-900/50 rounded transition-colors disabled:opacity-50"
                                        >
                                            {revertingId === rev.revision_id ? (
                                                <>
                                                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                                    <span>Reverting...</span>
                                                </>
                                            ) : (
                                                <>
                                                    <RotateCcw className="h-3.5 w-3.5" />
                                                    <span>Restore this version</span>
                                                </>
                                            )}
                                        </button>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}
