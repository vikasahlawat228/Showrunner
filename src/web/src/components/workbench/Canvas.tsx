"use client";

import { PanelLeft, ChevronLeft, ChevronRight } from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { ContainerCard } from "@/components/ContainerCard";
import { WorkflowBar } from "./WorkflowBar";
import { DirectorControls } from "./DirectorControls";

export function Canvas() {
  const {
    project,
    characters,
    scenes,
    workflow,
    loading,
    error,
    directorActing,
    lastDirectorResult,
    sidebarCollapsed,
    selectedItem,
    currentChapter,
    directorAct,
    clearError,
    toggleSidebar,
    selectItem,
    setChapter,
  } = useStudioStore();

  const handleDirectorAct = async () => {
    try {
      await directorAct();
    } catch {
      // Error stored in state
    }
  };

  return (
    <div className="flex-1 h-full flex flex-col overflow-hidden">
      {/* Header */}
      <header className="px-6 py-4 border-b border-gray-800 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          {sidebarCollapsed && (
            <button
              onClick={toggleSidebar}
              className="p-1.5 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
          <div>
            <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Antigravity Studio
            </h1>
            {project && (
              <p className="text-gray-500 text-xs">{project.name}</p>
            )}
          </div>
        </div>
        <DirectorControls
          acting={directorActing}
          lastResult={lastDirectorResult}
          onAct={handleDirectorAct}
        />
      </header>

      {/* Workflow Progress */}
      {workflow && (
        <div className="px-6 py-3 border-b border-gray-800/50 shrink-0">
          <WorkflowBar workflow={workflow} />
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="mx-6 mt-3 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm flex justify-between items-center shrink-0">
          <span>{error}</span>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-200 ml-4 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 overflow-y-auto p-6">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-gray-500 text-lg">Loading studio...</div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Characters Section */}
            <section>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Characters
                <span className="ml-2 text-gray-600 font-normal normal-case">
                  {characters.length}
                </span>
              </h2>
              {characters.length === 0 ? (
                <p className="text-gray-600 text-sm">
                  No characters yet. Use the Director or CLI to create characters.
                </p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {characters.map((c) => (
                    <div
                      key={c.id}
                      onClick={() =>
                        selectItem({ id: c.id, type: "character", name: c.name })
                      }
                      className={
                        selectedItem?.id === c.id
                          ? "ring-2 ring-blue-500 rounded-lg"
                          : ""
                      }
                    >
                      <ContainerCard
                        id={c.id}
                        type="character"
                        title={c.name}
                        subtitle={c.role}
                        metadata={
                          [c.one_line, c.has_dna ? "DNA ready" : null]
                            .filter(Boolean)
                            .join(" · ") || undefined
                        }
                      />
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Scenes Section */}
            <section>
              <div className="flex items-center gap-3 mb-3">
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Scenes
                  <span className="ml-2 text-gray-600 font-normal normal-case">
                    {scenes.length}
                  </span>
                </h2>

                {/* Chapter Navigation */}
                <div className="flex items-center gap-1 ml-auto">
                  <button
                    onClick={() => setChapter(Math.max(1, currentChapter - 1))}
                    disabled={currentChapter <= 1}
                    className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="text-xs text-gray-400 font-medium px-1 min-w-[4rem] text-center">
                    Ch. {currentChapter}
                  </span>
                  <button
                    onClick={() => setChapter(currentChapter + 1)}
                    className="p-1 rounded hover:bg-gray-800 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {scenes.length === 0 ? (
                <p className="text-gray-600 text-sm">
                  No scenes yet. Progress through the workflow to create scenes.
                </p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                  {scenes.map((s) => (
                    <div
                      key={s.id}
                      onClick={() =>
                        selectItem({ id: s.id, type: "scene", name: s.title })
                      }
                      className={
                        selectedItem?.id === s.id
                          ? "ring-2 ring-purple-500 rounded-lg"
                          : ""
                      }
                    >
                      <ContainerCard
                        id={s.id}
                        type="scene"
                        title={s.title}
                        subtitle={`Scene ${s.scene_number} · ${s.scene_type}`}
                        metadata={
                          s.tension_level > 0
                            ? `Tension: ${s.tension_level}/10`
                            : undefined
                        }
                        characterCount={s.characters_present.length}
                      />
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
