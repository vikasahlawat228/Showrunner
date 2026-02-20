"use client";

import { Globe } from "lucide-react";
import { cn } from "@/lib/cn";
import type { WorldSettings } from "@/lib/api";

interface WorldStatusProps {
  world: WorldSettings | null;
  selected?: boolean;
  onClick: () => void;
}

export function WorldStatus({ world, selected, onClick }: WorldStatusProps) {
  if (!world) {
    return (
      <div className="px-3 py-4 text-center">
        <Globe className="w-8 h-8 text-gray-700 mx-auto mb-2" />
        <p className="text-gray-600 text-xs">
          No world built yet. Use the Director or CLI to build your world.
        </p>
      </div>
    );
  }

  return (
    <div
      onClick={onClick}
      className={cn(
        "px-3 py-3 rounded-md cursor-pointer transition-colors",
        selected
          ? "bg-blue-600/20 border border-blue-500/30"
          : "hover:bg-gray-800"
      )}
    >
      <div className="flex items-center gap-2 mb-1">
        <Globe className="w-4 h-4 text-emerald-400" />
        <span className="font-medium text-white text-sm">{world.name}</span>
      </div>
      <div className="text-xs text-gray-400 space-y-0.5">
        {world.genre && <div>Genre: {world.genre}</div>}
        {world.time_period && <div>Era: {world.time_period}</div>}
        {world.tone && <div>Tone: {world.tone}</div>}
        {world.locations.length > 0 && (
          <div>{world.locations.length} location{world.locations.length !== 1 ? "s" : ""}</div>
        )}
        {world.factions.length > 0 && (
          <div>{world.factions.length} faction{world.factions.length !== 1 ? "s" : ""}</div>
        )}
      </div>
    </div>
  );
}
