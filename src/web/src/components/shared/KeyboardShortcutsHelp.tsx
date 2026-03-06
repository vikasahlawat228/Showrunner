// @ts-nocheck
/**
 * Keyboard Shortcuts Help Component
 *
 * Displays all available keyboard shortcuts in a formatted modal/dialog.
 */

'use client';

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { SHORTCUTS, getShortcutsByCategory, formatShortcut } from '@/lib/keyboard-shortcuts';

interface KeyboardShortcutsHelpProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function KeyboardShortcutsHelp({
  open = false,
  onOpenChange,
}: KeyboardShortcutsHelpProps) {
  const [isOpen, setIsOpen] = useState(open);
  const isMac = typeof window !== 'undefined' && navigator.platform.includes('Mac');

  const handleOpenChange = (newOpen: boolean) => {
    setIsOpen(newOpen);
    onOpenChange?.(newOpen);
  };

  const categories = getShortcutsByCategory();

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Press <kbd className="px-2 py-1 bg-gray-100 rounded text-xs">?</kbd> anytime to show this help
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {Object.entries(categories).map(([category, shortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
                {category}
              </h3>
              <div className="grid grid-cols-1 gap-2">
                {shortcuts.map(shortcut => (
                  <div
                    key={shortcut.action}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50"
                  >
                    <span className="text-sm text-gray-700">
                      {shortcut.description}
                    </span>
                    <kbd className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 border border-gray-200 rounded text-xs font-mono">
                      {formatShortcut(shortcut.action, isMac)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="pt-4 border-t text-xs text-gray-500">
          <p>
            {isMac ? 'Cmd' : 'Ctrl'}-based shortcuts work system-wide. Other shortcuts work within the application.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
