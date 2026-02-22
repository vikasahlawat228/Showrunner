"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Check, Clock, AlertCircle } from "lucide-react";

export function OpenPlotThreads() {
    const [threads, setThreads] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [resolvingId, setResolvingId] = useState<string | null>(null);

    const loadThreads = async () => {
        try {
            setLoading(true);
            const res = await api.getUnresolvedThreads();
            setThreads(res.threads || []);
            setError(null);
        } catch (err: any) {
            setError(err.message || "Failed to load plot threads.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadThreads();
    }, []);

    const handleResolve = async (edgeId: string) => {
        try {
            setResolvingId(edgeId);
            await api.resolveThread(edgeId, "current");
            // Optimistic update
            setThreads(prev => prev.filter(t => t.edge_id !== edgeId));
        } catch (err: any) {
            setError(err.message || "Failed to resolve thread.");
        } finally {
            setResolvingId(null);
        }
    };

    if (loading) {
        return <div className="p-4 text-sm text-slate-500">Loading open plot threads...</div>;
    }

    if (error) {
        return (
            <div className="p-4 text-sm text-red-500 flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                {error}
            </div>
        );
    }

    if (threads.length === 0) {
        return (
            <div className="p-6 text-center border border-dashed rounded-lg border-slate-700 bg-slate-800/30 text-slate-400">
                <Check className="w-6 h-6 mx-auto mb-2 opacity-50" />
                <p className="text-sm">All known plot threads are resolved!</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {threads.map((thread) => (
                <div key={thread.edge_id} className="p-3 border rounded-lg bg-slate-800/50 border-slate-700 shadow-sm flex items-start justify-between group transition-colors hover:border-slate-600">
                    <div className="flex-1 pr-4">
                        <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-slate-200">{thread.source}</span>
                            <span className="text-xs text-slate-500 uppercase tracking-wider">{thread.relationship}</span>
                            <span className="font-medium text-slate-200">{thread.target}</span>
                        </div>

                        {thread.description && (
                            <p className="text-sm text-slate-400 mt-1">{thread.description}</p>
                        )}

                        {thread.created_in && (
                            <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                                <Clock className="w-3 h-3" />
                                <span>Origins: {thread.created_in}</span>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={() => handleResolve(thread.edge_id)}
                        disabled={resolvingId === thread.edge_id}
                        className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-emerald-400 bg-emerald-400/10 hover:bg-emerald-400/20 rounded border border-emerald-400/20 transition-colors disabled:opacity-50"
                    >
                        {resolvingId === thread.edge_id ? "Resolving..." : (
                            <>
                                <Check className="w-3.5 h-3.5" />
                                Resolve
                            </>
                        )}
                    </button>
                </div>
            ))}
        </div>
    );
}
