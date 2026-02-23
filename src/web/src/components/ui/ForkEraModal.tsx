"use client";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Copy, Sparkles, AlertCircle } from "lucide-react";
import { useStudioStore } from "@/lib/store";

export function ForkEraModal() {
    const [isOpen, setIsOpen] = useState(false);
    const [containerId, setContainerId] = useState<string>("");
    const [containerName, setContainerName] = useState<string>("");
    const [eraId, setEraId] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const handleOpen = (e: Event) => {
            const customEvent = e as CustomEvent;
            if (customEvent.detail?.containerId) {
                setContainerId(customEvent.detail.containerId);
                setContainerName(customEvent.detail.containerName || "Entity");
                setEraId("");
                setIsOpen(true);
            }
        };

        window.addEventListener("open:fork-era", handleOpen);
        return () => window.removeEventListener("open:fork-era", handleOpen);
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!eraId.trim() || !containerId) return;

        setIsSubmitting(true);
        try {
            await api.forkEra(containerId, eraId.trim());
            toast.success(`Forked ${containerName} to era: ${eraId}`);
            setIsOpen(false);

            // Refresh local store
            useStudioStore.getState().fetchAll();
        } catch (error: any) {
            toast.error(error.message || `Failed to fork era`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-indigo-500/10 rounded-lg">
                            <Copy className="w-5 h-5 text-indigo-400" />
                        </div>
                        <h2 className="text-lg font-medium text-gray-100">Fork to Era</h2>
                    </div>
                    <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white transition-colors">
                        ✕
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6">
                    <div className="mb-6">
                        <p className="text-sm text-gray-400 mb-4">
                            Create a separate version of <span className="text-gray-100 font-medium">{containerName}</span> for a new story era (e.g. Season 2). Global attributes will be copied over.
                        </p>

                        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">Era Identifier</label>
                        <div className="relative">
                            <input
                                type="text"
                                value={eraId}
                                onChange={(e) => setEraId(e.target.value)}
                                placeholder="e.g. season_2, five_years_later"
                                className="w-full bg-gray-950 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 pl-10 transition-all"
                                autoFocus
                            />
                            <div className="absolute left-3 top-2.5 text-gray-500">
                                <Sparkles className="w-4 h-4" />
                            </div>
                        </div>
                    </div>

                    <div className="flex justify-end gap-3 pt-2 border-t border-gray-800 mt-2">
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!eraId.trim() || isSubmitting}
                            className="flex items-center gap-2 px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-all shadow-lg active:scale-95"
                        >
                            {isSubmitting ? "Forking..." : "Fork Version"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
