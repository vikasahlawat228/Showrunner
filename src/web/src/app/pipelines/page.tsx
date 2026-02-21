"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Zap, Plus, Trash2, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { PipelineBuilder } from "@/components/pipeline-builder/PipelineBuilder";
import { TemplateGallery } from "@/components/pipeline-builder/TemplateGallery";
import { NLPipelineWizard } from "@/components/pipeline-builder/NLPipelineWizard";
import {
    usePipelineBuilderStore,
    type PipelineDefSummary,
} from "@/lib/store/pipelineBuilderSlice";
import { api } from "@/lib/api";

export default function PipelinesPage() {
    const {
        definitions,
        loadDefinitions,
        loadDefinition,
        loadRegistry,
        resetBuilder,
        currentDefinitionId,
    } = usePipelineBuilderStore();

    const [showGallery, setShowGallery] = useState(true);
    const [showNLWizard, setShowNLWizard] = useState(false);

    useEffect(() => {
        loadRegistry();
        loadDefinitions();
    }, [loadRegistry, loadDefinitions]);

    const handleLoadDefinition = (id: string) => {
        loadDefinition(id);
        setShowGallery(false);
    };

    const handleNewPipeline = () => {
        resetBuilder();
        setShowGallery(false);
    };

    const handleTemplateCreated = (definitionId: string) => {
        loadDefinitions();
        loadDefinition(definitionId);
        setShowGallery(false);
    };

    const handleDeleteDefinition = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        await api.deletePipelineDefinition(id);
        loadDefinitions();
    };

    return (
        <div className="h-screen flex flex-col bg-gray-950 text-white">
            {/* Top bar */}
            <header className="flex items-center justify-between px-4 py-2 border-b border-gray-800/60 bg-gray-950/90 backdrop-blur-sm shrink-0">
                <div className="flex items-center gap-3">
                    <Link
                        href="/dashboard"
                        className="flex items-center gap-1.5 text-gray-500 hover:text-gray-300 transition-colors text-sm"
                    >
                        <ArrowLeft className="w-4 h-4" />
                        Dashboard
                    </Link>
                    <div className="w-px h-4 bg-gray-800" />
                    <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-yellow-400" />
                        <span className="text-sm font-semibold text-gray-200">
                            Pipeline Builder
                        </span>
                    </div>
                </div>

                <nav className="flex items-center gap-1">
                    <Link
                        href="/dashboard"
                        className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
                    >
                        Canvas
                    </Link>
                    <Link
                        href="/zen"
                        className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
                    >
                        Zen Mode
                    </Link>
                    <span className="px-3 py-1.5 rounded text-xs text-yellow-400 bg-yellow-500/10">
                        Pipelines
                    </span>
                    <Link
                        href="/schemas"
                        className="px-3 py-1.5 rounded text-xs text-gray-500 hover:text-gray-300 hover:bg-gray-800 transition-colors"
                    >
                        Schemas
                    </Link>
                </nav>
            </header>

            {/* Content */}
            {showGallery && !currentDefinitionId ? (
                <div className="flex-1 overflow-y-auto p-8">
                    <div className="max-w-5xl mx-auto">
                        <div className="flex items-center justify-between mb-8">
                            <div>
                                <h1 className="text-2xl font-bold text-white">Pipelines</h1>
                                <p className="text-sm text-gray-500 mt-1">
                                    Build composable AI workflows from reusable steps
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => setShowNLWizard(true)}
                                    className="flex items-center gap-2 px-3 py-2 bg-purple-600/20 text-purple-300 rounded-lg hover:bg-purple-600/30 border border-purple-500/30 transition-colors text-sm font-medium"
                                >
                                    <Sparkles className="w-4 h-4" />
                                    Create from Description
                                </button>
                                <button
                                    onClick={handleNewPipeline}
                                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
                                >
                                    <Plus className="w-4 h-4" />
                                    New Pipeline
                                </button>
                            </div>
                        </div>

                        {/* Template Gallery */}
                        <TemplateGallery onTemplateCreated={handleTemplateCreated} />

                        {/* Divider */}
                        <div className="flex items-center gap-3 mb-5">
                            <div className="h-px flex-1 bg-gray-800/60" />
                            <span className="text-[11px] text-gray-600 font-medium uppercase tracking-wider">
                                Your Pipelines
                            </span>
                            <div className="h-px flex-1 bg-gray-800/60" />
                        </div>

                        {definitions.length === 0 ? (
                            <div className="text-center py-16 border border-dashed border-gray-800 rounded-xl">
                                <Zap className="w-10 h-10 mx-auto mb-3 text-gray-700" />
                                <p className="text-gray-500 mb-4">
                                    No pipelines yet. Create your first one or start from a template above!
                                </p>
                                <button
                                    onClick={handleNewPipeline}
                                    className="px-4 py-2 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 text-sm transition-colors"
                                >
                                    Create Pipeline
                                </button>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {definitions.map((def) => (
                                    <button
                                        key={def.id}
                                        onClick={() => handleLoadDefinition(def.id)}
                                        className="text-left p-4 rounded-xl border border-gray-800 bg-gray-900/50 hover:bg-gray-800/80 hover:border-gray-700 transition-all group"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <h3 className="font-semibold text-white">{def.name}</h3>
                                            <button
                                                onClick={(e) => handleDeleteDefinition(def.id, e)}
                                                className="p-1 rounded text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                        {def.description && (
                                            <p className="text-xs text-gray-500 mb-2 line-clamp-2">
                                                {def.description}
                                            </p>
                                        )}
                                        <div className="flex items-center gap-3 text-[10px] text-gray-600">
                                            <span>{def.step_count} steps</span>
                                            <span>
                                                {new Date(def.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                <div className="flex-1 overflow-hidden">
                    <PipelineBuilder />
                </div>
            )}
            {/* Wizard Modal */}
            <NLPipelineWizard
                isOpen={showNLWizard}
                onClose={() => setShowNLWizard(false)}
                onCreated={(definitionId) => {
                    loadDefinitions();
                    loadDefinition(definitionId);
                    setShowGallery(false);
                    setShowNLWizard(false);
                    toast.success("Pipeline created from description!");
                }}
            />
        </div>
    );
}
