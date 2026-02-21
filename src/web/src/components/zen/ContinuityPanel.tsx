import React, { useEffect, useState } from 'react';
import { api, ContinuityCheckResponse } from '@/lib/api';
import { AlertCircle, AlertTriangle, CheckCircle, RefreshCw } from 'lucide-react';
import { useZenStore } from '@/lib/store/zenSlice';

export function ContinuityPanel() {
    const [issues, setIssues] = useState<ContinuityCheckResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const currentFragmentId = useZenStore(state => state.currentFragmentId);

    const fetchIssues = async () => {
        setLoading(true);
        setError(null);
        try {
            // For a real scene, we would pass the container ID.
            // If we don't have a specific container, we fetch general issues.
            const res = await api.getContinuityIssues('all');
            setIssues(res);
        } catch (err) {
            console.error("Failed to fetch continuity issues", err);
            setError("Failed to load continuity issues.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchIssues();
    }, [currentFragmentId]);

    return (
        <div className="flex flex-col h-full bg-[#1A1A1A] text-gray-200">
            <div className="flex items-center justify-between p-4 border-b border-[#2A2A2A]">
                <h3 className="text-sm font-semibold tracking-wide text-gray-300">
                    Continuity Checker
                </h3>
                <button
                    onClick={fetchIssues}
                    disabled={loading}
                    className="p-1.5 text-gray-400 hover:text-white hover:bg-[#333] rounded-md transition-colors"
                    title="Refresh Issues"
                >
                    <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {error && (
                    <div className="p-3 text-sm text-red-400 bg-red-400/10 border border-red-500/20 rounded-md">
                        {error}
                    </div>
                )}

                {!loading && issues.length === 0 && !error && (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-gray-500">
                        <CheckCircle className="w-8 h-8 mb-2 text-emerald-500/50" />
                        <p className="text-sm">No continuity issues detected.</p>
                    </div>
                )}

                {issues.map((issue, i) => (
                    <div
                        key={i}
                        className={`p-3 rounded-lg border ${issue.severity === 'high'
                            ? 'bg-rose-500/10 border-rose-500/20'
                            : issue.severity === 'medium'
                                ? 'bg-amber-500/10 border-amber-500/20'
                                : 'bg-emerald-500/10 border-emerald-500/20'
                            }`}
                    >
                        <div className="flex items-start gap-3">
                            <div className="mt-0.5">
                                {issue.severity === 'high' ? (
                                    <AlertCircle className="w-5 h-5 text-rose-500" />
                                ) : issue.severity === 'medium' ? (
                                    <AlertTriangle className="w-5 h-5 text-amber-500" />
                                ) : (
                                    <CheckCircle className="w-5 h-5 text-emerald-500" />
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                    <span className={`text-xs font-semibold uppercase tracking-wider ${issue.severity === 'high' ? 'text-rose-400'
                                        : issue.severity === 'medium' ? 'text-amber-400'
                                            : 'text-emerald-400'
                                        }`}>
                                        {issue.status}
                                    </span>
                                </div>
                                <p className="text-sm text-gray-200 mb-2">{issue.reasoning}</p>

                                {issue.suggestions && typeof issue.suggestions === 'string' && (
                                    <div className="mt-2 p-2 bg-black/40 rounded border border-white/5">
                                        <p className="text-xs text-indigo-300 font-medium mb-1">Suggestion:</p>
                                        <p className="text-xs text-gray-300">{issue.suggestions}</p>
                                    </div>
                                )}

                                {issue.affected_entities && issue.affected_entities.length > 0 && (
                                    <div className="mt-3 flex flex-wrap gap-1.5">
                                        {issue.affected_entities.map(ent => (
                                            <span key={ent} className="px-1.5 py-0.5 text-[10px] bg-white/10 text-gray-300 rounded">
                                                {ent}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
