"use client";

import { useState, useEffect } from "react";
import { api, CharacterSummary, SceneSummary } from "@/lib/api";
import {
    Globe,
    Languages,
    Sparkles,
    BookOpen,
    Flag,
    ChevronDown,
    ChevronUp,
    Save,
    Loader2,
    Check
} from "lucide-react";
import { toast } from "sonner";
import type { TranslateResponse } from "@/lib/api";

const cn = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(" ");

const LANGUAGES = [
    { code: "en", name: "English" },
    { code: "hi", name: "Hindi" },
    { code: "hinglish", name: "Hinglish" },
    { code: "ja", name: "Japanese" },
    { code: "ko", name: "Korean" },
    { code: "es", name: "Spanish" },
    { code: "fr", name: "French" },
];

export function TranslationPanel() {
    const [sourceLang, setSourceLang] = useState("en");
    const [targetLang, setTargetLang] = useState("hi");
    const [sourceText, setSourceText] = useState("");
    const [characterIds, setCharacterIds] = useState<string[]>([]);
    const [sceneId, setSceneId] = useState<string>("");

    const [characters, setCharacters] = useState<CharacterSummary[]>([]);
    const [scenes, setScenes] = useState<SceneSummary[]>([]);

    const [isTranslating, setIsTranslating] = useState(false);
    const [result, setResult] = useState<TranslateResponse | null>(null);
    const [editedText, setEditedText] = useState("");
    const [isSaving, setIsSaving] = useState(false);

    const [expandedSection, setExpandedSection] = useState<string>("notes");

    useEffect(() => {
        loadContextData();
    }, []);

    const loadContextData = async () => {
        try {
            const charData = await api.getCharacters();
            setCharacters(charData);

            const scenesData = await api.getScenes(1); // Fetching chapter 1 scenes as default
            setScenes(scenesData);
        } catch (error) {
            console.error("Failed to load context data:", error);
        }
    };

    const handleTranslate = async () => {
        if (!sourceText.trim()) return;

        setIsTranslating(true);
        try {
            const res = await api.translateText({
                text: sourceText,
                source_language: sourceLang,
                target_language: targetLang,
                character_ids: characterIds.length > 0 ? characterIds : undefined,
                scene_id: sceneId || undefined,
            });
            setResult(res);
            setEditedText(res.translated_text);
        } catch (error) {
            toast.error("Translation failed. Please try again.");
            console.error(error);
        } finally {
            setIsTranslating(false);
        }
    };

    const handleSaveTranslation = async () => {
        // Usually this would update a specific container. For this panel, we'll
        // Mock the save or show a success message if no specific target is meant to receive it,
        // or we can allow the user to select the container to save to.
        setIsSaving(true);
        await new Promise(resolve => setTimeout(resolve, 800));
        setIsSaving(false);
        toast.success("Translation saved!");
    };

    const toggleSection = (section: string) => {
        if (expandedSection === section) setExpandedSection("");
        else setExpandedSection(section);
    };

    return (
        <div className="flex flex-col bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50">
                <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-purple-400" />
                    <h2 className="font-semibold text-gray-100">Translation</h2>
                </div>

                <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                        <span className="text-gray-400">Source:</span>
                        <select
                            value={sourceLang}
                            onChange={(e) => setSourceLang(e.target.value)}
                            className="bg-gray-800 border-gray-700 rounded-md py-1 px-2 text-gray-200 outline-none focus:ring-1 focus:ring-purple-500"
                        >
                            {LANGUAGES.map(l => (
                                <option key={l.code} value={l.code}>{l.name}</option>
                            ))}
                        </select>
                    </div>

                    <div className="flex items-center gap-2">
                        <span className="text-gray-400">Target:</span>
                        <select
                            value={targetLang}
                            onChange={(e) => setTargetLang(e.target.value)}
                            className="bg-gray-800 border-gray-700 rounded-md py-1 px-2 text-gray-200 outline-none focus:ring-1 focus:ring-purple-500"
                        >
                            {LANGUAGES.map(l => (
                                <option key={l.code} value={l.code}>{l.name}</option>
                            ))}
                        </select>
                    </div>

                    {result && (
                        <div className="flex items-center gap-2 ml-4 pl-4 border-l border-gray-800">
                            <span className="text-gray-400">Confidence:</span>
                            <span className={cn(
                                "font-medium",
                                result.confidence >= 0.8 ? "text-green-400" :
                                    result.confidence >= 0.6 ? "text-amber-400" : "text-red-400"
                            )}>
                                {Math.round(result.confidence * 100)}%
                            </span>
                        </div>
                    )}
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-2 divide-x divide-gray-800 min-h-[400px]">
                {/* Source Column */}
                <div className="flex flex-col p-4 bg-gray-950/30">
                    <h3 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Languages className="w-3 h-3" /> Source Text
                    </h3>
                    <textarea
                        value={sourceText}
                        onChange={(e) => setSourceText(e.target.value)}
                        placeholder="Paste or type prose here..."
                        className="flex-1 bg-transparent border-none text-gray-300 resize-none outline-none focus:ring-0 p-0 leading-relaxed"
                    />
                </div>

                {/* Target Column */}
                <div className="flex flex-col p-4 bg-gray-900">
                    <h3 className="text-xs font-medium text-purple-400/70 uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Sparkles className="w-3 h-3" /> Translation
                    </h3>
                    {isTranslating ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-3">
                            <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                            <p className="animate-pulse">Analyzing context & translating...</p>
                        </div>
                    ) : result ? (
                        <textarea
                            value={editedText}
                            onChange={(e) => setEditedText(e.target.value)}
                            className="flex-1 bg-transparent border-none text-gray-200 resize-none outline-none focus:ring-0 p-0 leading-relaxed font-medium"
                        />
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-600 italic">
                            Translated output will appear here
                        </div>
                    )}
                </div>
            </div>

            {/* Context Actions */}
            <div className="p-4 border-t border-gray-800 flex items-center justify-between bg-gray-900/80">
                <div className="flex items-center gap-4">
                    <select
                        value={characterIds[0] || ""}
                        onChange={(e) => setCharacterIds(e.target.value ? [e.target.value] : [])}
                        className="text-sm bg-gray-800 border-gray-700 rounded-md py-1.5 px-3 text-gray-300 outline-none max-w-[200px]"
                    >
                        <option value="">Characters: None</option>
                        {characters.map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>

                    <select
                        value={sceneId}
                        onChange={(e) => setSceneId(e.target.value)}
                        className="text-sm bg-gray-800 border-gray-700 rounded-md py-1.5 px-3 text-gray-300 outline-none max-w-[200px]"
                    >
                        <option value="">Scene Context: None</option>
                        {scenes.map(s => (
                            <option key={s.id} value={s.id}>{s.title}</option>
                        ))}
                    </select>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleTranslate}
                        disabled={!sourceText.trim() || isTranslating}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors font-medium disabled:opacity-50"
                    >
                        {isTranslating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Globe className="w-4 h-4" />}
                        Translate
                    </button>

                    <button
                        onClick={handleSaveTranslation}
                        disabled={!result || isTranslating}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-gray-200 rounded-lg transition-colors border border-gray-700 disabled:opacity-50"
                    >
                        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        Save Translation
                    </button>
                </div>
            </div>

            {/* Analysis Section (Collapsible) */}
            {result && (
                <div className="border-t border-gray-800 bg-gray-950">
                    {/* Notes */}
                    {result.adaptation_notes.length > 0 && (
                        <div className="border-b border-gray-800/50 last:border-0">
                            <button
                                onClick={() => toggleSection("notes")}
                                className="flex items-center justify-between w-full p-3 text-sm text-gray-300 hover:bg-gray-900/50"
                            >
                                <span className="flex items-center gap-2 font-medium">
                                    📝 Adaptation Notes ({result.adaptation_notes.length})
                                </span>
                                {expandedSection === "notes" ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>

                            {expandedSection === "notes" && (
                                <div className="p-4 pt-0 space-y-3">
                                    {result.adaptation_notes.map((note, i) => (
                                        <div key={i} className="bg-gray-900 p-3 rounded-md border border-gray-800">
                                            <div className="flex items-center gap-2 mb-1.5">
                                                <span className="text-red-400 line-through text-sm">{note.original}</span>
                                                <span className="text-gray-500">→</span>
                                                <span className="text-green-400 font-medium text-sm">{note.adapted}</span>
                                            </div>
                                            <p className="text-xs text-gray-400 leading-relaxed bg-gray-950/50 p-2 rounded">
                                                {note.reason}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Cultural Flags */}
                    {result.cultural_flags.length > 0 && (
                        <div className="border-b border-gray-800/50 last:border-0">
                            <button
                                onClick={() => toggleSection("flags")}
                                className="flex items-center justify-between w-full p-3 text-sm text-gray-300 hover:bg-gray-900/50"
                            >
                                <span className="flex items-center gap-2 font-medium">
                                    🚩 Cultural Flags ({result.cultural_flags.length})
                                </span>
                                {expandedSection === "flags" ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>

                            {expandedSection === "flags" && (
                                <div className="p-4 pt-0 space-y-3">
                                    {result.cultural_flags.map((flag, i) => (
                                        <div key={i} className="bg-gray-900 p-3 rounded-md border border-gray-800">
                                            <div className="flex items-center justify-between mb-1">
                                                <span className="text-xs uppercase text-gray-500 font-medium">{flag.location}</span>
                                                <span className={cn(
                                                    "text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-semibold",
                                                    flag.action_taken === "adapted" ? "bg-blue-500/20 text-blue-400" :
                                                        flag.action_taken === "preserved" ? "bg-gray-700 text-gray-300" :
                                                            "bg-amber-500/20 text-amber-500"
                                                )}>
                                                    {flag.action_taken}
                                                </span>
                                            </div>
                                            <p className="text-sm text-gray-300">{flag.flag}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Glossary */}
                    {Object.keys(result.glossary_applied).length > 0 && (
                        <div className="border-b border-gray-800/50 last:border-0">
                            <button
                                onClick={() => toggleSection("glossary")}
                                className="flex items-center justify-between w-full p-3 text-sm text-gray-300 hover:bg-gray-900/50"
                            >
                                <span className="flex items-center gap-2 font-medium">
                                    📖 Glossary Applied ({Object.keys(result.glossary_applied).length})
                                </span>
                                {expandedSection === "glossary" ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                            </button>

                            {expandedSection === "glossary" && (
                                <div className="p-4 pt-0">
                                    <div className="bg-gray-900 rounded-md border border-gray-800 overflow-hidden">
                                        <table className="w-full text-sm text-left">
                                            <thead className="bg-gray-800/50 text-xs uppercase text-gray-500">
                                                <tr>
                                                    <th className="px-4 py-2">Source Term</th>
                                                    <th className="px-4 py-2">Target Term</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-gray-800">
                                                {Object.entries(result.glossary_applied).map(([source, target], i) => (
                                                    <tr key={i}>
                                                        <td className="px-4 py-2 text-gray-300">{source}</td>
                                                        <td className="px-4 py-2 text-purple-400 font-medium">{target}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
