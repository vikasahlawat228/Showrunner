"use client";

import { ChevronLeft } from "lucide-react";
import { cn } from "@/lib/cn";
import { useStudioStore, type SidebarTab } from "@/lib/store";
import { SidebarItem } from "./SidebarItem";
import { WorldStatus } from "./WorldStatus";

const TABS: { key: SidebarTab; label: string }[] = [
  { key: "characters", label: "Characters" },
  { key: "scenes", label: "Scenes" },
  { key: "world", label: "World" },
];

export function Sidebar() {
  const {
    characters,
    scenes,
    world,
    sidebarCollapsed,
    sidebarTab,
    selectedItem,
    toggleSidebar,
    setSidebarTab,
    selectItem,
  } = useStudioStore();

  return (
    <aside
      className={cn(
        "h-full bg-gray-900 border-r border-gray-800 flex flex-col transition-all duration-200 overflow-hidden",
        sidebarCollapsed ? "w-0" : "w-72"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <span className="text-sm font-semibold text-gray-300">Assets</span>
        <button
          onClick={toggleSidebar}
          className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-800 shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSidebarTab(tab.key)}
            className={cn(
              "flex-1 px-2 py-2 text-xs font-medium transition-colors",
              sidebarTab === tab.key
                ? "text-blue-400 border-b-2 border-blue-400"
                : "text-gray-500 hover:text-gray-300"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sidebarTab === "characters" && (
          <>
            {characters.length === 0 ? (
              <p className="text-gray-600 text-xs px-2 py-4 text-center">
                No characters yet.
              </p>
            ) : (
              characters.map((c) => (
                <SidebarItem
                  key={c.id}
                  id={c.id}
                  type="character"
                  name={c.name}
                  subtitle={c.role}
                  selected={selectedItem?.id === c.id}
                  onClick={() =>
                    selectItem({ id: c.id, type: "character", name: c.name })
                  }
                />
              ))
            )}
          </>
        )}

        {sidebarTab === "scenes" && (
          <>
            {scenes.length === 0 ? (
              <p className="text-gray-600 text-xs px-2 py-4 text-center">
                No scenes yet.
              </p>
            ) : (
              scenes.map((s) => (
                <SidebarItem
                  key={s.id}
                  id={s.id}
                  type="scene"
                  name={s.title}
                  subtitle={`Scene ${s.scene_number} · ${s.scene_type}`}
                  selected={selectedItem?.id === s.id}
                  onClick={() =>
                    selectItem({ id: s.id, type: "scene", name: s.title })
                  }
                />
              ))
            )}
          </>
        )}

        {sidebarTab === "world" && (
          <WorldStatus
            world={world}
            selected={selectedItem?.type === "world"}
            onClick={() => {
              if (world) {
                selectItem({ id: world.id, type: "world", name: world.name });
              }
            }}
          />
        )}
      </div>
    </aside>
  );
}
