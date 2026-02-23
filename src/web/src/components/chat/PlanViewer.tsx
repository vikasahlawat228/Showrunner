import React, { useState } from "react";
import { CheckSquare, Play } from "lucide-react";

interface PlanViewerProps {
    content: string;
    onSend?: (message: string) => void;
}

export function PlanViewer({ content, onSend }: PlanViewerProps) {
    const lines = content.split('\n');
    const goalLine = lines.find(l => l.startsWith('## Plan:'));
    const goal = goalLine ? goalLine.replace('## Plan:', '').trim() : '';

    const stepLines = lines.filter(l => /^\s*\d+\.\s+/.test(l));
    const steps = stepLines.map(l => {
        const match = l.match(/^\s*(\d+)\.\s+(.*)$/);
        return match ? { num: parseInt(match[1]), text: match[2] } : null;
    }).filter(Boolean) as { num: number, text: string }[];

    const [selectedSteps, setSelectedSteps] = useState<number[]>([]);
    const [isModifying, setIsModifying] = useState(false);
    const [modifyInstructions, setModifyInstructions] = useState('');

    const toggleStep = (num: number) => {
        if (selectedSteps.includes(num)) {
            setSelectedSteps(selectedSteps.filter(n => n !== num));
        } else {
            setSelectedSteps([...selectedSteps, num]);
        }
    };

    if (steps.length === 0) {
        return <div className="whitespace-pre-wrap text-sm">{content}</div>;
    }

    return (
        <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 my-2 shadow-inner">
            <h3 className="text-sm font-semibold text-gray-200 mb-2">Plan: {goal}</h3>
            <div className="space-y-2 mb-4">
                {steps.map(step => (
                    <label key={step.num} className="flex items-start gap-2 cursor-pointer hover:bg-gray-800 p-1.5 rounded transition-colors text-sm text-gray-300">
                        <input
                            type="checkbox"
                            className="mt-1 bg-gray-700 border-gray-600 rounded text-indigo-500 focus:ring-indigo-500"
                            checked={selectedSteps.includes(step.num)}
                            onChange={() => toggleStep(step.num)}
                        />
                        <span className="flex-1 whitespace-normal">
                            <span className="font-semibold text-gray-400 mr-1">{step.num}.</span>
                            {step.text}
                        </span>
                    </label>
                ))}
            </div>

            <div className="mb-4">
                {isModifying ? (
                    <div className="flex gap-2">
                        <input
                            type="text"
                            className="flex-1 bg-gray-800 border border-gray-700 rounded text-sm text-gray-200 px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                            placeholder="New instructions..."
                            value={modifyInstructions}
                            onChange={(e) => setModifyInstructions(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === 'Enter' && modifyInstructions.trim()) {
                                    onSend?.(`/replan ${modifyInstructions.trim()}`);
                                    setIsModifying(false);
                                    setModifyInstructions('');
                                }
                            }}
                            autoFocus
                        />
                        <button
                            onClick={() => {
                                if (modifyInstructions.trim()) {
                                    onSend?.(`/replan ${modifyInstructions.trim()}`);
                                    setIsModifying(false);
                                    setModifyInstructions('');
                                }
                            }}
                            className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded text-xs font-semibold transition-colors shrink-0"
                        >
                            Re-plan
                        </button>
                        <button
                            onClick={() => {
                                setIsModifying(false);
                                setModifyInstructions('');
                            }}
                            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded text-xs font-semibold transition-colors shrink-0"
                        >
                            Cancel
                        </button>
                    </div>
                ) : (
                    <button
                        onClick={() => setIsModifying(true)}
                        className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                    >
                        Modify Plan...
                    </button>
                )}
            </div>

            {onSend && (
                <div className="flex gap-2 border-t border-gray-700 pt-3">
                    <button
                        onClick={() => onSend(`/approve ${selectedSteps.join(',')}`)}
                        disabled={selectedSteps.length === 0}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-900/50 disabled:text-indigo-500/50 text-white rounded text-xs font-semibold transition-colors"
                    >
                        <CheckSquare className="w-4 h-4" />
                        Approve Selected
                    </button>
                    <button
                        onClick={() => onSend('/execute')}
                        className="flex items-center justify-center gap-2 px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold transition-colors"
                    >
                        <Play className="w-4 h-4" />
                        Execute Run
                    </button>
                </div>
            )}
        </div>
    );
}
