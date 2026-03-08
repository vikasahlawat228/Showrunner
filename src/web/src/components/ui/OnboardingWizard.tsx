"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
    Loader2, Sparkles, BookOpen, Film, PenTool, Users, Map,
    ChevronRight, ChevronLeft, Check
} from "lucide-react";
import { api } from "@/lib/api";

const ONBOARDED_KEY = "showrunner:onboarded";

// Genre options with emoji and colors
const GENRES = [
    { value: "cyberpunk", label: "Cyberpunk", emoji: "🌆", color: "from-cyan-500/20 to-blue-600/20 border-cyan-500/40" },
    { value: "high-fantasy", label: "High Fantasy", emoji: "🐉", color: "from-emerald-500/20 to-teal-600/20 border-emerald-500/40" },
    { value: "sci-fi", label: "Sci-Fi", emoji: "🚀", color: "from-violet-500/20 to-purple-600/20 border-violet-500/40" },
    { value: "noir", label: "Noir / Mystery", emoji: "🕵️", color: "from-gray-500/20 to-slate-600/20 border-gray-500/40" },
    { value: "romance", label: "Romance", emoji: "💕", color: "from-pink-500/20 to-rose-600/20 border-pink-500/40" },
    { value: "horror", label: "Horror", emoji: "👻", color: "from-red-500/20 to-orange-600/20 border-red-500/40" },
    { value: "slice-of-life", label: "Slice of Life", emoji: "☕", color: "from-amber-500/20 to-yellow-600/20 border-amber-500/40" },
    { value: "action", label: "Action / Shonen", emoji: "⚔️", color: "from-orange-500/20 to-red-600/20 border-orange-500/40" },
];

type Step = "welcome" | "premise" | "genre" | "character" | "ready";
const STEPS: Step[] = ["welcome", "premise", "genre", "character", "ready"];

export function OnboardingWizard() {
    const router = useRouter();
    const [isOpen, setIsOpen] = useState(false);
    const [step, setStep] = useState<Step>("welcome");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Form state
    const [title, setTitle] = useState("");
    const [premise, setPremise] = useState("");
    const [genre, setGenre] = useState("");
    const [customGenre, setCustomGenre] = useState("");
    const [characterName, setCharacterName] = useState("");
    const [characterRole, setCharacterRole] = useState("protagonist");

    // Auto-detect first visit
    useEffect(() => {
        const alreadyOnboarded = localStorage.getItem(ONBOARDED_KEY);
        if (!alreadyOnboarded) {
            // Small delay for a smoother first impression
            const timer = setTimeout(() => setIsOpen(true), 600);
            return () => clearTimeout(timer);
        }
    }, []);

    // Also listen for manual trigger
    useEffect(() => {
        const handler = () => setIsOpen(true);
        window.addEventListener("open:onboarding", handler);
        return () => window.removeEventListener("open:onboarding", handler);
    }, []);

    const currentStepIdx = STEPS.indexOf(step);

    const canAdvance = useCallback((): boolean => {
        switch (step) {
            case "welcome": return true;
            case "premise": return title.trim().length > 0 && premise.trim().length > 0;
            case "genre": return genre.length > 0 || customGenre.trim().length > 0;
            case "character": return characterName.trim().length > 0;
            case "ready": return true;
            default: return false;
        }
    }, [step, title, premise, genre, customGenre, characterName]);

    const nextStep = () => {
        const idx = STEPS.indexOf(step);
        if (idx < STEPS.length - 1) setStep(STEPS[idx + 1]);
    };

    const prevStep = () => {
        const idx = STEPS.indexOf(step);
        if (idx > 0) setStep(STEPS[idx - 1]);
    };

    const handleFinish = async () => {
        setIsSubmitting(true);
        try {
            const finalGenre = genre === "custom" ? customGenre : genre;

            // 1. Update project settings
            await api.updateProjectSettings({
                name: title,
                description: premise,
                variables: { genre: finalGenre },
            });

            // 2. Create the first character if provided
            if (characterName.trim()) {
                try {
                    await api.createContainer({
                        container_type: "character",
                        name: characterName.trim(),
                        attributes: { role: characterRole },
                    });
                } catch {
                    // Non-critical: character creation might fail if API doesn't support it this way
                    console.warn("Character creation via container failed, will use chat instead");
                }
            }

            // 3. Mark onboarding complete
            localStorage.setItem(ONBOARDED_KEY, new Date().toISOString());

            // 4. Inject a plan command into chat
            window.dispatchEvent(new CustomEvent("chat:inject", {
                detail: {
                    message: `/plan Generate initial structure for a new ${finalGenre} story titled "${title}" about: ${premise}. Create 3 chapters with scene outlines. The protagonist is ${characterName || "unnamed"} (${characterRole}).`
                },
            }));

            setIsOpen(false);

            // 5. Navigate to Zen mode
            router.push("/zen");
        } catch (error) {
            console.error("Onboarding failed:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSkip = () => {
        localStorage.setItem(ONBOARDED_KEY, new Date().toISOString());
        setIsOpen(false);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl max-w-lg w-full mx-4 shadow-2xl overflow-hidden">
                {/* Progress Bar */}
                <div className="flex gap-1 px-6 pt-5">
                    {STEPS.map((s, i) => (
                        <div
                            key={s}
                            className={`h-1 flex-1 rounded-full transition-all duration-500 ${i <= currentStepIdx ? "bg-indigo-500" : "bg-gray-800"
                                }`}
                        />
                    ))}
                </div>

                <div className="p-6">
                    {/* ─── Step: Welcome ────────────────────────────── */}
                    {step === "welcome" && (
                        <div className="text-center py-4">
                            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-600/30 to-purple-600/30 text-indigo-400 mb-6 mx-auto border border-indigo-500/30">
                                <Sparkles className="w-8 h-8" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-3">
                                Welcome to Showrunner Studio
                            </h2>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-sm mx-auto">
                                Your AI-powered creative studio for building stories, characters, and worlds.
                                Let's set up your project in under a minute.
                            </p>
                        </div>
                    )}

                    {/* ─── Step: Premise ────────────────────────────── */}
                    {step === "premise" && (
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <BookOpen className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-lg font-semibold text-white">What's your story about?</h2>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Project Title</label>
                                    <input
                                        type="text"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                        className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                                        placeholder="e.g. Neon Shadows"
                                        autoFocus
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Core Premise / Logline</label>
                                    <textarea
                                        value={premise}
                                        onChange={(e) => setPremise(e.target.value)}
                                        className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all min-h-[90px] resize-none"
                                        placeholder="In a world where memories can be bought and sold, a rogue detective investigates the theft of their own past..."
                                    />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ─── Step: Genre Picker ──────────────────────── */}
                    {step === "genre" && (
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Film className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-lg font-semibold text-white">Pick a genre</h2>
                            </div>
                            <div className="grid grid-cols-2 gap-2 mb-3">
                                {GENRES.map((g) => (
                                    <button
                                        key={g.value}
                                        onClick={() => { setGenre(g.value); setCustomGenre(""); }}
                                        className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-all text-left
                                            ${genre === g.value
                                                ? `bg-gradient-to-r ${g.color} text-white border-opacity-100`
                                                : "bg-gray-950 text-gray-400 border-gray-800 hover:border-gray-600 hover:text-gray-200"
                                            }`}
                                    >
                                        <span className="text-lg">{g.emoji}</span>
                                        <span>{g.label}</span>
                                        {genre === g.value && <Check className="w-3.5 h-3.5 ml-auto text-white" />}
                                    </button>
                                ))}
                            </div>
                            <div className="mt-3">
                                <input
                                    type="text"
                                    value={customGenre}
                                    onChange={(e) => { setCustomGenre(e.target.value); setGenre("custom"); }}
                                    className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                                    placeholder="Or type your own genre..."
                                />
                            </div>
                        </div>
                    )}

                    {/* ─── Step: First Character ───────────────────── */}
                    {step === "character" && (
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <Users className="w-5 h-5 text-indigo-400" />
                                <h2 className="text-lg font-semibold text-white">Create your first character</h2>
                            </div>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Character Name</label>
                                    <input
                                        type="text"
                                        value={characterName}
                                        onChange={(e) => setCharacterName(e.target.value)}
                                        className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                                        placeholder="e.g. Kira Nakamura"
                                        autoFocus
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1.5">Role</label>
                                    <div className="flex gap-2">
                                        {["protagonist", "antagonist", "supporting"].map((r) => (
                                            <button
                                                key={r}
                                                onClick={() => setCharacterRole(r)}
                                                className={`flex-1 px-3 py-2 rounded-lg border text-sm font-medium capitalize transition-all
                                                    ${characterRole === r
                                                        ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/40"
                                                        : "bg-gray-950 text-gray-400 border-gray-800 hover:border-gray-600"
                                                    }`}
                                            >
                                                {r}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ─── Step: Ready ──────────────────────────────── */}
                    {step === "ready" && (
                        <div className="text-center py-4">
                            <div className="flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-600/30 to-teal-600/30 text-emerald-400 mb-6 mx-auto border border-emerald-500/30">
                                <PenTool className="w-8 h-8" />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-3">You're all set!</h2>
                            <p className="text-gray-400 text-sm leading-relaxed max-w-sm mx-auto mb-4">
                                We'll open the Zen Mode editor so you can start writing right away.
                                Your AI co-pilot will help structure the story in the background.
                            </p>
                            <div className="bg-gray-950 rounded-lg p-4 text-left space-y-2 border border-gray-800">
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Title</span>
                                    <span className="text-white font-medium">{title || "—"}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Genre</span>
                                    <span className="text-white font-medium">{genre === "custom" ? customGenre : GENRES.find(g => g.value === genre)?.label || "—"}</span>
                                </div>
                                <div className="flex justify-between text-sm">
                                    <span className="text-gray-500">Protagonist</span>
                                    <span className="text-white font-medium">{characterName || "—"}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>

                {/* ─── Navigation Footer ───────────────────────── */}
                <div className="flex items-center justify-between px-6 pb-5">
                    <div>
                        {currentStepIdx > 0 ? (
                            <button
                                onClick={prevStep}
                                className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                <ChevronLeft className="w-4 h-4" /> Back
                            </button>
                        ) : (
                            <button
                                onClick={handleSkip}
                                className="text-sm text-gray-600 hover:text-gray-400 transition-colors"
                            >
                                Skip for now
                            </button>
                        )}
                    </div>

                    <div>
                        {step === "ready" ? (
                            <button
                                onClick={handleFinish}
                                disabled={isSubmitting}
                                className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isSubmitting ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <>
                                        Start Writing
                                        <PenTool className="w-4 h-4" />
                                    </>
                                )}
                            </button>
                        ) : (
                            <button
                                onClick={nextStep}
                                disabled={!canAdvance()}
                                className="flex items-center gap-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Continue <ChevronRight className="w-4 h-4" />
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
