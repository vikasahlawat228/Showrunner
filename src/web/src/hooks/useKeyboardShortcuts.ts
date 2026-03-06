/**
 * useKeyboardShortcuts Hook
 *
 * Registers keyboard event listeners and dispatches shortcut actions.
 * Use with ShortcutsProvider for global shortcuts.
 */

import { useEffect, useCallback } from 'react';
import { useShortcuts } from '@/context/ShortcutsContext';
import { matchesShortcut, ShortcutAction } from '@/lib/keyboard-shortcuts';

export function useKeyboardShortcuts() {
  const { registerHandler, dispatchAction } = useShortcuts();

  // Register a handler for a specific shortcut
  const onShortcut = useCallback(
    (action: ShortcutAction, callback: () => void) => {
      registerHandler(action, callback);
    },
    [registerHandler]
  );

  // Set up global keyboard listener
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Don't trigger shortcuts if user is typing in an input
      const target = event.target as HTMLElement;
      const isInput =
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.contentEditable === 'true';

      // Allow some shortcuts in inputs (like Escape, Ctrl+S)
      const allowedInInput = [
        'close-modal',
        'save-current-file',
        'open-search',
      ] as ShortcutAction[];

      // Check all actions and dispatch if matched
      const actions: ShortcutAction[] = [
        'undo',
        'redo',
        'open-search',
        'open-quick-palette',
        'send-chat-message',
        'commit-story',
        'save-current-file',
        'open-pipeline',
        'focus-chat',
        'focus-editor',
        'new-session',
        'show-help',
        'toggle-sidebar',
        'close-modal',
        'next-panel',
        'prev-panel',
      ];

      for (const action of actions) {
        if (matchesShortcut(event, action)) {
          const allowInInput = allowedInInput.includes(action);

          if (!isInput || allowInInput) {
            event.preventDefault();
            dispatchAction(action);
          }
          break;
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [dispatchAction]);

  return { onShortcut };
}
