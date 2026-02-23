"use client";

import React, { useEffect, useState } from "react";

import { PanelLeft } from "lucide-react";
import { toast } from "sonner";
import { useStudioStore } from "@/lib/store";
import InfiniteCanvas from "@/components/canvas/InfiniteCanvas";
import { WorkflowBar } from "./WorkflowBar";
import { DirectorControls } from "./DirectorControls";
import { usePipelineStream } from "@/components/pipeline/usePipelineStream";
import { PromptReviewModal } from "@/components/pipeline/PromptReviewModal";
import { TimelineView } from "@/components/timeline/TimelineView";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { api } from "@/lib/api";

export function Canvas() {
  const {
    project,
    characters,
    scenes,
    workflow,
    loading,
    error,
    pipelineRunId,
    mainView,
    sidebarCollapsed,
    selectedItem,
    currentChapter,
    startPipeline,
    clearError,
    toggleSidebar,
    setMainView,
    selectItem,
    setChapter,
    fetchAll,
  } = useStudioStore();
  const { state, payload, stepName, agentId, error: streamError, isConnecting } = usePipelineStream(pipelineRunId || undefined);

  const [isStarting, setIsStarting] = useState(false);

  const handleStartPipeline = async () => {
    try {
      setIsStarting(true);
      await startPipeline();
    } catch {
      // Error stored in state
    } finally {
      setIsStarting(false);
    }
  };

  const handleResume = async (payload: { prompt_text: string; model?: string; refine_instructions?: string }) => {
    if (pipelineRunId) {
      await api.resumePipeline(pipelineRunId, payload);
    }
  };

  // refresh data when pipeline completes
  useEffect(() => {
    if (state === 'COMPLETED') {
      toast.success("Pipeline completed");
      fetchAll();
    } else if (state === 'FAILED') {
      toast.error("Pipeline failed");
    }
  }, [state, fetchAll]);

  return (
    <div className="flex-1 h-full flex flex-col overflow-hidden">
      <PromptReviewModal
        isOpen={state === 'PAUSED_FOR_USER'}
        initialPrompt={payload?.prompt_text}
        stepName={stepName}
        agentId={agentId}
        contextBuckets={payload?.gathered_context_meta?.buckets}
        modelUsed={payload?.resolved_model}
        tokenCount={payload?.gathered_context_meta?.token_estimate}
        onResume={handleResume}
      />
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

          {/* Main View Toggle */}
          <div className="ml-8 flex items-center bg-gray-900 rounded-lg p-1 border border-gray-800">
            <button
              onClick={() => setMainView('canvas')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${mainView === 'canvas' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
            >
              Graph
            </button>
            <button
              onClick={() => setMainView('timeline')}
              className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${mainView === 'timeline' ? 'bg-gray-800 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
            >
              Timeline
            </button>
          </div>
        </div>
        <DirectorControls
          pipelineState={state}
          isStarting={isStarting || isConnecting}
          agentId={agentId}
          onStartPipeline={handleStartPipeline}
        />
      </header>

      {/* Workflow Progress */}
      {workflow && (
        <div className="px-6 py-3 border-b border-gray-800/50 shrink-0">
          <WorkflowBar workflow={workflow} />
        </div>
      )}

      {/* Error Banner */}
      {(error || streamError) && (
        <div className="mx-6 mt-3 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm flex justify-between items-center shrink-0">
          <span>{error || streamError}</span>
          <button
            onClick={clearError}
            className="text-red-400 hover:text-red-200 ml-4 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Content */}
      <main className="flex-1 w-full relative overflow-hidden">
        {mainView === 'canvas' ? (
          loading ? (
            <div className="p-8 grid grid-cols-3 gap-4 animate-in fade-in">
              {Array.from({ length: 9 }).map((_, i) => (
                <SkeletonCard key={i} />
              ))}
            </div>
          ) : (
            <InfiniteCanvas />
          )
        ) : (
          <TimelineView />
        )}
      </main>
    </div>
  );
}
