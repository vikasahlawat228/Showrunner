"use client";

import React, { useState, useRef, useCallback, useEffect } from "react";
import { MentionAutocomplete } from "./MentionAutocomplete";
import { SlashCommandAutocomplete, SLASH_COMMANDS } from "./SlashCommandAutocomplete";

interface ChatInputProps {
    onSend: (content: string, mentionedEntityIds: string[]) => void;
    disabled?: boolean;
    isStreaming?: boolean;
    onAbort?: () => void;
}

export function ChatInput({ onSend, disabled, isStreaming, onAbort }: ChatInputProps) {
    const [content, setContent] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    const [autocompleteState, setAutocompleteState] = useState<{
        type: "mention" | "command" | null;
        query: string;
        startIndex: number;
        activeIndex: number;
    }>({ type: null, query: "", startIndex: -1, activeIndex: 0 });

    const handleSend = useCallback(() => {
        const trimmed = content.trim();
        if (!trimmed || disabled) return;

        // Extract @-mentioned entity IDs. 
        // Using `[\w-]+` to support ULID, dashes, etc.
        const mentions = Array.from(trimmed.matchAll(/@([\w-]+)/g)).map((m) => m[1]);

        onSend(trimmed, mentions);
        setContent("");
        setAutocompleteState({ type: null, query: "", startIndex: -1, activeIndex: 0 });

        // Reset textarea height
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
        }
    }, [content, disabled, onSend]);

    // Detect autocomplete triggers
    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        const val = e.target.value;
        setContent(val);

        const cursorPosition = e.target.selectionStart;
        if (cursorPosition === null) return;

        const textBeforeCursor = val.slice(0, cursorPosition);

        // Command Check: start of string or newline followed by /
        const commandMatch = textBeforeCursor.match(/(?:^|\n)\/(\w*)$/);
        if (commandMatch) {
            setAutocompleteState({
                type: "command",
                query: commandMatch[1],
                startIndex: textBeforeCursor.lastIndexOf("/") + 1,
                activeIndex: 0
            });
            return;
        }

        // Mention Check: space or start of string followed by @
        const mentionMatch = textBeforeCursor.match(/(?:^|\s)@([\w-]*)$/);
        if (mentionMatch) {
            setAutocompleteState({
                type: "mention",
                query: mentionMatch[1],
                startIndex: textBeforeCursor.lastIndexOf("@") + 1,
                activeIndex: 0
            });
            return;
        }

        setAutocompleteState((prev) => prev.type !== null ? { ...prev, type: null } : prev);
    };

    const handleSelectAutocomplete = (replacement: string, type: "mention" | "command") => {
        const prefix = content.slice(0, autocompleteState.startIndex - 1); // remove the @ or /
        const suffix = content.slice(textareaRef.current?.selectionStart || content.length);

        // For mentions, we inject `@ID ` (so the backend can extract the ID). 
        // For commands, we inject `/command `
        const inserted = type === "mention" ? `@${replacement} ` : `${replacement} `;

        const newContent = prefix + inserted + suffix;
        setContent(newContent);
        setAutocompleteState({ type: null, query: "", startIndex: -1, activeIndex: 0 });

        // Give focus back to textarea
        setTimeout(() => {
            if (textareaRef.current) {
                textareaRef.current.focus();
                const newPos = prefix.length + inserted.length;
                textareaRef.current.setSelectionRange(newPos, newPos);
            }
        }, 0);
    };

    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
            if (autocompleteState.type) {
                if (e.key === "ArrowDown") {
                    e.preventDefault();
                    setAutocompleteState(s => ({ ...s, activeIndex: s.activeIndex + 1 }));
                    return;
                }
                if (e.key === "ArrowUp") {
                    e.preventDefault();
                    setAutocompleteState(s => ({ ...s, activeIndex: Math.max(0, s.activeIndex - 1) }));
                    return;
                }
                if (e.key === "Enter" || e.key === "Tab") {
                    e.preventDefault();
                    // Just dispatch a custom event or let the autocomplete component handle it?
                    // Or we handle selection directly since we know the items if it's commands, but for mentions we don't have the results array here.
                    // Actually, for Enter/Tab to work, `MentionAutocomplete` needs to pass results back, or we let it listen.
                    // Instead, we can pass `activeIndex` and the Enter key can be handled securely if we just let the sub-components know.
                    // Workaround: We dispatch a custom event that subcomponents listen to.
                    const event = new CustomEvent("chat-autocomplete-select", { detail: autocompleteState.activeIndex });
                    document.dispatchEvent(event);
                    return;
                }
                if (e.key === "Escape") {
                    e.preventDefault();
                    setAutocompleteState({ type: null, query: "", startIndex: -1, activeIndex: 0 });
                    return;
                }
            }

            if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        },
        [handleSend, autocompleteState]
    );

    // Provide a way for SlashCommandAutocomplete to know how many items are there
    // For SlashCommand, handle its Enter directly here if easier:
    useEffect(() => {
        const handleSelect = (e: Event) => {
            const customEvent = e as CustomEvent;
            const index = customEvent.detail;

            if (autocompleteState.type === "command") {
                const q = autocompleteState.query.toLowerCase();
                const filtered = SLASH_COMMANDS.filter((c) => c.command.toLowerCase().includes(q));
                if (filtered[index]) {
                    handleSelectAutocomplete(filtered[index].command, "command");
                }
            }
        };
        document.addEventListener("chat-autocomplete-select", handleSelect);
        return () => document.removeEventListener("chat-autocomplete-select", handleSelect);
    }, [autocompleteState]);

    const handleInput = useCallback(() => {
        const ta = textareaRef.current;
        if (ta) {
            ta.style.height = "auto";
            ta.style.height = Math.min(ta.scrollHeight, 150) + "px";
        }
    }, []);

    return (
        <div className="relative border-t border-gray-700 p-3 bg-gray-900">
            {autocompleteState.type === "mention" && (
                <MentionAutocomplete
                    query={autocompleteState.query}
                    activeIndex={autocompleteState.activeIndex}
                    onSelect={(id, name) => handleSelectAutocomplete(id, "mention")}
                />
            )}

            {autocompleteState.type === "command" && (
                <SlashCommandAutocomplete
                    query={autocompleteState.query}
                    activeIndex={autocompleteState.activeIndex}
                    onSelect={(cmd) => handleSelectAutocomplete(cmd, "command")}
                />
            )}

            <div className="flex items-end gap-2">
                <textarea
                    ref={textareaRef}
                    value={content}
                    onChange={handleInputChange}
                    onKeyDown={handleKeyDown}
                    onInput={handleInput}
                    placeholder="Type a message... (Enter to send, Shift+Enter for newline)"
                    disabled={disabled || isStreaming}
                    rows={1}
                    className="flex-1 resize-none bg-gray-800 text-gray-100 rounded-lg px-3 py-2 text-sm
                               placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500
                               disabled:opacity-50"
                />
                {isStreaming ? (
                    <button
                        onClick={onAbort}
                        className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm
                                   transition-colors"
                    >
                        Stop
                    </button>
                ) : (
                    <button
                        onClick={handleSend}
                        disabled={disabled || !content.trim()}
                        className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700
                                   disabled:text-gray-500 text-white rounded-lg text-sm transition-colors"
                    >
                        Send
                    </button>
                )}
            </div>
        </div>
    );
}
