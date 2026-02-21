"use client";

import React, { useState, useEffect } from "react";
import { api } from "@/lib/api";
import { Loader2, Globe, Replace, ArrowDown, X, AlertTriangle, ChevronDown, ChevronRight, Check } from "lucide-react";

interface InlineTranslationProps {
    sourceText: string;
    onReplace: (translatedText: string) => void;
    onInsertBelow: (translatedText: string) => void;
    onClose: () => void;
}

const LANGUAGES = [
    { value: "en", label: "English" },
    { value: "ja", label: "Japanese" },
    { value: "ko", label: "Korean" },
    { value: "zh", label: "Chinese" },
    { value: "es", label: "Spanish" },
    { value: "fr", label: "French" },
];

export function InlineTranslation({
    sourceText,
    onReplace,
    onInsertBelow,
    onClose,
}: InlineTranslationProps) {
    const [sourceLang, setSourceLang] = useState("en");
    const [targetLang, setTargetLang] = useState("ja");
    const [isTranslating, setIsTranslating] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [showNotes, setShowNotes] = useState(false);
    const [showFlags, setShowFlags] = useState(false);

    const handleTranslate = async () => {
        if (!sourceText.trim()) return;
        setIsTranslating(true);
        setError(null);
        try {
            const res = await api.translateText({
                text: sourceText,
                source_language: sourceLang,
                target_language: targetLang,
            });
            setResult(res);
            if (res.cultural_flags?.length > 0) setShowFlags(true);
            if (res.adaptation_notes?.length > 0) setShowNotes(true);
        } catch (err: any) {
            setError(err.message || "Failed to translate");
        } finally {
            setIsTranslating(false);
        }
    };

    // Auto-translate on mount if we have text but not too long
    useEffect(() => {
        if (sourceText.length > 0 && sourceText.length < 500) {
            handleTranslate();
        }
    }, [sourceText]);

    return (
        <div className="flex flex-col border border-gray-700 bg-gray-900 rounded-lg overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between px-3 py-2 border-b border-gray-800 bg-gray-950/50">
                <div className="flex items-center gap-2 text-sm text-gray-300 font-medium">
                    <Globe className="w-4 h-4 text-emerald-400" />
                    Translation
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1 text-xs">
                        <select
                            value={sourceLang}
                            onChange={(e) => setSourceLang(e.target.value)}
                            className="bg-gray-800 border border-gray-700 rounded px-1.5 py-0.5 text-gray-300 focus:outline-none"
                        >
                            {LANGUAGES.map((l) => (
                                <option key={l.value} value={l.value}>
                                    {l.label}
                                </option>
                            ))}
                        </select>
                        <span className="text-gray-500">→</span>
                        <select
                            value={targetLang}
                            onChange={(e) => setTargetLang(e.target.value)}
                            className="bg-gray-800 border border-gray-700 rounded px-1.5 py-0.5 text-gray-300 focus:outline-none"
                        >
                            {LANGUAGES.map((l) => (
                                <option key={l.value} value={l.value}>
                                    {l.label}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            <div className="p-3 space-y-3">
                {/* Source Input */}
                <div className="relative">
                    <textarea
                        value={sourceText}
                        readOnly
                        rows={Math.min(5, Math.max(2, sourceText.split("\\n").length))}
                        className="w-full bg-gray-950/50 border border-gray-800 rounded p-2 text-sm text-gray-400 focus:outline-none resize-none"
                    />
                </div>

                {/* Translate action if not auto-triggered */}
                {!result && !isTranslating && !error && (
                    <button
                        onClick={handleTranslate}
                        className="w-full flex items-center justify-center gap-2 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded transition-colors"
                    >
                        Translate
                    </button>
                )}

                {/* State: Loading */}
                {isTranslating && (
                    <div className="flex items-center justify-center py-4 text-indigo-400 gap-2 text-sm">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Translating...
                    </div>
                )}

                {/* State: Error */}
                {error && (
                    <div className="bg-red-500/10 border border-red-500/20 rounded p-3">
                        <div className="flex items-start gap-2 text-red-400 text-sm">
                            <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0" />
                            <div className="flex-1">
                                <span className="font-semibold block mb-1">Translation Failed</span>
                                <span className="text-red-300/80">{error}</span>
                            </div>
                        </div>
                        <button
                            onClick={handleTranslate}
                            className="mt-2 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-300 px-2 py-1 rounded transition-colors"
                        >
                            Try Again
                        </button>
                    </div>
                )}

                {/* State: Success Output */}
                {result && !isTranslating && (
                    <div className="space-y-3 animate-in fade-in slide-in-from-top-1">
                        <div className="relative">
                            <textarea
                                value={result.translated_text}
                                readOnly
                                rows={Math.min(6, Math.max(3, result.translated_text.split("\\n").length))}
                                className="w-full bg-indigo-500/5 border border-indigo-500/20 rounded p-2 text-sm text-gray-200 focus:outline-none resize-none"
                            />
                            {result.confidence && (
                                <div
                                    className="absolute top-2 right-2 flex items-center gap-1 text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-black/40 text-emerald-400 shadow backdrop-blur-sm"
                                    title={`Model Confidence: ${(result.confidence * 100).toFixed(0)}%`}
                                >
                                    <Check className="w-3 h-3" />
                                    {(result.confidence * 100).toFixed(0)}%
                                </div>
                            )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => onReplace(result.translated_text)}
                                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded transition-colors"
                            >
                                <Replace className="w-3.5 h-3.5" />
                                Replace
                            </button>
                            <button
                                onClick={() => onInsertBelow(result.translated_text)}
                                className="flex-1 flex items-center justify-center gap-1.5 py-1.5 border border-gray-700 hover:bg-gray-800 text-gray-300 text-xs font-medium rounded transition-colors"
                            >
                                <ArrowDown className="w-3.5 h-3.5" />
                                Insert Below
                            </button>
                        </div>

                        {/* Collapsible Metadata Sections */}
                        {(result.adaptation_notes?.length > 0 || result.cultural_flags?.length > 0) && (
                            <div className="space-y-1.5 pt-2 border-t border-gray-800">
                                {result.adaptation_notes?.length > 0 && (
                                    <div className="rounded border border-gray-800 bg-gray-950/50">
                                        <button
                                            onClick={() => setShowNotes(!showNotes)}
                                            className="w-full flex items-center justify-between px-2 py-1.5 text-xs text-gray-400 hover:text-gray-300 transition-colors"
                                        >
                                            <span className="flex items-center gap-1.5 font-medium">
                                                {showNotes ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                                Adaptation Notes ({result.adaptation_notes.length})
                                            </span>
                                        </button>
                                        {showNotes && (
                                            <div className="px-2 pb-2 space-y-2 mt-1">
                                                {result.adaptation_notes.map((note: any, i: number) => (
                                                    <div key={i} className="text-xs bg-gray-900 border border-gray-800 rounded p-1.5">
                                                        <div className="flex justify-between mb-1">
                                                            <span className="text-gray-500 line-through truncate max-w-[45%]">{note.original}</span>
                                                            <span className="text-emerald-400 truncate max-w-[45%]">{note.adapted}</span>
                                                        </div>
                                                        <div className="text-gray-400 italic">"{note.reason}"</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {result.cultural_flags?.length > 0 && (
                                    <div className="rounded border border-red-900/40 bg-red-950/20">
                                        <button
                                            onClick={() => setShowFlags(!showFlags)}
                                            className="w-full flex items-center justify-between px-2 py-1.5 text-xs text-red-400 hover:text-red-300 transition-colors"
                                        >
                                            <span className="flex items-center gap-1.5 font-medium">
                                                {showFlags ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                                Cultural Flags ({result.cultural_flags.length})
                                            </span>
                                        </button>
                                        {showFlags && (
                                            <div className="px-2 pb-2 space-y-2 mt-1">
                                                {result.cultural_flags.map((flag: any, i: number) => (
                                                    <div key={i} className="text-xs bg-red-950/40 border border-red-900/50 rounded p-1.5 text-red-300/90">
                                                        <div className="font-semibold">{flag.location}</div>
                                                        <div>{flag.flag}</div>
                                                        <div className="mt-1 text-emerald-400/90">→ {flag.action_taken}</div>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <button
                onClick={onClose}
                className="w-full py-1.5 border-t border-gray-800 text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors flex items-center justify-center gap-1"
            >
                <X className="w-3.5 h-3.5" /> Close
            </button>
        </div>
    );
}
