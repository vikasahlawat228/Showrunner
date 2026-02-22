import { mergeAttributes, Node } from "@tiptap/core";
import { ReactNodeViewRenderer, NodeViewWrapper, type NodeViewProps } from "@tiptap/react";
import React from "react";
import { Check, X } from "lucide-react";
import * as diff from "diff";

export interface DiffOptions {
    HTMLAttributes: Record<string, any>;
}

declare module "@tiptap/core" {
    interface Commands<ReturnType> {
        diffNode: {
            insertDiffNode: (options: { originalText: string; newText: string }) => ReturnType;
        };
    }
}

const DiffComponent = (props: NodeViewProps) => {
    const { originalText, newText } = props.node.attrs;

    const changes = React.useMemo(() => {
        return diff.diffWordsWithSpace(originalText || "", newText || "");
    }, [originalText, newText]);

    const acceptDiff = () => {
        const pos = typeof props.getPos === 'function' ? props.getPos() : props.getPos;
        if (typeof pos !== 'number') return;

        // Replace this entire node with just the new text
        props.editor.chain().focus().insertContentAt(
            { from: pos, to: pos + props.node.nodeSize },
            newText
        ).run();
    };

    const rejectDiff = () => {
        const pos = typeof props.getPos === 'function' ? props.getPos() : props.getPos;
        if (typeof pos !== 'number') return;

        // Replace this entire node with the old text (reverting)
        props.editor.chain().focus().insertContentAt(
            { from: pos, to: pos + props.node.nodeSize },
            originalText
        ).run();
    };

    return (
        <NodeViewWrapper className="block my-4">
            <div className="relative group border border-indigo-500/30 bg-indigo-950/20 rounded-lg p-3 font-mono text-sm leading-relaxed shadow-sm transition-all hover:bg-indigo-950/30">
                <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                        onClick={acceptDiff}
                        className="p-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/40 rounded shadow-sm flex items-center gap-1"
                        title="Accept Fix"
                    >
                        <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                        onClick={rejectDiff}
                        className="p-1.5 bg-rose-500/20 text-rose-400 hover:bg-rose-500/40 rounded shadow-sm"
                        title="Reject Fix"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>

                <div className="pr-16 break-words whitespace-pre-wrap">
                    {changes.map((part, index) => {
                        if (part.added) {
                            return (
                                <span key={index} className="bg-emerald-500/20 text-emerald-300 rounded-sm px-0.5">
                                    {part.value}
                                </span>
                            );
                        }
                        if (part.removed) {
                            return (
                                <span key={index} className="bg-rose-500/20 text-rose-300 line-through opacity-70 rounded-sm px-0.5 mr-1">
                                    {part.value}
                                </span>
                            );
                        }
                        return <span key={index} className="text-gray-300">{part.value}</span>;
                    })}
                </div>
            </div>
        </NodeViewWrapper>
    );
};

export const DiffExtension = Node.create<DiffOptions>({
    name: "diffNode",
    group: "block",
    atom: true, // Treated as a single uneditable atomic node by the editor

    addAttributes() {
        return {
            originalText: {
                default: "",
            },
            newText: {
                default: "",
            },
        };
    },

    parseHTML() {
        return [
            {
                tag: 'div[data-type="diff-node"]',
            },
        ];
    },

    renderHTML({ HTMLAttributes }) {
        return ['div', mergeAttributes(HTMLAttributes, { 'data-type': 'diff-node' })];
    },

    addNodeView() {
        return ReactNodeViewRenderer(DiffComponent);
    },

    addCommands() {
        return {
            insertDiffNode:
                (options) =>
                    ({ commands }) => {
                        return commands.insertContent({
                            type: this.name,
                            attrs: options,
                        });
                    },
        };
    },
});
