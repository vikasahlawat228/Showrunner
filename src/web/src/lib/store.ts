import { create } from "zustand";
import {
  api,
  type ProjectInfo,
  type CharacterSummary,
  type SceneSummary,
  type SceneDetail,
  type WorkflowResponse,
  type DirectorResult,
  type CharacterDetail,
  type WorldSettings,
} from "./api";

// ── Selection ───────────────────────────────────────────────

export type SidebarTab = "characters" | "scenes" | "world";

export interface Selection {
  id: string;
  type: "character" | "scene" | "world";
  name: string;
}

// ── Store ───────────────────────────────────────────────────

export interface StudioState {
  // Data
  project: ProjectInfo | null;
  characters: CharacterSummary[];
  scenes: SceneSummary[];
  workflow: WorkflowResponse | null;
  world: WorldSettings | null;

  // UI
  loading: boolean;
  error: string | null;
  directorActing: boolean;
  lastDirectorResult: DirectorResult | null;

  // Sidebar
  sidebarCollapsed: boolean;
  sidebarTab: SidebarTab;

  // Chapter
  currentChapter: number;

  // Inspector
  selectedItem: Selection | null;
  inspectorData: CharacterDetail | SceneSummary | SceneDetail | WorldSettings | null;
  inspectorLoading: boolean;

  // Actions
  fetchProject: () => Promise<void>;
  fetchCharacters: () => Promise<void>;
  fetchScenes: (chapter: number) => Promise<void>;
  fetchWorkflow: () => Promise<void>;
  fetchWorld: () => Promise<void>;
  fetchAll: () => Promise<void>;
  directorAct: (stepOverride?: string) => Promise<DirectorResult>;
  clearError: () => void;

  // Sidebar actions
  toggleSidebar: () => void;
  setSidebarTab: (tab: SidebarTab) => void;

  // Chapter actions
  setChapter: (chapter: number) => Promise<void>;

  // Selection actions
  selectItem: (selection: Selection) => Promise<void>;
  clearSelection: () => void;

  // Drag-drop linking
  linkCharacterToScene: (characterId: string, sceneId: string) => Promise<void>;
  unlinkCharacterFromScene: (characterId: string, sceneId: string) => Promise<void>;
}

export const useStudioStore = create<StudioState>((set, get) => ({
  // Initial state
  project: null,
  characters: [],
  scenes: [],
  workflow: null,
  world: null,
  loading: true,
  error: null,
  directorActing: false,
  lastDirectorResult: null,
  sidebarCollapsed: false,
  sidebarTab: "characters",
  currentChapter: 1,
  selectedItem: null,
  inspectorData: null,
  inspectorLoading: false,

  fetchProject: async () => {
    try {
      const project = await api.getProject();
      set({ project });
    } catch (e) {
      set({ error: `Failed to load project: ${e instanceof Error ? e.message : e}` });
    }
  },

  fetchCharacters: async () => {
    try {
      const characters = await api.getCharacters();
      set({ characters });
    } catch (e) {
      set({ error: `Failed to load characters: ${e instanceof Error ? e.message : e}` });
    }
  },

  fetchScenes: async (chapter: number) => {
    try {
      const scenes = await api.getScenes(chapter);
      set({ scenes });
    } catch {
      set({ scenes: [] });
    }
  },

  fetchWorkflow: async () => {
    try {
      const workflow = await api.getWorkflow();
      set({ workflow });
    } catch (e) {
      set({ error: `Failed to load workflow: ${e instanceof Error ? e.message : e}` });
    }
  },

  fetchWorld: async () => {
    try {
      const world = await api.getWorld();
      set({ world });
    } catch {
      // World may not exist yet — not an error
      set({ world: null });
    }
  },

  fetchAll: async () => {
    set({ loading: true, error: null });
    try {
      const [project, characters, workflow] = await Promise.all([
        api.getProject(),
        api.getCharacters(),
        api.getWorkflow(),
      ]);
      set({ project, characters, workflow });

      // Fetch world (may not exist)
      try {
        const world = await api.getWorld();
        set({ world });
      } catch {
        set({ world: null });
      }

      // Fetch scenes for the current chapter
      const chapter = workflow.current_chapter ?? 1;
      set({ currentChapter: chapter });
      try {
        const scenes = await api.getScenes(chapter);
        set({ scenes });
      } catch {
        set({ scenes: [] });
      }
    } catch (e) {
      set({ error: `Failed to load studio data: ${e instanceof Error ? e.message : e}` });
    } finally {
      set({ loading: false });
    }
  },

  directorAct: async (stepOverride?: string) => {
    set({ directorActing: true, error: null });
    try {
      const result = await api.directorAct(
        stepOverride ? { step_override: stepOverride } : undefined
      );
      set({ lastDirectorResult: result });

      // Refresh all data after director acts
      const state = get();
      await state.fetchAll();

      return result;
    } catch (e) {
      const msg = `Director failed: ${e instanceof Error ? e.message : e}`;
      set({ error: msg });
      throw e;
    } finally {
      set({ directorActing: false });
    }
  },

  clearError: () => set({ error: null }),

  // Sidebar
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSidebarTab: (tab) => set({ sidebarTab: tab }),

  // Selection
  selectItem: async (selection: Selection) => {
    set({ selectedItem: selection, inspectorLoading: true, inspectorData: null });

    try {
      if (selection.type === "character") {
        const data = await api.getCharacter(selection.name);
        // Guard against race condition — user may have clicked something else
        if (get().selectedItem?.id === selection.id) {
          set({ inspectorData: data, inspectorLoading: false });
        }
      } else if (selection.type === "scene") {
        // Use the scene from the existing array (no detail endpoint yet)
        const scene = get().scenes.find((s) => s.id === selection.id);
        if (get().selectedItem?.id === selection.id) {
          set({ inspectorData: scene ?? null, inspectorLoading: false });
        }
      } else if (selection.type === "world") {
        const data = await api.getWorld();
        if (get().selectedItem?.id === selection.id) {
          set({ inspectorData: data, inspectorLoading: false });
        }
      }
    } catch (e) {
      if (get().selectedItem?.id === selection.id) {
        set({
          inspectorLoading: false,
          error: `Failed to load ${selection.type}: ${e instanceof Error ? e.message : e}`,
        });
      }
    }
  },

  clearSelection: () =>
    set({ selectedItem: null, inspectorData: null, inspectorLoading: false }),

  // Chapter navigation
  setChapter: async (chapter: number) => {
    set({ currentChapter: chapter });
    try {
      const scenes = await api.getScenes(chapter);
      set({ scenes });
    } catch {
      set({ scenes: [] });
    }
  },

  // Drag-drop linking
  linkCharacterToScene: async (characterId: string, sceneId: string) => {
    const { scenes, currentChapter } = get();
    const scene = scenes.find((s) => s.id === sceneId);
    if (!scene) return;

    // Duplicate guard
    if (scene.characters_present.includes(characterId)) return;

    const updated = [...scene.characters_present, characterId];
    try {
      await api.updateScene(currentChapter, scene.scene_number, {
        characters_present: updated,
      });
      // Refresh scenes to get updated data
      const freshScenes = await api.getScenes(currentChapter);
      set({ scenes: freshScenes });

      // If this scene is currently selected, refresh inspector
      const sel = get().selectedItem;
      if (sel?.id === sceneId) {
        const freshScene = freshScenes.find((s) => s.id === sceneId);
        if (freshScene) set({ inspectorData: freshScene });
      }
    } catch (e) {
      set({ error: `Failed to link character: ${e instanceof Error ? e.message : e}` });
    }
  },

  unlinkCharacterFromScene: async (characterId: string, sceneId: string) => {
    const { scenes, currentChapter } = get();
    const scene = scenes.find((s) => s.id === sceneId);
    if (!scene) return;

    const updated = scene.characters_present.filter((id) => id !== characterId);
    try {
      await api.updateScene(currentChapter, scene.scene_number, {
        characters_present: updated,
      });
      const freshScenes = await api.getScenes(currentChapter);
      set({ scenes: freshScenes });

      // Refresh inspector if this scene is selected
      const sel = get().selectedItem;
      if (sel?.id === sceneId) {
        const freshScene = freshScenes.find((s) => s.id === sceneId);
        if (freshScene) set({ inspectorData: freshScene });
      }
    } catch (e) {
      set({ error: `Failed to unlink character: ${e instanceof Error ? e.message : e}` });
    }
  },
}));
