import { mergeAttributes, Node } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import React from "react";
import { ChevronLeft, ChevronRight, CopyPlus } from "lucide-react";

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

    const addNewTake = () => {
        const newTakes = [...takes, ""]; // Empty new take
        updateTakes(newTakes, newTakes.length - 1);
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
