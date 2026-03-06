"use client";

import { useEffect, useState, useCallback } from "react";
import { GitBranch, GitCommit, ListPlus, Loader2, Check, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";

interface GitStatus {
    branch: string;
    is_dirty: boolean;
    untracked: string[];
    modified: string[];
    deleted: string[];
}

interface GitLogEntry {
    hash: string;
    message: string;
    author: string;
    date: string;
}

export function GitPanel() {
    const [status, setStatus] = useState<GitStatus | null>(null);
    const [logs, setLogs] = useState<GitLogEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [staging, setStaging] = useState(false);
    const [committing, setCommitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchData = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const [statusRes, logRes] = await Promise.all([
                api.gitStatus(),
                api.gitLog(10)
            ]);
            setStatus(statusRes);
            setLogs(logRes);
        } catch (err: any) {
            setError(err.message || "Failed to load Git status");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleStageAll = async () => {
        setStaging(true);
        try {
            await api.gitStage();
            await fetchData();
        } catch (err: any) {
            setError(err.message || "Failed to stage files");
        } finally {
            setStaging(false);
        }
    };

    const handleCommit = async () => {
        setCommitting(true);
        try {
            await api.gitCommit({ auto_message: true });
            await fetchData();
        } catch (err: any) {
            setError(err.message || "Failed to commit files");
        } finally {
            setCommitting(false);
        }
    };

    const changesCount = status ? (status.untracked?.length || 0) + (status.modified?.length || 0) + (status.deleted?.length || 0) : 0;
    const hasChanges = changesCount > 0;

    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm overflow-hidden flex flex-col h-full min-h-[400px]">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800/60 flex items-center justify-between shrink-0">
                <div className="flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Git Operations
                    </span>
                    {status?.branch && (
                        <span className="px-2 py-0.5 rounded text-[10px] bg-gray-800 text-gray-300 font-mono">
                            {status.branch}
                        </span>
                    )}
                </div>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="p-1 text-gray-500 hover:text-gray-300 transition-colors disabled:opacity-50"
                    title="Refresh Git status"
                >
                    <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
                </button>
            </div>

            {/* Content Body */}
            <div className="p-4 flex flex-col gap-4 overflow-y-auto min-h-0 flex-1">
                {error && (
                    <div className="p-2 rounded bg-red-500/10 border border-red-500/20 text-xs text-red-400">
                        {error}
                    </div>
                )}

                {/* Changes Section */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <label className="text-[10px] uppercase tracking-wider text-gray-500">
                            Uncommitted Changes ({loading ? "..." : changesCount})
                        </label>
                        <div className="flex gap-2">
                            <button
                                onClick={handleStageAll}
                                disabled={!hasChanges || staging || committing}
                                className={`px-2 py-1 rounded text-[10px] font-medium flex items-center gap-1 transition-all ${hasChanges && !staging && !committing
                                    ? "bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                                    : "bg-gray-800 text-gray-600 cursor-not-allowed"
                                    }`}
                            >
                                {staging ? <Loader2 className="w-3 h-3 animate-spin" /> : <ListPlus className="w-3 h-3" />}
                                Stage All
                            </button>
                            <button
                                onClick={handleCommit}
                                disabled={!hasChanges || staging || committing}
                                className={`px-2 py-1 rounded text-[10px] font-medium flex items-center gap-1 transition-all ${hasChanges && !committing && !staging
                                    ? "bg-blue-500/20 text-blue-400 hover:bg-blue-500/30"
                                    : "bg-gray-800 text-gray-600 cursor-not-allowed"
                                    }`}
                            >
                                {committing ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                Auto Commit
                            </button>
                        </div>
                    </div>

                    <div className="rounded-lg border border-gray-800 bg-gray-800/40 p-2 max-h-32 overflow-y-auto space-y-1">
                        {loading && !status ? (
                            <div className="text-xs text-gray-500 py-2 text-center">Loading...</div>
                        ) : !hasChanges ? (
                            <div className="text-xs text-gray-500 py-2 text-center italic">Working tree clean</div>
                        ) : (
                            <>
                                {status?.untracked?.map(f => (
                                    <div key={`u_${f}`} className="text-xs font-mono text-emerald-400/80 truncate" title={`?? ${f}`}>?? {f}</div>
                                ))}
                                {status?.modified?.map(f => (
                                    <div key={`m_${f}`} className="text-xs font-mono text-blue-400/80 truncate" title={`M  ${f}`}>M  {f}</div>
                                ))}
                                {status?.deleted?.map(f => (
                                    <div key={`d_${f}`} className="text-xs font-mono text-red-400/80 truncate" title={`D  ${f}`}>D  {f}</div>
                                ))}
                            </>
                        )}
                    </div>
                </div>

                {/* Recent Commits Section */}
                <div className="flex-1 flex flex-col min-h-0 mt-2">
                    <label className="text-[10px] uppercase tracking-wider text-gray-500 mb-2 block shrink-0">
                        Recent History
                    </label>
                    <div className="flex-1 overflow-y-auto rounded-lg border border-gray-800 bg-gray-800/40 divide-y divide-gray-800/60 hide-scrollbar">
                        {loading && logs.length === 0 ? (
                            <div className="text-xs text-gray-500 py-4 text-center">Loading history...</div>
                        ) : logs.length === 0 ? (
                            <div className="text-xs text-gray-500 py-4 text-center italic">No commits yet</div>
                        ) : (
                            logs.map((log) => (
                                <div key={log.hash} className="p-2 gap-2 flex items-start group hover:bg-gray-800/60 transition-colors">
                                    <GitCommit className="w-3.5 h-3.5 mt-0.5 text-gray-600 group-hover:text-gray-400 shrink-0" />
                                    <div className="min-w-0 flex-1">
                                        <div className="text-xs text-gray-300 font-medium break-words leading-snug">
                                            {log.message}
                                        </div>
                                        <div className="flex items-center gap-2 mt-1 opacity-70">
                                            <span className="text-[9px] font-mono text-purple-400">{log.hash.substring(0, 7)}</span>
                                            <span className="text-[9px] text-gray-500">{new Date(log.date).toLocaleString()}</span>
                                            <span className="text-[9px] text-gray-500 truncate">{log.author}</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
