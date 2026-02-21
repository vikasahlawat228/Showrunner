"use client";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Plus } from "lucide-react";
import { useStudioStore } from "@/lib/store";

export function QuickAddModal() {
    const [isOpen, setIsOpen] = useState(false);
    const [type, setType] = useState<string>("character");
    const [name, setName] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        const handleOpen = (e: Event) => {
            const customEvent = e as CustomEvent;
            if (customEvent.detail?.type) {
                setType(customEvent.detail.type);
            }
            if (customEvent.detail?.predefinedName) {
                setName(customEvent.detail.predefinedName);
            } else {
                setName("");
            }
            setIsOpen(true);
        };

        window.addEventListener("open:quick-add", handleOpen);
        return () => window.removeEventListener("open:quick-add", handleOpen);
    }, []);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name.trim()) return;

        setIsSubmitting(true);
        try {
            await api.createContainer({
                container_type: type,
                name: name.trim()
            });
            toast.success(`Created ${type.replace('_', ' ')}: ${name}`);
            setIsOpen(false);

            // Refresh local store so mentions are instantly updated
            useStudioStore.getState().fetchAll();
        } catch (error: any) {
            toast.error(error.message || `Failed to create ${type.replace('_', ' ')}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[200] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
            <div className="bg-gray-900 border border-gray-700 rounded-xl w-full max-w-md shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
                <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50">
                    <h2 className="text-lg font-medium text-gray-100 capitalize">Quick Add {type.replace('_', ' ')}</h2>
                    <button onClick={() => setIsOpen(false)} className="text-gray-400 hover:text-white">
                        ✕
                    </button>
                </div>
                <form onSubmit={handleSubmit} className="p-6">
                    <div className="mb-6">
                        <label className="block text-sm font-medium text-gray-400 mb-2">Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder={`e.g. ${type === 'character' ? 'Zara' : type === 'scene' ? 'Scene 4' : 'Idea'}`}
                            className="w-full bg-gray-950 border border-gray-700 rounded-md px-4 py-2 text-gray-100 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                            autoFocus
                        />
                    </div>
                    <div className="flex justify-end gap-3">
                        <button
                            type="button"
                            onClick={() => setIsOpen(false)}
                            className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={!name.trim() || isSubmitting}
                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md transition-colors shadow-sm"
                        >
                            <Plus className="w-4 h-4" />
                            {isSubmitting ? "Creating..." : "Create"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
