"use client";

import React from "react";
import { ImageIcon } from "lucide-react";

/**
 * Placeholder storyboard strip for Phase C.
 * Shows panel thumbnails for the current scene once storyboard is built.
 */
export function StoryboardStrip() {
    return (
        <div className="border-t border-gray-800/60 bg-gray-950/50 px-6 py-2">
            <div className="flex items-center gap-3">
                <span className="text-[10px] uppercase font-semibold text-gray-600 tracking-wider">
                    Storyboard
                </span>
                <div className="flex items-center gap-2">
                    {[1, 2, 3].map((i) => (
                        <div
                            key={i}
                            className="w-12 h-16 rounded border border-dashed border-gray-700/50 flex items-center justify-center text-gray-700"
                        >
                            <ImageIcon className="w-4 h-4" />
                        </div>
                    ))}
                    <button className="w-12 h-16 rounded border border-dashed border-gray-700/50 flex items-center justify-center text-gray-700 hover:text-gray-500 hover:border-gray-600 transition-colors text-lg">
                        +
                    </button>
                </div>
                <span className="text-[10px] text-gray-700 ml-auto">
                    Panel generation coming in Phase C
                </span>
            </div>
        </div>
    );
}
