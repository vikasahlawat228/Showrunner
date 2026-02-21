"use client";

import React, {
    forwardRef,
    useEffect,
    useImperativeHandle,
    useState,
} from "react";
import {
    Sparkles,
    PenTool,
    ImageIcon,
    MessageCircle,
    Wand2,
    Eye,
    BookOpen,
    Expand,
    Globe,
} from "lucide-react";

export interface SlashCommand {
    id: string;
    label: string;
    description: string;
    icon: React.ReactNode;
    action: string;
}

export interface SlashCommandListRef {
    onKeyDown: (props: { event: KeyboardEvent }) => boolean;
}

interface SlashCommandListProps {
    items: SlashCommand[];
    command: (item: SlashCommand) => void;
}

export const SLASH_COMMANDS: SlashCommand[] = [
    {
        id: "brainstorm",
        label: "Brainstorm",
        description: "AI brainstorming with current context",
        icon: <Sparkles className="w-4 h-4 text-yellow-400" />,
        action: "brainstorm",
    },
    {
        id: "generate",
        label: "Generate",
        description: "Generate prose for the current scene",
        icon: <PenTool className="w-4 h-4 text-blue-400" />,
        action: "generate",
    },
    {
        id: "visualize",
        label: "Visualize",
        description: "Generate a panel image from this text",
        icon: <ImageIcon className="w-4 h-4 text-purple-400" />,
        action: "visualize",
    },
    {
        id: "analyze",
        label: "Analyze",
        description: "Analyze character arcs and continuity",
        icon: <Eye className="w-4 h-4 text-green-400" />,
        action: "analyze",
    },
    {
        id: "rewrite",
        label: "Rewrite",
        description: "Rewrite the selected text with AI",
        icon: <Wand2 className="w-4 h-4 text-orange-400" />,
        action: "rewrite",
    },
    {
        id: "chat",
        label: "Chat",
        description: "Open inline AI chat about this text",
        icon: <MessageCircle className="w-4 h-4 text-indigo-400" />,
        action: "chat",
    },
    {
        id: "research",
        label: "Research",
        description: "Research real-world topics for accuracy",
        icon: <BookOpen className="w-4 h-4 text-cyan-400" />,
        action: "research",
    },
    {
        id: "expand",
        label: "Expand",
        description: "Expand and elaborate on the current text",
        icon: <Expand className="w-4 h-4 text-teal-400" />,
        action: "expand",
    },
    {
        id: "check-style",
        label: "Check Style",
        description: "Evaluate prose style",
        icon: <Sparkles className="w-4 h-4 text-indigo-400" />,
        action: "check-style",
    },
    {
        id: "translate",
        label: "Translate",
        description: "Translate selected text to another language",
        icon: <Globe className="w-4 h-4 text-emerald-400" />,
        action: "translate",
    },
];

export const SlashCommandList = forwardRef<SlashCommandListRef, SlashCommandListProps>(
    ({ items, command }, ref) => {
        const [selectedIndex, setSelectedIndex] = useState(0);

        useEffect(() => setSelectedIndex(0), [items]);

        const selectItem = (index: number) => {
            const item = items[index];
            if (item) command(item);
        };

        useImperativeHandle(ref, () => ({
            onKeyDown: ({ event }) => {
                if (event.key === "ArrowUp") {
                    setSelectedIndex((prev) =>
                        prev <= 0 ? items.length - 1 : prev - 1
                    );
                    return true;
                }
                if (event.key === "ArrowDown") {
                    setSelectedIndex((prev) =>
                        prev >= items.length - 1 ? 0 : prev + 1
                    );
                    return true;
                }
                if (event.key === "Enter") {
                    selectItem(selectedIndex);
                    return true;
                }
                return false;
            },
        }));

        if (!items.length) {
            return (
                <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-3 text-sm text-gray-500">
                    No commands match
                </div>
            );
        }

        return (
            <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden max-h-80 overflow-y-auto min-w-[260px]">
                {items.map((item, index) => (
                    <button
                        key={item.id}
                        onClick={() => selectItem(index)}
                        className={`w-full text-left px-3 py-2.5 flex items-center gap-3 text-sm transition-colors ${index === selectedIndex
                            ? "bg-indigo-600/30 text-white"
                            : "text-gray-300 hover:bg-gray-800"
                            }`}
                    >
                        {item.icon}
                        <div>
                            <div className="font-medium">{item.label}</div>
                            <div className="text-xs text-gray-500">{item.description}</div>
                        </div>
                    </button>
                ))}
            </div>
        );
    }
);

SlashCommandList.displayName = "SlashCommandList";
