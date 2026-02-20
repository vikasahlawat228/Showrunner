'use client';

import React, { useState, useEffect } from 'react';

interface PromptReviewModalProps {
    isOpen: boolean;
    initialPrompt?: string;
    stepName?: string;
    onResume: (editedText: string) => void;
    onCancel?: () => void;
}

export const PromptReviewModal: React.FC<PromptReviewModalProps> = ({
    isOpen,
    initialPrompt = '',
    stepName = 'Assemble Prompt',
    onResume,
    onCancel
}) => {
    const [promptText, setPromptText] = useState(initialPrompt);

    // Sync initialPrompt changes if modal is reopened or prompt updates from SSE payload
    useEffect(() => {
        setPromptText(initialPrompt);
    }, [initialPrompt]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-2xl bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">

                {/* Header */}
                <div className="px-6 py-4 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                        <div className="relative flex h-3 w-3">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
                        </div>
                        <div>
                            <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">AI Waiting for Alignment</h2>
                            <p className="text-sm text-zinc-500 dark:text-zinc-400">Step: {stepName}</p>
                        </div>
                    </div>
                </div>

                {/* Body */}
                <div className="p-6 flex-grow">
                    <label htmlFor="prompt-edit" className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">
                        Review and edit the AI&apos;s prompt before continuing:
                    </label>
                    <textarea
                        id="prompt-edit"
                        className="w-full h-48 p-4 text-sm bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-xl focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-500 focus:border-transparent outline-none resize-none text-zinc-900 dark:text-zinc-100"
                        value={promptText}
                        onChange={(e) => setPromptText(e.target.value)}
                        placeholder="Edit the prompt here..."
                    />
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-zinc-50 dark:bg-zinc-900/50 border-t border-zinc-100 dark:border-zinc-800 flex justify-end space-x-3">
                    {onCancel && (
                        <button
                            onClick={onCancel}
                            className="px-4 py-2 text-sm font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 transition-colors"
                        >
                            Cancel
                        </button>
                    )}
                    <button
                        onClick={() => onResume(promptText)}
                        className="px-5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg shadow-sm transition-colors focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-zinc-900 flex items-center space-x-2"
                    >
                        <span>Resume Pipeline</span>
                        <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    );
};
