"use client";

import { useEffect, useState } from "react";
import { Clock, ArrowRight, CheckCircle2, AlertCircle } from "lucide-react";
import { api, type PipelineRunSummary } from "@/lib/api";

export function PendingApprovals() {
    const [runs, setRuns] = useState<PipelineRunSummary[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            try {
                const data = await api.getPipelineRuns("PAUSED_FOR_USER");
                if (!cancelled) setRuns(data);
            } catch {
                if (!cancelled) setRuns([]);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        load();
        return () => { cancelled = true; };
    }, []);

    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Pending Approvals
                    </span>
                </div>
                {runs.length > 0 && (
                    <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-bold tabular-nums">
                        {runs.length}
                    </span>
                )}
            </div>

            {/* Content */}
            <div className="max-h-56 overflow-y-auto">
                {loading ? (
                    <div className="px-4 py-6 text-center">
                        <div className="w-5 h-5 mx-auto rounded-full border-2 border-gray-600 border-t-amber-400 animate-spin" />
                    </div>
                ) : runs.length === 0 ? (
                    <div className="px-4 py-8 text-center">
                        <CheckCircle2 className="w-8 h-8 mx-auto text-gray-700 mb-2" />
                        <p className="text-gray-500 text-sm">All caught up!</p>
                        <p className="text-gray-600 text-xs mt-1">
                            No pipelines waiting for your review.
                        </p>
                    </div>
                ) : (
                    runs.map((run) => (
                        <div
                            key={run.id}
                            className="px-4 py-3 border-b border-gray-800/40 last:border-b-0 hover:bg-gray-800/30 transition-colors group"
                        >
                            <div className="flex items-start justify-between gap-3">
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-1">
                                        <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                                        <p className="text-sm font-medium text-white truncate">
                                            {run.title || `Pipeline ${run.id.slice(0, 8)}`}
                                        </p>
                                    </div>
                                    {run.current_step_name && (
                                        <p className="text-xs text-gray-500 ml-5">
                                            Step: <span className="text-gray-400">{run.current_step_name}</span>
                                        </p>
                                    )}
                                    <p className="text-[10px] text-gray-600 ml-5 mt-1">
                                        {new Date(run.updated_at).toLocaleString()}
                                    </p>
                                </div>
                                <a
                                    href="/pipelines"
                                    className="shrink-0 px-3 py-1.5 rounded-lg bg-amber-500/10 text-amber-400 text-xs font-medium flex items-center gap-1 hover:bg-amber-500/20 transition-colors opacity-0 group-hover:opacity-100"
                                >
                                    Review
                                    <ArrowRight className="w-3 h-3" />
                                </a>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
