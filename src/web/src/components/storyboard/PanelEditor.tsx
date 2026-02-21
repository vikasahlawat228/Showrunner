"use client";

import React from "react";
import { useStoryboardStore, type PanelData } from "@/lib/store/storyboardSlice";
import {
    X,
    ImageIcon,
    Sparkles,
    Camera,
    MessageCircle,
    Clock,
    Users,
} from "lucide-react";

const PANEL_TYPES = ["dialogue", "action", "establishing", "closeup", "transition", "montage"];
const CAMERA_ANGLES = ["wide", "medium", "close", "extreme_close", "over_shoulder", "birds_eye", "low_angle", "dutch", "pov"];

export function PanelEditor() {
    const { panelsByScene, selectedPanelId, selectPanel, updatePanel } =
        useStoryboardStore();

    const panel = selectedPanelId
        ? Object.values(panelsByScene).flat().find((p) => p.id === selectedPanelId)
        : null;

    if (!panel) {
        return (
            <div className="p-6 text-center text-gray-600 text-sm mt-12">
                <Camera className="w-8 h-8 mx-auto mb-3 opacity-30" />
                <p>Select a panel to edit details</p>
            </div>
        );
    }

    const handleUpdate = (key: string, value: any) => {
        updatePanel(panel.id, { [key]: value } as Partial<PanelData>);
    };

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between shrink-0">
                <h3 className="text-sm font-semibold text-gray-300">
                    Panel #{panel.panel_number + 1}
                </h3>
                <button
                    onClick={() => selectPanel(null)}
                    className="p-1 rounded text-gray-500 hover:text-gray-300"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-4">
                {/* Image preview */}
                <div className="rounded-lg bg-gray-950 border border-gray-800 h-40 flex items-center justify-center overflow-hidden">
                    {panel.image_ref ? (
                        <img
                            src={panel.image_ref}
                            alt={panel.description}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="flex flex-col items-center gap-1.5 text-gray-700">
                            <ImageIcon className="w-8 h-8" />
                            <button className="flex items-center gap-1 text-[10px] text-indigo-400 hover:text-indigo-300">
                                <Sparkles className="w-3 h-3" />
                                Generate Image
                            </button>
                        </div>
                    )}
                </div>

                {/* Panel Type */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Panel Type
                    </label>
                    <select
                        value={panel.panel_type}
                        onChange={(e) => handleUpdate("panel_type", e.target.value)}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    >
                        {PANEL_TYPES.map((t) => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>

                {/* Camera Angle */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Camera Angle
                    </label>
                    <select
                        value={panel.camera_angle}
                        onChange={(e) => handleUpdate("camera_angle", e.target.value)}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    >
                        {CAMERA_ANGLES.map((a) => (
                            <option key={a} value={a}>{a.replace(/_/g, " ")}</option>
                        ))}
                    </select>
                </div>

                {/* Description */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Visual Description
                    </label>
                    <textarea
                        value={panel.description}
                        onChange={(e) => handleUpdate("description", e.target.value)}
                        rows={3}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-xs text-white focus:border-indigo-500 focus:outline-none resize-none"
                        placeholder="Describe what we see in this panel..."
                    />
                </div>

                {/* Dialogue */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1 flex items-center gap-1">
                        <MessageCircle className="w-3 h-3" />
                        Dialogue
                    </label>
                    <textarea
                        value={panel.dialogue}
                        onChange={(e) => handleUpdate("dialogue", e.target.value)}
                        rows={2}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-xs text-white focus:border-indigo-500 focus:outline-none resize-none"
                        placeholder="Character dialogue..."
                    />
                </div>

                {/* Action Notes */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                        Action Notes
                    </label>
                    <textarea
                        value={panel.action_notes}
                        onChange={(e) => handleUpdate("action_notes", e.target.value)}
                        rows={2}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-xs text-white focus:border-indigo-500 focus:outline-none resize-none"
                        placeholder="Stage directions..."
                    />
                </div>

                {/* Duration */}
                <div>
                    <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        Duration (seconds)
                    </label>
                    <input
                        type="number"
                        value={panel.duration_seconds}
                        onChange={(e) => handleUpdate("duration_seconds", parseFloat(e.target.value) || 3)}
                        min={0.5}
                        max={30}
                        step={0.5}
                        className="w-full px-3 py-1.5 rounded-md bg-gray-900 border border-gray-700 text-sm text-white focus:border-indigo-500 focus:outline-none"
                    />
                </div>

                {/* Image Prompt Preview */}
                {panel.image_prompt && (
                    <div>
                        <label className="block text-[10px] uppercase font-bold text-gray-600 mb-1">
                            Image Prompt
                        </label>
                        <div className="text-[10px] text-gray-500 bg-gray-900 border border-gray-800 rounded-md px-3 py-2 leading-relaxed">
                            {panel.image_prompt}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
