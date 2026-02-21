import React, { useState } from "react";
import { Sparkles, Plus, X, ChevronUp, ChevronDown } from "lucide-react";
import type { BrainstormSuggestion } from "@/lib/api";

interface SuggestionPanelProps {
    suggestion: BrainstormSuggestion | null;
    isLoading: boolean;
    onApplyEdge: (sourceId: string, targetId: string, label: string) => void;
    onApplyCard: (text: string, nearCardId: string) => void;
    onClose: () => void;
}

export function SuggestionPanel({
    suggestion,
    isLoading,
    onApplyEdge,
    onApplyCard,
    onClose,
}: SuggestionPanelProps) {
    const [isExpanded, setIsExpanded] = useState(true);

    if (!suggestion && !isLoading) {
        return null; // Hidden when no suggestions and not loading
    }

    return (
        <div
            className={`absolute bottom-6 left-1/2 -translate-x-1/2 w-[500px] max-w-[90vw] bg-gray-900/95 backdrop-blur-md border border-gray-800 rounded-xl shadow-2xl transition-all duration-300 z-50 overflow-hidden flex flex-col ${isExpanded ? "max-h-[60vh]" : "max-h-14"
                }`}
        >
            {/* Header / Handle */}
            <div
                className="flex items-center justify-between px-4 py-3 shrink-0 border-b border-gray-800 cursor-pointer bg-gray-900/50 hover:bg-gray-900/80 transition-colors"
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-amber-500" />
                    <span className="font-semibold text-sm text-gray-200">
                        {isLoading ? "Analyzing Canvas..." : "AI Suggestions"}
                    </span>
                    {!isLoading && suggestion && (
                        <span className="ml-2 text-[10px] font-medium px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                            {suggestion.suggested_edges?.length || 0} edges,{" "}
                            {suggestion.suggested_cards?.length || 0} cards
                        </span>
                    )}
                </div>
                <div className="flex items-center gap-1">
                    <button
                        className="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-gray-800 rounded-md transition-colors"
                        onClick={(e) => {
                            e.stopPropagation();
                            setIsExpanded(!isExpanded);
                        }}
                    >
                        {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                        ) : (
                            <ChevronUp className="w-4 h-4" />
                        )}
                    </button>
                    <button
                        className="p-1.5 text-gray-500 hover:text-red-400 hover:bg-gray-800 rounded-md transition-colors ml-1"
                        onClick={(e) => {
                            e.stopPropagation();
                            onClose();
                        }}
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>

            {/* Content Area */}
            <div className={`overflow-y-auto p-4 space-y-6 ${!isExpanded && "hidden"}`}>
                {isLoading ? (
                    <div className="py-8 flex flex-col items-center justify-center gap-4 text-gray-400">
                        <div className="w-8 h-8 rounded-full border-2 border-amber-500/30 border-t-amber-500 animate-spin" />
                        <p className="text-sm">Finding connections and gaps...</p>
                    </div>
                ) : suggestion ? (
                    <>
                        {/* New Cards Section */}
                        {suggestion.suggested_cards && suggestion.suggested_cards.length > 0 && (
                            <div className="space-y-3">
                                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    Suggested Missing Links
                                </h3>
                                <div className="space-y-2">
                                    {suggestion.suggested_cards.map((card, idx) => (
                                        <div
                                            key={`card-${idx}`}
                                            className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-3 text-sm flex gap-3 group hover:border-amber-500/30 hover:bg-gray-800 transition-colors"
                                        >
                                            <div className="flex-1">
                                                <div className="font-medium text-gray-200 mb-1 leading-snug">
                                                    {card.text}
                                                </div>
                                                <div className="text-xs text-gray-500 italic">
                                                    {card.reasoning}
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => onApplyCard(card.text, card.near_card_id)}
                                                className="shrink-0 h-8 self-center px-2 py-1 bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 text-xs font-medium rounded border border-amber-500/20 transition-colors flex items-center gap-1 opacity-80 group-hover:opacity-100"
                                            >
                                                <Plus className="w-3 h-3" /> Add
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Edges Section */}
                        {suggestion.suggested_edges && suggestion.suggested_edges.length > 0 && (
                            <div className="space-y-3">
                                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                                    Suggested Connections
                                </h3>
                                <div className="space-y-2">
                                    {suggestion.suggested_edges.map((edge, idx) => (
                                        <div
                                            key={`edge-${idx}`}
                                            className="bg-gray-800/60 border border-gray-700/50 rounded-lg p-3 text-sm flex flex-col gap-2 group hover:border-emerald-500/30 hover:bg-gray-800 transition-colors"
                                        >
                                            <div className="flex items-center gap-2 text-gray-300">
                                                <span className="font-mono text-[10px] bg-gray-900 px-1.5 py-0.5 rounded text-gray-500">
                                                    {edge.source.slice(0, 8)}
                                                </span>
                                                <span className="text-emerald-400/80 text-xs">
                                                    ── {edge.label} ──→
                                                </span>
                                                <span className="font-mono text-[10px] bg-gray-900 px-1.5 py-0.5 rounded text-gray-500">
                                                    {edge.target.slice(0, 8)}
                                                </span>
                                            </div>
                                            <div className="flex gap-3 mt-1">
                                                <div className="flex-1 text-xs text-gray-500 italic">
                                                    {edge.reasoning}
                                                </div>
                                                <button
                                                    onClick={() => onApplyEdge(edge.source, edge.target, edge.label)}
                                                    className="shrink-0 px-2 py-1 bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 text-xs font-medium rounded border border-emerald-500/20 transition-colors flex items-center gap-1 opacity-80 group-hover:opacity-100 h-6"
                                                >
                                                    <Plus className="w-3 h-3" /> Connect
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Themes Section */}
                        {suggestion.themes && suggestion.themes.length > 0 && (
                            <div className="pt-2">
                                <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
                                    Identified Themes
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {suggestion.themes.map((theme, idx) => (
                                        <div
                                            key={`theme-${idx}`}
                                            className="px-2 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs rounded-md flex items-center gap-2 font-medium"
                                        >
                                            {theme.name}
                                            <span className="bg-blue-900/50 text-blue-300 px-1.5 py-0.5 rounded text-[10px]">
                                                {theme.card_ids.length} cards
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {(!suggestion.suggested_cards?.length && !suggestion.suggested_edges?.length && !suggestion.themes?.length) && (
                            <div className="text-center py-4 text-sm text-gray-500">
                                No new suggestions found based on the current canvas. Try adding more ideas!
                            </div>
                        )}
                    </>
                ) : null}
            </div>
        </div>
    );
}

export default SuggestionPanel;
