import { create } from "zustand";
import { api } from "@/lib/api";
// ── Dummy Slices ─────────────────────────────────────────

export interface ChatArtifact {
  artifact_type: string;
  title: string;
  content: string;
  is_saved?: boolean;
  container_id?: string;
}

export interface ChatActionTrace {
  id?: string;
  parent_id?: string | null;
  tool_name: string;
  duration_ms: number;
  context_summary?: string;
  containers_used?: string[];
  result_preview?: string;
  prompt?: string;
  raw_json?: string;
}

export interface ChatMessage {
  role: string;
  content: string;
  created_at: string | number;
  action_traces: ChatActionTrace[];
  artifacts: ChatArtifact[];
}

export interface ChatSessionSummary {
  id: string;
  name?: string;
  state: string;
  message_count: number;
  updated_at: string | number;
  last_message_preview?: string;
  tags: string[];
  token_usage: number;
  context_budget: number;
}

export interface ChatSlice {
  chatSessions: any[];
  activeSessionId: string | null;
  chatMessages: any[];
  isStreaming: boolean;
  streamingContent: string;
  streamingTraces: any[];
  streamingArtifacts: any[];
  chatError: string | null;
  pendingApproval: any | null;
  backgroundStatus: string | null;
  fetchChatSessions: () => void;
  createChatSession: () => Promise<string>;
  setActiveSession: (id: string) => void;
  loadMessages: (id: string) => void;
  appendToken: (token: string) => void;
  addActionTrace: (trace: any) => void;
  addArtifact: (artifact: any) => void;
  completeMessage: (message: any) => void;
  setStreaming: (isStreaming: boolean) => void;
  clearStreamingContent: () => void;
  setChatError: (error: string | null) => void;
  deleteSession: (id: string) => void;
  setPendingApproval: (approval: any) => void;
  setBackgroundStatus: (status: string | null) => void;
}

const createChatSlice = (set: any): ChatSlice => ({
  chatSessions: [],
  activeSessionId: null,
  chatMessages: [],
  isStreaming: false,
  streamingContent: "",
  streamingTraces: [],
  streamingArtifacts: [],
  chatError: null,
  pendingApproval: null,
  backgroundStatus: null,
  fetchChatSessions: async () => {
    try {
      const sessions = await api.getChatSessions();
      set({ chatSessions: sessions, chatError: null });
    } catch (err) {
      set({ chatError: (err as Error).message });
    }
  },
  createChatSession: async () => {
    try {
      const session = await api.createChatSession({});
      set((state: any) => ({
        chatSessions: [session, ...state.chatSessions],
        activeSessionId: session.id
      }));
      return session.id;
    } catch (err) {
      set({ chatError: (err as Error).message });
      return "";
    }
  },
  setActiveSession: (id) => set({ activeSessionId: id }),
  loadMessages: async (id: string) => {
    try {
      const messages = await api.getChatMessages(id);
      set({ chatMessages: messages, activeSessionId: id, chatError: null });
    } catch (err) {
      set({ chatError: (err as Error).message });
    }
  },
  appendToken: (token: string) => {
    set((state: any) => ({ streamingContent: state.streamingContent + token }));
  },
  addActionTrace: (trace: any) => {
    set((state: any) => ({ streamingTraces: [...state.streamingTraces, trace] }));
  },
  addArtifact: (artifact: any) => {
    set((state: any) => ({ streamingArtifacts: [...state.streamingArtifacts, artifact] }));
  },
  completeMessage: (message: any) => {
    set((state: any) => ({
      chatMessages: [...state.chatMessages, message],
      streamingContent: "",
      streamingTraces: [],
      streamingArtifacts: [],
      isStreaming: false,
    }));
  },
  setStreaming: (isStreaming) => set({ isStreaming }),
  clearStreamingContent: () => set({ streamingContent: "" }),
  setChatError: (error) => set({ chatError: error }),
  deleteSession: async (id: string) => {
    try {
      await api.deleteChatSession(id);
      set((state: any) => ({
        chatSessions: state.chatSessions.filter((s: any) => s.id !== id),
        activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
        chatMessages: state.activeSessionId === id ? [] : state.chatMessages,
      }));
    } catch (err) {
      set({ chatError: (err as Error).message });
    }
  },
  setPendingApproval: (approval) => set({ pendingApproval: approval }),
  setBackgroundStatus: (status) => set({ backgroundStatus: status }),
});

// ── Dummy Slices ─────────────────────────────────────────

export interface GraphDataSlice {
  nodes: any[];
  edges: any[];
  setNodes: (nodes: any[]) => void;
  setEdges: (edges: any[]) => void;
  onNodesChange: (changes: any) => void;
  onEdgesChange: (changes: any) => void;
  onConnect: (connection: any) => void;
  buildGraph: () => void;
  fetchAll: () => void;
  characters: any[];
  scenes: any[];
  world: any;
  workflow: any;
  fetchCharacters: () => void;
  fetchScenes: (chapter: number) => void;
  fetchWorld: () => void;
  linkCharacterToScene: (characterId: string, sceneId: string) => void;
}

const createGraphDataSlice = (set: any): GraphDataSlice => ({
  nodes: [],
  edges: [],
  characters: [],
  scenes: [],
  world: null,
  workflow: null,
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  onNodesChange: (changes) => { },
  onEdgesChange: (changes) => { },
  onConnect: (connection) => { },
  buildGraph: () => { },
  fetchAll: async () => {
    try {
      const data = await api.getGraph();
      set({ nodes: data.nodes || [], edges: data.edges || [] });
    } catch (err) {
      console.error("Failed to fetch graph:", err);
    }
  },
  fetchCharacters: async () => {
    try {
      const characters = await api.getCharacters();
      set({ characters });
    } catch (err) {
      console.error("Failed to fetch characters:", err);
    }
  },
  fetchScenes: async (chapter) => {
    try {
      const scenes = await api.getScenes(chapter);
      set({ scenes });
    } catch (err) {
      console.error("Failed to fetch scenes:", err);
    }
  },
  fetchWorld: async () => {
    try {
      const world = await api.getWorld();
      set({ world });
    } catch (err) {
      console.error("Failed to fetch world:", err);
    }
  },
  linkCharacterToScene: async (characterId: string, sceneId: string) => {
    console.log("Linking", characterId, "to", sceneId);
  },
});

export interface CanvasUISlice {
  selectedNodeId: string | null;
  setSelectedNode: (id: string | null) => void;
  selectedItem: any | null;
  setSelectedItem: (item: any | null) => void;
}

const createCanvasUISlice = (set: any): CanvasUISlice => ({
  selectedNodeId: null,
  setSelectedNode: (id) => set({ selectedNodeId: id }),
  selectedItem: null,
  setSelectedItem: (item) => set({ selectedItem: item }),
});

export interface ReactFlowSlice {
  rfInstance: any;
  setRfInstance: (instance: any) => void;
}

const createReactFlowSlice = (set: any): ReactFlowSlice => ({
  rfInstance: null,
  setRfInstance: (instance) => set({ rfInstance: instance }),
});

export interface ProjectSlice {
  projectId: string | null;
  setProjectId: (id: string | null) => void;
  projects: any[];
  projectsLoading: boolean;
  activeProjectId: string | null;
  fetchProjects: () => void;
  structureTree: any[];
  fetchStructure: (id: string) => void;
}

const createProjectSlice = (set: any): ProjectSlice => ({
  projectId: null,
  setProjectId: (id) => set({ projectId: id }),
  projects: [],
  projectsLoading: false,
  activeProjectId: null,
  structureTree: [],
  fetchProjects: async () => {
    set({ projectsLoading: true });
    try {
      const data = await api.listProjects();
      set({ projects: data, activeProjectId: data.length > 0 ? data[0].id : null, projectsLoading: false });
    } catch (err) {
      console.error("Failed to fetch projects:", err);
      set({ projectsLoading: false });
    }
  },
  fetchStructure: async () => {
    try {
      const data = await api.getProjectStructure();
      set({ structureTree: data });
    } catch (err) {
      console.error("Failed to fetch structure:", err);
    }
  },
});

export interface ModelConfigSlice {
  modelParams: any;
  setModelParams: (params: any) => void;
  modelConfig: any;
  availableModels: string[];
  modelConfigLoading: boolean;
  modelConfigSaving: boolean;
  fetchModelConfig: () => void;
  fetchAvailableModels: () => void;
  updateModelConfig: (config: any) => void;
}

const createModelConfigSlice = (set: any): ModelConfigSlice => ({
  modelParams: {},
  setModelParams: (params) => set({ modelParams: params }),
  modelConfig: null,
  availableModels: [],
  modelConfigLoading: false,
  modelConfigSaving: false,
  fetchModelConfig: async () => {
    set({ modelConfigLoading: true });
    try {
      const config = await api.getModelConfig();
      set({ modelConfig: config, modelConfigLoading: false });
    } catch (err) {
      console.error("Failed to fetch model config:", err);
      set({ modelConfigLoading: false });
    }
  },
  fetchAvailableModels: async () => {
    try {
      const models = await api.getAvailableModels();
      set({ availableModels: models });
    } catch (err) {
      console.error("Failed to fetch available models:", err);
    }
  },
  updateModelConfig: async (config: any) => {
    set({ modelConfigSaving: true });
    try {
      const updated = await api.updateModelConfig(config);
      set({ modelConfig: updated, modelConfigSaving: false });
    } catch (err) {
      console.error("Failed to update model config:", err);
      set({ modelConfigSaving: false });
    }
  },
});

// ── Selection & UI ──────────────────────────────────────────

export type SidebarTab = "characters" | "scenes" | "world";

export interface Selection {
  id: string;
  type: "character" | "scene" | "world" | "faction" | "location";
  name: string;
}

// ── Main Store Definition ───────────────────────────────────

export type StudioState = GraphDataSlice & CanvasUISlice & ReactFlowSlice & ProjectSlice & ModelConfigSlice & ChatSlice & Record<string, any>;

export const useStudioStore = create<StudioState>()((set) => ({
  ...createGraphDataSlice(set),
  ...createCanvasUISlice(set),
  ...createReactFlowSlice(set),
  ...createProjectSlice(set),
  ...createModelConfigSlice(set),
  ...createChatSlice(set),
}));
