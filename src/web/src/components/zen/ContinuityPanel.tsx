import React, { useEffect, useState } from 'react';
import { api, ContinuityCheckResponse, ResolutionOption } from '@/lib/api';
import { AlertCircle, AlertTriangle, CheckCircle, RefreshCw, Wand2, ArrowRight } from 'lucide-react';
import { useZenStore } from '@/lib/store/zenSlice';

export function ContinuityPanel() {
    const [issues, setIssues] = useState<ContinuityCheckResponse[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [resolutions, setResolutions] = useState<Record<number, ResolutionOption[]>>({});
    const [loadingResolutions, setLoadingResolutions] = useState<Record<number, boolean>>({});

    const currentFragmentId = useZenStore(state => state.currentFragmentId);

    const fetchIssues = async () => {
        setLoading(true);
        setError(null);
        setResolutions({});
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

    const handleSuggestFixes = async (issue: ContinuityCheckResponse, index: number) => {
        setLoadingResolutions(prev => ({ ...prev, [index]: true }));
        try {
            const data = await api.suggestContinuityResolutions(issue);
            setResolutions(prev => ({ ...prev, [index]: data }));
        } catch (err) {
            console.error("Failed to suggest resolutions:", err);
        } finally {
            setLoadingResolutions(prev => ({ ...prev, [index]: false }));
        }
    };

    const applyResolution = (issue: ContinuityCheckResponse, option: ResolutionOption) => {
        // Find the original text that caused the issue. The Continuity Analyst doesn't strictly provide
        // the exact matching snippet by default in its response, so we'll use the reasoning as context
        // or just insert the replacement text. Since we want to show a diff, let's assume `option.edits` 
        // string represents the "newText" and we'll attempt to Diff it against the selected or current context.
        // For accurate diffs, we would ideally change the backend to return `original_text` as well.
        // For now, we simulate originalText being a generic chunk or empty if unknown, and let the user see the new text.

        window.dispatchEvent(
            new CustomEvent("zen:applyDiff", {
                detail: {
                    originalText: `(Replace this with original text related to: ${issue.reasoning})`,
                    newText: option.edits
                }
            })
        );
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

                                {issue.severity !== 'low' && !resolutions[i] && (
                                    <button
                                        onClick={() => handleSuggestFixes(issue, i)}
                                        disabled={loadingResolutions[i]}
                                        className="mt-3 flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium bg-black/30 hover:bg-black/50 text-indigo-300 rounded border border-indigo-500/30 transition-colors"
                                    >
                                        <Wand2 className={`w-3.5 h-3.5 ${loadingResolutions[i] ? 'animate-spin' : ''}`} />
                                        {loadingResolutions[i] ? 'Thinking...' : 'Suggest Fixes'}
                                    </button>
                                )}

                                {resolutions[i] && (
                                    <div className="mt-4 space-y-2">
                                        <p className="text-xs font-semibold text-indigo-400 mb-2 border-b border-white/10 pb-1">Resolution Options</p>
                                        {resolutions[i].map((res, rIdx) => (
                                            <div key={rIdx} className="p-2.5 bg-black/40 rounded-lg border border-white/10 text-xs">
                                                <div className="flex justify-between items-start mb-1.5">
                                                    <span className="font-medium text-gray-200">{res.description}</span>
                                                    <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase tracking-wider ${res.risk === 'low' ? 'bg-emerald-500/20 text-emerald-300' : res.risk === 'medium' ? 'bg-amber-500/20 text-amber-300' : 'bg-rose-500/20 text-rose-300'}`}>
                                                        {res.risk} Risk
                                                    </span>
                                                </div>
                                                <p className="text-gray-400 mb-2">{res.edits}</p>
                                                {res.trade_off && (
                                                    <p className="text-[10px] text-gray-500 italic mb-2">Trade-off: {res.trade_off}</p>
                                                )}
                                                <button
                                                    onClick={() => applyResolution(issue, res)}
                                                    className="w-full flex justify-center items-center gap-1 px-2 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 rounded transition-colors"
                                                >
                                                    Apply Fix (Diff) <ArrowRight className="w-3 h-3" />
                                                </button>
                                            </div>
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
