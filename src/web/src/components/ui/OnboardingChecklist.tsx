"use client";

import { useEffect, useState } from "react";
import { Check, Circle, ChevronDown, ChevronUp } from "lucide-react";
import { useStudioStore } from "@/lib/store";

interface ChecklistItem {
    id: string;
    label: string;
    description: string;
    check: (data: ChecklistData) => boolean;
}

interface ChecklistData {
    characterCount: number;
    sceneCount: number;
    hasWorld: boolean;
    hasFragment: boolean;
    hasPanels: boolean;
}

const CHECKLIST_ITEMS: ChecklistItem[] = [
    {
        id: "world",
        label: "Create your World",
        description: "Set up the world, genre, and setting",
        check: (d) => d.hasWorld,
    },
    {
        id: "characters",
        label: "Add Characters (3+)",
        description: "Create at least 3 characters for your story",
        check: (d) => d.characterCount >= 3,
    },
    {
        id: "outline",
        label: "Outline Chapter 1",
        description: "Create scenes for your first chapter",
        check: (d) => d.sceneCount >= 1,
    },
    {
        id: "write",
        label: "Write First Scene",
        description: "Open Zen Mode and start writing",
        check: (d) => d.hasFragment,
    },
    {
        id: "panels",
        label: "Generate First Panel",
        description: "Create a storyboard panel from a scene",
        check: (d) => d.hasPanels,
    },
];

export function OnboardingChecklist() {
    const [expanded, setExpanded] = useState(true);
    const [data, setData] = useState<ChecklistData>({
        characterCount: 0,
        sceneCount: 0,
        hasWorld: false,
        hasFragment: false,
        hasPanels: false,
    });

    const characters = useStudioStore((s) => s.characters);
    const scenes = useStudioStore((s) => s.scenes);
    const worldData = useStudioStore((s) => s.worldData);

    useEffect(() => {
        setData({
            characterCount: characters?.length || 0,
            sceneCount: scenes?.length || 0,
            hasWorld: !!worldData?.name,
            hasFragment: !!localStorage.getItem("showrunner:hasWritten"),
            hasPanels: !!localStorage.getItem("showrunner:hasPanel"),
        });
    }, [characters, scenes, worldData]);

    const completedCount = CHECKLIST_ITEMS.filter((item) => item.check(data)).length;
    const allDone = completedCount === CHECKLIST_ITEMS.length;
    const progress = (completedCount / CHECKLIST_ITEMS.length) * 100;

    // Don't show if all done
    if (allDone) return null;

    return (
        <div className="bg-gray-900/50 border border-gray-800 rounded-xl overflow-hidden">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-800/30 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className="relative w-8 h-8">
                        <svg className="w-8 h-8 -rotate-90" viewBox="0 0 32 32">
                            <circle cx="16" cy="16" r="13" fill="none" stroke="#1f2937" strokeWidth="3" />
                            <circle
                                cx="16" cy="16" r="13" fill="none" stroke="#6366f1" strokeWidth="3"
                                strokeDasharray={`${progress * 0.817} 100`}
                                strokeLinecap="round"
                                className="transition-all duration-700"
                            />
                        </svg>
                        <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-indigo-400">
                            {completedCount}/{CHECKLIST_ITEMS.length}
                        </span>
                    </div>
                    <div className="text-left">
                        <span className="text-sm font-semibold text-gray-200">Getting Started</span>
                        <span className="block text-xs text-gray-500">{completedCount} of {CHECKLIST_ITEMS.length} complete</span>
                    </div>
                </div>
                {expanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-500" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                )}
            </button>

            {expanded && (
                <div className="px-4 pb-4 space-y-1">
                    {CHECKLIST_ITEMS.map((item) => {
                        const done = item.check(data);
                        return (
                            <div
                                key={item.id}
                                className={`flex items-start gap-3 px-3 py-2 rounded-lg transition-colors ${done ? "opacity-60" : "hover:bg-gray-800/30"
                                    }`}
                            >
                                {done ? (
                                    <div className="mt-0.5 w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center shrink-0">
                                        <Check className="w-3 h-3 text-emerald-400" />
                                    </div>
                                ) : (
                                    <div className="mt-0.5 w-5 h-5 rounded-full border border-gray-700 flex items-center justify-center shrink-0">
                                        <Circle className="w-2 h-2 text-gray-600" />
                                    </div>
                                )}
                                <div>
                                    <span className={`text-sm font-medium ${done ? "text-gray-500 line-through" : "text-gray-300"}`}>
                                        {item.label}
                                    </span>
                                    <span className="block text-xs text-gray-600">{item.description}</span>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
