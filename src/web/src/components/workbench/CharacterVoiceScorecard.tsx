"use client";

import { useState } from "react";
import { Loader2, AlertTriangle, MessageSquareQuote, Shuffle } from "lucide-react";
import { toast } from "sonner";
import { api, VoiceProfile, VoiceScorecardResponse } from "@/lib/api";

interface CharacterVoiceScorecardProps {
    characterId: string;
    characterName: string;
}

function MetricBar({
    value,
    max,
    label,
    formatPercent = false,
    gradient = false,
}: {
    value: number;
    max: number;
    label: string;
    formatPercent?: boolean;
    gradient?: boolean;
}) {
    const percentage = Math.min((value / max) * 100, 100);
    const displayValue = formatPercent
        ? `${Math.round(value * 100)}%`
        : value.toFixed(1);

    return (
        <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
                <span>{label}</span>
                <span className="text-gray-300 font-medium">{displayValue}</span>
            </div>
            <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={`h-full rounded-full ${gradient
                            ? "bg-gradient-to-r from-blue-500 to-purple-500"
                            : "bg-gray-400"
                        }`}
                    style={{ width: `${percentage}%` }}
                />
            </div>
            {gradient && (
                <div className="flex justify-between text-[10px] text-gray-500 mt-0.5">
                    <span>Casual</span>
                    <span>Formal</span>
                </div>
            )}
        </div>
    );
}

export function CharacterVoiceScorecard({
    characterId,
    characterName,
}: CharacterVoiceScorecardProps) {
    const [data, setData] = useState<VoiceScorecardResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    const handleAnalyze = async (allCharacters = false) => {
        setIsLoading(true);
        try {
            const ids = allCharacters ? undefined : [characterId];
            const result = await api.getVoiceScorecard(ids);
            setData(result);
            toast.success("Voice analysis complete");
        } catch (err: any) {
            toast.error(err.message || "Failed to analyze voice patterns");
        } finally {
            setIsLoading(false);
        }
    };

    const profile = data?.profiles.find((p) => p.character_id === characterId);

    // Filter warnings relevant to this character
    const relevantWarnings = data?.warnings.filter(w => w.includes(characterName)) || [];

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-1.5">
                    <MessageSquareQuote className="w-4 h-4 text-emerald-500" />
                    Voice Profile
                </h3>
                <div className="flex gap-2">
                    <button
                        onClick={() => handleAnalyze(false)}
                        disabled={isLoading}
                        className="px-2 py-1 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-xs font-medium text-gray-300 rounded transition-colors flex items-center gap-1"
                    >
                        {isLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : null}
                        Analyze
                    </button>
                    {data && (
                        <button
                            onClick={() => handleAnalyze(true)}
                            disabled={isLoading}
                            title="Compare all characters"
                            className="px-2 py-1 bg-gray-800 hover:bg-gray-700 disabled:opacity-50 text-xs font-medium text-gray-300 rounded transition-colors flex items-center justify-center"
                        >
                            <Shuffle className="w-3 h-3" />
                        </button>
                    )}
                </div>
            </div>

            {!data && !isLoading && (
                <p className="text-xs text-gray-500">
                    Run analysis to generate metrics based on {characterName}'s dialogue.
                </p>
            )}

            {profile && (
                <div className="space-y-4 pt-2">
                    {/* Metrics */}
                    <div>
                        <MetricBar
                            label="Avg Sentence Length (words)"
                            value={profile.avg_sentence_length}
                            max={30}
                        />
                        <MetricBar
                            label="Vocabulary Diversity"
                            value={profile.vocabulary_diversity}
                            max={1}
                            formatPercent
                        />
                        <MetricBar
                            label="Formality Level"
                            value={profile.formality_score}
                            max={1}
                            formatPercent
                            gradient
                        />
                    </div>

                    {/* Top Phrases */}
                    {profile.top_phrases.length > 0 && (
                        <div>
                            <span className="text-xs text-gray-500 mb-1.5 block">
                                Distinctive Phrases
                            </span>
                            <div className="flex flex-wrap gap-1.5">
                                {profile.top_phrases.map((phrase, i) => (
                                    <span
                                        key={i}
                                        className="px-2 py-0.5 rounded border border-gray-700 bg-gray-800/50 text-[11px] text-gray-300"
                                    >
                                        "{phrase}"
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Warnings */}
                    {relevantWarnings.length > 0 && (
                        <div className="space-y-2 mt-4">
                            {relevantWarnings.map((warning, i) => {
                                // Parse the string if it contains "Suggestion:"
                                const parts = warning.split("Suggestion:");
                                const mainWarning = parts[0];
                                const suggestion = parts.length > 1 ? parts[1] : null;

                                return (
                                    <div
                                        key={i}
                                        className="p-2.5 rounded bg-yellow-900/10 border border-yellow-700/30 flex items-start gap-2"
                                    >
                                        <AlertTriangle className="w-4 h-4 text-yellow-500 mt-0.5 shrink-0" />
                                        <div>
                                            <p className="text-xs text-yellow-200/90 leading-relaxed font-medium">
                                                {mainWarning.replace("⚠️", "")}
                                            </p>
                                            {suggestion && (
                                                <p className="text-[11px] text-yellow-400/80 mt-1">
                                                    Suggestion: {suggestion}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    <div className="text-[10px] text-gray-600 pt-2 border-t border-gray-800">
                        Based on {profile.dialogue_sample_count} dialogue samples.
                    </div>
                </div>
            )}
        </div>
    );
}
