"use client";

import { DndContext, type DragEndEvent } from "@dnd-kit/core";
import { useStudioStore } from "@/lib/store";
import { Sidebar } from "./Sidebar";
import { Canvas } from "./Canvas";
import { Inspector } from "./Inspector";

export function WorkbenchLayout() {
  const linkCharacterToScene = useStudioStore((s) => s.linkCharacterToScene);
  const selectedItem = useStudioStore((s) => s.selectedItem);

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
      <div className="h-screen flex bg-gray-950 text-white overflow-hidden">
        <Sidebar />
        <Canvas />
        <Inspector />
      </div>
    </DndContext>
  );
}
