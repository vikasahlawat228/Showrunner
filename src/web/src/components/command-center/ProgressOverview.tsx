"use client";

import { useEffect, useMemo, useState } from "react";
import { Layers, BookOpen, Film, BarChart3, Download, MessageSquare, Clock } from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { ExportModal } from "@/components/ui/ExportModal";
import type { StructureNode } from "@/lib/api";

function countByType(nodes: StructureNode[]): Record<string, number> {
    const counts: Record<string, number> = {};
    function walk(list: StructureNode[]) {
        for (const n of list) {
            counts[n.container_type] = (counts[n.container_type] || 0) + 1;
            if (n.children) walk(n.children);
        }
    }
    walk(nodes);
    return counts;
}

interface StatCardProps {
    label: string;
    count: number;
    icon: React.ReactNode;
    gradient: string;
}

function StatCard({ label, count, icon, gradient }: StatCardProps) {
    return (
        <div className="relative overflow-hidden rounded-lg border border-gray-800 bg-gray-900/60 p-4 group hover:border-gray-700 transition-all duration-200">
            <div
                className={`absolute inset-0 opacity-[0.04] bg-gradient-to-br ${gradient} group-hover:opacity-[0.08] transition-opacity`}
            />
            <div className="relative flex items-center gap-3">
                <div
                    className={`w-10 h-10 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg`}
                >
                    {icon}
                </div>
                <div>
                    <p className="text-2xl font-bold text-white tabular-nums">{count}</p>
                    <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
                </div>
            </div>
        </div>
    );
}

export function ProgressOverview() {
    const activeProjectId = useStudioStore((s) => s.activeProjectId);
    const structureTree = useStudioStore((s) => s.structureTree);
    const fetchStructure = useStudioStore((s) => s.fetchStructure);
    const chatSessions = useStudioStore((s) => s.chatSessions);
    const fetchChatSessions = useStudioStore((s) => s.fetchChatSessions);
    const setActiveSession = useStudioStore((s) => s.setActiveSession);
    const [exportOpen, setExportOpen] = useState(false);

    useEffect(() => {
        if (activeProjectId) {
            fetchStructure(activeProjectId);
        }
        fetchChatSessions();
    }, [activeProjectId, fetchStructure, fetchChatSessions]);

    useEffect(() => {
        const handler = () => setExportOpen(true);
        window.addEventListener('open:export', handler);
        return () => window.removeEventListener('open:export', handler);
    }, []);

    const counts = useMemo(() => countByType(structureTree), [structureTree]);

    const stats: StatCardProps[] = [
        {
            label: "Seasons",
            count: counts["season"] || 0,
            icon: <Layers className="w-5 h-5 text-white" />,
            gradient: "from-violet-500 to-purple-600",
        },
        {
            label: "Chapters",
            count: counts["chapter"] || 0,
            icon: <BookOpen className="w-5 h-5 text-white" />,
            gradient: "from-blue-500 to-cyan-500",
        },
        {
            label: "Scenes",
            count: counts["scene"] || 0,
            icon: <Film className="w-5 h-5 text-white" />,
            gradient: "from-emerald-500 to-teal-500",
        },
    ];

    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800/60 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                    Story Progress
                </span>
                <button
                    onClick={() => setExportOpen(true)}
                    className="ml-auto p-1.5 rounded-lg text-gray-500 hover:text-emerald-400 hover:bg-gray-800/50 transition-colors"
                    title="Export project"
                >
                    <Download className="w-3.5 h-3.5" />
                </button>
            </div>

            {/* Stat Grid */}
            <div className="p-3 grid grid-cols-3 gap-2">
                {stats.map((s) => (
                    <StatCard key={s.label} {...s} />
                ))}
            </div>

            {/* Total */}
            <div className="px-4 py-2 border-t border-gray-800/60 bg-gray-950/40 flex justify-between items-center">
                <span className="text-[10px] uppercase tracking-widest text-gray-600">
                    Total Elements
                </span>
                <span className="text-xs font-mono text-gray-400">
                    {Object.values(counts).reduce((a, b) => a + b, 0)}
                </span>
            </div>

            {/* Last Chat Session */}
            {chatSessions.length > 0 && (() => {
                const latest = chatSessions[0];
                const updatedMs = new Date(latest.updated_at).getTime();
                const diffH = Math.floor((Date.now() - updatedMs) / (1000 * 60 * 60));
                const timeAgo = diffH < 1 ? "just now" : diffH < 24 ? `${diffH}h ago` : `${Math.floor(diffH / 24)}d ago`;
                return (
                    <div className="px-3 pb-3 pt-1">
                        <div className="rounded-lg border border-gray-800 bg-gray-900/60 p-3 group hover:border-indigo-500/30 transition-all duration-200">
                            <div className="flex items-center gap-2 mb-2">
                                <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow">
                                    <MessageSquare className="w-3.5 h-3.5 text-white" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs font-semibold text-gray-200 truncate">{latest.name}</p>
                                    <div className="flex items-center gap-2 text-[10px] text-gray-500">
                                        <span className="flex items-center gap-0.5"><Clock className="w-2.5 h-2.5" />{timeAgo}</span>
                                        <span>·</span>
                                        <span>{latest.message_count} msgs</span>
                                    </div>
                                </div>
                            </div>
                            {latest.last_message_preview && (
                                <p className="text-[11px] text-gray-500 truncate mb-2">{latest.last_message_preview}</p>
                            )}
                            <button
                                onClick={() => {
                                    setActiveSession(latest.id);
                                    window.dispatchEvent(new CustomEvent('chat:open'));
                                }}
                                className="w-full py-1.5 text-[11px] font-medium rounded-md bg-indigo-600/20 text-indigo-300 border border-indigo-500/20 hover:bg-indigo-600/40 transition-colors"
                            >
                                Resume Session
                            </button>
                        </div>
                    </div>
                );
            })()}

            <ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />
        </div>
    );
}
