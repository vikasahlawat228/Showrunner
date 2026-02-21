"use client";

import { X } from "lucide-react";
import { useStudioStore } from "@/lib/store";
import type { CharacterDetail, SceneSummary, WorldSettings } from "@/lib/api";
import { CharacterInspector } from "./CharacterInspector";
import { SceneInspector } from "./SceneInspector";
import { SkeletonInspector } from "@/components/ui/Skeleton";

function WorldInspector({ world }: { world: WorldSettings }) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          World
        </h3>
        <div className="text-sm text-gray-300 space-y-1">
          {world.genre && <div><span className="text-gray-500">Genre:</span> {world.genre}</div>}
          {world.time_period && <div><span className="text-gray-500">Era:</span> {world.time_period}</div>}
          {world.tone && <div><span className="text-gray-500">Tone:</span> {world.tone}</div>}
          {world.technology_level && <div><span className="text-gray-500">Tech:</span> {world.technology_level}</div>}
        </div>
      </div>

      {world.one_line && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Summary
          </h3>
          <p className="text-sm text-gray-300">{world.one_line}</p>
        </div>
      )}

      {world.description && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Description
          </h3>
          <p className="text-sm text-gray-400 leading-relaxed">{world.description}</p>
        </div>
      )}

      {world.locations.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Locations ({world.locations.length})
          </h3>
          <div className="space-y-2">
            {world.locations.map((loc) => (
              <div key={loc.id} className="text-sm">
                <div className="font-medium text-gray-300">{loc.name}</div>
                <div className="text-xs text-gray-500">{loc.type}</div>
                {loc.description && (
                  <div className="text-xs text-gray-400 mt-0.5">{loc.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {world.rules.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Rules ({world.rules.length})
          </h3>
          <div className="space-y-2">
            {world.rules.map((rule) => (
              <div key={rule.name} className="text-sm">
                <div className="font-medium text-gray-300">{rule.name}</div>
                <div className="text-xs text-gray-500">{rule.category}</div>
                {rule.description && (
                  <div className="text-xs text-gray-400 mt-0.5">{rule.description}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {world.factions.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
            Factions ({world.factions.length})
          </h3>
          <div className="space-y-2">
            {world.factions.map((fac) => (
              <div key={fac.id} className="text-sm">
                <div className="font-medium text-gray-300">{fac.name}</div>
                <div className="text-xs text-gray-500">{fac.type}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function Inspector() {
  const { selectedItem, inspectorData, inspectorLoading, clearSelection } =
    useStudioStore();

  if (!selectedItem) return null;

  const typeLabel = selectedItem.type.toUpperCase();

  return (
    <aside className="w-80 h-full bg-gray-900 border-l border-gray-800 flex flex-col shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 shrink-0">
        <div className="min-w-0">
          <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">
            {typeLabel}
          </span>
          <h2 className="text-sm font-semibold text-white truncate">
            {selectedItem.name}
          </h2>
        </div>
        <button
          onClick={clearSelection}
          className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4">
        {inspectorLoading ? (
          <SkeletonInspector />
        ) : inspectorData ? (
          <>
            {selectedItem.type === "character" && (
              <CharacterInspector
                character={inspectorData as CharacterDetail}
              />
            )}
            {selectedItem.type === "scene" && (
              <SceneInspector scene={inspectorData as SceneSummary} />
            )}
            {selectedItem.type === "world" && (
              <WorldInspector world={inspectorData as WorldSettings} />
            )}
          </>
        ) : (
          <p className="text-gray-600 text-sm text-center py-8">
            No data available.
          </p>
        )}
      </div>
    </aside>
  );
}
