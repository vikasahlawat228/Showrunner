"use client";

import React from "react";
import { Sparkles, X } from "lucide-react";

interface WelcomeBackBannerProps {
    daysSince: number;
    summary: string;
    onDismiss: () => void;
    onCatchUp: () => void;
}

export function WelcomeBackBanner({
    daysSince,
    summary,
    onDismiss,
    onCatchUp,
}: WelcomeBackBannerProps) {
    return (
        <div
            className="relative mx-3 mt-3 rounded-lg border border-indigo-500/30 overflow-hidden animate-in slide-in-from-top-2 fade-in duration-500"
            style={{
                background:
                    "linear-gradient(135deg, rgba(79,70,229,0.15) 0%, rgba(147,51,234,0.15) 100%)",
            }}
        >
            {/* Dismiss button */}
            <button
                onClick={onDismiss}
                className="absolute top-2 right-2 p-1 rounded text-gray-500 hover:text-gray-300 transition-colors z-10"
                title="Dismiss"
            >
                <X className="w-3.5 h-3.5" />
            </button>

            <div className="p-4 pr-8">
                {/* Header */}
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-7 h-7 rounded-md bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow">
                        <Sparkles className="w-3.5 h-3.5 text-white" />
                    </div>
                    <div>
                        <p className="text-sm font-semibold text-gray-100">
                            Welcome back!
                        </p>
                        <p className="text-[11px] text-gray-400">
                            It&apos;s been{" "}
                            {daysSince === 1
                                ? "1 day"
                                : `${daysSince} days`}{" "}
                            since your last session
                        </p>
                    </div>
                </div>

                {/* Summary */}
                {summary && (
                    <p className="text-xs text-gray-300 leading-relaxed mb-3 line-clamp-3">
                        {summary}
                    </p>
                )}

                {/* CTA */}
                <button
                    onClick={onCatchUp}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/50 hover:text-indigo-200 transition-all duration-200"
                >
                    <Sparkles className="w-3 h-3" />
                    Catch me up
                </button>
            </div>
        </div>
    );
}
