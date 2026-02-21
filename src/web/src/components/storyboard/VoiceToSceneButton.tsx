"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, Square, Loader2, Wand2, X } from "lucide-react";
import { api, LayoutSuggestion } from "@/lib/api";
import { toast } from "sonner";
import { useStoryboardStore } from "@/lib/store/storyboardSlice";

// Web Speech API interfaces
declare global {
    interface Window {
        SpeechRecognition: any;
        webkitSpeechRecognition: any;
    }
}

interface VoiceToSceneButtonProps {
    onPanelsGenerated: (sceneId: string, panels: any[]) => void;
}

export function VoiceToSceneButton({ onPanelsGenerated }: VoiceToSceneButtonProps) {
    const { scenes } = useStoryboardStore();
    const [isSupported, setIsSupported] = useState(true);
    const [isRecording, setIsRecording] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [showModal, setShowModal] = useState(false);

    const [transcript, setTranscript] = useState("");
    const [selectedSceneId, setSelectedSceneId] = useState("");
    const [panelCount, setPanelCount] = useState(6);

    const [layoutSuggestion, setLayoutSuggestion] = useState<LayoutSuggestion | null>(null);
    const [generatedPanels, setGeneratedPanels] = useState<any[]>([]);

    const recognitionRef = useRef<any>(null);

    useEffect(() => {
        if (typeof window !== "undefined") {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (SpeechRecognition) {
                recognitionRef.current = new SpeechRecognition();
                recognitionRef.current.continuous = true;
                recognitionRef.current.interimResults = true;

                recognitionRef.current.onresult = (event: any) => {
                    let text = "";
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        text += event.results[i][0].transcript;
                    }
                    setTranscript((prev) => {
                        // Very basic approach: just appending interim results might cause duplication,
                        // but since continuous is true, we should replace the interim and keep final.
                        // For simplicity in this demo, let's just collect final transcripts.

                        let final = "";
                        for (let i = 0; i < event.results.length; ++i) {
                            final += event.results[i][0].transcript;
                        }
                        return final;
                    });
                };

                recognitionRef.current.onerror = (event: any) => {
                    console.error("Speech recognition error", event.error);
                    if (event.error !== "no-speech") {
                        setIsRecording(false);
                        toast.error("Speech recognition failed: " + event.error);
                    }
                };

                recognitionRef.current.onend = () => {
                    setIsRecording(false);
                };
            } else {
                setIsSupported(false);
            }
        }

        if (scenes.length > 0 && !selectedSceneId) {
            setSelectedSceneId(scenes[0].id);
        }
    }, [scenes]);

    const handleStartRecording = () => {
        if (!isSupported) {
            // Show modal anyway to allow typing fallback
            setShowModal(true);
            return;
        }

        setTranscript("");
        setLayoutSuggestion(null);
        setGeneratedPanels([]);
        try {
            recognitionRef.current.start();
            setIsRecording(true);
            setShowModal(true);
        } catch (error) {
            console.error(error);
            toast.error("Could not start recording.");
        }
    };

    const handleStopRecording = () => {
        if (isRecording && recognitionRef.current) {
            recognitionRef.current.stop();
            setIsRecording(false);
        }
    };

    const handleGenerate = async () => {
        if (!transcript.trim()) {
            toast.error("Please provide some scene description first.");
            return;
        }

        if (!selectedSceneId) {
            toast.error("Please select a target scene.");
            return;
        }

        setIsProcessing(true);
        try {
            const sceneName = scenes.find((s: any) => s.id === selectedSceneId)?.name || "Voice Scene";

            // Call the voice-to-scene API
            const result = await api.voiceToScene(transcript, sceneName, panelCount);

            setLayoutSuggestion(result.layout_suggestion);
            setGeneratedPanels(result.panels);
            toast.success("Panels generated successfully!");

        } catch (error) {
            console.error(error);
            toast.error("Failed to generate panels from voice input");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleApply = async () => {
        if (generatedPanels.length === 0 || !selectedSceneId) return;

        setIsProcessing(true);
        try {
            // Optimistic apply (or proper backend apply)
            // In a real scenario, the voice-to-scene endpoint creates new standalone panels or we save them now
            // But since the API generated them, we can assume they exist or need to be attached if they were just returned.
            // Wait, the API already saves them (svc.generate_panels_for_scene saves to container repo).
            // Let's ensure the frontend knows which scene they belong to.
            // The API receives `scene_id="voice_scene"` temporarily according to our script, but actually we should pass real scene ID.
            // Wait! Our voiceToScene API currently uses "voice_scene" as hardcoded scene_id in the script.
            // We should ideally update them to the selected scene. 
            // For now, let's just update each panel's scene_id via updateStoryboardPanel.

            for (const p of generatedPanels) {
                await api.updateStoryboardPanel(p.id, { scene_id: selectedSceneId });
            }

            onPanelsGenerated(selectedSceneId, generatedPanels);
            setShowModal(false);
            setTranscript("");
            setGeneratedPanels([]);
            setLayoutSuggestion(null);
        } catch (error) {
            console.error(error);
            toast.error("Failed to apply panels to scene");
        } finally {
            setIsProcessing(false);
        }
    };

    if (!showModal) {
        return (
            <button
                onClick={handleStartRecording}
                className="flex items-center gap-1.5 px-3 py-1 text-xs font-medium rounded-md transition-colors bg-gray-900 border border-gray-800 text-gray-400 hover:text-emerald-400 hover:border-emerald-500/30"
                title="Voice Dictation"
            >
                <div className="relative">
                    <Mic className="w-4 h-4" />
                </div>
                Voice to Scene
            </button>
        );
    }

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
            <div className="bg-gray-900 border border-gray-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between bg-gray-900/50">
                    <div className="flex items-center gap-2">
                        <div className="p-2 bg-emerald-500/10 rounded-lg">
                            <Mic className="w-5 h-5 text-emerald-500" />
                        </div>
                        <h2 className="text-lg font-semibold text-gray-200">Voice to Scene</h2>
                    </div>
                    <button
                        onClick={() => {
                            if (isRecording) handleStopRecording();
                            setShowModal(false);
                        }}
                        className="text-gray-500 hover:text-gray-300 transition-colors p-1"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 overflow-y-auto flex-1 space-y-6">

                    {!isSupported && (
                        <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-500/90 text-sm">
                            Your browser doesn't support the Speech Recognition API. You can still type your scene description below.
                        </div>
                    )}

                    {/* Recording Controls */}
                    <div className="flex items-start gap-4">
                        <div className="flex-1">
                            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
                                Scene Description Transcript
                            </label>
                            <textarea
                                value={transcript}
                                onChange={(e) => setTranscript(e.target.value)}
                                className={`w-full h-32 bg-gray-950 border rounded-lg p-3 text-sm text-gray-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 transition-colors resize-none ${isRecording ? "border-emerald-500/50 shadow-[0_0_15px_rgba(16,185,129,0.1)]" : "border-gray-800"
                                    }`}
                                placeholder="Speak your scene description aloud, or type it here..."
                            />
                        </div>

                        <div className="flex flex-col gap-2 pt-6">
                            {isRecording ? (
                                <button
                                    onClick={handleStopRecording}
                                    className="flex items-center justify-center gap-2 px-4 py-8 bg-red-500/10 border border-red-500/20 text-red-500 rounded-lg hover:bg-red-500/20 transition-all font-medium min-w-[120px]"
                                >
                                    <Square className="w-5 h-5 fill-current" />
                                    <span>Stop</span>
                                </button>
                            ) : (
                                <button
                                    onClick={handleStartRecording}
                                    disabled={!isSupported}
                                    className="flex items-center justify-center gap-2 px-4 py-8 bg-gray-800 border border-gray-700 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors font-medium min-w-[120px] disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <Mic className="w-5 h-5" />
                                    <span>Record</span>
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Settings */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
                                Target Scene
                            </label>
                            <select
                                value={selectedSceneId}
                                onChange={(e) => setSelectedSceneId(e.target.value)}
                                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-emerald-500/50"
                            >
                                <option value="" disabled>Select a scene...</option>
                                {scenes.map((s: any) => (
                                    <option key={s.id} value={s.id}>{s.name || s.id}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-gray-400 mb-2 uppercase tracking-wide">
                                Base Panel Count
                            </label>
                            <select
                                value={panelCount}
                                onChange={(e) => setPanelCount(Number(e.target.value))}
                                className="w-full bg-gray-950 border border-gray-800 rounded-lg p-2.5 text-sm text-gray-200 focus:outline-none focus:border-emerald-500/50"
                            >
                                {[3, 4, 6, 8, 10, 12].map((n) => (
                                    <option key={n} value={n}>{n} Panels</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Generate Button */}
                    <div className="pt-2">
                        <button
                            onClick={handleGenerate}
                            disabled={isRecording || isProcessing || !transcript.trim()}
                            className="w-full flex items-center justify-center gap-2 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors disabled:bg-gray-800 disabled:text-gray-500"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Drawing Storyboard...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="w-5 h-5" />
                                    Generate Panels
                                </>
                            )}
                        </button>
                    </div>

                    {/* Results Preview */}
                    {generatedPanels.length > 0 && (
                        <div className="pt-4 border-t border-gray-800 space-y-4 animate-in slide-in-from-bottom-4">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-semibold text-emerald-400">
                                    Generated {generatedPanels.length} Panels
                                </h3>
                                {layoutSuggestion && (
                                    <span className="text-xs text-gray-400 bg-gray-800 px-2 py-1 rounded">
                                        Pacing: {layoutSuggestion.pacing_notes?.slice(0, 30)}...
                                    </span>
                                )}
                            </div>

                            <div className="flex gap-3 overflow-x-auto pb-2 snap-x">
                                {generatedPanels.map((p, i) => (
                                    <div key={p.id} className="shrink-0 w-40 bg-gray-950 border border-gray-800 rounded-lg p-3 snap-center flex flex-col h-32">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-bold text-gray-500">P{p.panel_number}</span>
                                            <span className="text-[10px] uppercase font-medium bg-gray-900 px-1.5 py-0.5 rounded text-emerald-500/70 border border-emerald-500/20">
                                                {p.camera_angle}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-300 line-clamp-4 leading-relaxed">
                                            {p.description}
                                        </p>
                                    </div>
                                ))}
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    onClick={() => setGeneratedPanels([])}
                                    className="px-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
                                >
                                    Discard
                                </button>
                                <button
                                    onClick={handleApply}
                                    disabled={isProcessing}
                                    className="px-6 py-2 bg-white text-black hover:bg-gray-200 text-sm font-semibold rounded-md transition-colors shadow-lg shadow-white/10"
                                >
                                    Apply to Scene
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
