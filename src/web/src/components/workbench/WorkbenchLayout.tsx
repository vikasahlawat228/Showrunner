"use client";

import { useState } from "react";
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
} from "@dnd-kit/core";
import { User, FileText } from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { Sidebar } from "./Sidebar";
import { Canvas } from "./Canvas";
import { Inspector } from "./Inspector";

interface DragData {
  type: "character" | "scene";
  name: string;
  id: string;
  source?: string;
}

export function WorkbenchLayout() {
  const linkCharacterToScene = useStudioStore((s) => s.linkCharacterToScene);
  const [activeDrag, setActiveDrag] = useState<DragData | null>(null);

  const handleDragStart = (event: DragStartEvent) => {
    const data = event.active.data.current as DragData | undefined;
    if (data) {
      setActiveDrag(data);
    }
  };

  const handleDragEnd = (event: DragEndEvent) => {
    setActiveDrag(null);
    const { active, over } = event;
    if (!active || !over) return;

    const activeData = active.data.current as DragData | undefined;
    const overData = over.data.current as DragData | undefined;
    if (!activeData || !overData) return;

    // Character dropped onto Scene → link
    if (activeData.type === "character" && overData.type === "scene") {
      linkCharacterToScene(activeData.id, overData.id);
    }
  };

  const handleDragCancel = () => {
    setActiveDrag(null);
  };

  return (
    <DndContext
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <div className="h-screen flex bg-gray-950 text-white overflow-hidden">
        <Sidebar />
        <Canvas />
        <Inspector />
      </div>

      <DragOverlay dropAnimation={null}>
        {activeDrag && (
          <div className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-600 shadow-xl flex items-center gap-2 text-sm text-white pointer-events-none">
            {activeDrag.type === "character" ? (
              <User className="w-4 h-4 text-blue-400" />
            ) : (
              <FileText className="w-4 h-4 text-purple-400" />
            )}
            <span className="font-medium">{activeDrag.name}</span>
          </div>
        )}
      </DragOverlay>
    </DndContext>
  );
}
