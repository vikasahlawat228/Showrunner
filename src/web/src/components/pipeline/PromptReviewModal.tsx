'use client';

import React, { useState, useEffect } from 'react';
import {
    MessageCircle,
    ClipboardPaste,
    Upload,
    SkipForward,
    Loader2,
    Send,
    Pin,
    RefreshCw,
    Sparkles,
} from 'lucide-react';
import { getAgentConfig } from '@/lib/agentConfig';
import { api, type StyleCheckResponse } from '@/lib/api';
import { ContextInspector } from '@/components/ui/ContextInspector';

interface PromptReviewModalProps {
    isOpen: boolean;
    initialPrompt?: string;
    stepName?: string;
    stepType?: string;
    agentId?: string;
    contextBuckets?: Array<{ id: string; name: string; type: string; summary: string }>;
    modelUsed?: string;
    tokenCount?: number;
    onResume: (payload: { prompt_text: string; model?: string; refine_instructions?: string; temperature?: number; pinned_context_ids?: string[]; regenerate?: boolean; }) => void;
    onCancel?: () => void;
}

type ModalTab = 'edit' | 'refine' | 'paste' | 'style';

export const PromptReviewModal: React.FC<PromptReviewModalProps> = ({
    isOpen,
    initialPrompt = '',
    stepName = 'Assemble Prompt',
    stepType,
    agentId,
    contextBuckets,
    modelUsed,
    tokenCount,
    onResume,
    onCancel
}) => {
    const [promptText, setPromptText] = useState(initialPrompt);
    const [activeTab, setActiveTab] = useState<ModalTab>('edit');
    const [refineInput, setRefineInput] = useState('');
    const [pasteText, setPasteText] = useState('');

    const [styleAnalysis, setStyleAnalysis] = useState<StyleCheckResponse | null>(null);
    const [isAnalyzingStyle, setIsAnalyzingStyle] = useState(false);

    // Model Selection & Overrides State
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [selectedModel, setSelectedModel] = useState<string>('');
    const [temperature, setTemperature] = useState<number>(0.7);
    const [pinnedContextIds, setPinnedContextIds] = useState<string[]>([]);

    const agent = getAgentConfig(agentId);
    const AgentIcon = agent.icon;

    useEffect(() => {
        setPromptText(initialPrompt);
    }, [initialPrompt]);

    useEffect(() => {
        if (isOpen) {
            api.getAvailableModels()
                .then(models => setAvailableModels(models))
                .catch(err => console.error("Failed to fetch available models", err));
            setRefineInput('');
            setActiveTab('edit');
            setTemperature(0.7);
            setPinnedContextIds([]);
            setStyleAnalysis(null);
        }
    }, [isOpen]);

    const togglePinContext = (id: string) => {
        setPinnedContextIds(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    };

    const handleRefineSubmit = () => {
        if (!refineInput.trim()) return;
        onResume({
            prompt_text: promptText || '',
            model: selectedModel || undefined,
            refine_instructions: refineInput
        });
        setRefineInput('');
        setActiveTab('edit');
    };

    const handlePasteApply = () => {
        if (pasteText.trim()) {
            setPromptText((prev) => `${prev}\n\n## External AI Response\n${pasteText}`);
            setPasteText('');
            setActiveTab('edit');
        }
    };

    const handleSkip = () => {
        onResume({
            prompt_text: promptText || '[SKIPPED]',
            model: selectedModel || undefined
        });
    };

    const handleAnalyzeStyle = async () => {
        setIsAnalyzingStyle(true);
        try {
            const res = await api.checkStyle(promptText);
            setStyleAnalysis(res);
        } catch (e) {
            console.error("Failed to analyze style:", e);
        } finally {
            setIsAnalyzingStyle(false);
        }
    };

    if (!isOpen) return null;

    const tabClass = (tab: ModalTab) =>
        `px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${activeTab === tab
            ? 'bg-gray-700 text-white'
            : 'text-gray-500 hover:text-gray-300'
        }`;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-3xl bg-gray-900 rounded-2xl shadow-2xl border border-gray-700 overflow-hidden flex flex-col max-h-[85vh]">

                {/* Header */}
                <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between shrink-0">
                    <div className="flex items-center space-x-3">
                        {/* Agent Identity Indicator */}
                        <div className={`relative flex items-center justify-center h-9 w-9 rounded-lg border ${agent.bgClass} ${agent.borderClass}`}>
                            <AgentIcon className={`w-4 h-4 ${agent.textClass}`} />
                            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75" />
                                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-amber-500" />
                            </span>
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-white">
                                <span className={agent.textClass}>{agent.displayName}</span>
                                <span className="text-gray-500 font-normal text-sm ml-2">awaiting alignment</span>
                            </h2>
                            <p className="text-sm text-gray-400">Step: {stepName}</p>
                        </div>
                    </div>

                    {/* Model & Tabs */}
                    <div className="flex items-center space-x-4">
                        <select
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                            className="bg-gray-800 border border-gray-700 text-gray-300 text-xs rounded-lg focus:ring-indigo-500 focus:border-indigo-500 block px-2.5 py-1.5 outline-none max-w-48"
                        >
                            <option value="">Default Model</option>
                            {availableModels.map(m => (
                                <option key={m} value={m}>{m}</option>
                            ))}
                        </select>
                        <div className="flex items-center gap-2 bg-gray-800 rounded-lg px-2.5 py-1">
                            <label className="text-xs text-gray-500 font-medium">Temp</label>
                            <input
                                type="range"
                                min="0" max="2" step="0.1"
                                value={temperature}
                                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                className="w-16 accent-indigo-500 bg-gray-700 h-1.5 rounded-lg appearance-none cursor-pointer"
                            />
                            <span className="text-xs text-gray-400 font-mono w-5">{temperature.toFixed(1)}</span>
                        </div>
                        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
                            <button onClick={() => setActiveTab('edit')} className={tabClass('edit')}>
                                ✏️ Edit
                            </button>
                            <button onClick={() => setActiveTab('refine')} className={tabClass('refine')}>
                                <MessageCircle className="w-3 h-3 inline mr-1" />
                                Refine
                            </button>
                            <button onClick={() => setActiveTab('paste')} className={tabClass('paste')}>
                                <ClipboardPaste className="w-3 h-3 inline mr-1" />
                                Paste
                            </button>
                            <button onClick={() => setActiveTab('style')} className={tabClass('style')}>
                                <Sparkles className="w-3 h-3 inline mr-1" />
                                Style
                            </button>
                        </div>
                    </div>
                </div>

                {/* Glass Box — Context Inspector */}
                {(contextBuckets || modelUsed) && (
                    <div className="px-6 pt-3 space-y-3">
                        <ContextInspector
                            operation={{
                                agentName: agent.displayName,
                                agentId: agentId || 'pipeline',
                                modelUsed: modelUsed || selectedModel || 'default',
                                contextBuckets: contextBuckets || [],
                                tokenCount: tokenCount,
                                promptPreview: initialPrompt,
                            }}
                        />
                        {contextBuckets && contextBuckets.length > 0 && (
                            <div className="bg-gray-900 border border-gray-800 rounded-lg p-3">
                                <h4 className="text-xs font-semibold text-gray-400 mb-2 px-1">Pin Context to Upcoming LLM Run</h4>
                                <div className="space-y-1">
                                    {contextBuckets.map(bucket => (
                                        <div key={bucket.id} className="flex items-center justify-between px-2 py-1.5 hover:bg-gray-800/50 rounded-md transition-colors">
                                            <span className="text-xs text-gray-300 font-medium truncate pr-4">{bucket.name}</span>
                                            <button
                                                onClick={() => togglePinContext(bucket.id)}
                                                className={`p-1 rounded-md transition-colors ${pinnedContextIds.includes(bucket.id) ? 'text-indigo-400 bg-indigo-500/10' : 'text-gray-500 hover:text-gray-300 hover:bg-gray-700'}`}
                                                title="Pin to prompt payload"
                                            >
                                                <Pin className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Body */}
                <div className="p-6 flex-grow overflow-y-auto">
                    {activeTab === 'edit' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Review and edit the AI&apos;s prompt:
                            </label>
                            <textarea
                                className="w-full h-56 p-4 text-sm bg-gray-950 border border-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none text-white"
                                value={promptText}
                                onChange={(e) => setPromptText(e.target.value)}
                                placeholder="Edit the prompt here..."
                            />
                        </div>
                    )}

                    {activeTab === 'refine' && (
                        <div className="flex flex-col h-56">
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Add instructions for <span className={agent.textClass}>{agent.displayName}</span> to refine the prompt (loops back to generation):
                            </label>
                            <textarea
                                className="flex-1 w-full p-4 mb-3 text-sm bg-gray-950 border border-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none text-white"
                                value={refineInput}
                                onChange={(e) => setRefineInput(e.target.value)}
                                placeholder='"Make the tone more mysterious", "Focus on the dialogue between Zara and Kael"'
                            />
                            <div className="flex justify-end">
                                <button
                                    onClick={handleRefineSubmit}
                                    disabled={!refineInput.trim()}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center space-x-2 disabled:opacity-50"
                                >
                                    <span>Send & Re-Run Pipeline</span>
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    )}

                    {activeTab === 'paste' && (
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-2">
                                Paste a response from ChatGPT, Claude, or another AI:
                            </label>
                            <textarea
                                className="w-full h-40 p-4 text-sm bg-gray-950 border border-gray-700 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none text-white"
                                value={pasteText}
                                onChange={(e) => setPasteText(e.target.value)}
                                placeholder="Paste external AI response here..."
                            />
                            <div className="flex items-center gap-3 mt-3">
                                <button
                                    onClick={handlePasteApply}
                                    disabled={!pasteText.trim()}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-emerald-700 hover:bg-emerald-600 text-white transition-colors disabled:opacity-50"
                                >
                                    <ClipboardPaste className="w-3 h-3" />
                                    Apply to Prompt
                                </button>
                                <label className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-300 cursor-pointer transition-colors">
                                    <Upload className="w-3 h-3" />
                                    Upload File
                                    <input type="file" className="hidden" onChange={() => { }} />
                                </label>
                            </div>
                        </div>
                    )}

                    {activeTab === 'style' && (
                        <div className="flex flex-col h-full space-y-4">
                            <div className="flex items-center justify-between shrink-0">
                                <label className="block text-sm font-medium text-gray-300">
                                    Style Analysis & Suggestions
                                </label>
                                <button
                                    onClick={handleAnalyzeStyle}
                                    disabled={isAnalyzingStyle || !promptText.trim()}
                                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-colors disabled:opacity-50"
                                >
                                    {isAnalyzingStyle ? <Loader2 className="w-3 h-3 animate-spin" /> : <Sparkles className="w-3 h-3" />}
                                    Analyze Current Prose
                                </button>
                            </div>

                            <div className="w-full flex-1 min-h-[14rem] p-4 text-sm bg-gray-950 border border-gray-700 rounded-xl overflow-y-auto text-white">
                                {!styleAnalysis && !isAnalyzingStyle && (
                                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                                        <Sparkles className="w-6 h-6 mb-2 text-gray-600" />
                                        <p>Run Style Enforcer to check this text.</p>
                                    </div>
                                )}

                                {isAnalyzingStyle && (
                                    <div className="flex flex-col items-center justify-center h-full text-indigo-400">
                                        <Loader2 className="w-6 h-6 mb-2 animate-spin" />
                                        <p>Analyzing style...</p>
                                    </div>
                                )}

                                {styleAnalysis && !isAnalyzingStyle && (
                                    <div className="space-y-4">
                                        <div className="flex items-center gap-3">
                                            <div className="text-2xl font-bold bg-gray-800 px-3 py-1 rounded-lg text-emerald-400">
                                                {(styleAnalysis.overall_score * 10).toFixed(1)}
                                            </div>
                                            <div className="text-sm text-gray-300">
                                                {styleAnalysis.summary}
                                            </div>
                                        </div>

                                        {styleAnalysis.strengths.length > 0 && (
                                            <div className="bg-emerald-500/10 border border-emerald-500/20 rounded p-3">
                                                <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-2">Strengths</h4>
                                                <ul className="list-disc list-inside text-emerald-200/80 text-xs space-y-1">
                                                    {styleAnalysis.strengths.map((s, i) => <li key={i}>{s}</li>)}
                                                </ul>
                                            </div>
                                        )}

                                        {styleAnalysis.issues.map((issue, idx) => (
                                            <div key={idx} className={`p-3 rounded border ${issue.severity === 'high' ? 'bg-rose-500/10 border-rose-500/20' : issue.severity === 'medium' ? 'bg-amber-500/10 border-amber-500/20' : 'bg-gray-800 border-gray-700'}`}>
                                                <div className="flex items-center gap-2 mb-1">
                                                    <span className={`text-xs font-semibold capitalize ${issue.severity === 'high' ? 'text-rose-400' : issue.severity === 'medium' ? 'text-amber-400' : 'text-gray-400'}`}>{issue.category}</span>
                                                    {issue.location && <span className="text-[10px] bg-black/40 px-1 py-0.5 rounded text-gray-500">{issue.location}</span>}
                                                </div>
                                                <p className="text-xs text-gray-300">{issue.description}</p>
                                                {issue.suggestion && (
                                                    <p className="text-xs text-indigo-300 mt-2 bg-black/40 p-1.5 rounded">Fix: {issue.suggestion}</p>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-gray-900/50 border-t border-gray-800 flex justify-between items-center shrink-0">
                    <div className="flex items-center gap-2">
                        <button
                            onClick={handleSkip}
                            className="flex items-center gap-1 px-3 py-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
                        >
                            <SkipForward className="w-3 h-3" />
                            Skip Step
                        </button>
                        {onCancel && (
                            <button
                                onClick={onCancel}
                                className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-300 transition-colors"
                            >
                                Cancel
                            </button>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => onResume({
                                prompt_text: promptText || '',
                                model: selectedModel || undefined,
                                temperature: temperature !== 0.7 ? temperature : undefined,
                                pinned_context_ids: pinnedContextIds.length > 0 ? pinnedContextIds : undefined,
                                regenerate: true,
                            })}
                            className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center"
                        >
                            <RefreshCw className="w-4 h-4 mr-1.5" />
                            Regenerate
                        </button>
                        <button
                            onClick={() => onResume({
                                prompt_text: promptText || '',
                                model: selectedModel || undefined,
                                temperature: temperature !== 0.7 ? temperature : undefined,
                                pinned_context_ids: pinnedContextIds.length > 0 ? pinnedContextIds : undefined,
                            })}
                            className="px-5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium rounded-lg shadow-sm transition-colors flex items-center space-x-2"
                        >
                            <span>Resume Pipeline</span>
                            <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
