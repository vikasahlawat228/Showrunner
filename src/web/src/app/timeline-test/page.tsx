"use client";

import React, { useState } from 'react';
import { TimelinePanel, type TimelineEvent } from '@/components/timeline/TimelinePanel';

const sampleEvents: TimelineEvent[] = [
    {
        id: 'evt_1',
        parent_event_id: null,
        branch_id: 'main',
        event_type: 'CREATE_WORLD',
        container_id: 'world_aethelgard',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
        payload: { name: 'Kingdom of Aethelgard' },
    },
    {
        id: 'evt_2',
        parent_event_id: 'evt_1',
        branch_id: 'main',
        event_type: 'CREATE_SCENE',
        container_id: 'scene_kings_court',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 23).toISOString(),
        payload: { name: "The King's Court" },
    },
    {
        id: 'evt_3',
        parent_event_id: 'evt_2',
        branch_id: 'main',
        event_type: 'CREATE_CHARACTER',
        container_id: 'char_lancelot',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 20).toISOString(),
        payload: { name: 'Sir Lancelot' },
    },
    {
        id: 'evt_4',
        parent_event_id: 'evt_3',
        branch_id: 'alt_ending_1',
        event_type: 'UPDATE_SCENE',
        container_id: 'scene_goblin_cave',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 18).toISOString(),
        payload: { name: 'Hero gets captured by goblins (Draft 1)' },
    },
    {
        id: 'evt_5',
        parent_event_id: 'evt_4',
        branch_id: 'alt_ending_1',
        event_type: 'UPDATE_SCENE',
        container_id: 'scene_goblin_cave',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 15).toISOString(),
        payload: { name: 'Hero escapes the goblin cave' },
    },
    {
        id: 'evt_6',
        parent_event_id: 'evt_3',
        branch_id: 'main',
        event_type: 'CREATE_SCENE',
        container_id: 'scene_dragon_fight',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 10).toISOString(),
        payload: { name: 'Hero fights the dragon instead' },
    },
    {
        id: 'evt_7',
        parent_event_id: 'evt_6',
        branch_id: 'main',
        event_type: 'UPDATE_SCENE',
        container_id: 'scene_dragon_fight',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
        payload: { name: 'Dragon is defeated, found treasure' },
    },
    {
        id: 'evt_8',
        parent_event_id: 'evt_7',
        branch_id: 'dark_path',
        event_type: 'UPDATE_CHARACTER',
        container_id: 'char_lancelot',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        payload: { name: 'Hero gets corrupted by the treasure' },
    },
    {
        id: 'evt_9',
        parent_event_id: 'evt_7',
        branch_id: 'main',
        event_type: 'UPDATE_SCENE',
        container_id: 'scene_kingdom_return',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 1).toISOString(),
        payload: { name: 'Hero returns to kingdom victorious' },
    }
];

export default function TimelineTestPage() {
    const [activeId, setActiveId] = useState<string>('evt_9');

    return (
        <div className="flex h-screen w-full bg-slate-100 p-8 justify-center items-center">
            <div className="w-[500px] h-[700px] bg-white rounded-xl shadow-xl overflow-hidden border border-slate-200">
                <TimelinePanel
                    events={sampleEvents}
                    onCheckout={(id) => {
                        console.log('Checking out:', id);
                        setActiveId(id);
                    }}
                    activeEventId={activeId}
                />
            </div>
        </div>
    );
}
