"use client";

import { useEffect, useState } from "react";
import { api, CharacterRibbonResponse } from "@/lib/api";
import { Loader2, Users } from "lucide-react";

// Generate a consistent color from string
const stringToColor = (str: string) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    const hue = Math.abs(hash) % 360;
    return `hsl(${hue}, 70%, 60%)`;
};

export function StoryRibbonsVisualization() {
    const [ribbons, setRibbons] = useState<CharacterRibbonResponse[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        async function fetchRibbons() {
            try {
                const data = await api.getCharacterRibbons();
                setRibbons(data);
            } catch (err) {
                console.error("Failed to load ribbons:", err);
            } finally {
                setIsLoading(false);
            }
        }
        fetchRibbons();
    }, []);

    if (isLoading) {
        return (
            <div className="w-full h-[300px] bg-gray-900/50 rounded-xl border border-gray-800/50 flex flex-col items-center justify-center mt-8">
                <Loader2 className="w-6 h-6 animate-spin text-gray-500 mb-2" />
                <span className="text-xs text-gray-500">Loading character ribbons...</span>
            </div>
        );
    }

    if (ribbons.length === 0) {
        return (
            <div className="w-full h-[300px] bg-gray-900/50 rounded-xl border border-gray-800/50 flex flex-col items-center justify-center p-6 text-center mt-8">
                <Users className="w-8 h-8 text-gray-600 mb-3" />
                <p className="text-gray-400 text-sm max-w-sm">No character presence data available. Link characters to scenes to see their arcs unfold over time.</p>
            </div>
        );
    }

    // Extract all unique characters across all scenes
    const allCharactersMap = new Map<string, { id: string, name: string }>();
    ribbons.forEach(scene => {
        scene.characters.forEach((char: any) => {
            if (!allCharactersMap.has(char.character_id)) {
                allCharactersMap.set(char.character_id, { id: char.character_id, name: char.character_name });
            }
        });
    });

    const characters = Array.from(allCharactersMap.values());

    // Sort characters by total prominence (roughly sorting main characters to top)
    const charScores = new Map<string, number>();
    ribbons.forEach(scene => {
        scene.characters.forEach((char: any) => {
            charScores.set(char.character_id, (charScores.get(char.character_id) || 0) + char.prominence);
        });
    });
    characters.sort((a, b) => (charScores.get(b.id) || 0) - (charScores.get(a.id) || 0));

    return (
        <div className="w-full bg-slate-900/40 dark:bg-slate-900/40 rounded-xl border border-slate-200 dark:border-slate-800/50 p-6 overflow-hidden flex flex-col mt-8 shadow-sm">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-slate-800 dark:text-slate-200 font-medium flex items-center gap-2">
                    <Users className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
                    Story Character Ribbons
                </h3>
                <span className="text-[10px] uppercase tracking-wider text-slate-500">Presence Heatmap</span>
            </div>

            <div className="flex-1 overflow-x-auto pb-4 custom-scrollbar">
                <div className="min-w-max flex">
                    {/* Character Labels Y-Axis */}
                    <div className="flex flex-col gap-[6px] pr-6 border-r border-slate-200 dark:border-slate-800 sticky left-0 bg-slate-50 dark:bg-slate-900/40 backdrop-blur-sm z-10 pt-6">
                        {characters.map(char => (
                            <div key={char.id} className="h-6 flex items-center justify-end text-xs font-medium text-slate-600 dark:text-slate-400 w-32 truncate" title={char.name}>
                                {char.name}
                            </div>
                        ))}
                    </div>

                    {/* Timeline Matrix */}
                    <div className="flex flex-col pt-6 pl-4">
                        {/* Scenes X-Axis */}
                        <div className="flex gap-1 mb-[6px]">
                            {ribbons.map((scene, i) => (
                                <div key={scene.scene_id} className="w-8 flex justify-center group relative">
                                    <div className="text-[10px] text-slate-400 dark:text-slate-500 group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors cursor-default">
                                        {i + 1}
                                    </div>
                                    <div className="absolute opacity-0 group-hover:opacity-100 bottom-full mb-1 left-1/2 -translate-x-1/2 whitespace-nowrap bg-slate-800 text-slate-200 text-[10px] px-2 py-1 rounded shadow-lg select-none pointer-events-none z-20">
                                        Scene {scene.chapter}.{scene.scene_number}: {scene.scene_name}
                                    </div>
                                    {/* Vertical guide line on hover */}
                                    <div className="absolute top-4 bottom-[-1000px] w-px bg-slate-200 dark:bg-slate-800 opacity-0 group-hover:opacity-100 pointer-events-none -z-10" />
                                </div>
                            ))}
                        </div>

                        {/* Ribbons */}
                        <div className="flex flex-col gap-[6px]">
                            {characters.map(char => {
                                const color = stringToColor(char.name);
                                return (
                                    <div key={char.id} className="flex gap-1 h-6 items-center">
                                        {ribbons.map((scene, sceneIdx) => {
                                            const presence = scene.characters.find((c: any) => c.character_id === char.id);
                                            const hasPresence = !!presence;

                                            const prevPresence = sceneIdx > 0 ? ribbons[sceneIdx - 1].characters.find((c: any) => c.character_id === char.id) : null;
                                            const nextPresence = sceneIdx < ribbons.length - 1 ? ribbons[sceneIdx + 1].characters.find((c: any) => c.character_id === char.id) : null;

                                            const isStart = hasPresence && !prevPresence;
                                            const isEnd = hasPresence && !nextPresence;
                                            const roundedClass = isStart && isEnd ? 'rounded-full' : isStart ? 'rounded-l-full' : isEnd ? 'rounded-r-full' : '';

                                            return (
                                                <div key={scene.scene_id} className="w-8 h-5 flex items-center justify-center group relative">
                                                    {hasPresence ? (
                                                        <div
                                                            className={`h-full w-full ${roundedClass} transition-all duration-300 hover:brightness-125 hover:shadow-[0_0_10px_rgba(255,255,255,0.2)]`}
                                                            style={{
                                                                backgroundColor: color,
                                                                opacity: presence.prominence === 1.0 ? 1 : 0.4,
                                                                transform: presence.prominence === 1.0 ? 'scaleY(1)' : 'scaleY(0.6)'
                                                            }}
                                                        />
                                                    ) : (
                                                        <div className="w-full h-px bg-slate-200 dark:bg-slate-800/40" />
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
