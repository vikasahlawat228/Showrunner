"use client";

import React, { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle, ChevronDown, ChevronUp } from "lucide-react";
import { Job } from "@/lib/api";

export function BackgroundJobsWidget() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [expanded, setExpanded] = useState(false);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        let evtSource: EventSource | null = null;
        let retryCount = 0;

        const connectSSE = () => {
            evtSource = new EventSource(
                `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/jobs/stream`
            );

            evtSource.addEventListener("jobs_update", (event) => {
                try {
                    const updatedJobs = JSON.parse(event.data);
                    setJobs(updatedJobs);
                } catch (e) {
                    console.error("Error parsing jobs", e);
                }
            });

            evtSource.onopen = () => {
                setIsConnected(true);
                retryCount = 0;
            };

            evtSource.onerror = (err) => {
                console.error("Job SSE error:", err);
                setIsConnected(false);
                evtSource?.close();
                // Basic backoff
                const timeout = Math.min(10000, 1000 * Math.pow(2, retryCount));
                retryCount++;
                setTimeout(connectSSE, timeout);
            };
        };

        connectSSE();

        return () => {
            evtSource?.close();
        };
    }, []);

    const runningJobs = jobs.filter((j) => j.status === "running" || j.status === "pending");
    const hasJobs = jobs.length > 0;

    if (!hasJobs) return null;

    return (
        <div className="relative z-50">
            <button
                onClick={() => setExpanded(!expanded)}
                className={`flex items-center gap-2 px-2 py-1.5 border rounded-md transition-colors text-xs font-medium ${runningJobs.length > 0
                        ? "border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20"
                        : "border-gray-700 bg-gray-900 text-gray-400 hover:border-gray-500 hover:text-gray-200"
                    }`}
            >
                {runningJobs.length > 0 ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" />
                ) : (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                )}
                <span className="hidden sm:inline">
                    {runningJobs.length > 0 ? `${runningJobs.length} Active` : "Done"}
                </span>
            </button>

            {expanded && (
                <div className="absolute right-0 top-full mt-2 w-72 bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden animate-in fade-in slide-in-from-top-2">
                    <div className="px-3 py-2 border-b border-gray-800 bg-gray-950 flex items-center justify-between">
                        <span className="font-semibold text-xs text-gray-200">Background Tasks</span>
                        <span className="text-[10px] text-gray-500">Global Queue</span>
                    </div>
                    <div className="max-h-64 overflow-y-auto">
                        {jobs.length === 0 ? (
                            <div className="p-4 text-center text-xs text-gray-500 italic">No recent tasks.</div>
                        ) : (
                            <div className="divide-y divide-gray-800">
                                {jobs.slice(0, 10).map((job) => (
                                    <div key={job.id} className="p-3 hover:bg-gray-800/50 transition-colors">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-2 overflow-hidden">
                                                {job.status === "pending" || job.status === "running" ? (
                                                    <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0 text-indigo-400" />
                                                ) : job.status === "failed" ? (
                                                    <XCircle className="w-3.5 h-3.5 shrink-0 text-red-500" />
                                                ) : (
                                                    <CheckCircle2 className="w-3.5 h-3.5 shrink-0 text-emerald-500" />
                                                )}
                                                <span className="text-xs font-medium text-gray-200 truncate">
                                                    {job.job_type === "pipeline" ? "Pipeline Execution" : job.job_type}
                                                </span>
                                            </div>
                                            <span className="text-[10px] text-gray-500 shrink-0 uppercase tracking-wider">
                                                {job.status}
                                            </span>
                                        </div>

                                        <div className="ml-5">
                                            <div className="text-[11px] text-gray-400 mb-1 line-clamp-2">
                                                {job.message || "Working..."}
                                            </div>

                                            {job.status === "failed" && job.error && (
                                                <div className="text-[10px] text-red-400 mt-1 mb-2 bg-red-950/30 p-1.5 rounded line-clamp-2">
                                                    {job.error}
                                                </div>
                                            )}

                                            {(job.status === "running" || job.status === "pending") && (
                                                <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-indigo-500 transition-all duration-300 ease-out"
                                                        style={{ width: `${job.progress || 10}%` }}
                                                    />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
