"use client";

import React, { useState, useEffect } from "react";
import { api, CharacterProgression, ProgressionCreateRequest, CharacterDNA } from "@/lib/api";
import { Plus, Edit2, Trash2, ChevronRight, X, Check } from "lucide-react";
import { toast } from "sonner";

interface CharacterProgressionTimelineProps {
    characterId: string;
    characterName: string;
    baseDNA: CharacterDNA;
}

export function CharacterProgressionTimeline({ characterId, characterName, baseDNA }: CharacterProgressionTimelineProps) {
    const [progressions, setProgressions] = useState<CharacterProgression[]>([]);
    const [loading, setLoading] = useState(true);
    const [isAdding, setIsAdding] = useState(false);
    const [editingId, setEditingId] = useState<string | null>(null);

    // Form State
    const [formChapter, setFormChapter] = useState(1);
    const [formLabel, setFormLabel] = useState("");
    const [formNotes, setFormNotes] = useState("");
    const [formChangesStr, setFormChangesStr] = useState("{}");

    useEffect(() => {
        fetchProgressions();
    }, [characterId]);

    const fetchProgressions = async () => {
        try {
            const data = await api.getCharacterProgressions(characterId);
            setProgressions(data);
        } catch (err) {
            console.error(err);
            toast.error("Failed to load progressions");
        } finally {
            setLoading(false);
        }
    };

    const handleAdd = async () => {
        try {
            const parsedChanges = JSON.parse(formChangesStr);
            const req: ProgressionCreateRequest = {
                chapter: formChapter,
                label: formLabel,
                notes: formNotes,
                changes: parsedChanges,
            };
            await api.addCharacterProgression(characterId, req);
            toast.success("Progression added");
            setIsAdding(false);
            fetchProgressions();
        } catch (err) {
            toast.error("Failed to add - Ensure changes is valid JSON");
        }
    };

    const handleUpdate = async (id: string) => {
        try {
            const parsedChanges = JSON.parse(formChangesStr);
            const req: Partial<ProgressionCreateRequest> = {
                chapter: formChapter,
                label: formLabel,
                notes: formNotes,
                changes: parsedChanges,
            };
            await api.updateCharacterProgression(characterId, id, req);
            toast.success("Progression updated");
            setEditingId(null);
            fetchProgressions();
        } catch (err) {
            toast.error("Failed to update - Ensure changes is valid JSON");
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm("Are you sure you want to delete this progression?")) return;
        try {
            await api.deleteCharacterProgression(characterId, id);
            toast.success("Progression deleted");
            fetchProgressions();
        } catch (err) {
            toast.error("Failed to delete");
        }
    };

    const openAdd = () => {
        setFormChapter(progressions.length ? Math.max(...progressions.map(p => p.chapter)) + 1 : 1);
        setFormLabel("");
        setFormNotes("");
        setFormChangesStr(JSON.stringify({
            face: {},
            hair: {},
            body: {},
            default_outfit: {}
        }, null, 2));
        setIsAdding(true);
        setEditingId(null);
    };

    const openEdit = (p: CharacterProgression) => {
        setFormChapter(p.chapter);
        setFormLabel(p.label);
        setFormNotes(p.notes);
        setFormChangesStr(JSON.stringify(p.changes, null, 2));
        setEditingId(p.id);
        setIsAdding(false);
    };

    const renderChangesSummary = (changes: Record<string, any>) => {
        const lines: string[] = [];
        if (changes.face && Object.keys(changes.face).length) lines.push(`Face: ${Object.keys(changes.face).join(', ')}`);
        if (changes.hair && Object.keys(changes.hair).length) lines.push(`Hair: ${Object.keys(changes.hair).join(', ')}`);
        if (changes.body && Object.keys(changes.body).length) lines.push(`Body: ${Object.keys(changes.body).join(', ')}`);
        if (changes.default_outfit && Object.keys(changes.default_outfit).length) lines.push(`Outfit: updated`);
        return lines.join(" | ");
    };

    if (loading) return <div className="text-xs text-gray-500 animate-pulse">Loading timeline...</div>;

    return (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mt-4">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-gray-300">Visual Evolution Timeline</h3>
                {!isAdding && !editingId && (
                    <button
                        onClick={openAdd}
                        className="flex items-center gap-1 text-xs bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 px-2 py-1 rounded transition-colors"
                    >
                        <Plus className="w-3 h-3" /> Add Stage
                    </button>
                )}
            </div>

            {(isAdding || editingId) && (
                <div className="bg-gray-950 border border-gray-800 p-3 rounded-md mb-4 space-y-3">
                    <div className="flex justify-between items-center text-xs font-semibold text-gray-400">
                        {isAdding ? "New Progression Stage" : "Edit Progression Stage"}
                        <button onClick={() => { setIsAdding(false); setEditingId(null); }} className="text-gray-500 hover:text-gray-300"><X className="w-4 h-4" /></button>
                    </div>
                    <div className="grid grid-cols-4 gap-2">
                        <div className="col-span-1">
                            <label className="text-xs text-gray-500 block mb-1">Ch.</label>
                            <input type="number" className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1 text-xs text-white" value={formChapter} onChange={e => setFormChapter(parseInt(e.target.value) || 1)} />
                        </div>
                        <div className="col-span-3">
                            <label className="text-xs text-gray-500 block mb-1">Label</label>
                            <input type="text" className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1 text-xs text-white" value={formLabel} onChange={e => setFormLabel(e.target.value)} placeholder="e.g. Battle-Scarred" />
                        </div>
                    </div>
                    <div>
                        <label className="text-xs text-gray-500 block mb-1">Notes / Catalyst Event</label>
                        <input type="text" className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1 text-xs text-gray-300" value={formNotes} onChange={e => setFormNotes(e.target.value)} placeholder="Why did their appearance change?" />
                    </div>
                    <div>
                        <label className="text-xs text-gray-500 block mb-1">DNA Changes (JSON Merge Patch)</label>
                        <textarea
                            rows={5}
                            className="w-full bg-gray-900 border border-gray-800 rounded px-2 py-1 text-xs text-green-400 font-mono"
                            value={formChangesStr}
                            onChange={e => setFormChangesStr(e.target.value)}
                        />
                    </div>
                    <div className="flex justify-end pt-1">
                        <button
                            onClick={() => isAdding ? handleAdd() : handleUpdate(editingId!)}
                            className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded text-xs transition-colors"
                        >
                            <Check className="w-3 h-3" /> Save Stage
                        </button>
                    </div>
                </div>
            )}

            {/* Horizontal Timeline visualization */}
            {progressions.length > 0 ? (
                <div className="relative pt-6 pb-2">
                    {/* Connector Line */}
                    <div className="absolute top-10 left-4 right-4 h-0.5 bg-gray-800 z-0"></div>

                    <div className="flex overflow-x-auto gap-4 relative z-10 pb-4 no-scrollbar">
                        {/* Origin Node (Base DNA) */}
                        <div className="flex flex-col items-center flex-shrink-0 w-32 border border-blue-900/50 bg-gray-950 rounded p-2">
                            <div className="text-xs text-gray-500 mb-2">Base</div>
                            <div className="w-3 h-3 rounded-full bg-blue-500 mb-2 ring-4 ring-gray-900"></div>
                            <div className="text-xs font-medium text-gray-300 text-center mb-1">Original</div>
                            <div className="text-[10px] text-gray-500 text-center line-clamp-2">
                                {baseDNA?.default_outfit?.name || "Initial"}
                            </div>
                        </div>

                        {progressions.map((p, idx) => (
                            <div key={p.id} className="flex flex-col items-center flex-shrink-0 w-36 border border-gray-800 bg-gray-950 rounded p-2 group shadow-sm hover:border-gray-700 transition-colors">
                                <div className="text-xs text-gray-500 mb-2">Ch. {p.chapter}</div>
                                <div className="w-3 h-3 rounded-full bg-emerald-500 mb-2 ring-4 ring-gray-900 relative">
                                    <ChevronRight className="w-3 h-3 text-gray-500 absolute -right-5 -top-0.5" />
                                </div>
                                <div className="text-xs font-medium text-gray-200 text-center mb-1 truncate w-full" title={p.label}>{p.label}</div>
                                <div className="text-[10px] text-gray-400 text-center line-clamp-2 mb-2 w-full h-7">
                                    {renderChangesSummary(p.changes) || p.notes}
                                </div>
                                {/* Actions overlay */}
                                <div className="flex gap-2 mt-auto w-full justify-center pt-2 border-t border-gray-800/50">
                                    <button onClick={() => openEdit(p)} className="text-blue-400 hover:text-blue-300 px-1 py-0.5 rounded text-[10px] flex items-center gap-1">
                                        <Edit2 className="w-3 h-3" /> Edit
                                    </button>
                                    <button onClick={() => handleDelete(p.id)} className="text-red-400 hover:text-red-300 px-1 py-0.5 rounded text-[10px] flex items-center gap-1">
                                        <Trash2 className="w-3 h-3" /> Delete
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ) : (
                !isAdding && (
                    <div className="text-center py-6 border border-dashed border-gray-800 rounded text-gray-500 text-xs">
                        No transformations added. Character remains mostly unchanged throughout story.
                    </div>
                )
            )}
        </div>
    );
}
