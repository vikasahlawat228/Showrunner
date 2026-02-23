import { mergeAttributes, Node } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import React from "react";
import { ChevronLeft, ChevronRight, CopyPlus, Sparkles, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { useZenStore } from "@/lib/store/zenSlice";
import { toast } from "sonner";

export interface AltTakeOptions {
    HTMLAttributes: Record<string, any>;
}

declare module "@tiptap/core" {
    interface Commands<ReturnType> {
        altTake: {
            insertAltTake: (options?: { initialText?: string }) => ReturnType;
        };
    }
}

const AltTakeComponent = (props: NodeViewProps) => {
    const { takes, activeIndex } = props.node.attrs;

    const currentText = takes[activeIndex] || "";

    const updateTakes = (newTakes: string[], newIndex: number) => {
        // We use updateAttributes to save the data in the prosemirror document.
        props.updateAttributes({
            takes: newTakes,
            activeIndex: newIndex,
        });
    };

    const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const newTakes = [...takes];
        newTakes[activeIndex] = e.target.value;
        updateTakes(newTakes, activeIndex);
    };

    const nextTake = () => {
        if (activeIndex < takes.length - 1) {
            updateTakes(takes, activeIndex + 1);
        }
    };

    const prevTake = () => {
        if (activeIndex > 0) {
            updateTakes(takes, activeIndex - 1);
        }
    };

    const [isGenerating, setIsGenerating] = React.useState(false);

    const addNewTake = () => {
        const newTakes = [...takes, ""]; // Empty new take
        updateTakes(newTakes, newTakes.length - 1);
    };

    const handleAIAction = async () => {
        const fragmentId = useZenStore.getState().currentFragmentId;
        if (!fragmentId) {
            toast.error("No active fragment found to generate take.");
            return;
        }

        const prompt = window.prompt("Shift the tone or rewrite this take:", "More dramatic");
        if (!prompt) return;

        setIsGenerating(true);
        try {
            const result = await api.createAltTake({
                fragment_id: fragmentId,
                highlighted_text: currentText || "...",
                prompt: prompt,
            });

            if (result.alt_text) {
                const newTakes = [...takes, result.alt_text];
                updateTakes(newTakes, newTakes.length - 1);
                toast.success("AI variation generated!");
            }
        } catch (err: any) {
            toast.error(err.message || "Failed to generate AI variation");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <NodeViewWrapper className="block my-4">
            <div className="group relative border border-dashed border-slate-600/50 hover:border-indigo-500/50 bg-slate-800/20 rounded-lg p-3 transition-colors">

                {/* Floating Toolbar */}
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 flex items-center gap-2 px-3 py-1 bg-slate-800 border border-slate-700 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 text-xs text-slate-300">
                    <button
                        onClick={prevTake}
                        disabled={activeIndex === 0}
                        className="p-1 hover:text-white disabled:opacity-30 disabled:hover:text-slate-300"
                    >
                        <ChevronLeft className="w-3.5 h-3.5" />
                    </button>

                    <span className="font-mono px-1">
                        Take {activeIndex + 1} / {takes.length}
                    </span>

                    <button
                        onClick={nextTake}
                        disabled={activeIndex === takes.length - 1}
                        className="p-1 hover:text-white disabled:opacity-30 disabled:hover:text-slate-300"
                    >
                        <ChevronRight className="w-3.5 h-3.5" />
                    </button>

                    <div className="w-px h-3 bg-slate-600 mx-1 border-r border-slate-600" />

                    <button
                        onClick={addNewTake}
                        className="p-1 text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                        title="Add Empty Take"
                    >
                        <CopyPlus className="w-3.5 h-3.5" />
                    </button>

                    <button
                        onClick={handleAIAction}
                        disabled={isGenerating}
                        className="p-1 text-amber-400 hover:text-amber-300 flex items-center gap-1 border-l border-slate-700 pl-2 ml-1"
                        title="Generate AI Variation"
                    >
                        {isGenerating ? (
                            <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                            <Sparkles className="w-3.5 h-3.5" />
                        )}
                    </button>
                </div>

                {/* Editor Content */}
                <textarea
                    value={currentText}
                    onChange={handleTextChange}
                    placeholder="Write an alternative take here..."
                    className="w-full min-h-[60px] bg-transparent resize-none outline-none text-gray-200 placeholder-gray-600 focus:ring-0 leading-relaxed"
                />
            </div>
        </NodeViewWrapper>
    );
};

export const AltTakeExtension = Node.create<AltTakeOptions>({
    name: "altTake",
    group: "block",
    atom: true, // we handle editing wholly inside React component

    addAttributes() {
        return {
            takes: {
                default: [""],
                parseHTML: element => {
                    const data = element.getAttribute('data-takes');
                    return data ? JSON.parse(data) : [""];
                },
                renderHTML: attributes => {
                    return {
                        'data-takes': JSON.stringify(attributes.takes),
                    };
                }
            },
            activeIndex: {
                default: 0,
            },
        };
    },

    parseHTML() {
        return [
            {
                tag: 'div[data-type="alt-take"]',
            },
        ];
    },

    renderHTML({ HTMLAttributes }) {
        return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'alt-take' })];
    },

    addNodeView() {
        return ReactNodeViewRenderer(AltTakeComponent);
    },

    addCommands() {
        return {
            insertAltTake:
                (options) =>
                    ({ commands }) => {
                        return commands.insertContent({
                            type: this.name,
                            attrs: {
                                takes: [options?.initialText || "", ""],
                                activeIndex: 1 // Jump to the new empty take out of the box
                            },
                        });
                    },
        };
    },
});
