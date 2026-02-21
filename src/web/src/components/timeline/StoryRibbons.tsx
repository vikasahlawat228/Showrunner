import React, { useState, useEffect } from "react";
import { api, CharacterRibbonResponse } from "@/lib/api";
import { useStudioStore } from "@/lib/store";
import { Loader2 } from "lucide-react";

const PALETTE = [
    "#ef4444", // red-500
    "#3b82f6", // blue-500
    "#10b981", // emerald-500
    "#f59e0b", // amber-500
    "#8b5cf6", // violet-500
    "#ec4899", // pink-500
    "#14b8a6", // teal-500
    "#f97316", // orange-500
    "#06b6d4", // cyan-500
    "#eab308", // yellow-500
    "#6366f1", // indigo-500
    "#d946ef", // fuchsia-500
];

const ROW_HEIGHT = 40;
const MAX_RIBBON_HEIGHT = 24;
const SVG_PADDING_Y = 20;

export function StoryRibbons({ chapter }: { chapter?: number }) {
    const [data, setData] = useState<CharacterRibbonResponse[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [hoveredData, setHoveredData] = useState<{
        x: number;
        y: number;
        charName: string;
        sceneName: string;
        prominence: number;
    } | null>(null);

    useEffect(() => {
        let active = true;
        const fetchData = async () => {
            setLoading(true);
            setError(null);
            try {
                const response = await api.getCharacterRibbons(chapter);
                if (active) setData(response);
            } catch (err: any) {
                if (active) setError(err.message || "Failed to load story ribbons.");
            } finally {
                if (active) setLoading(false);
            }
        };
        fetchData();
        return () => { active = false; };
    }, [chapter]);

    if (loading) {
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-8 flex items-center justify-center text-gray-500">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span className="text-sm">Loading ribbons...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div className="bg-red-900/20 text-red-400 border border-red-900 p-3 rounded text-sm mb-0">
                    {error}
                </div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-500 text-sm">
                No character presence data available for these scenes.
            </div>
        );
    }

    // Extract all unique characters to establish rows
    const allCharIds = new Set<string>();
    const charIdToName: Record<string, string> = {};
    data.forEach((scene) => {
        scene.characters?.forEach((c) => {
            allCharIds.add(c.character_id);
            charIdToName[c.character_id] = c.character_name;
        });
    });

    const charsList = Array.from(allCharIds);
    // Sort them loosely alphabetically so order is deterministic
    charsList.sort((a, b) => charIdToName[a].localeCompare(charIdToName[b]));

    const width = Math.max(800, data.length * 80 + 150);
    const height = Math.max(200, charsList.length * ROW_HEIGHT + SVG_PADDING_Y * 2 + 30);
    const labelWidth = 120;
    const columnWidth = (width - labelWidth - 20) / data.length;

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 relative">
            <h3 className="text-lg font-semibold text-gray-200 mb-4 px-2">Story Ribbons</h3>

            <div className="w-full overflow-x-auto scrollbar-thin scrollbar-thumb-gray-700">
                <div style={{ minWidth: `${width}px`, height: `${height}px`, position: "relative" }}>
                    <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
                        {/* Draw character labels and base lines */}
                        {charsList.map((charId, idx) => {
                            const yCenter = SVG_PADDING_Y + idx * ROW_HEIGHT + ROW_HEIGHT / 2;
                            return (
                                <g key={`row-${charId}`}>
                                    <text
                                        x={labelWidth - 10}
                                        y={yCenter}
                                        fill="#9CA3AF"
                                        fontSize="12"
                                        textAnchor="end"
                                        alignmentBaseline="middle"
                                    >
                                        {charIdToName[charId]}
                                    </text>
                                    <line
                                        x1={labelWidth}
                                        y1={yCenter}
                                        x2={width - 20}
                                        y2={yCenter}
                                        stroke="#374151"
                                        strokeWidth="1"
                                    />
                                </g>
                            );
                        })}

                        {/* Draw ribbons per scene */}
                        {data.map((scene, colIdx) => {
                            const xPos = labelWidth + colIdx * columnWidth;

                            // Draw scene X-axis labels at bottom
                            const bottomY = height - 10;

                            return (
                                <g key={`col-${scene.scene_id}`}>
                                    {/* Scene dividing line (very faint) */}
                                    <line
                                        x1={xPos}
                                        y1={SVG_PADDING_Y}
                                        x2={xPos}
                                        y2={bottomY - 20}
                                        stroke="#1F2937"
                                        strokeWidth="1"
                                        strokeDasharray="4 4"
                                    />

                                    {/* Scene label */}
                                    <text
                                        x={xPos + columnWidth / 2}
                                        y={bottomY}
                                        fill="#6B7280"
                                        fontSize="10"
                                        textAnchor="middle"
                                    >
                                        Sc{scene.scene_number}
                                    </text>

                                    {/* Draw characters in this scene */}
                                    {charsList.map((charId, rowIdx) => {
                                        const charData = scene.characters?.find(c => c.character_id === charId);
                                        const color = PALETTE[rowIdx % PALETTE.length];
                                        const yCenter = SVG_PADDING_Y + rowIdx * ROW_HEIGHT + ROW_HEIGHT / 2;

                                        if (charData && charData.prominence > 0) {
                                            const rectHeight = Math.max(2, charData.prominence * MAX_RIBBON_HEIGHT);
                                            const rectY = yCenter - rectHeight / 2;

                                            return (
                                                <rect
                                                    key={`rect-${charId}-${scene.scene_id}`}
                                                    x={xPos}
                                                    y={rectY}
                                                    width={columnWidth - 2} // -2 for slight gap
                                                    height={rectHeight}
                                                    fill={color}
                                                    rx={2}
                                                    onMouseEnter={(e) => {
                                                        const rect = e.currentTarget.getBoundingClientRect();
                                                        setHoveredData({
                                                            x: e.clientX,
                                                            y: e.clientY - rectHeight - 10,
                                                            charName: charIdToName[charId],
                                                            sceneName: scene.scene_name,
                                                            prominence: charData.prominence
                                                        });
                                                    }}
                                                    onMouseLeave={() => setHoveredData(null)}
                                                    className="transition-all duration-200 cursor-pointer hover:opacity-80 stroke-gray-900"
                                                    strokeWidth="1"
                                                />
                                            );
                                        }
                                        return null;
                                    })}
                                </g>
                            );
                        })}
                    </svg>

                    {/* Tooltip (Portal-like floating div relative to viewport) */}
                    {hoveredData && (
                        <div
                            className="fixed bg-gray-800 border border-gray-700 p-2 rounded shadow-xl text-xs z-50 pointer-events-none transform -translate-x-1/2 -translate-y-full"
                            style={{ left: hoveredData.x, top: hoveredData.y - 10 }}
                        >
                            <div className="font-semibold text-gray-200 mb-1">{hoveredData.charName}</div>
                            <div className="text-gray-400">{hoveredData.sceneName}</div>
                            <div className="text-gray-300 mt-1">Prominence: {Math.round(hoveredData.prominence * 100)}%</div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
