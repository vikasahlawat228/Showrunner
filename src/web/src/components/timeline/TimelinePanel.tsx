"use client";

import React, { useMemo } from 'react';
import { GitBranch } from 'lucide-react';
import { TimelineEventNode } from './TimelineEventNode';

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
    onZoom?: (eventId: string) => void;
    activeEventId?: string | null;
    newEventIds?: Set<string>;
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

export function TimelinePanel({ events, onCheckout, onZoom, activeEventId, newEventIds }: TimelinePanelProps) {
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
                    <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">Timeline &amp; Branches</h2>
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

                {/* Nodes Layer — now using TimelineEventNode */}
                <div className="relative z-10 w-full mt-2">
                    {events.map((evt) => {
                        const pos = eventPositions[evt.id];
                        const colIndex = branchColumns[evt.branch_id];
                        const strokeColor = BRANCH_COLORS[colIndex % BRANCH_COLORS.length];
                        const isActive = activeEventId === evt.id;
                        const isNew = newEventIds?.has(evt.id) ?? false;

                        return (
                            <TimelineEventNode
                                key={evt.id}
                                event={evt}
                                isActive={isActive}
                                isNew={isNew}
                                strokeColor={strokeColor}
                                nodeX={pos.x}
                                rowHeight={ROW_HEIGHT}
                                row={pos.row}
                                totalColumnsWidth={totalColumns * COL_WIDTH}
                                paddingX={PADDING_X}
                                onCheckout={onCheckout}
                                onZoom={onZoom}
                            />
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
