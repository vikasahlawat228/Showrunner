"use client";

import React, { memo } from "react";
import { useSortable } from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useStoryboardStore, type PanelData } from "@/lib/store/storyboardSlice";
import {
    ImageIcon,
    MessageCircle,
    Camera,
    GripVertical,
    Trash2,
    Sparkles,
} from "lucide-react";

const PANEL_TYPE_COLORS: Record<string, string> = {
    dialogue: "bg-blue-500/20 text-blue-300",
    action: "bg-red-500/20 text-red-300",
    establishing: "bg-emerald-500/20 text-emerald-300",
    closeup: "bg-purple-500/20 text-purple-300",
    transition: "bg-gray-500/20 text-gray-300",
    montage: "bg-amber-500/20 text-amber-300",
};

const CAMERA_ICONS: Record<string, string> = {
    wide: "🔭",
    medium: "📷",
    close: "🔬",
    extreme_close: "🎯",
    over_shoulder: "🤝",
    birds_eye: "🦅",
    low_angle: "⬆️",
    dutch: "↗️",
    pov: "👁️",
};

function PanelCardComponent({ panel }: { panel: PanelData }) {
    const { selectPanel, deletePanel } = useStoryboardStore();

    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: panel.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.5 : 1,
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            className={`group relative w-48 rounded-xl border border-gray-800 bg-gray-900/80 hover:border-gray-700 transition-all cursor-pointer shrink-0 ${isDragging ? "shadow-2xl ring-2 ring-indigo-400/40" : ""
                }`}
            onClick={() => selectPanel(panel.id)}
        >
            {/* Drag handle */}
            <div
                {...attributes}
                {...listeners}
                className="absolute top-1 left-1 p-0.5 rounded text-gray-600 hover:text-gray-400 cursor-grab active:cursor-grabbing z-10"
            >
                <GripVertical className="w-3 h-3" />
            </div>

            {/* Delete */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    deletePanel(panel.id, panel.scene_id);
                }}
                className="absolute top-1 right-1 p-0.5 rounded text-gray-700 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all z-10"
            >
                <Trash2 className="w-3 h-3" />
            </button>

            {/* Panel number */}
            <div className="absolute top-1 left-1/2 -translate-x-1/2 text-[9px] font-bold text-gray-600">
                #{panel.panel_number + 1}
            </div>

            {/* Image area */}
            <div className="h-28 rounded-t-xl bg-gray-950 flex items-center justify-center border-b border-gray-800/60 overflow-hidden">
                {panel.image_ref ? (
                    <img
                        src={panel.image_ref}
                        alt={panel.description}
                        className="w-full h-full object-cover"
                    />
                ) : (
                    <div className="flex flex-col items-center gap-1 text-gray-700">
                        <ImageIcon className="w-6 h-6" />
                        <span className="text-[9px]">No image</span>
                    </div>
                )}
            </div>

            {/* Content */}
            <div className="p-2 space-y-1.5">
                {/* Type + Camera badges */}
                <div className="flex items-center gap-1">
                    <span
                        className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${PANEL_TYPE_COLORS[panel.panel_type] ?? "bg-gray-600/20 text-gray-400"
                            }`}
                    >
                        {panel.panel_type}
                    </span>
                    <span className="text-xs" title={panel.camera_angle}>
                        {CAMERA_ICONS[panel.camera_angle] ?? "📷"}
                    </span>
                </div>

                {/* Description */}
                <p className="text-[10px] text-gray-400 leading-tight line-clamp-2">
                    {panel.description || "No description"}
                </p>

                {/* Dialogue indicator */}
                {panel.dialogue && (
                    <div className="flex items-center gap-1 text-[10px] text-blue-400">
                        <MessageCircle className="w-2.5 h-2.5" />
                        <span className="truncate">{panel.dialogue.slice(0, 30)}…</span>
                    </div>
                )}

                {/* Duration */}
                <div className="text-[9px] text-gray-600 text-right">
                    {panel.duration_seconds}s
                </div>
            </div>
        </div>
    );
}

export const PanelCard = memo(PanelCardComponent);
