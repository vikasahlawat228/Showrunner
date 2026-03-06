const fs = require('fs');
const path = require('path');

const storePath = path.join(process.cwd(), 'src/web/src/lib/store/pipelineBuilderSlice.ts');
let storeContent = fs.readFileSync(storePath, 'utf8');

if (!storeContent.includes('import { api } from "@/lib/api"')) {
    storeContent = storeContent.replace('import { create } from "zustand";', 'import { create } from "zustand";\nimport { api } from "@/lib/api";');
}

storeContent = storeContent.replace(
    /export const usePipelineBuilderStore = create<PipelineBuilderState>\(\(set\) => \(\{[\s\S]*\}\)\);/,
    `export const usePipelineBuilderStore = create<PipelineBuilderState>((set, get) => ({
    definitions: [],
    loadDefinitions: async () => {
        try {
            const data = await api.getPipelineDefinitions();
            set({ definitions: data });
        } catch (err) {
            console.error(err);
        }
    },
    loadDefinition: async (id: string) => {
        try {
            const data = await api.getPipelineDefinition(id);
            set({
                currentDefinitionId: data.id,
                pipelineName: data.name,
                pipelineDescription: data.description,
                nodes: data.steps.map((s: any) => ({
                    id: s.id,
                    type: "stepNode",
                    position: s.position,
                    data: {
                        label: s.label,
                        stepType: s.step_type,
                        config: s.config,
                    }
                })),
                edges: data.edges.map((e: any) => ({
                    id: \`e-\${e.source}-\${e.target}\`,
                    source: e.source,
                    target: e.target,
                }))
            });
        } catch (err) {
            console.error(err);
        }
    },
    loadRegistry: async () => {
        try {
            const data = await api.getPipelineStepRegistry();
            set({ stepRegistry: data, registryLoaded: true });
        } catch (err) {
            console.error(err);
            set({ registryLoaded: true });
        }
    },
    resetBuilder: () => set({ currentDefinitionId: null, nodes: [], edges: [], pipelineName: "", pipelineDescription: "", selectedStepId: null }),
    currentDefinitionId: null,
    selectStep: (id) => set({ selectedStepId: id }),
    removeStep: (id: string) => {
        set((state) => ({
            nodes: state.nodes.filter((n) => n.id !== id),
            edges: state.edges.filter((e) => e.source !== id && e.target !== id),
            selectedStepId: state.selectedStepId === id ? null : state.selectedStepId
        }));
    },
    stepRegistry: [],
    registryLoaded: false,
    addStep: (type, position) => {
        const id = \`step_\${Math.random().toString(36).substr(2, 9)}\`;
        const reg = get().stepRegistry.find(r => r.step_type === type);
        const newNode = {
            id,
            type: "stepNode",
            position,
            data: {
                label: reg?.label || type,
                stepType: type,
                config: {},
                category: reg?.category,
                icon: reg?.icon
            }
        };
        set((state) => ({ nodes: [...state.nodes, newNode] }));
    },
    nodes: [],
    edges: [],
    setNodes: (nodes) => set({ nodes }),
    setEdges: (edges) => set({ edges }),
    onConnect: (params) => {
        set((state) => ({ edges: [...state.edges, { ...params, id: \`e-\${params.source}-\${params.target}\` }] }));
    },
    pipelineName: "",
    pipelineDescription: "",
    setPipelineName: (pipelineName) => set({ pipelineName }),
    setPipelineDescription: (pipelineDescription) => set({ pipelineDescription }),
    saveDefinition: async () => {
        const state = get();
        set({ isSaving: true });
        try {
            const body = {
                name: state.pipelineName,
                description: state.pipelineDescription,
                steps: state.nodes.map(n => ({
                    id: n.id,
                    step_type: n.data.stepType,
                    label: n.data.label,
                    config: n.data.config || {},
                    position: n.position
                })),
                edges: state.edges.map(e => ({
                    source: e.source,
                    target: e.target
                }))
            };
            if (state.currentDefinitionId) {
                await api.updatePipelineDefinition(state.currentDefinitionId, body);
            } else {
                const res = await api.createPipelineDefinition(body);
                set({ currentDefinitionId: res.id });
            }
        } catch (err) {
            console.error(err);
        } finally {
            set({ isSaving: false });
        }
    },
    runPipeline: () => { console.log('Run Pipeline triggered in mocked slice.'); },
    isSaving: false,
    isRunning: false,
    selectedStepId: null,
    updateStepConfig: (id, config) => {
        set((state) => ({
            nodes: state.nodes.map(n => n.id === id ? { ...n, data: { ...n.data, config: { ...n.data.config, ...config } } } : n)
        }));
    },
    updateStepLabel: (id, label) => {
        set((state) => ({
            nodes: state.nodes.map(n => n.id === id ? { ...n, data: { ...n.data, label } } : n)
        }));
    },
}));`
);

fs.writeFileSync(storePath, storeContent);
