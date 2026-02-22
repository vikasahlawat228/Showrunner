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

// Canvas & Layout Components
import { Canvas } from "@/components/workbench/Canvas";
import { Sidebar } from "@/components/workbench/Sidebar";
import { Inspector } from "@/components/workbench/Inspector";

export default function DashboardPage() {
  const fetchAll = useStudioStore((s) => s.fetchAll);
  const linkCharacterToScene = useStudioStore((s) => s.linkCharacterToScene);
  const selectedItem = useStudioStore((s) => s.selectedItem);

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
      <div className="flex h-screen w-full bg-gray-950 text-white overflow-hidden font-sans">

        {/* Left Column: Command Center (Scrollable) */}
        <div className="w-80 shrink-0 border-r border-gray-800/80 bg-gray-950/50 flex flex-col overflow-y-auto">
          <div className="p-4 space-y-4">
            <ProjectSwitcher />
            <ProgressOverview />
            <PendingApprovals />
            <ModelConfigPanel />
            <DatabaseStats />
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
