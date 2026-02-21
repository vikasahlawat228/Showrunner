"use client";

import React, { useEffect, useState } from "react";
import {
    Pencil,
    Film,
    Workflow,
    GitBranch,
    Circle,
    Clock,
    CopyCheck,
    CircleDot,
} from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { TimelineEvent } from "./TimelinePanel";

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

/* ── Event-type icon + colour mapping ─────────────────────── */

interface EventStyle {
    icon: React.ReactNode;
    bgColor: string;   // icon badge bg
    textColor: string;  // icon badge text
}

function getEventStyle(eventType: string): EventStyle {
    if (eventType.includes("fragment_saved")) {
        return {
            icon: <Pencil className="w-3.5 h-3.5" />,
            bgColor: "bg-amber-100 dark:bg-amber-900/40",
            textColor: "text-amber-600 dark:text-amber-400",
        };
    }
    if (eventType.includes("panel_created") || eventType.includes("panel_reordered")) {
        return {
            icon: <Film className="w-3.5 h-3.5" />,
            bgColor: "bg-purple-100 dark:bg-purple-900/40",
            textColor: "text-purple-600 dark:text-purple-400",
        };
    }
    if (eventType.includes("pipeline_def_created")) {
        return {
            icon: <Workflow className="w-3.5 h-3.5" />,
            bgColor: "bg-cyan-100 dark:bg-cyan-900/40",
            textColor: "text-cyan-600 dark:text-cyan-400",
        };
    }
    if (eventType.includes("checkout_branch")) {
        return {
            icon: <GitBranch className="w-3.5 h-3.5" />,
            bgColor: "bg-emerald-100 dark:bg-emerald-900/40",
            textColor: "text-emerald-600 dark:text-emerald-400",
        };
    }
    return {
        icon: <Circle className="w-3.5 h-3.5" />,
        bgColor: "bg-slate-100 dark:bg-slate-800",
        textColor: "text-slate-500 dark:text-slate-400",
    };
}

/* ── Props ────────────────────────────────────────────────── */

export interface TimelineEventNodeProps {
    event: TimelineEvent;
    isActive: boolean;
    isNew: boolean;
    strokeColor: string;
    nodeX: number;       // absolute X of the dot
    rowHeight: number;
    row: number;
    totalColumnsWidth: number; // left margin for the card
    paddingX: number;
    onCheckout: (eventId: string) => void;
}

/* ── Component ────────────────────────────────────────────── */

export function TimelineEventNode({
    event,
    isActive,
    isNew,
    strokeColor,
    nodeX,
    rowHeight,
    row,
    totalColumnsWidth,
    paddingX,
    onCheckout,
}: TimelineEventNodeProps) {
    const style = getEventStyle(event.event_type);

    // Auto-remove the "new" pulse after ~3 seconds so it doesn't re-trigger on re-render.
    const [showPulse, setShowPulse] = useState(isNew);
    useEffect(() => {
        if (!isNew) {
            setShowPulse(false);
            return;
        }
        setShowPulse(true);
        const timer = setTimeout(() => setShowPulse(false), 3000);
        return () => clearTimeout(timer);
    }, [isNew]);

    return (
        <div
            className="absolute flex items-center pr-2 group"
            style={{
                height: rowHeight,
                top: row * rowHeight,
                width: "100%",
            }}
        >
            {/* Visual Node dot */}
            <div
                className={cn(
                    "absolute w-[12px] h-[12px] rounded-full border-2 bg-white dark:bg-slate-900 shadow-sm transition-transform duration-200 cursor-pointer group-hover:scale-[1.3] z-20",
                    isActive
                        ? "ring-2 ring-offset-2 ring-slate-400 dark:ring-slate-500"
                        : "",
                    showPulse ? "animate-pulse-new" : ""
                )}
                style={{
                    left: nodeX - 6,
                    borderColor: strokeColor,
                }}
                title={`Event: ${event.id}`}
                onClick={() => onCheckout(event.id)}
            />

            {/* Event Details Card */}
            <div
                className={cn(
                    "flex flex-1 items-center ml-auto h-[60px] mr-2 px-3 py-2 rounded-xl border transition-all duration-200 ease-in-out cursor-pointer",
                    isActive
                        ? "border-blue-200 bg-blue-50/50 shadow-sm dark:border-blue-900/50 dark:bg-blue-900/20"
                        : "border-transparent hover:border-slate-200 hover:bg-white hover:shadow-sm dark:hover:border-slate-700/80 dark:hover:bg-slate-800/80",
                    showPulse ? "animate-pulse-new" : ""
                )}
                style={{
                    marginLeft: totalColumnsWidth + paddingX + 16,
                }}
                onClick={() => onCheckout(event.id)}
            >
                {/* Event-type icon badge */}
                <div
                    className={cn(
                        "flex items-center justify-center w-7 h-7 rounded-lg mr-2.5 flex-shrink-0",
                        style.bgColor,
                        style.textColor
                    )}
                >
                    {style.icon}
                </div>

                <div className="flex flex-col flex-1 min-w-0 pr-4">
                    <div className="flex items-center gap-2 mb-1">
                        <span
                            className="text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded-md text-white flex items-center shadow-sm shadow-black/10"
                            style={{ backgroundColor: strokeColor }}
                        >
                            {event.branch_id}
                        </span>
                        <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500 flex items-center">
                            <Clock className="w-3 h-3 mr-1" />
                            {new Date(event.timestamp).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                            })}
                        </span>
                    </div>
                    <p
                        className="text-sm font-medium text-slate-700 dark:text-slate-200 pr-2 truncate"
                        title={`${event.event_type} → ${event.container_id}`}
                    >
                        {event.event_type}
                        {event.container_id ? ` → ${event.container_id}` : ""}
                    </p>
                </div>

                {/* Checkout / Active button */}
                <div
                    className={cn(
                        "transition-opacity duration-200 flex-shrink-0",
                        isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                    )}
                >
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            onCheckout(event.id);
                        }}
                        className={cn(
                            "flex items-center text-xs font-semibold px-3 py-1.5 rounded-lg shadow-sm transition-colors",
                            isActive
                                ? "bg-slate-800 text-white dark:bg-slate-100 dark:text-slate-900"
                                : "bg-white text-slate-600 border border-slate-200 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700 dark:hover:bg-slate-700 hover:border-slate-300"
                        )}
                    >
                        {isActive ? (
                            <>
                                <CopyCheck className="w-3.5 h-3.5 mr-1.5" /> Active
                            </>
                        ) : (
                            <>
                                <CircleDot className="w-3.5 h-3.5 mr-1.5" /> Checkout
                            </>
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}
