"use client";

import React from "react";
import { type LayoutSuggestion } from "@/lib/api";
import { X, Check } from "lucide-react";

interface LayoutSuggestionPanelProps {
    suggestion: LayoutSuggestion;
    sceneName: string;
    onApply: () => void;
    onDiscard: () => void;
}

export function LayoutSuggestionPanel({ suggestion, sceneName, onApply, onDiscard }: LayoutSuggestionPanelProps) {
    const getBeatColor = (beat: string) => {
        switch (beat.toLowerCase()) {
            case 'action': return 'bg-red-500/20 text-red-300 border-red-500/30';
            case 'dialogue': return 'bg-blue-500/20 text-blue-300 border-blue-500/30';
            case 'dramatic_reveal': return 'bg-purple-500/20 text-purple-300 border-purple-500/30';
            case 'transition': return 'bg-amber-500/20 text-amber-300 border-amber-500/30';
            case 'montage': return 'bg-teal-500/20 text-teal-300 border-teal-500/30';
            case 'emotional': return 'bg-pink-500/20 text-pink-300 border-pink-500/30';
            default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
        }
    };

    const getSizeWidth = (size: string) => {
        switch (size.toLowerCase()) {
            case 'large': return 'w-[280px]';
            case 'medium': return 'w-[200px]';
            case 'small': return 'w-[140px]';
            case 'splash': return 'w-full min-w-[400px] text-center';
            default: return 'w-[200px]';
        }
    };

    return (
        <div className="border border-indigo-500/30 rounded-xl bg-gray-900/80 overflow-hidden m-3 shadow-lg shadow-indigo-500/10">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-indigo-500/20 bg-indigo-950/30">
                <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold text-white">Layout Suggestion for &quot;{sceneName}&quot;</h3>
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${getBeatColor(suggestion.beat_type)}`}>
                        Beat Type: {suggestion.beat_type}
                    </span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs text-indigo-300 mr-2">{suggestion.suggested_panel_count} panels suggested</span>
                </div>
            </div>

            {/* Visual Preview */}
            <div className="p-4 bg-black/20 overflow-x-auto">
                <div className="flex flex-wrap gap-3">
                    {suggestion.layout.map((panel, idx) => (
                        <div
                            key={idx}
                            className={`${getSizeWidth(panel.size_hint)} bg-gray-800/80 border border-gray-700 p-3 rounded-lg flex flex-col gap-1.5`}
                        >
                            <div className="flex justify-between items-start">
                                <span className="text-xs font-semibold text-gray-300">
                                    Panel {panel.panel_number + 1}
                                    <span className="ml-1 text-[9px] text-gray-500">({panel.size_hint.toUpperCase()})</span>
                                </span>
                            </div>
                            <div className="text-[10px] font-mono text-indigo-400">
                                {panel.panel_type.toUpperCase()} • {panel.camera_angle.toUpperCase()}
                            </div>
                            <p className="text-xs text-gray-400 leading-snug break-words">
                                &quot;{panel.description_hint}&quot;
                            </p>
                        </div>
                    ))}
                </div>
            </div>

            {/* Analysis & Actions */}
            <div className="p-4 grid grid-cols-[1fr_auto] gap-6 items-end bg-gray-900/50">
                <div className="space-y-3">
                    <div>
                        <span className="text-xs font-semibold text-gray-400">Reasoning:</span>
                        <p className="text-xs text-gray-300 mt-0.5 leading-relaxed">{suggestion.reasoning}</p>
                    </div>
                    {suggestion.pacing_notes && (
                        <div>
                            <span className="text-xs font-semibold text-gray-400">Pacing:</span>
                            <p className="text-xs text-gray-300 mt-0.5 leading-relaxed">{suggestion.pacing_notes}</p>
                        </div>
                    )}
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={onDiscard}
                        className="px-3 py-2 text-xs text-gray-400 hover:text-white transition-colors border border-gray-700 hover:bg-gray-800 rounded-lg"
                    >
                        Discard
                    </button>
                    <button
                        onClick={onApply}
                        className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded-lg shadow-sm transition-colors"
                    >
                        <Check className="w-3.5 h-3.5" />
                        Apply & Generate
                    </button>
                </div>
            </div>
        </div>
    );
}
