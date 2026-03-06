/**
 * useAutoSave Hook
 *
 * Automatically saves content after user stops typing.
 * Debounces to avoid excessive API calls.
 */

import { useEffect, useRef, useCallback, useState } from 'react';

interface UseAutoSaveOptions {
  debounceMs?: number;
  onSave: (content: string) => Promise<void>;
  enabled?: boolean;
}

interface UseAutoSaveReturn {
  isSaving: boolean;
  lastSaved: Date | null;
  saveNow: () => Promise<void>;
}

export function useAutoSave({
  debounceMs = 1000,
  onSave,
  enabled = true,
}: UseAutoSaveOptions): UseAutoSaveReturn {
  const [content, setContent] = useState<string>('');
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();
  const lastSavedContentRef = useRef<string>('');

  // Save function
  const saveNow = useCallback(async () => {
    if (!enabled || !content || content === lastSavedContentRef.current) {
      return;
    }

    try {
      setIsSaving(true);
      await onSave(content);
      lastSavedContentRef.current = content;
      setLastSaved(new Date());
    } finally {
      setIsSaving(false);
    }
  }, [content, enabled, onSave]);

  // Set up debounced auto-save
  useEffect(() => {
    if (!enabled) return;

    // Clear existing timer
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // Set new timer
    timeoutRef.current = setTimeout(() => {
      saveNow();
    }, debounceMs);

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [content, debounceMs, enabled, saveNow]);

  return {
    isSaving,
    lastSaved,
    saveNow,
  };
}

/**
 * Hook to track content changes
 */
export function useContentTracking(initialContent: string = '') {
  const [content, setContent] = useState(initialContent);
  const [isDirty, setIsDirty] = useState(false);
  const initialContentRef = useRef(initialContent);

  const handleChange = useCallback((newContent: string) => {
    setContent(newContent);
    setIsDirty(newContent !== initialContentRef.current);
  }, []);

  const markClean = useCallback(() => {
    initialContentRef.current = content;
    setIsDirty(false);
  }, [content]);

  return {
    content,
    setContent: handleChange,
    isDirty,
    markClean,
  };
}
