import React, { useEffect, useState, useRef } from 'react';
import { api } from '@/lib/api';
import { useZenStore } from '@/lib/store/zenSlice';
import { Loader2, Clapperboard, Video, Image as ImageIcon, Camera } from 'lucide-react';

export interface LivePanelData {
    id?: string;
    panel_type?: string;
    camera_angle?: string;
    description?: string;
    action_notes?: string;
}

export function LiveStoryboardSidebar() {
    const { editorContent, activeSceneId, sidebarVisible } = useZenStore();
    const [livePanels, setLivePanels] = useState<LivePanelData[]>([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const debounceRef = useRef<NodeJS.Timeout | null>(null);
    const lastSketchTextRef = useRef<string>('');
    const panelsEndRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new panels arrive
    useEffect(() => {
        panelsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [livePanels, isGenerating]);

    // Debounced listener to trigger live sketch generation
    useEffect(() => {
        // Only trigger if sidebar is visible to save tokens
        if (!sidebarVisible) return;

        const cleanText = editorContent.trim();

        // Don't generate if text hasn't changed enough or is too short
        if (cleanText.length < 50 || cleanText === lastSketchTextRef.current) {
            return;
        }

        if (debounceRef.current) clearTimeout(debounceRef.current);

        debounceRef.current = setTimeout(async () => {
            setIsGenerating(true);
            try {
                // To keep it fast, we only send the last few paragraphs
                const recentProse = cleanText.split('\n\n').slice(-3).join('\n\n');
                const res = await api.liveSketch({
                    recent_prose: recentProse,
                    scene_id: activeSceneId || undefined
                });

                setLivePanels(prev => {
                    const next = [...prev, { ...res.panel, id: crypto.randomUUID() }];
                    // Keep only the last 5 panels to avoid clutter
                    return next.slice(-5);
                });
                lastSketchTextRef.current = cleanText;
            } catch (err) {
                console.error("Failed to generate live sketch:", err);
            } finally {
                setIsGenerating(false);
            }
        }, 5000); // 5 sec idle before requesting a sketch panel to save tokens

        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
        }
    }, [editorContent, activeSceneId, sidebarVisible]);

    if (!sidebarVisible) return null;

    return (
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 max-w-[300px] min-w-[300px] border-l border-gray-800 bg-gray-900/40">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                    <Clapperboard className="w-4 h-4 text-indigo-400" />
                    Live Margin Sketch
                </h3>
            </div>

            <p className="text-xs text-gray-500 leading-relaxed mb-2">
                As you write, the AI automatically visualizes the latest cinematic beats.
            </p>

            <div className="relative w-full flex flex-col gap-4 mt-2">
                {!isGenerating && livePanels.length === 0 && (
                    <div className="bg-gray-800/50 border border-gray-700/50 rounded-lg p-6 flex flex-col items-center justify-center gap-3 text-gray-500 text-center min-h-[160px] border-dashed">
                        <Video className="w-6 h-6 opacity-40" />
                        <span className="text-xs">Keep writing to generate storyboard sketches.</span>
                    </div>
                )}

                {livePanels.map((panel, idx) => (
                    <div key={panel.id || idx} className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden shadow-lg flex flex-col transition-all duration-300 opacity-90 hover:opacity-100">
                        {/* Mock Image Area - since we aren't generating real images yet to save time/cost */}
                        <div className="h-32 bg-gray-900 flex items-center justify-center border-b border-gray-700 relative overflow-hidden group">
                            <ImageIcon className="w-8 h-8 text-gray-700" />
                            <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-transparent to-transparent opacity-60 pointer-events-none" />
                            <span className="absolute bottom-2 left-2 text-[10px] font-mono text-gray-400 uppercase tracking-wider bg-black/60 px-1.5 py-0.5 rounded">
                                {panel.panel_type}
                            </span>
                        </div>

                        <div className="p-4 flex flex-col gap-3">
                            <div>
                                <h4 className="text-xs font-medium text-gray-300 flex items-center gap-1.5 mb-1">
                                    <Camera className="w-3 h-3 text-gray-500" />
                                    {panel.camera_angle} Shot
                                </h4>
                                <p className="text-xs text-gray-400 leading-relaxed">
                                    {panel.description}
                                </p>
                            </div>

                            {panel.action_notes && (
                                <div>
                                    <h4 className="text-[10px] uppercase font-semibold text-gray-500 mb-0.5">Action Notes</h4>
                                    <p className="text-[11px] text-indigo-300 italic align-left leading-relaxed">
                                        {panel.action_notes}
                                    </p>
                                </div>
                            )}

                            <div className="mt-2 pt-3 border-t border-gray-700/50 flex justify-between items-center text-[10px] text-gray-500">
                                <span>Ephemeral Sketch</span>

                                <button
                                    className="hover:text-indigo-400 transition-colors"
                                >
                                    Save to Storyboard
                                </button>
                            </div>
                        </div>
                    </div>
                ))}

                {isGenerating && (
                    <div className="bg-indigo-900/20 border border-indigo-500/30 rounded-lg p-6 flex flex-col items-center justify-center gap-3 text-indigo-400 min-h-[160px] animate-pulse transition-all duration-300">
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span className="text-xs font-medium">Visualizing next beat...</span>
                    </div>
                )}
                <div ref={panelsEndRef} />
            </div>
        </div>
    );
}
