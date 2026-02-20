import { create } from "zustand";
import { createGraphDataSlice, type GraphDataSlice } from "./store/graphDataSlice";
import { createCanvasUISlice, type CanvasUISlice } from "./store/canvasUISlice";
import { createReactFlowSlice, type ReactFlowSlice } from "./store/reactFlowSlice";

// ── Selection & UI ──────────────────────────────────────────

export type SidebarTab = "characters" | "scenes" | "world";

export interface Selection {
  id: string;
  type: "character" | "scene" | "world" | "faction" | "location";
  name: string;
}

// ── Main Store Definition ───────────────────────────────────

export type StudioState = GraphDataSlice & CanvasUISlice & ReactFlowSlice;

export const useStudioStore = create<StudioState>()((...a) => ({
  ...createGraphDataSlice(...a),
  ...createCanvasUISlice(...a),
  ...createReactFlowSlice(...a),
}));
