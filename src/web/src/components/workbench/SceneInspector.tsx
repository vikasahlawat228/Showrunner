"use client";

import { X, User } from "lucide-react";
import { useDroppable } from "@dnd-kit/core";
import type { SceneSummary } from "@/lib/api";
import { useStudioStore } from "@/lib/store";

interface SceneInspectorProps {
  scene: SceneSummary;
}

function Field({ label, value }: { label: string; value?: string | number | null }) {
  if (value === undefined || value === null || value === "") return null;
  return (
    <div className="text-sm mb-1">
      <span className="text-gray-500">{label}:</span>{" "}
      <span className="text-gray-300">{String(value)}</span>
    </div>
  );
}

export function SceneInspector({ scene }: SceneInspectorProps) {
  const characters = useStudioStore((s) => s.characters);
  const unlinkCharacterFromScene = useStudioStore((s) => s.unlinkCharacterFromScene);
  const { isOver, setNodeRef } = useDroppable({ id: "scene-inspector-drop" });

  const tensionPercent = (scene.tension_level / 10) * 100;

  // Resolve character IDs to names
  const linkedCharacters = scene.characters_present.map((charId) => {
    const found = characters.find((c) => c.id === charId);
    return { id: charId, name: found?.name ?? charId, role: found?.role };
  });

  return (
    <div className="space-y-4">
      {/* Info */}
      <div>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Scene Info
        </h3>
        <Field label="Chapter" value={scene.chapter} />
        <Field label="Scene #" value={scene.scene_number} />
        <Field label="Type" value={scene.scene_type.replace(/_/g, " ")} />
      </div>

      {/* Tension Bar */}
      <div>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Tension Level
        </h3>
        <div className="flex items-center gap-2">
          <div className="flex-1 h-2 bg-gray-800 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${tensionPercent}%`,
                background: `linear-gradient(90deg, #22c55e ${0}%, #eab308 ${50}%, #ef4444 ${100}%)`,
              }}
            />
          </div>
          <span className="text-xs text-gray-400 font-mono w-8 text-right">
            {scene.tension_level}/10
          </span>
        </div>
      </div>

      {/* Linked Characters — drop zone for sidebar characters */}
      <div
        ref={setNodeRef}
        className={`rounded-lg p-2 -m-2 transition-colors ${isOver ? "bg-blue-900/30 ring-1 ring-blue-500/50" : ""}`}
      >
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
          Characters ({linkedCharacters.length})
        </h3>
        {linkedCharacters.length === 0 ? (
          <p className={`text-xs ${isOver ? "text-blue-400" : "text-gray-600"}`}>
            {isOver ? "Drop to link character" : "Drag a character onto this scene to link them."}
          </p>
        ) : (
          <div className="space-y-1">
            {linkedCharacters.map((char) => (
              <div
                key={char.id}
                className="flex items-center justify-between px-2 py-1.5 rounded bg-gray-800/50 group"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <User className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <div className="min-w-0">
                    <div className="text-sm text-gray-300 truncate">
                      {char.name}
                    </div>
                    {char.role && (
                      <div className="text-xs text-gray-500">{char.role}</div>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => unlinkCharacterFromScene(char.id, scene.id)}
                  className="p-0.5 rounded hover:bg-gray-700 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all shrink-0"
                  title="Unlink character"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
