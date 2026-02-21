import React, { useState } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Trash2, Loader2, AlertTriangle } from "lucide-react";

export interface IdeaCardNodeData {
    text: string;
    color?: string;
    tags?: string[];
    syncState?: "syncing" | "error" | "synced";
    onDelete?: (id: string) => void;
    onRetry?: (id: string) => void;
    onChange?: (id: string, text: string) => void;
    [key: string]: unknown;
}

const PRESET_COLORS = [
    "#4F46E5", // Indigo
    "#10B981", // Emerald
    "#F59E0B", // Amber
    "#EF4444", // Red
    "#8B5CF6", // Violet
    "#EC4899", // Pink
];

export function IdeaCardNode({ id, data, selected }: NodeProps) {
    const nodeData = data as unknown as IdeaCardNodeData;
    const [isEditing, setIsEditing] = useState(false);
    const [text, setText] = useState(nodeData.text);

    const borderColor = nodeData.color || PRESET_COLORS[0];

    const handleDoubleClick = () => {
        setIsEditing(true);
    };

    const handleBlur = () => {
        setIsEditing(false);
        if (text !== nodeData.text && nodeData.onChange) {
            nodeData.onChange(id, text);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleBlur();
        }
    };

    return (
        <div
            className={`relative min-w-[200px] max-w-[250px] bg-gray-800 rounded-lg shadow-xl cursor-grab active:cursor-grabbing group ${selected ? "ring-2 ring-blue-500 ring-offset-2 ring-offset-gray-950" : ""
                }`}
            style={{ borderLeft: `4px solid ${borderColor}` }}
            onDoubleClick={handleDoubleClick}
        >
            <Handle
                type="target"
                position={Position.Left}
                className="w-2 h-2 !bg-gray-500 border-none"
            />

            <div className="p-3">
                {/* Delete button (shows on hover) */}
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        if (nodeData.onDelete) nodeData.onDelete(id);
                    }}
                    className="absolute top-2 right-2 p-1 text-gray-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity bg-gray-800 rounded-md"
                    title="Delete Idea"
                >
                    <Trash2 className="w-3.5 h-3.5" />
                </button>

                {/* Sync State Indicator */}
                {nodeData.syncState === "syncing" && (
                    <div className="absolute bottom-2 right-2 text-indigo-400" title="Syncing changes...">
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    </div>
                )}
                {nodeData.syncState === "error" && (
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            if (nodeData.onRetry) nodeData.onRetry(id);
                        }}
                        className="absolute bottom-2 right-2 text-red-400 hover:text-red-300 transition-colors"
                        title="Failed to sync. Click to retry."
                    >
                        <AlertTriangle className="w-3.5 h-3.5" />
                    </button>
                )}

                {/* Content */}
                {isEditing ? (
                    <textarea
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onBlur={handleBlur}
                        onKeyDown={handleKeyDown}
                        autoFocus
                        className="w-full min-h-[60px] max-h-[150px] bg-gray-900 text-gray-200 text-sm rounded border border-gray-600 p-2 focus:outline-none focus:border-blue-500 resize-none nodrag"
                        placeholder="Enter your idea..."
                        rows={3}
                    />
                ) : (
                    <div className="text-sm text-gray-200 min-h-[40px] break-words whitespace-pre-wrap leading-relaxed pr-6 line-clamp-3 group-hover:line-clamp-none">
                        {nodeData.text || "Empty idea card..."}
                    </div>
                )}

                {/* Tags */}
                {nodeData.tags && nodeData.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-3">
                        {nodeData.tags.map((tag) => (
                            <span
                                key={tag}
                                className="px-1.5 py-0.5 text-[10px] font-medium bg-gray-700 text-gray-300 rounded"
                            >
                                #{tag}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            <Handle
                type="source"
                position={Position.Right}
                className="w-2 h-2 !bg-gray-500 border-none"
            />
        </div>
    );
}

export default IdeaCardNode;
