"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { ArrowLeft, BookOpen, Clock, Activity, AlertTriangle, Play, Pause, FastForward } from "lucide-react";
import { api, ReadingSimResult, PanelReadingMetrics } from "@/lib/api";

export default function PreviewSimulatorPage() {
    const [chapter, setChapter] = useState(1);
    const [simData, setSimData] = useState<ReadingSimResult[]>([]);
    const [loading, setLoading] = useState(true);

    // Auto-scroll state
    const [isPlaying, setIsPlaying] = useState(false);
    const [speedMultiplier, setSpeedMultiplier] = useState(1.0);
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const animationRef = useRef<number>(0);

    useEffect(() => {
        const fetchSim = async () => {
            setLoading(true);
            try {
                const results = await api.getReadingSimChapter(chapter);
                setSimData(results || []);
            } catch (err) {
                console.error("Failed to load sim:", err);
                setSimData([]);
            } finally {
                setLoading(false);
            }
        };
        fetchSim();
    }, [chapter]);

    // Smooth auto-scroll physics engine
    useEffect(() => {
        if (!isPlaying || !scrollContainerRef.current) {
            cancelAnimationFrame(animationRef.current || 0);
            return;
        }

        let lastTime = performance.now();
        const container = scrollContainerRef.current;

        // Target pixels per second (average speed, user sets multiplier to fine tune)
        // A generic reading speed assumption for webtoons is ~150px / sec
        const BASE_PX_PER_SEC = 60 * speedMultiplier;

        const smoothStep = (time: number) => {
            if (!isPlaying || !container) return;
            const deltaSec = (time - lastTime) / 1000;
            lastTime = time;

            if (deltaSec > 0 && deltaSec < 0.1) { // cap delta to prevent jumps
                container.scrollTop += (BASE_PX_PER_SEC * deltaSec);

                // Pause if hit bottom
                if (container.scrollTop >= (container.scrollHeight - container.clientHeight - 2)) {
                    setIsPlaying(false);
                    return; // Done scrolling
                }
            }
            animationRef.current = requestAnimationFrame(smoothStep);
        };

        animationRef.current = requestAnimationFrame(smoothStep);

        return () => {
            cancelAnimationFrame(animationRef.current || 0);
        };
    }, [isPlaying, speedMultiplier]);


    const renderPanelCard = (p: PanelReadingMetrics) => {
        const typeBorder = {
            fast: "border-emerald-900/50",
            medium: "border-gray-800",
            slow: "border-red-900/50",
        }[p.pacing_type] || "border-gray-800";

        const typeBg = p.is_info_dense ? "bg-amber-900/10" : "bg-gray-900/50";

        // Approximating height roughly proportional to reading time
        const minHeight = 120;
        const calcHeight = Math.max(minHeight, p.estimated_reading_seconds * 30);

        return (
            <div
                key={p.panel_id}
                className={`w-full max-w-2xl mx-auto border-2 ${typeBorder} ${typeBg} rounded-xl p-5 shadow-lg relative mb-8 flex flex-col justify-center transition-all`}
                style={{ minHeight: `${calcHeight}px` }}
            >
                {p.is_info_dense && (
                    <div className="absolute top-2 right-2 flex items-center gap-1 text-[10px] bg-amber-900/30 text-amber-500 px-2 py-0.5 rounded-full border border-amber-900/50">
                        <AlertTriangle className="w-3 h-3" /> INFO DENSE
                    </div>
                )}
                <div className="absolute -left-12 top-1/2 -translate-y-1/2 text-gray-600 text-xs font-mono">
                    #{p.panel_number}
                </div>
                <div className="flex justify-between items-start mb-3">
                    <span className="text-xs font-semibold text-gray-500 tracking-wider uppercase">
                        {p.panel_type.replace(/_/g, " ")} Panel
                    </span>
                    <span className="flex items-center gap-1 text-xs text-gray-400 bg-gray-950 px-2 py-1 rounded">
                        <Clock className="w-3 h-3" /> {p.estimated_reading_seconds.toFixed(1)}s
                    </span>
                </div>

                {/* Fake content representation to simulate scroll space */}
                <div className="flex-1 border border-dashed border-gray-800 rounded bg-gray-950/20 flex items-center justify-center">
                    <div className="text-center p-4">
                        <div className="h-2 w-3/4 mx-auto bg-gray-800 rounded mb-2"></div>
                        <div className="h-2 w-full bg-gray-800 rounded mb-2"></div>
                        {p.text_density > 0.4 && <div className="h-2 w-5/6 mx-auto bg-gray-800 rounded mb-2"></div>}
                        {p.text_density > 0.7 && <div className="h-2 w-full mx-auto bg-gray-800 rounded mb-2"></div>}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white overflow-hidden">
            {/* Top bar */}
            <header className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
                <div className="flex items-center gap-3">
                    <Link
                        href="/storyboard"
                        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-300 transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Storyboard
                    </Link>
                    <div className="w-px h-4 bg-gray-800" />
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-4 h-4 text-emerald-400" />
                        <span className="text-sm font-semibold text-gray-200">
                            Reader Simulation
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">Chapter</span>
                        <select
                            className="bg-gray-900 border border-gray-700 rounded px-3 py-1 text-sm text-white focus:outline-none focus:border-emerald-500"
                            value={chapter}
                            onChange={(e) => {
                                setChapter(parseInt(e.target.value));
                                setIsPlaying(false);
                            }}
                        >
                            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                    </div>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Scroll Area (Left) */}
                <div
                    ref={scrollContainerRef}
                    className="flex-1 overflow-y-auto scroll-smooth py-12 px-8 custom-scrollbar border-r border-gray-800 relative bg-black/50"
                >
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-gray-500">
                            Simulating metrics...
                        </div>
                    ) : simData.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <AlertTriangle className="w-8 h-8 mb-4 opacity-50" />
                            <p>No storyboard panels found for Chapter {chapter}.</p>
                            <Link href="/storyboard" className="mt-4 text-emerald-400 text-sm hover:underline">
                                Go to Storyboard
                            </Link>
                        </div>
                    ) : (
                        simData.map((scene) => (
                            <div key={scene.scene_id} className="mb-24">
                                <div className="flex items-center justify-center gap-4 mb-16 opacity-50">
                                    <div className="h-px bg-gray-700 flex-1"></div>
                                    <span className="text-xs uppercase tracking-widest text-gray-400">{scene.scene_name}</span>
                                    <div className="h-px bg-gray-700 flex-1"></div>
                                </div>
                                {scene.panels.map(p => renderPanelCard(p))}
                            </div>
                        ))
                    )}
                </div>

                {/* Sidebar (Right) */}
                <aside className="w-80 bg-gray-950 shrink-0 overflow-y-auto p-5 border-l border-gray-800">
                    <h2 className="text-base font-semibold text-gray-200 mb-6 flex items-center gap-2">
                        <Activity className="w-4 h-4 text-emerald-400" /> Analysis
                    </h2>

                    <div className="space-y-6">
                        {simData.map(scene => (
                            <div key={scene.scene_id} className="bg-gray-900 p-4 rounded-lg border border-gray-800">
                                <div className="text-sm font-medium text-gray-300 mb-3 truncate" title={scene.scene_name}>
                                    {scene.scene_name}
                                </div>

                                <div className="flex justify-between text-xs text-gray-500 mb-1">
                                    <span>Pacing Map</span>
                                    <span>{scene.total_reading_seconds}s</span>
                                </div>

                                {/* Heatmap */}
                                <div className="flex h-4 gap-[1px] mb-4">
                                    {scene.panels.map(p => {
                                        const color = p.pacing_type === 'fast' ? 'bg-emerald-500'
                                            : p.pacing_type === 'slow' ? 'bg-red-500'
                                                : 'bg-gray-600';
                                        return (
                                            <div
                                                key={p.panel_id}
                                                className={`flex-1 rounded-sm ${color}`}
                                                title={`Panel ${p.panel_number}: ${p.pacing_type}`}
                                            ></div>
                                        );
                                    })}
                                </div>

                                <div className="flex items-center justify-between mb-4">
                                    <span className="text-xs text-gray-400">Engagement Score</span>
                                    <span className={`text-xs font-bold ${scene.engagement_score > 0.7 ? 'text-emerald-400' : 'text-amber-400'}`}>
                                        {Math.round(scene.engagement_score * 100)}%
                                    </span>
                                </div>

                                {scene.pacing_dead_zones.length > 0 && (
                                    <div className="mb-3">
                                        <div className="flex items-center gap-1 text-xs text-red-400 mb-1">
                                            <AlertTriangle className="w-3 h-3" /> Dead Zones Detected
                                        </div>
                                        {scene.pacing_dead_zones.map((w, i) => (
                                            <div key={i} className="text-[10px] text-gray-500 ml-4">
                                                panels {w.start_panel}-{w.end_panel}: {w.reason}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {scene.recommendations.length > 0 && (
                                    <div className="mt-4 pt-3 border-t border-gray-800">
                                        <span className="text-xs font-semibold text-gray-400 block mb-2">Suggestions</span>
                                        <ul className="text-[11px] text-gray-500 list-disc list-inside space-y-1">
                                            {scene.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </aside>
            </div>

            {/* Bottom Playback Controls */}
            <footer className="h-16 flex items-center justify-center gap-6 border-t border-gray-800 bg-gray-900 shrink-0">
                <div className="flex items-center gap-4 bg-gray-950 p-2 border border-gray-800 rounded-full px-6">
                    <button
                        className="p-2 hover:bg-gray-800 rounded-full text-gray-400 hover:text-white transition-colors"
                        onClick={() => setIsPlaying(!isPlaying)}
                    >
                        {isPlaying ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5 ml-0.5" />}
                    </button>
                    <div className="w-px h-6 bg-gray-800"></div>
                    <div className="flex items-center gap-2">
                        <FastForward className="w-4 h-4 text-gray-500" />
                        <select
                            className="bg-transparent text-sm text-gray-300 focus:outline-none"
                            value={speedMultiplier}
                            onChange={(e) => setSpeedMultiplier(parseFloat(e.target.value))}
                        >
                            <option value={0.5}>0.5x</option>
                            <option value={1.0}>1.0x</option>
                            <option value={1.5}>1.5x</option>
                            <option value={2.0}>2.0x</option>
                        </select>
                    </div>
                </div>
            </footer>
        </div>
    );
}
