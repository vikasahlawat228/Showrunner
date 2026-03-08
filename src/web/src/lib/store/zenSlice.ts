import { create } from "zustand";
import { api } from "@/lib/api";
import { toast } from "sonner";

export interface ContextEntry { [key: string]: any; }
export interface ZenState {
    setFocusMode: (v: any) => void;
    isDetecting: boolean;
    isSaving: boolean;
    isSearching: boolean;
    activeBranch: string;
    setActiveBranch: (branch: string) => void;
    checkoutBranch: (branch?: string) => void;
    editorContent: string;
    setEditorContent: (content: string) => void;
    activeSceneId: string | null;
    activeChapterId: string | null;
    sidebarVisible: boolean;
    detectedEntities: any[];
    currentFragmentId: string | null;
    saveFragment: (content: string, summary?: string) => Promise<void>;
    showTranslation: boolean;
    translationSource: string;
    setShowTranslation: (show: boolean) => void;
    isFocusTyping: boolean;
    ghostTextContent: string;
    ghostTextConstraints: string;
    fetchGhostText: (text?: string, sceneId?: string) => Promise<void>;
    setGhostTextContent: (content: string) => void;
    setGhostTextConstraints: (constraints: string) => void;
    focusMode: boolean;
    setLastAIOperation: (operation: any) => void;
    ghostTextTemperament: string;
    setGhostTextTemperament: (temperament: string) => void;
    sessionWordsWritten: number;
    updateSessionWords: (count: number) => void;
    setSessionStartWordCount: (count: number) => void;
    sessionStartTime: number | null;
    startSession: () => void;
}

export type ExtendedZenState = ZenState & Record<string, any>;

export const useZenStore = create<ExtendedZenState>((set, get) => ({
    isDetecting: false,
    isSaving: false,
    isSearching: false,
    activeBranch: "main",
    setActiveBranch: (branch) => set({ activeBranch: branch }),
    checkoutBranch: () => { },
    editorContent: "",
    setEditorContent: (content) => set({ editorContent: content }),
    activeSceneId: null,
    activeChapterId: null,
    sidebarVisible: false,
    detectedEntities: [],
    currentFragmentId: null,
    saveFragment: async (content: string, summary?: string) => {
        set({ isSaving: true });
        try {
            const data = await api.saveFragment({
                text: content,
                title: summary,
                branch_id: get().activeBranch,
            });
            set({ currentFragmentId: data.id, detectedEntities: data.detected_entities });

            // Mark that user has written (for onboarding checklist)
            try { localStorage.setItem("showrunner:hasWritten", "true"); } catch { }

            toast("Scene saved", {
                description: "Run cascade update to sync related entities?",
                action: {
                    label: "Update",
                    onClick: async () => {
                        try {
                            const result = await api.cascadeUpdate({
                                file_path: data.id.endsWith(".yaml") ? data.id : `${data.id}.yaml`,
                                dry_run: false
                            });
                            toast.success(`Updated ${result.entities_updated} entities`);
                        } catch (err) {
                            toast.error("Cascade update failed");
                        }
                    },
                },
            });
        } catch (err) {
            console.error("Failed to save fragment:", err);
        } finally {
            set({ isSaving: false });
        }
    },
    showTranslation: false,
    translationSource: "",
    setShowTranslation: (show) => set({ showTranslation: show }),
    isFocusTyping: false,
    ghostTextContent: "",
    ghostTextConstraints: "",
    fetchGhostText: async () => {
        try {
            const res = await api.suggestGhostText({
                current_text: get().editorContent,
                constraints: get().ghostTextConstraints,
                temperament: get().ghostTextTemperament,
            });
            set({ ghostTextContent: res.suggestion });
        } catch (err) {
            console.error("Failed to fetch ghost text:", err);
        }
    },
    setGhostTextContent: (content) => set({ ghostTextContent: content }),
    setGhostTextConstraints: (constraints) => set({ ghostTextConstraints: constraints }),
    focusMode: false,
    setLastAIOperation: () => { },
    ghostTextTemperament: "Default",
    setGhostTextTemperament: (temperament) => set({ ghostTextTemperament: temperament }),
    // Session words — hydrate from localStorage
    sessionWordsWritten: (() => {
        try {
            return parseInt(localStorage.getItem("showrunner:sessionWords") || "0", 10);
        } catch { return 0; }
    })(),
    updateSessionWords: (count) => set((state) => {
        const newTotal = state.sessionWordsWritten + count;
        try { localStorage.setItem("showrunner:sessionWords", String(newTotal)); } catch { }
        return { sessionWordsWritten: newTotal };
    }),
    setSessionStartWordCount: () => { },
    sessionStartTime: (() => {
        try {
            const v = localStorage.getItem("showrunner:sessionStartTime");
            return v ? parseInt(v, 10) : null;
        } catch { return null; }
    })(),
    startSession: () => {
        const now = Date.now();
        const prev = get();
        // Persist previous session to history before resetting
        if (prev.sessionWordsWritten > 0) {
            try {
                const history = JSON.parse(localStorage.getItem("showrunner:wordHistory") || "[]");
                history.push({ date: new Date().toISOString(), words: prev.sessionWordsWritten });
                // Keep last 30 entries
                localStorage.setItem("showrunner:wordHistory", JSON.stringify(history.slice(-30)));
            } catch { }
        }
        try { localStorage.setItem("showrunner:sessionStartTime", String(now)); } catch { }
        try { localStorage.setItem("showrunner:sessionWords", "0"); } catch { }
        set({ sessionStartTime: now, sessionWordsWritten: 0 });
    },
    setFocusMode: (v: any) => set({ focusMode: !!v }),
}));

