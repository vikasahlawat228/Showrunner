"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useEditor, EditorContent, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Mention from "@tiptap/extension-mention";
import Placeholder from "@tiptap/extension-placeholder";
import { ReactRenderer } from "@tiptap/react";
import tippy, { type Instance as TippyInstance } from "tippy.js";
import { MentionList, type MentionItem, type MentionListRef } from "./MentionList";
import {
    SlashCommandList,
    SLASH_COMMANDS,
    type SlashCommand,
    type SlashCommandListRef,
} from "./SlashCommandList";
import { toast } from "sonner";
import { useZenStore } from "@/lib/store/zenSlice";
import { useStudioStore } from "@/lib/store";
import { api } from "@/lib/api";
import { type AIOperationContext } from "@/components/ui/ContextInspector";
import { Save, Clock, Loader2, Focus } from "lucide-react";

// ── Suggestion utilities ────────────────────────────────────

function createMentionSuggestion() {
    return {
        items: async ({ query }: { query: string }): Promise<MentionItem[]> => {
            if (!query || query.length < 1) return [];

            const q = query.toLowerCase();
            const { characters, scenes } = useStudioStore.getState();

            // Local synchronous search
            const results: MentionItem[] = [
                ...characters.map(c => ({ id: c.id, name: c.name, container_type: 'character' })),
                ...scenes.map(s => ({ id: s.id, name: s.title, container_type: 'scene' }))
            ].filter(item => item.name.toLowerCase().includes(q));

            // Return top 8 matches
            let finalResults = results.slice(0, 8);

            // If no exact match, add an option to create it inline
            const exactMatch = results.find(item => item.name.toLowerCase() === q);
            if (!exactMatch) {
                finalResults.push({
                    id: `create-${query}`,
                    name: `Create "${query}"...`,
                    container_type: 'action', // special type for creation
                });
            }

            return finalResults;
        },
        render: () => {
            let component: ReactRenderer<MentionListRef> | null = null;
            let popup: TippyInstance[] | null = null;

            return {
                onStart: (props: any) => {
                    component = new ReactRenderer(MentionList, {
                        props,
                        editor: props.editor,
                    });

                    if (!props.clientRect) return;

                    popup = tippy("body", {
                        getReferenceClientRect: props.clientRect,
                        appendTo: () => document.body,
                        content: component.element,
                        showOnCreate: true,
                        interactive: true,
                        trigger: "manual",
                        placement: "bottom-start",
                    });
                },
                onUpdate: (props: any) => {
                    component?.updateProps(props);
                    if (popup?.[0] && props.clientRect) {
                        popup[0].setProps({ getReferenceClientRect: props.clientRect });
                    }
                },
                onKeyDown: (props: any) => {
                    if (props.event.key === "Escape") {
                        popup?.[0]?.hide();
                        return true;
                    }
                    return component?.ref?.onKeyDown(props) ?? false;
                },
                onExit: () => {
                    popup?.[0]?.destroy();
                    component?.destroy();
                },
            };
        },
        command: ({ editor, range, props }: any) => {
            if (props.container_type === 'action' && props.id.startsWith('create-')) {
                // Delete the typed text that triggered this
                editor.chain().focus().deleteRange(range).run();

                // Extract the entity name from the ID
                const nameToCreate = props.id.replace('create-', '');

                // Dispatch event to open Quick Add modal
                // We default to character since it's the most common inline creation
                window.dispatchEvent(new CustomEvent('open:quick-add', {
                    detail: { type: 'character', predefinedName: nameToCreate }
                }));
                return;
            }

            // Normal insertion for existing items
            editor
                .chain()
                .focus()
                .insertContent([
                    {
                        type: "mention",
                        attrs: {
                            id: props.id,
                            label: props.name,
                            container_type: props.container_type,
                        },
                    },
                    {
                        type: "text",
                        text: " ",
                    },
                ])
                .run();
        },
    };
}

function createSlashSuggestion() {
    return {
        char: "/",
        items: ({ query }: { query: string }): SlashCommand[] => {
            const q = query.toLowerCase();
            return SLASH_COMMANDS.filter(
                (cmd) =>
                    cmd.label.toLowerCase().includes(q) ||
                    cmd.description.toLowerCase().includes(q)
            );
        },
        render: () => {
            let component: ReactRenderer<SlashCommandListRef> | null = null;
            let popup: TippyInstance[] | null = null;

            return {
                onStart: (props: any) => {
                    component = new ReactRenderer(SlashCommandList, {
                        props,
                        editor: props.editor,
                    });

                    if (!props.clientRect) return;

                    popup = tippy("body", {
                        getReferenceClientRect: props.clientRect,
                        appendTo: () => document.body,
                        content: component.element,
                        showOnCreate: true,
                        interactive: true,
                        trigger: "manual",
                        placement: "bottom-start",
                    });
                },
                onUpdate: (props: any) => {
                    component?.updateProps(props);
                    if (popup?.[0] && props.clientRect) {
                        popup[0].setProps({ getReferenceClientRect: props.clientRect });
                    }
                },
                onKeyDown: (props: any) => {
                    if (props.event.key === "Escape") {
                        popup?.[0]?.hide();
                        return true;
                    }
                    return component?.ref?.onKeyDown(props) ?? false;
                },
                onExit: () => {
                    popup?.[0]?.destroy();
                    component?.destroy();
                },
            };
        },
        command: ({ editor, range, props: cmd }: any) => {
            // Delete the slash command text
            editor.chain().focus().deleteRange(range).run();

            if (cmd.action === "translate") {
                const selection = editor.state.selection;
                // If it's just a cursor, textBetween might just be empty. Better to grab it like this:
                let text = "";
                if (!selection.empty) {
                    text = editor.state.doc.textBetween(selection.from, selection.to, "\n");
                }
                const store = useZenStore.getState();
                store.setTranslationSource(text || editor.getText() || "");
                store.setShowTranslation(true);
                return;
            }

            if (cmd.action === "check-style") {
                const selection = editor.state.selection;
                let text = "";
                if (!selection.empty) {
                    text = editor.state.doc.textBetween(selection.from, selection.to, "\n");
                }
                const textToAnalyze = text || editor.getText();
                const store = useZenStore.getState();
                store.setStyleCheckText(textToAnalyze);
                store.setActiveSidebarTab("style");
                if (!store.sidebarVisible) {
                    store.toggleSidebar();
                }
                return;
            }

            // Dispatch to backend agent
            const text = editor.getText();
            const intent = `${cmd.action}: ${text.slice(0, 500)}`;
            toast.info(`Running ${cmd.label}...`);

            api.directorDispatch(intent, { source: "zen", action: cmd.action })
                .then((result) => {
                    if (result.response) {
                        // Insert the agent's response at cursor
                        editor
                            .chain()
                            .focus()
                            .insertContent(`\n\n${result.response}`)
                            .run();
                        toast.success(`${cmd.label} complete`, {
                            description: `Agent: ${result.skill_used}`,
                        });

                        // Populate Glass Box with AI operation metadata
                        const glassBox: AIOperationContext = {
                            agentName: result.skill_used,
                            agentId: result.skill_used,
                            modelUsed: result.model_used || "default",
                            contextBuckets: result.context_used.map((key) => ({
                                id: key,
                                name: key,
                                type: "context",
                                summary: "",
                            })),
                        };
                        useZenStore.getState().setLastAIOperation(glassBox);
                    }
                })
                .catch((err) => {
                    toast.error(`${cmd.label} failed`, {
                        description: err instanceof Error ? err.message : String(err),
                    });
                });
        },
    };
}

// ── Editor Component ────────────────────────────────────────

export function ZenEditor() {
    const {
        saveFragment, detectEntities, isSaving, lastSavedAt, isDetecting,
        sessionWordsWritten, updateSessionWords, setSessionStartWordCount, sessionStartTime, startSession,
        focusMode, setFocusMode, setIsFocusTyping
    } = useZenStore();
    const [wordCount, setWordCount] = useState(0);
    const [charCount, setCharCount] = useState(0);
    const [showShortcuts, setShowShortcuts] = useState(false);

    const readingTime = Math.max(1, Math.ceil(wordCount / 250));
    const debounceRef = useRef<NodeJS.Timeout | null>(null);
    const detectDebounceRef = useRef<NodeJS.Timeout | null>(null);
    const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    // Mouse movement listener to break focus typing fade
    useEffect(() => {
        const handleMouseMove = () => {
            if (useZenStore.getState().isFocusTyping) {
                setIsFocusTyping(false);
            }
        };
        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, [setIsFocusTyping]);

    // Track session word count
    useEffect(() => {
        if (wordCount > 0 && !sessionStartTime) {
            startSession();
            setSessionStartWordCount(wordCount);
        }
    }, [wordCount, sessionStartTime, startSession, setSessionStartWordCount]);

    useEffect(() => {
        updateSessionWords(wordCount);
    }, [wordCount, updateSessionWords]);

    const editor = useEditor({
        immediatelyRender: false,
        extensions: [
            StarterKit.configure({
                heading: { levels: [1, 2, 3] },
            }),
            Placeholder.configure({
                placeholder:
                    "Start writing your story… Use @ to mention characters, locations, or scenes. Use / for AI commands.",
                emptyEditorClass: "is-editor-empty",
            }),
            Mention.configure({
                HTMLAttributes: {
                    class: "mention",
                },
                suggestion: createMentionSuggestion(),
            }),
            // Slash commands use Mention under the hood with "/" trigger
            Mention.extend({ name: "slashCommand" }).configure({
                HTMLAttributes: {
                    class: "slash-command",
                },
                suggestion: createSlashSuggestion(),
            }),
        ],
        editorProps: {
            attributes: {
                class:
                    "prose prose-invert prose-lg max-w-none focus:outline-none min-h-[60vh] px-2 py-4",
            },
        },
        onSelectionUpdate: ({ editor }) => {
            if (!focusMode) return;
            const editorEl = document.querySelector('.ProseMirror');
            editorEl?.querySelectorAll('.is-active').forEach(el => el.classList.remove('is-active'));
            const { $from } = editor.state.selection;
            const pos = $from.before(1);
            const dom = editor.view.nodeDOM(pos);
            if (dom instanceof HTMLElement) {
                dom.classList.add('is-active');
            }
        },
        onUpdate: ({ editor }) => {
            const text = editor.getText();
            const words = text.trim() ? text.trim().split(/\s+/).length : 0;
            setWordCount(words);
            setCharCount(text.length);

            // Sync content to store for Chat Context Injection (CUJ 14)
            useZenStore.getState().setEditorContent(text);

            // Debounced auto-save (3 seconds)
            if (debounceRef.current) clearTimeout(debounceRef.current);
            debounceRef.current = setTimeout(() => {
                if (text.trim().length > 10) {
                    saveFragment(text);
                }
            }, 3000);

            // Debounced entity detection (1.5 seconds) - Micro-context (current block)
            if (detectDebounceRef.current) clearTimeout(detectDebounceRef.current);
            detectDebounceRef.current = setTimeout(() => {
                const { $from } = editor.state.selection;
                const activeBlockText = $from.parent.textContent;
                if (activeBlockText.trim().length > 10) {
                    detectEntities(activeBlockText);
                }
            }, 1500);

            // Auto-fade focus mode typing detection
            if (useZenStore.getState().focusMode) {
                setIsFocusTyping(true);
                if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
                typingTimeoutRef.current = setTimeout(() => {
                    setIsFocusTyping(false);
                }, 2000);
            }
        },
    });

    // Clean up debounce timers
    useEffect(() => {
        return () => {
            if (debounceRef.current) clearTimeout(debounceRef.current);
            if (detectDebounceRef.current) clearTimeout(detectDebounceRef.current);
            if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
        };
    }, []);

    // Keyboard shortcut handlers
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === "s") {
                e.preventDefault();
                const text = editor?.getText() ?? "";
                if (text.trim().length > 5) {
                    saveFragment(text);
                }
                return;
            }
            if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'f') {
                e.preventDefault();
                setFocusMode(prev => !prev);
                return;
            }
            if ((e.metaKey || e.ctrlKey) && e.key === '/') {
                e.preventDefault();
                setShowShortcuts(prev => !prev);
                return;
            }
            if (e.key === "Escape" && showShortcuts) {
                setShowShortcuts(false);
                return;
            }
        };
        document.addEventListener("keydown", handleKeyDown);
        return () => document.removeEventListener("keydown", handleKeyDown);
    }, [editor, saveFragment, showShortcuts]);

    // Handle external translation replace/insert events
    useEffect(() => {
        const handleReplace = (e: CustomEvent<string>) => {
            if (editor) {
                editor.chain().focus().insertContent(e.detail).run();
            }
        };
        const handleInsertBelow = (e: CustomEvent<string>) => {
            if (editor) {
                const { to } = editor.state.selection;
                editor.chain().focus().insertContentAt(to, `\n\n${e.detail}`).run();
            }
        };
        window.addEventListener("zen:replace", handleReplace as any);
        window.addEventListener("zen:insertBelow", handleInsertBelow as any);
        return () => {
            window.removeEventListener("zen:replace", handleReplace as any);
            window.removeEventListener("zen:insertBelow", handleInsertBelow as any);
        };
    }, [editor]);

    return (
        <div className="flex flex-col flex-1 min-w-0 relative">
            {/* Toolbar */}
            {!focusMode && (
                <div className="flex items-center justify-between px-6 py-2 border-b border-gray-800/60 transition-all">
                    <div className="flex items-center gap-4">
                        <EditorToolbar editor={editor} />
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                        {isDetecting && (
                            <span className="flex items-center gap-1 text-indigo-400">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                Detecting…
                            </span>
                        )}
                        {isSaving && (
                            <span className="flex items-center gap-1 text-yellow-400">
                                <Loader2 className="w-3 h-3 animate-spin" />
                                Saving…
                            </span>
                        )}
                        {!isSaving && lastSavedAt && (
                            <span className="flex items-center gap-1">
                                <Clock className="w-3 h-3" />
                                Saved {formatTime(lastSavedAt)}
                            </span>
                        )}

                        <div className="flex items-center gap-2 text-[11px] text-gray-600 border-r border-gray-800 pr-3 mr-1">
                            {sessionWordsWritten > 0 && (
                                <span className="text-emerald-500/80 mr-1">
                                    +{sessionWordsWritten} this session
                                </span>
                            )}
                            <span className="text-gray-300">{wordCount.toLocaleString()} words</span>
                            <span>|</span>
                            <span>{charCount.toLocaleString()} chars</span>
                            <span>|</span>
                            <span>~{readingTime} min read</span>
                        </div>

                        <button
                            onClick={() => setFocusMode(!focusMode)}
                            className={`p-1 rounded transition-colors ${focusMode
                                ? 'bg-indigo-600/30 text-indigo-300'
                                : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800'
                                }`}
                            title="Focus mode (⌘⇧F)"
                        >
                            <Focus className="w-3.5 h-3.5" />
                        </button>

                        <button
                            onClick={() => {
                                const text = editor?.getText() ?? "";
                                if (text.trim()) saveFragment(text);
                            }}
                            className="flex items-center gap-1 px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"
                            title="Save (⌘S)"
                        >
                            <Save className="w-3 h-3" />
                            Save
                        </button>
                    </div>
                </div>
            )}

            {/* Floating Focus Status Bar */}
            {focusMode && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40
                    bg-gray-900/90 backdrop-blur-sm border border-gray-800 rounded-full
                    px-4 py-1.5 flex items-center gap-4 text-[11px] text-gray-500
                    opacity-0 hover:opacity-100 transition-opacity duration-300 shadow-xl">
                    {sessionWordsWritten > 0 && (
                        <span className="text-emerald-500/80">
                            +{sessionWordsWritten} this session
                        </span>
                    )}
                    <span className="text-gray-300">{wordCount.toLocaleString()} words</span>
                    <span>~{readingTime} min</span>
                    <button
                        onClick={() => setFocusMode(false)}
                        className="text-gray-400 hover:text-white transition-colors ml-1 font-medium"
                    >
                        Exit Focus (⌘⇧F)
                    </button>
                </div>
            )}

            {/* Editor surface */}
            <div className={`flex-1 overflow-y-auto px-6 lg:px-16 xl:px-24 2xl:px-32 ${focusMode ? 'zen-focus-mode pt-32' : ''}`}>
                <EditorContent editor={editor} />
            </div>

            {/* Shortcuts Overlay */}
            {showShortcuts && (
                <div
                    className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center transition-all"
                    onClick={() => setShowShortcuts(false)}
                >
                    <div
                        className="bg-gray-900 border border-gray-700 rounded-xl p-6 max-w-md w-full mx-4 shadow-2xl"
                        onClick={e => e.stopPropagation()}
                    >
                        <h3 className="text-sm font-semibold text-white mb-4">Keyboard Shortcuts</h3>
                        <div className="space-y-3">
                            {[
                                { keys: '⌘S', desc: 'Save fragment' },
                                { keys: '⌘⇧F', desc: 'Toggle focus mode' },
                                { keys: '⌘/', desc: 'Show shortcuts' },
                                { keys: '@', desc: 'Mention a character, location, or scene' },
                                { keys: '/', desc: 'Slash commands (AI actions)' },
                                { keys: '⌘B', desc: 'Bold' },
                                { keys: '⌘I', desc: 'Italic' },
                                { keys: '⌘⇧7', desc: 'Ordered list' },
                                { keys: '⌘⇧8', desc: 'Bullet list' },
                            ].map(({ keys, desc }) => (
                                <div key={keys} className="flex items-center justify-between">
                                    <span className="text-sm text-gray-400">{desc}</span>
                                    <kbd className="px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-xs text-gray-300 font-mono tracking-widest">
                                        {keys}
                                    </kbd>
                                </div>
                            ))}
                        </div>
                        <button
                            onClick={() => setShowShortcuts(false)}
                            className="mt-6 w-full py-2 text-xs text-gray-500 hover:text-gray-300 transition-colors bg-gray-800/50 rounded-lg hover:bg-gray-800"
                        >
                            Press Escape or ⌘/ to close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}

// ── Toolbar ─────────────────────────────────────────────────

function EditorToolbar({ editor }: { editor: Editor | null }) {
    if (!editor) return null;

    const btnClass = (active: boolean) =>
        `px-2 py-1 rounded text-xs font-medium transition-colors ${active
            ? "bg-indigo-600/30 text-indigo-300"
            : "text-gray-500 hover:text-gray-300 hover:bg-gray-800"
        }`;

    return (
        <>
            <button
                onClick={() => editor.chain().focus().toggleBold().run()}
                className={btnClass(editor.isActive("bold"))}
            >
                B
            </button>
            <button
                onClick={() => editor.chain().focus().toggleItalic().run()}
                className={btnClass(editor.isActive("italic"))}
            >
                I
            </button>
            <button
                onClick={() =>
                    editor.chain().focus().toggleHeading({ level: 2 }).run()
                }
                className={btnClass(editor.isActive("heading", { level: 2 }))}
            >
                H2
            </button>
            <button
                onClick={() =>
                    editor.chain().focus().toggleHeading({ level: 3 }).run()
                }
                className={btnClass(editor.isActive("heading", { level: 3 }))}
            >
                H3
            </button>
            <button
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                className={btnClass(editor.isActive("blockquote"))}
            >
                ❝
            </button>
            <button
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                className={btnClass(editor.isActive("bulletList"))}
            >
                •
            </button>
        </>
    );
}

// ── Helpers ─────────────────────────────────────────────────

function formatTime(date: Date): string {
    const now = new Date();
    const diff = Math.round((now.getTime() - date.getTime()) / 1000);
    if (diff < 5) return "just now";
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.round(diff / 60)}m ago`;
    return date.toLocaleTimeString();
}
