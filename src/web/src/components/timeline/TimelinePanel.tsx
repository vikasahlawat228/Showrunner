"use client";

import React, { useMemo } from 'react';
import { GitBranch, Clock, CopyCheck, CircleDot } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export interface TimelineEvent {
    id: string;
    parent_event_id: string | null;
    branch_id: string;
    event_type: string;
    container_id: string;
    timestamp: string;
    payload: any;
}

export interface TimelinePanelProps {
    events: TimelineEvent[];
    onCheckout: (eventId: string) => void;
    activeEventId?: string | null;
}

const BRANCH_COLORS = [
    '#3b82f6', // blue-500
    '#10b981', // emerald-500
    '#a855f7', // purple-500
    '#ec4899', // pink-500
    '#f59e0b', // amber-500
    '#06b6d4', // cyan-500
    '#f43f5e', // rose-500
    '#6366f1', // indigo-500
];

const ROW_HEIGHT = 80;
const COL_WIDTH = 28;
const PADDING_X = 24;

export function TimelinePanel({ events, onCheckout, activeEventId }: TimelinePanelProps) {
    const { branchColumns, eventPositions, connections, totalColumns } = useMemo(() => {
        const columns: Record<string, number> = {};
        const positions: Record<string, { x: number; y: number; col: number; row: number }> = {};
        const conns: Array<{ x1: number; y1: number; x2: number; y2: number; color: string; branch: string }> = [];

        let nextCol = 0;

        // Assign consistent columns to branches based on first appearance
        events.forEach((evt) => {
            if (columns[evt.branch_id] === undefined) {
                columns[evt.branch_id] = nextCol++;
            }
        });

        // Calculate node coordinates
        events.forEach((evt, row) => {
            const col = columns[evt.branch_id];
            positions[evt.id] = {
                col,
                row,
                x: PADDING_X + col * COL_WIDTH,
                y: row * ROW_HEIGHT + ROW_HEIGHT / 2,
            };
        });

        // Calculate connections (lines from parent to child)
        events.forEach((evt) => {
            if (evt.parent_event_id && positions[evt.parent_event_id]) {
                const parentPos = positions[evt.parent_event_id];
                const childPos = positions[evt.id];

                const colorIndex = columns[evt.branch_id] % BRANCH_COLORS.length;

                conns.push({
                    x1: parentPos.x,
                    y1: parentPos.y,
                    x2: childPos.x,
                    y2: childPos.y,
                    color: BRANCH_COLORS[colorIndex],
                    branch: evt.branch_id,
                });
            }
        });

        return { branchColumns: columns, eventPositions: positions, connections: conns, totalColumns: nextCol };
    }, [events]);

    return (
        <div className="flex flex-col w-full h-full bg-slate-50/50 dark:bg-slate-900 overflow-y-auto overflow-x-hidden relative">
            {/* Header */}
            <div className="sticky top-0 z-30 flex items-center p-4 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
                <div className="flex items-center justify-center p-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 mr-3">
                    <GitBranch className="w-4 h-4 shrink-0" />
                </div>
                <div>
                    <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">Timeline & Branches</h2>
                    <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 leading-tight">Event sourcing log</p>
                </div>
            </div>

            <div className="relative p-2" style={{ height: events.length * ROW_HEIGHT + ROW_HEIGHT }}>
                {/* SVG Path Layer */}
                <svg
                    className="absolute inset-0 z-0 pointer-events-none"
                    width="100%"
                    height="100%"
                >
                    {connections.map((conn, idx) => {
                        // Curving math for branching using cubic bezier
                        let pathData = '';
                        if (conn.x1 === conn.x2) {
                            pathData = `M ${conn.x1} ${conn.y1} L ${conn.x2} ${conn.y2}`;
                        } else {
                            // Smooth curve switching columns
                            const midY = conn.y1 + (conn.y2 - conn.y1) / 2;
                            pathData = `M ${conn.x1} ${conn.y1} C ${conn.x1} ${midY}, ${conn.x2} ${midY}, ${conn.x2} ${conn.y2}`;
                        }

                        return (
                            <path
                                key={idx}
                                d={pathData}
                                fill="none"
                                stroke={conn.color}
                                strokeWidth="2.5"
                                className="opacity-60 dark:opacity-50 transition-all duration-300"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        );
                    })}
                </svg>

                {/* Nodes Layer */}
                <div className="relative z-10 w-full mt-2">
                    {events.map((evt, row) => {
                        const pos = eventPositions[evt.id];
                        const colIndex = branchColumns[evt.branch_id];
                        const strokeColor = BRANCH_COLORS[colIndex % BRANCH_COLORS.length];
                        const isActive = activeEventId === evt.id;

                        return (
                            <div
                                key={evt.id}
                                className="absolute flex items-center pr-2 group"
                                style={{
                                    height: ROW_HEIGHT,
                                    top: row * ROW_HEIGHT,
                                    width: '100%',
                                }}
                            >
                                {/* Visual Node mapped to absolute X */}
                                <div
                                    className={cn(
                                        "absolute w-[12px] h-[12px] rounded-full border-2 bg-white dark:bg-slate-900 shadow-sm transition-transform duration-200 cursor-pointer group-hover:scale-[1.3] z-20",
                                        isActive ? "ring-2 ring-offset-2 ring-slate-400 dark:ring-slate-500" : ""
                                    )}
                                    style={{
                                        left: pos.x - 6, // Center dot (-6 for half of 12px width)
                                        borderColor: strokeColor
                                    }}
                                    title={`Event: ${evt.id}`}
                                    onClick={() => onCheckout(evt.id)}
                                />

                                {/* Event Details Content Card */}
                                <div
                                    className={cn(
                                        "flex flex-1 items-center ml-auto h-[60px] mr-2 px-3 py-2 rounded-xl border transition-all duration-200 ease-in-out cursor-pointer",
                                        isActive
                                            ? "border-blue-200 bg-blue-50/50 shadow-sm dark:border-blue-900/50 dark:bg-blue-900/20"
                                            : "border-transparent hover:border-slate-200 hover:bg-white hover:shadow-sm dark:hover:border-slate-700/80 dark:hover:bg-slate-800/80"
                                    )}
                                    style={{
                                        marginLeft: totalColumns * COL_WIDTH + PADDING_X + 16,
                                    }}
                                    onClick={() => onCheckout(evt.id)}
                                >
                                    <div className="flex flex-col flex-1 min-w-0 pr-4">
                                        <div className="flex items-center gap-2 mb-1">
                                            <span
                                                className="text-[10px] uppercase tracking-wider font-bold px-1.5 py-0.5 rounded-md text-white flex items-center shadow-sm shadow-black/10"
                                                style={{ backgroundColor: strokeColor }}
                                            >
                                                {evt.branch_id}
                                            </span>
                                            <span className="text-[11px] font-medium text-slate-400 dark:text-slate-500 flex items-center">
                                                <Clock className="w-3 h-3 mr-1" />
                                                {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                        <p className="text-sm font-medium text-slate-700 dark:text-slate-200 pr-2 truncate" title={`${evt.event_type} → ${evt.container_id}`}>
                                            {evt.event_type}{evt.container_id ? ` → ${evt.container_id}` : ''}
                                        </p>
                                    </div>

                                    {/* Actions */}
                                    <div className={cn(
                                        "transition-opacity duration-200 flex-shrink-0",
                                        isActive ? "opacity-100" : "opacity-0 group-hover:opacity-100"
                                    )}>
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                onCheckout(evt.id);
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
                    })}
                </div>
            </div>
        </div>
    );
}
