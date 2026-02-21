"use client";

import React, { useState, useEffect } from "react";
import { Loader2, ArrowRight, Layers } from "lucide-react";
import { type WorkflowTemplate } from "@/lib/api";
import { api } from "@/lib/api";

interface TemplateGalleryProps {
    onTemplateCreated: (definitionId: string) => void;
}

const categoryColors: Record<string, { bg: string; text: string; border: string }> = {
    writing: { bg: "bg-violet-500/10", text: "text-violet-400", border: "border-violet-500/20" },
    research: { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/20" },
    production: { bg: "bg-amber-500/10", text: "text-amber-400", border: "border-amber-500/20" },
    quality: { bg: "bg-sky-500/10", text: "text-sky-400", border: "border-sky-500/20" },
};

const categoryGradients: Record<string, string> = {
    writing: "from-violet-600/20 to-fuchsia-600/10",
    research: "from-emerald-600/20 to-teal-600/10",
    production: "from-amber-600/20 to-orange-600/10",
    quality: "from-sky-600/20 to-cyan-600/10",
};

export function TemplateGallery({ onTemplateCreated }: TemplateGalleryProps) {
    const [templates, setTemplates] = useState<WorkflowTemplate[]>([]);
    const [loadingId, setLoadingId] = useState<string | null>(null);
    const [isLoadingTemplates, setIsLoadingTemplates] = useState<boolean>(true);

    useEffect(() => {
        const fetchTemplates = async () => {
            try {
                const data = await api.getWorkflowTemplates();
                setTemplates(data);
            } catch (err) {
                console.error("Failed to fetch templates:", err);
            } finally {
                setIsLoadingTemplates(false);
            }
        };
        fetchTemplates();
    }, []);

    const handleUseTemplate = async (template: WorkflowTemplate) => {
        if (loadingId) return;
        setLoadingId(template.template_id);
        try {
            const result = await api.createFromTemplate(template.template_id);
            onTemplateCreated(result.id);
        } catch (err) {
            console.error("Failed to create pipeline from template:", err);
        } finally {
            setLoadingId(null);
        }
    };

    if (isLoadingTemplates) {
        return (
            <div className="flex items-center justify-center p-12">
                <Loader2 className="w-6 h-6 animate-spin text-gray-500" />
            </div>
        );
    }

    return (
        <section className="mb-10">
            {/* Section header */}
            <div className="flex items-center gap-2.5 mb-5">
                <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/20">
                    <Layers className="w-3.5 h-3.5 text-indigo-400" />
                </div>
                <div>
                    <h2 className="text-sm font-semibold text-gray-200">
                        Start from a Template
                    </h2>
                    <p className="text-[11px] text-gray-500">
                        Pre-built workflows to get you started quickly
                    </p>
                </div>
            </div>

            {/* Template grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {templates.map((template) => {
                    const colors = categoryColors[template.category] || categoryColors.writing;
                    const gradient = categoryGradients[template.category] || categoryGradients.writing;
                    const isLoading = loadingId === template.template_id;

                    return (
                        <div
                            key={template.template_id}
                            className="group relative flex flex-col rounded-xl border border-gray-800/80 bg-gray-900/60 hover:bg-gray-900/90 hover:border-gray-700/80 transition-all duration-300 overflow-hidden"
                        >
                            {/* Gradient accent */}
                            <div
                                className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none`}
                            />

                            <div className="relative flex flex-col flex-1 p-4">
                                {/* Icon + category */}
                                <div className="flex items-start justify-between mb-3">
                                    <span className="text-2xl leading-none" role="img" aria-label={template.name}>
                                        {/* Fallback emoji based on category if no icon provided */
                                            template.category === 'writing' ? '✍️' :
                                                template.category === 'research' ? '🔍' :
                                                    template.category === 'production' ? '🎬' : '✨'}
                                    </span>
                                    <span
                                        className={`px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider border ${colors.bg} ${colors.text} ${colors.border}`}
                                    >
                                        {template.category}
                                    </span>
                                </div>

                                {/* Title + description */}
                                <h3 className="text-sm font-semibold text-white mb-1.5 group-hover:text-gray-50 transition-colors">
                                    {template.name}
                                </h3>
                                <p className="text-xs text-gray-500 leading-relaxed mb-4 line-clamp-2 flex-1">
                                    {template.description}
                                </p>

                                {/* Footer */}
                                <div className="flex items-center justify-between mt-auto">
                                    <span className="text-[10px] text-gray-600 font-medium">
                                        {template.steps.length} steps · {template.edges.length} connections
                                    </span>
                                    <button
                                        onClick={() => handleUseTemplate(template)}
                                        disabled={!!loadingId}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 ${isLoading
                                            ? "bg-indigo-600/50 text-indigo-300 cursor-wait"
                                            : "bg-indigo-600/80 hover:bg-indigo-500 text-white cursor-pointer shadow-sm hover:shadow-indigo-500/20 hover:shadow-md"
                                            }`}
                                    >
                                        {isLoading ? (
                                            <>
                                                <Loader2 className="w-3 h-3 animate-spin" />
                                                Creating…
                                            </>
                                        ) : (
                                            <>
                                                Use Template
                                                <ArrowRight className="w-3 h-3 opacity-70 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                                            </>
                                        )}
                                    </button>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </section>
    );
}
