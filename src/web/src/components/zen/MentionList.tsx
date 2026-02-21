"use client";

import React, {
    forwardRef,
    useEffect,
    useImperativeHandle,
    useState,
} from "react";

export interface MentionItem {
    id: string;
    name: string;
    container_type: string;
    similarity?: number;
}

export interface MentionListRef {
    onKeyDown: (props: { event: KeyboardEvent }) => boolean;
}

interface MentionListProps {
    items: MentionItem[];
    command: (item: MentionItem) => void;
}

const TYPE_COLORS: Record<string, string> = {
    character: "bg-violet-500/20 text-violet-300",
    scene: "bg-blue-500/20 text-blue-300",
    location: "bg-emerald-500/20 text-emerald-300",
    world: "bg-amber-500/20 text-amber-300",
    fragment: "bg-gray-500/20 text-gray-300",
};

export const MentionList = forwardRef<MentionListRef, MentionListProps>(
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
                    No results
                </div>
            );
        }

        return (
            <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden max-h-64 overflow-y-auto min-w-[200px]">
                {items.map((item, index) => (
                    <button
                        key={item.id}
                        onClick={() => selectItem(index)}
                        className={`w-full text-left px-3 py-2 flex items-center gap-2 text-sm transition-colors ${index === selectedIndex
                            ? "bg-indigo-600/30 text-white"
                            : "text-gray-300 hover:bg-gray-800"
                            }`}
                    >
                        <span
                            className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded ${TYPE_COLORS[item.container_type] ?? "bg-gray-600/20 text-gray-400"
                                }`}
                        >
                            {item.container_type}
                        </span>
                        <span className="truncate flex-1">{item.name}</span>
                        {item.similarity !== undefined && (
                            <span
                                className={`w-1.5 h-1.5 rounded-full shrink-0 ${item.similarity > 0.8 ? "bg-green-400" :
                                        item.similarity > 0.5 ? "bg-amber-400" : "bg-gray-500"
                                    }`}
                                title={`Relevance: ${(item.similarity * 100).toFixed(0)}%`}
                            />
                        )}
                    </button>
                ))}
            </div>
        );
    }
);

MentionList.displayName = "MentionList";
