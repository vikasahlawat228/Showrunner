import React from "react";
import { Terminal, CheckSquare, Play, Minimize2 } from "lucide-react";

export interface SlashCommand {
    command: string;
    description: string;
    icon: React.ElementType;
}

export const SLASH_COMMANDS: SlashCommand[] = [
    { command: "/plan", description: "Propose a multi-step plan for a goal", icon: CheckSquare },
    { command: "/approve", description: "Approve specific steps (e.g., /approve 1,2 or all)", icon: CheckSquare },
    { command: "/execute", description: "Run all approved steps sequentially", icon: Play },
    { command: "/compact", description: "Compact session history to save tokens", icon: Minimize2 },
];

interface SlashCommandAutocompleteProps {
    query: string;
    onSelect: (command: string) => void;
    activeIndex: number;
}

export function SlashCommandAutocomplete({ query, onSelect, activeIndex }: SlashCommandAutocompleteProps) {
    const q = query.toLowerCase();
    const filtered = SLASH_COMMANDS.filter((c) => c.command.toLowerCase().includes(q));

    if (filtered.length === 0) return null;

    return (
        <div className="absolute bottom-full left-0 mb-2 w-72 bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50">
            <div className="px-3 py-2 border-b border-gray-800 text-xs font-semibold text-gray-400">
                Commands
            </div>
            <ul className="max-h-64 overflow-y-auto python">
                {filtered.map((cmd, idx) => {
                    const Icon = cmd.icon;
                    return (
                        <li
                            key={cmd.command}
                            onClick={() => onSelect(cmd.command)}
                            className={`px-3 py-2 cursor-pointer flex items-center gap-3 ${idx === activeIndex ? "bg-indigo-600/20 text-indigo-300" : "hover:bg-gray-800 text-gray-200"
                                }`}
                        >
                            <Icon className="w-4 h-4 text-emerald-400" />
                            <div>
                                <div className="text-sm font-medium">{cmd.command}</div>
                                <div className="text-xs text-gray-500">{cmd.description}</div>
                            </div>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}
