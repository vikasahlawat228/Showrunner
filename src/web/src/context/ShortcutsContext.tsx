/**
 * ShortcutsContext
 *
 * Global context for managing keyboard shortcuts.
 * Allows components to register handlers for shortcut actions.
 */

'use client';

import React, { createContext, useContext, useCallback, useState } from 'react';
import { ShortcutAction } from '@/lib/keyboard-shortcuts';

interface ShortcutsContextType {
  registerHandler: (action: ShortcutAction, callback: () => void) => void;
  unregisterHandler: (action: ShortcutAction) => void;
  dispatchAction: (action: ShortcutAction) => void;
}

const ShortcutsContext = createContext<ShortcutsContextType | undefined>(undefined);

export function ShortcutsProvider({ children }: { children: React.ReactNode }) {
  const [handlers, setHandlers] = useState<Record<ShortcutAction, (() => void)[]>>({} as any);

  const registerHandler = useCallback((action: ShortcutAction, callback: () => void) => {
    setHandlers(prev => {
      const existing = prev[action] || [];
      // Use Set to avoid duplicate handlers
      const newHandlers = [...existing];
      if (!newHandlers.includes(callback)) {
        newHandlers.push(callback);
      }
      return { ...prev, [action]: newHandlers };
    });
  }, []);

  const unregisterHandler = useCallback((action: ShortcutAction) => {
    setHandlers(prev => {
      const copy = { ...prev };
      delete copy[action];
      return copy;
    });
  }, []);

  const dispatchAction = useCallback((action: ShortcutAction) => {
    const callbacks = handlers[action] || [];
    // Call all registered handlers (most recent first for LIFO)
    for (let i = callbacks.length - 1; i >= 0; i--) {
      callbacks[i]();
    }
  }, [handlers]);

  return (
    <ShortcutsContext.Provider value={{ registerHandler, unregisterHandler, dispatchAction }}>
      {children}
    </ShortcutsContext.Provider>
  );
}

export function useShortcuts(): ShortcutsContextType {
  const context = useContext(ShortcutsContext);
  if (!context) {
    throw new Error('useShortcuts must be used within ShortcutsProvider');
  }
  return context;
}
