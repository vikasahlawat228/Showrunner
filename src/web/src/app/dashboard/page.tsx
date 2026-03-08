"use client";

import { useEffect } from "react";
import { DndContext, type DragEndEvent } from "@dnd-kit/core";
import { useStudioStore } from "@/lib/store";

// Command Center Components
import { ProjectSwitcher } from "@/components/command-center/ProjectSwitcher";
import { ProgressOverview } from "@/components/command-center/ProgressOverview";
import { PendingApprovals } from "@/components/command-center/PendingApprovals";
import { ModelConfigPanel } from "@/components/command-center/ModelConfigPanel";
import { DatabaseStats } from "@/components/command-center/DatabaseStats";
import { GitPanel } from "@/components/command-center/GitPanel";

// Writer Dashboard
import { WriterDashboard } from "@/components/dashboard/WriterDashboard";

// Canvas & Layout Components
import { Canvas } from "@/components/workbench/Canvas";
import { Sidebar } from "@/components/workbench/Sidebar";
import { Inspector } from "@/components/workbench/Inspector";

import { useState } from "react";
import { ChevronDown, ChevronUp, Wrench } from "lucide-react";

export default function DashboardPage() {
  const fetchAll = useStudioStore((s) => s.fetchAll);
  const linkCharacterToScene = useStudioStore((s) => s.linkCharacterToScene);
  const selectedItem = useStudioStore((s) => s.selectedItem);

  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event;
    if (!over) return;

    const dragData = active.data.current;
    if (
      dragData?.source === "sidebar" &&
      dragData?.type === "character" &&
      over.id === "scene-inspector-drop" &&
      selectedItem?.type === "scene"
    ) {
      linkCharacterToScene(dragData.id, selectedItem.id);
    }
  }

  return (
    <DndContext onDragEnd={handleDragEnd}>
      <div className="flex h-full w-full bg-gray-950 text-white overflow-hidden font-sans">

        {/* Left Column: Writer Dashboard */}
        <div className="w-96 shrink-0 border-r border-gray-800/80 bg-gray-950/50 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            <WriterDashboard />
          </div>

          {/* Advanced Tools (collapsed by default) */}
          <div className="border-t border-gray-800">
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-xs text-gray-500 hover:text-gray-400 transition-colors"
            >
              <span className="flex items-center gap-1.5 font-medium uppercase tracking-wider">
                <Wrench className="w-3 h-3" /> Advanced Tools
              </span>
              {showAdvanced ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
            </button>
            {showAdvanced && (
              <div className="p-3 space-y-3 max-h-80 overflow-y-auto border-t border-gray-800/50">
                <ProjectSwitcher />
                <ProgressOverview />
                <PendingApprovals />
                <ModelConfigPanel />
                <GitPanel />
                <DatabaseStats />
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Workbench Canvas */}
        <div className="flex-1 flex overflow-hidden bg-[#0A0A0A] relative shadow-[-10px_0_30px_rgba(0,0,0,0.5)] z-10">
          <Sidebar />
          <Canvas />
          <Inspector />
        </div>

      </div>
    </DndContext>
  );
}
