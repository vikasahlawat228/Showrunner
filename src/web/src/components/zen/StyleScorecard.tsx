import React, { useState } from 'react';
import { api, StyleCheckResponse, StyleIssueResponse } from '@/lib/api';
import { useZenStore } from '@/lib/store/zenSlice';
import { CheckCircle, AlertTriangle, AlertCircle, Sparkles, Loader2 } from 'lucide-react';

export function StyleScorecard() {
    const [evaluation, setEvaluation] = useState<StyleCheckResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [textToAnalyze, setTextToAnalyze] = useState('');

    // In a real app we might get this from the editor context or a prop
    const currentSceneId = "scene-123";

    const handleAnalyze = async () => {
        if (!textToAnalyze.trim()) return;
        setLoading(true);
        setError(null);
        try {
            const res = await api.checkStyle(textToAnalyze, currentSceneId);
            setEvaluation(res);
        } catch (err) {
            console.error("Failed to analyze style", err);
            setError("Failed to analyze style.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#1A1A1A] text-gray-200">
            <div className="p-4 border-b border-[#2A2A2A]">
                <h3 className="text-sm font-semibold tracking-wide text-gray-300 mb-2">
                    Style Enforcer
                </h3>
                <p className="text-xs text-gray-500 mb-3">
                    Paste text to evaluate against narrative style guidelines.
                </p>
                <textarea
                    value={textToAnalyze}
                    onChange={(e) => setTextToAnalyze(e.target.value)}
                    placeholder="Paste up to 500 words..."
                    className="w-full h-24 bg-black/40 border border-white/10 rounded-lg p-2 text-sm text-gray-300 resize-none focus:outline-none focus:border-indigo-500/50"
                />
                <button
                    onClick={handleAnalyze}
                    disabled={loading || !textToAnalyze.trim()}
                    className="mt-3 w-full flex items-center justify-center gap-2 py-1.5 px-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-xs font-medium rounded transition-colors"
                >
                    {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Sparkles className="w-4 h-4" />
                    )}
                    Analyze Prose
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {error && (
                    <div className="p-3 text-sm text-red-400 bg-red-400/10 border border-red-500/20 rounded-md">
                        {error}
                    </div>
                )}

                {!evaluation && !loading && !error && (
                    <div className="flex flex-col items-center justify-center py-12 text-center text-gray-500">
                        <Sparkles className="w-8 h-8 mb-2 text-gray-600" />
                        <p className="text-sm">Ready to check style.</p>
                    </div>
                )}

                {evaluation && (
                    <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                        {/* Score Overview */}
                        <div className="flex items-center gap-4 bg-white/5 p-3 rounded-lg border border-white/10">
                            <div className="relative w-12 h-12 flex items-center justify-center shrink-0">
                                <svg className="w-full h-full transform -rotate-90">
                                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="none" className="text-gray-700" />
                                    <circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="4" fill="none"
                                        className={evaluation.overall_score >= 0.8 ? "text-emerald-500" : evaluation.overall_score >= 0.6 ? "text-amber-500" : "text-rose-500"}
                                        strokeDasharray="125.6" strokeDashoffset={125.6 * (1 - evaluation.overall_score)} />
                                </svg>
                                <span className="absolute text-sm font-bold">{(evaluation.overall_score * 10).toFixed(1)}</span>
                            </div>
                            <div>
                                <div className="font-semibold text-gray-200">Style Score</div>
                                <div className="text-xs text-gray-400">{evaluation.summary}</div>
                            </div>
                        </div>

                        {/* Strengths */}
                        {evaluation.strengths.length > 0 && (
                            <div>
                                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Strengths</h4>
                                <ul className="space-y-1 w-full bg-emerald-500/5 border border-emerald-500/10 rounded-lg p-3">
                                    {evaluation.strengths.map((str, idx) => (
                                        <li key={idx} className="flex gap-2 text-sm text-emerald-200/80">
                                            <CheckCircle className="w-4 h-4 shrink-0 text-emerald-500/70" />
                                            <span>{str}</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        )}

                        {/* Issues */}
                        {evaluation.issues.length > 0 && (
                            <div>
                                <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Detected Issues</h4>
                                <div className="space-y-2">
                                    {evaluation.issues.map((issue, idx) => (
                                        <div key={idx} className={`p-3 rounded-lg border ${issue.severity === 'high' ? 'bg-rose-500/10 border-rose-500/20' :
                                                issue.severity === 'medium' ? 'bg-amber-500/10 border-amber-500/20' :
                                                    'bg-gray-500/10 border-gray-500/20'
                                            }`}>
                                            <div className="flex items-start gap-3">
                                                <div className="mt-0.5">
                                                    {issue.severity === 'high' ? (
                                                        <AlertCircle className="w-4 h-4 text-rose-500" />
                                                    ) : issue.severity === 'medium' ? (
                                                        <AlertTriangle className="w-4 h-4 text-amber-500" />
                                                    ) : (
                                                        <AlertCircle className="w-4 h-4 text-gray-400" />
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex justify-between items-start mb-1">
                                                        <span className="text-xs font-medium text-gray-300 capitalize">{issue.category.replace('_', ' ')}</span>
                                                        {issue.location && issue.location !== 'overall' && (
                                                            <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-black/40 text-gray-400 border border-white/5 truncate max-w-[120px]">
                                                                {issue.location}
                                                            </span>
                                                        )}
                                                    </div>
                                                    <p className="text-sm text-gray-200 mb-2">{issue.description}</p>
                                                    {issue.suggestion && (
                                                        <div className="mt-2 p-2 bg-black/40 rounded border border-white/5">
                                                            <p className="text-xs text-indigo-300 font-medium mb-1">Fix:</p>
                                                            <p className="text-xs text-gray-300">{issue.suggestion}</p>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
