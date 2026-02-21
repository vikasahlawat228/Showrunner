import React, { useState, useEffect } from "react";
import { api, EmotionalArcResponse } from "@/lib/api";
import { useStudioStore } from "@/lib/store";
import { Loader2, RefreshCw } from "lucide-react";
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from "recharts";

export function EmotionalArcChart({ chapter }: { chapter?: number }) {
    const [data, setData] = useState<EmotionalArcResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const selectItem = useStudioStore((state) => state.selectItem);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await api.getEmotionalArc(chapter);
            setData(response);
        } catch (err: any) {
            setError(err.message || "Failed to analyze emotional arc.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [chapter]);

    const handleDotClick = (datakey: any, event: any) => {
        if (event && event.payload) {
            const { scene_id, scene_name } = event.payload;
            if (scene_id) {
                selectItem({ id: scene_id, type: "scene", name: scene_name });
            }
        }
    };

    const CustomTooltip = ({ active, payload, label }: any) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-gray-800 border border-gray-700 p-3 rounded shadow-lg text-sm">
                    <p className="font-semibold text-gray-200 mb-1">{payload[0].payload.scene_name}</p>
                    <p className="text-gray-400 text-xs mb-2 truncate max-w-[250px]">
                        {payload[0].payload.summary}
                    </p>
                    {payload.map((entry: any, i: number) => (
                        <div key={i} className="flex justify-between items-center gap-4">
                            <span style={{ color: entry.color }} className="capitalize">
                                {entry.name}:
                            </span>
                            <span className="text-gray-300 font-mono">
                                {entry.value.toFixed(2)}
                            </span>
                        </div>
                    ))}
                </div>
            );
        }
        return null;
    };

    const getPacingBadgeColor = (grade: string) => {
        switch (grade) {
            case "A": return "bg-green-500/20 text-green-400 border-green-500/30";
            case "B": return "bg-teal-500/20 text-teal-400 border-teal-500/30";
            case "C": return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
            case "D": return "bg-orange-500/20 text-orange-400 border-orange-500/30";
            case "F": return "bg-red-500/20 text-red-400 border-red-500/30";
            default: return "bg-gray-500/20 text-gray-400 border-gray-500/30";
        }
    };

    // Convert scores to chart format
    const chartData = data?.scores.map((s) => ({
        ...s,
        label: `Sc${s.scene_number}`,
    })) || [];

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col gap-4">
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-200">Emotional Arc</h3>
                <button
                    onClick={fetchData}
                    disabled={loading}
                    className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 text-gray-300 px-3 py-1.5 rounded transition-colors disabled:opacity-50 text-sm font-medium border border-gray-700"
                >
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                    Analyze
                </button>
            </div>

            {error && (
                <div className="bg-red-900/20 text-red-400 border border-red-900 p-3 rounded text-sm">
                    {error}
                </div>
            )}

            {loading && !data && (
                <div className="h-[300px] flex items-center justify-center text-gray-500 flex-col gap-2">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <p className="text-sm">Running ML analysis on scenes...</p>
                </div>
            )}

            {data && chartData.length > 0 && (
                <>
                    <div className="h-[300px] w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#374151" vertical={false} />
                                <XAxis dataKey="label" stroke="#9CA3AF" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                                <YAxis domain={[0, 1]} stroke="#9CA3AF" tick={{ fill: "#9CA3AF", fontSize: 12 }} />
                                <Tooltip content={<CustomTooltip />} />
                                <Legend wrapperStyle={{ fontSize: '12px', color: '#9CA3AF' }} />

                                <Line type="monotone" dataKey="tension" stroke="#f87171" strokeWidth={2} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6, onClick: handleDotClick }} />
                                <Line type="monotone" dataKey="hope" stroke="#4ade80" strokeWidth={2} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6, onClick: handleDotClick }} />
                                <Line type="monotone" dataKey="conflict" stroke="#fb923c" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5, onClick: handleDotClick }} />
                                <Line type="monotone" dataKey="joy" stroke="#facc15" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5, onClick: handleDotClick }} />
                                <Line type="monotone" dataKey="sadness" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5, onClick: handleDotClick }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-2">
                        <div className="bg-gray-800/50 border border-gray-700 rounded p-3">
                            <div className="text-xs text-gray-500 uppercase font-semibold mb-2">Pacing Grade</div>
                            <div className="flex items-center gap-3">
                                <span className={`px-2.5 py-1 rounded text-lg font-bold border ${getPacingBadgeColor(data.pacing_grade)}`}>
                                    {data.pacing_grade}
                                </span>
                                {data.recommendations.length > 0 && (
                                    <span className="text-xs text-gray-400 line-clamp-2">
                                        {data.recommendations[0]}
                                    </span>
                                )}
                            </div>
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700 rounded p-3">
                            <div className="text-xs text-gray-500 uppercase font-semibold mb-2">Peak Moments</div>
                            {data.peak_moments.length === 0 ? (
                                <div className="text-sm text-gray-400">No intense peaks detected.</div>
                            ) : (
                                <ul className="text-sm text-gray-300 space-y-1 max-h-[60px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-gray-600">
                                    {data.peak_moments.slice(0, 3).map((p, i) => {
                                        const sceneName = chartData.find(c => c.scene_id === p.scene_id)?.scene_name || 'Unknown';
                                        return (
                                            <li key={i} className="flex justify-between truncate">
                                                <span>⭐ {sceneName}</span>
                                                <span className="text-gray-500 text-xs ml-2">({p.emotion})</span>
                                            </li>
                                        );
                                    })}
                                </ul>
                            )}
                        </div>

                        <div className="bg-gray-800/50 border border-gray-700 rounded p-3 lg:col-span-2">
                            <div className="text-xs text-gray-500 uppercase font-semibold mb-2">Flat Zones (Warnings)</div>
                            {data.flat_zones.length === 0 ? (
                                <div className="text-sm text-green-400/80">No significant flat zones detected.</div>
                            ) : (
                                <ul className="text-sm text-orange-400/90 space-y-1">
                                    {data.flat_zones.map((fz, i) => (
                                        <li key={i} className="flex items-start gap-2">
                                            <span className="mt-0.5 text-[10px]">⚠️</span>
                                            <span>
                                                <span className="font-medium text-gray-300">{fz.start_scene} ➔ {fz.end_scene}</span>: {fz.reason}
                                            </span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </div>
                    </div>
                </>
            )}

            {!loading && !data && !error && (
                <div className="text-center py-8 text-gray-500 text-sm">
                    Click Analyze to generate the emotional arc for these scenes.
                </div>
            )}
        </div>
    );
}
