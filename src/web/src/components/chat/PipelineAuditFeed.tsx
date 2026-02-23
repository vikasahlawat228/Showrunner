import React, { useState } from 'react';
import { ShieldCheck, ChevronDown, ChevronRight, RotateCcw, Edit2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface AutoApprovedStep {
    step_id: string;
    step_name: string;
    prompt_text?: string;
    model?: string;
    confidence_score: number;
    continuity_errors: string[];
    generated_text?: string;
}

interface PipelineAuditFeedProps {
    steps: AutoApprovedStep[];
    onReverse?: (stepId: string) => void;
    onEditRetry?: (stepId: string, newPrompt: string) => void;
}

export function PipelineAuditFeed({ steps, onReverse, onEditRetry }: PipelineAuditFeedProps) {
    if (!steps || steps.length === 0) return null;

    return (
        <div className="mt-3 border-t border-gray-700 pt-3">
            <div className="flex items-center gap-2 mb-2 px-1">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <span className="text-xs font-semibold text-gray-300 uppercase tracking-wider">Audit Trail</span>
                <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded-full">
                    {steps.length} auto-approved
                </span>
            </div>
            <div className="space-y-2">
                {steps.map((step, idx) => (
                    <AuditFeedItem key={`${step.step_id}-${idx}`} step={step} onReverse={onReverse} onEditRetry={onEditRetry} />
                ))}
            </div>
        </div>
    );
}

function AuditFeedItem({ step, onReverse, onEditRetry }: { step: AutoApprovedStep, onReverse?: (id: string) => void, onEditRetry?: (id: string, prompt: string) => void }) {
    const [expanded, setExpanded] = useState(false);
    const [isEditing, setIsEditing] = useState(false);
    const [editPrompt, setEditPrompt] = useState(step.prompt_text || "");

    return (
        <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg overflow-hidden transition-all duration-200">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between p-2 hover:bg-gray-800/80 transition-colors text-left"
            >
                <div className="flex items-center gap-2">
                    {expanded ? <ChevronDown className="w-3.5 h-3.5 text-gray-400" /> : <ChevronRight className="w-3.5 h-3.5 text-gray-400" />}
                    <span className="text-sm text-gray-200 font-medium">{step.step_name}</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">
                        {step.confidence_score}% Conf
                    </span>
                    {step.model && (
                        <span className="text-[10px] font-mono text-gray-500 truncate max-w-[80px]">
                            {step.model.split('/').pop()}
                        </span>
                    )}
                </div>
            </button>

            {expanded && (
                <div className="p-3 border-t border-gray-700/50 bg-gray-900/50 space-y-3">
                    {/* Prompt Section */}
                    <div>
                        <div className="text-[10px] uppercase text-gray-500 font-semibold mb-1">Prompt Used</div>
                        {isEditing ? (
                            <div className="space-y-2">
                                <textarea
                                    className="w-full bg-gray-950 border border-indigo-500/50 rounded p-2 text-xs text-gray-300 min-h-[100px] focus:outline-none focus:ring-1 focus:ring-indigo-500 scrollbar-thin scrollbar-thumb-gray-700"
                                    value={editPrompt}
                                    onChange={(e) => setEditPrompt(e.target.value)}
                                />
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => {
                                            setIsEditing(false);
                                            onEditRetry?.(step.step_id, editPrompt);
                                        }}
                                        className="px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white text-xs rounded transition-colors"
                                    >
                                        Execute Retry
                                    </button>
                                    <button
                                        onClick={() => setIsEditing(false)}
                                        className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs rounded transition-colors"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="bg-gray-950 rounded p-2 text-xs text-gray-400 max-h-32 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800">
                                {step.prompt_text || "No prompt recorded"}
                            </div>
                        )}
                    </div>

                    {/* Generated Context */}
                    {step.generated_text && !isEditing && (
                        <div>
                            <div className="text-[10px] uppercase text-gray-500 font-semibold mb-1">Generated Output</div>
                            <div className="bg-gray-950 rounded p-2 text-xs text-gray-300 max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-800 prose prose-invert prose-sm">
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                    {step.generated_text}
                                </ReactMarkdown>
                            </div>
                        </div>
                    )}

                    {/* Actions */}
                    {!isEditing && (
                        <div className="flex items-center gap-2 pt-1 border-t border-gray-800/80">
                            <button
                                onClick={() => setIsEditing(true)}
                                className="flex items-center gap-1.5 px-2 py-1 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs rounded transition-colors"
                            >
                                <Edit2 className="w-3 h-3" /> Edit & Retry
                            </button>
                            <button
                                onClick={() => onReverse?.(step.step_id)}
                                className="flex items-center gap-1.5 px-2 py-1 bg-red-900/30 hover:bg-red-900/50 text-red-400 border border-red-900/50 hover:border-red-500/50 text-xs rounded transition-colors ml-auto"
                            >
                                <RotateCcw className="w-3 h-3" /> Reverse State
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
