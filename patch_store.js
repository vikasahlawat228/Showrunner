const fs = require('fs');
const path = require('path');

const storePath = path.join(process.cwd(), 'src/web/src/lib/store.ts');
let storeContent = fs.readFileSync(storePath, 'utf8');

// Add import api
if (!storeContent.includes('import { api } from "@/lib/api"')) {
    storeContent = storeContent.replace('import { create } from "zustand";', 'import { create } from "zustand";\nimport { api } from "@/lib/api";');
}

// ProjectSlice
storeContent = storeContent.replace(
    /const createProjectSlice = \(set: any\): ProjectSlice => \(\{[\s\S]*?\}\);/,
    `const createProjectSlice = (set: any): ProjectSlice => ({
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
});`
);

// GraphDataSlice
storeContent = storeContent.replace(
    /const createGraphDataSlice = \(set: any\): GraphDataSlice => \(\{[\s\S]*?\}\);/,
    `const createGraphDataSlice = (set: any): GraphDataSlice => ({
  nodes: [],
  edges: [],
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  fetchAll: async () => {
    try {
      const data = await api.getGraph();
      set({ nodes: data.nodes || [], edges: data.edges || [] });
    } catch (err) {
      console.error("Failed to fetch graph:", err);
    }
  },
});`
);

// ModelConfigSlice
storeContent = storeContent.replace(
    /const createModelConfigSlice = \(set: any\): ModelConfigSlice => \(\{[\s\S]*?\}\);/,
    `const createModelConfigSlice = (set: any): ModelConfigSlice => ({
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
});`
);

fs.writeFileSync(storePath, storeContent);
