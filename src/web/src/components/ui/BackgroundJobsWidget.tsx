"use client";

import React, { useEffect, useState, useCallback, useRef } from "react";
import { Loader2, CheckCircle2, XCircle, ChevronDown, ChevronUp, Briefcase } from "lucide-react";
import type { Job } from "@/lib/api";
import { api } from "@/lib/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export function BackgroundJobsWidget() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [expanded, setExpanded] = useState(false);
    const sseRef = useRef<EventSource | null>(null);

    // Poll for initial state + SSE for real-time updates
    useEffect(() => {
        // Initial fetch
        api.getJobs(true)
            .then(setJobs)
            .catch(() => { });

        // SSE stream
        const sse = new EventSource(`${API_BASE}/api/v1/jobs/stream`);
        sseRef.current = sse;

        sse.addEventListener("jobs_update", (e) => {
            try {
                const data = JSON.parse(e.data);
                setJobs(data);
            } catch { }
        });

        sse.onerror = () => {
            // SSE reconnection is automatic, but clear stale state
            setTimeout(() => {
                api.getJobs(true)
                    .then(setJobs)
                    .catch(() => { });
            }, 3000);
        };

        return () => {
            sse.close();
            sseRef.current = null;
        };
    }, []);

    const activeJobs = jobs.filter(j => j.status === "running" || j.status === "pending");
    const recentDone = jobs.filter(j => j.status === "completed" || j.status === "failed");

    if (activeJobs.length === 0 && recentDone.length === 0) return null;

    const statusIcon = (status: string) => {
        switch (status) {
            case "running":
            case "pending":
                return <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin" />;
            case "completed":
                return <CheckCircle2 className="w-3.5 h-3.5 text-green-400" />;
            case "failed":
                return <XCircle className="w-3.5 h-3.5 text-red-400" />;
            default:
                return <Briefcase className="w-3.5 h-3.5 text-gray-400" />;
        }
    };

    return (
        <div className="fixed bottom-16 right-4 z-50 w-80 animate-in slide-in-from-bottom-4 fade-in duration-300">
            <div className="bg-gray-900/95 backdrop-blur-md border border-gray-700/60 rounded-xl shadow-2xl shadow-black/30 overflow-hidden">
                {/* Header */}
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-gray-800/50 transition-colors"
                >
                    <div className="flex items-center gap-2.5">
                        {activeJobs.length > 0 ? (
                            <div className="relative">
                                <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
                                <span className="absolute -top-1 -right-1 w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
                            </div>
                        ) : (
                            <CheckCircle2 className="w-4 h-4 text-green-400" />
                        )}
                        <span className="text-xs font-medium text-gray-200">
                            {activeJobs.length > 0
                                ? `${activeJobs.length} background task${activeJobs.length > 1 ? "s" : ""} running`
                                : "All tasks complete"
                            }
                        </span>
                    </div>
                    {expanded ? (
                        <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
                    ) : (
                        <ChevronUp className="w-3.5 h-3.5 text-gray-500" />
                    )}
                </button>

                {/* Compact active job preview (always visible) */}
                {!expanded && activeJobs.length > 0 && (
                    <div className="px-4 pb-2.5 space-y-1.5">
                        {activeJobs.slice(0, 2).map(job => (
                            <div key={job.id} className="flex items-center gap-2">
                                {statusIcon(job.status)}
                                <span className="text-[11px] text-gray-400 truncate flex-1">{job.message}</span>
                                {job.progress > 0 && (
                                    <span className="text-[10px] text-indigo-300 font-mono">{job.progress}%</span>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Expanded view */}
                {expanded && (
                    <div className="border-t border-gray-800 max-h-60 overflow-y-auto">
                        {[...activeJobs, ...recentDone].map(job => (
                            <div
                                key={job.id}
                                className="flex items-start gap-2.5 px-4 py-2 border-b border-gray-800/50 last:border-0 hover:bg-gray-800/30 transition-colors"
                            >
                                <div className="mt-0.5">{statusIcon(job.status)}</div>
                                <div className="flex-1 min-w-0">
                                    <div className="text-xs text-gray-200 font-medium truncate">
                                        {job.job_type}
                                    </div>
                                    <div className="text-[11px] text-gray-500 truncate">{job.message}</div>
                                    {job.progress > 0 && job.progress < 100 && (
                                        <div className="mt-1 w-full bg-gray-800 rounded-full h-1 overflow-hidden">
                                            <div
                                                className="bg-indigo-500 h-full rounded-full transition-all duration-500"
                                                style={{ width: `${job.progress}%` }}
                                            />
                                        </div>
                                    )}
                                    {job.error && (
                                        <div className="text-[10px] text-red-400 mt-0.5 truncate">{job.error}</div>
                                    )}
                                </div>
                            </div>
                        ))}
                        {activeJobs.length === 0 && recentDone.length === 0 && (
                            <div className="px-4 py-3 text-xs text-gray-500 text-center">No background tasks</div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
