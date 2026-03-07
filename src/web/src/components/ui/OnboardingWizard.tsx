"use client";

import { useState, useEffect } from "react";
import { Loader2, Sparkles, BookOpen, Film } from "lucide-react";
import { api } from "@/lib/api";

export function OnboardingWizard() {
    const [isOpen, setIsOpen] = useState(false);
    const [title, setTitle] = useState("");
    const [genre, setGenre] = useState("");
    const [premise, setPremise] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const handler = () => setIsOpen(true);
        window.addEventListener('open:onboarding', handler);
        return () => window.removeEventListener('open:onboarding', handler);
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title || !genre || !premise) return;

        setIsSubmitting(true);
        try {
            await api.updateProjectSettings({
                name: title,
                description: premise,
                variables: { genre }
            });

            // Dispatch command to open chat sidebar and send initial prompt
            window.dispatchEvent(new CustomEvent('chat:inject', {
                detail: { message: `/plan Generate initial structure for a new ${genre} story about ${premise}. Use the Project Initializer skill if available.` }
            }));

            setIsOpen(false);
        } catch (error) {
            console.error("Failed to update project settings:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-[100] flex items-center justify-center">
            <div className="bg-gray-900 border border-gray-700 rounded-2xl p-8 max-w-lg w-full mx-4 shadow-2xl">
                <div className="flex items-center justify-center w-12 h-12 rounded-full bg-indigo-600/20 text-indigo-400 mb-6 mx-auto">
                    <Sparkles className="w-6 h-6" />
                </div>

                <h2 className="text-2xl font-bold text-white text-center mb-2">Welcome to your new Story</h2>
                <p className="text-gray-400 text-center text-sm mb-8">
                    Let's set up the foundation of your project. The AI Showrunner will help you build the rest.
                </p>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Project Title</label>
                        <input
                            type="text"
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                            placeholder="e.g. Neon Shadows"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Genre / Setting</label>
                        <input
                            type="text"
                            required
                            value={genre}
                            onChange={(e) => setGenre(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all"
                            placeholder="e.g. Cyberpunk Noir, High Fantasy"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">Core Premise / Logline</label>
                        <textarea
                            required
                            value={premise}
                            onChange={(e) => setPremise(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all min-h-[100px] resize-none"
                            placeholder="In a world where memories can be bought and sold, a rogue detective investigates the theft of their own past..."
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={isSubmitting || !title || !genre || !premise}
                        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg px-4 py-3 flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isSubmitting ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <>
                                Initialize Project
                                <Sparkles className="w-4 h-4" />
                            </>
                        )}
                    </button>

                    <button
                        type="button"
                        onClick={() => setIsOpen(false)}
                        className="w-full text-gray-500 hover:text-gray-300 text-sm py-2 font-medium transition-colors"
                    >
                        Skip for now
                    </button>
                </form>
            </div>
        </div>
    );
}
