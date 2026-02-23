import { Extension } from '@tiptap/core';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';

export interface GhostTextOptions {
    /**
     * Current ghost text to display.
     */
    suggestion: string;
}

export const GhostTextPluginKey = new PluginKey('ghostText');

export const GhostTextExtension = Extension.create<GhostTextOptions>({
    name: 'ghostText',

    addOptions() {
        return {
            suggestion: '',
        };
    },

    addProseMirrorPlugins() {
        const { editor } = this;

        return [
            new Plugin({
                key: GhostTextPluginKey,
                state: {
                    init: () => DecorationSet.empty,
                    apply: (tr, oldState) => {
                        // Get the current suggestion from the extension options
                        const suggestion = this.options.suggestion;

                        if (!suggestion) {
                            return DecorationSet.empty;
                        }

                        // Map old decorations through the transaction so they shift correctly if text before them changes
                        // Here we re-calculate the decoration position to always be at the end of the selection

                        // Only show decoration if the selection is empty (a cursor) and at the end of a line, or similar logic.
                        // For simplicity, we just put it at the current cursor position.
                        const { selection } = tr;
                        if (!selection.empty) {
                            return DecorationSet.empty;
                        }

                        const position = selection.from;

                        const widget = document.createElement('span');
                        widget.classList.add('ghost-text');
                        widget.textContent = suggestion;
                        // Unselectable ghost styling is handled in index.css

                        const deco = Decoration.widget(position, widget, {
                            side: 1, // Insert after the cursor
                        });

                        return DecorationSet.create(tr.doc, [deco]);
                    },
                },
                props: {
                    decorations(state) {
                        return this.getState(state);
                    },
                    handleKeyDown(view, event) {
                        const suggestion = this.spec.options?.suggestion;

                        // If there's a suggestion and the user presses Tab, accept it
                        if (suggestion && event.key === 'Tab') {
                            event.preventDefault();
                            event.stopPropagation();

                            // Get the current extension reference to clear it via options
                            const pluginState = this.getState(view.state);

                            // Clear the suggestion state first (handled upstream usually by the component, 
                            // but we can dispatch an event or rely on editor state)

                            // Insert the text
                            view.dispatch(view.state.tr.insertText(suggestion));

                            // Dispatch a custom event so ZenEditor can clear the suggestion
                            window.dispatchEvent(new CustomEvent('zen:clearGhostText'));
                            return true;
                        }

                        // On any other key press (typing), we clear the suggestion
                        if (suggestion && event.key.length === 1) { // Normal typing character
                            window.dispatchEvent(new CustomEvent('zen:clearGhostText'));
                        }

                        return false;
                    },
                },
            }),
        ];
    },

    onUpdate() {
        // Whenever the editor updates, if we change the options, we might need to force a plugin re-eval.
        // ProseMirror handles this largely if we dispatch an empty transaction.
        this.editor.view.dispatch(this.editor.view.state.tr.setMeta('ghostText', true));
    }
});
