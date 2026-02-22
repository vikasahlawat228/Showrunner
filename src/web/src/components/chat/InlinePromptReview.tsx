'use client';

import React, { useState, useEffect } from 'react';
import { Send, Sparkles, RefreshCw, Pin } from 'lucide-react';
import { api, type StyleCheckResponse } from '@/lib/api';

interface InlinePromptReviewProps {
    initialPrompt: string;
    stepName: string;
    agentId?: string;
    onResume: (payload: { prompt_text: string; model?: string; refine_instructions?: string; temperature?: number; pinned_context_ids?: string[]; regenerate?: boolean; }) => void;
}

export const InlinePromptReview: React.FC<InlinePromptReviewProps> = ({
    initialPrompt,
    stepName,
    agentId,
    onResume
}) => {
    const [promptText, setPromptText] = useState(initialPrompt);
    const [refineInput, setRefineInput] = useState('');
    const [activeTab, setActiveTab] = useState<'edit' | 'refine'>('edit');

    useEffect(() => {
        setPromptText(initialPrompt);
    }, [initialPrompt]);

    const handleResume = () => {
        onResume({ prompt_text: promptText });
    };

    const handleRefine = () => {
        if (!refineInput.trim()) return;
        onResume({
            prompt_text: promptText,
            refine_instructions: refineInput,
            regenerate: true
        });
        setRefineInput('');
    };

    return (
        <div className="mt-3 border border-indigo-500/30 rounded-lg overflow-hidden bg-gray-900 shadow-md">
            <div className="bg-indigo-500/10 px-3 py-2 flex items-center justify-between border-b border-indigo-500/20">
                <span className="text-xs font-semibold text-indigo-300">Human Approval Required: {stepName}</span>
                <div className="flex gap-2">
                    <button
                        onClick={() => setActiveTab('edit')}
                        className={`text-[10px] px-2 py-0.5 rounded ${activeTab === 'edit' ? 'bg-indigo-500/30 text-indigo-100' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                        Edit
                    </button>
                    <button
                        onClick={() => setActiveTab('refine')}
                        className={`text-[10px] px-2 py-0.5 rounded ${activeTab === 'refine' ? 'bg-indigo-500/30 text-indigo-100' : 'text-gray-400 hover:text-gray-200'}`}
                    >
                        Refine
                    </button>
                </div>
            </div>

            <div className="p-3">
                {activeTab === 'edit' ? (
                    <div>
                        <textarea
                            className="w-full h-32 p-2 text-xs bg-gray-950 border border-gray-700 rounded-md focus:ring-1 focus:ring-indigo-500 outline-none text-gray-200 resize-none font-mono"
                            value={promptText}
                            onChange={(e) => setPromptText(e.target.value)}
                        />
                        <div className="mt-2 flex justify-end">
                            <button
                                onClick={handleResume}
                                className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium rounded shadow-sm transition-colors flex items-center gap-1.5"
                            >
                                Approve & Continue <span>→</span>
                            </button>
                        </div>
                    </div>
                ) : (
                    <div>
                        <textarea
                            className="w-full h-20 p-2 text-xs bg-gray-950 border border-gray-700 rounded-md focus:ring-1 focus:ring-indigo-500 outline-none text-gray-200 resize-none"
                            value={refineInput}
                            onChange={(e) => setRefineInput(e.target.value)}
                            placeholder="Instruct the AI how to refine this prompt... (e.g. 'Make it darker')"
                        />
                        <div className="mt-2 flex justify-end">
                            <button
                                onClick={handleRefine}
                                disabled={!refineInput.trim()}
                                className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white text-xs font-medium rounded shadow-sm transition-colors flex items-center gap-1.5"
                            >
                                <RefreshCw className="w-3 h-3" />
                                Refine & Re-run
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
