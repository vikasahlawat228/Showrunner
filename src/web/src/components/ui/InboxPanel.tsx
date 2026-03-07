"use client";

import React, { useEffect, useState } from "react";
import { useStudioStore } from "@/lib/store";
import { Inbox, Trash2, Check, ArrowRight, Loader } from "lucide-react";
import { Badge } from "@/components/ui/Badge";

interface CapturedIdea {
  id: string;
  text: string;
  tags: string[];
  captured_at: string;
  processed: boolean;
  converted_to: string | null;
}

interface InboxPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function InboxPanel({ isOpen, onClose }: InboxPanelProps) {
  const [ideas, setIdeas] = useState<CapturedIdea[]>([]);
  const [unprocessedOnly, setUnprocessedOnly] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [containerInput, setContainerInput] = useState<string>("");
  const [showContainerInput, setShowContainerInput] = useState<string | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(false);
  const { briefContext } = useStudioStore();

  // Fetch captures from backend
  useEffect(() => {
    if (!isOpen) return;

    const fetchCaptures = async () => {
      try {
        setIsLoading(true);
        const response = await fetch("/api/inbox/list");
        if (response.ok) {
          const data = await response.json();
          setIdeas(data.captures || []);
        }
      } catch (error) {
        console.error("Failed to fetch captures:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCaptures();
  }, [isOpen]);

  const handleConvert = async (ideaId: string, containerId: string) => {
    if (!containerId.trim()) return;

    try {
      setProcessingId(ideaId);
      const response = await fetch("/api/inbox/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          capture_id: ideaId,
          action: "convert",
          container_id: containerId,
        }),
      });

      if (response.ok) {
        // Update local state
        setIdeas((prev) =>
          prev.map((idea) =>
            idea.id === ideaId
              ? {
                  ...idea,
                  processed: true,
                  converted_to: containerId,
                }
              : idea
          )
        );
        setShowContainerInput(null);
        setContainerInput("");
      }
    } catch (error) {
      console.error("Failed to convert idea:", error);
    } finally {
      setProcessingId(null);
    }
  };

  const handleDiscard = async (ideaId: string) => {
    try {
      setProcessingId(ideaId);
      const response = await fetch("/api/inbox/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          capture_id: ideaId,
          action: "discard",
        }),
      });

      if (response.ok) {
        // Update local state
        setIdeas((prev) =>
          prev.map((idea) =>
            idea.id === ideaId
              ? { ...idea, processed: true, converted_to: null }
              : idea
          )
        );
      }
    } catch (error) {
      console.error("Failed to discard idea:", error);
    } finally {
      setProcessingId(null);
    }
  };

  const handleClearProcessed = async () => {
    if (!confirm("Delete all processed ideas? This cannot be undone.")) return;

    try {
      const response = await fetch("/api/inbox/clear", { method: "POST" });
      if (response.ok) {
        setIdeas((prev) => prev.filter((idea) => !idea.processed));
      }
    } catch (error) {
      console.error("Failed to clear processed ideas:", error);
    }
  };

  const filteredIdeas = unprocessedOnly
    ? ideas.filter((idea) => !idea.processed)
    : ideas;

  const unprocessedCount = ideas.filter((idea) => !idea.processed).length;
  const processedCount = ideas.filter((idea) => idea.processed).length;

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-end">
      <div className="w-full max-w-2xl bg-gray-900 border-t border-gray-700 rounded-t-lg shadow-xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <Inbox className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-lg font-semibold text-gray-100">
                Brain Dump Inbox
              </h2>
              <p className="text-xs text-gray-400">
                {unprocessedCount} unprocessed · {processedCount} processed
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-gray-400 hover:text-gray-200 hover:bg-gray-800 rounded transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Filter tabs */}
        <div className="flex items-center gap-2 px-6 py-3 border-b border-gray-700">
          <button
            onClick={() => setUnprocessedOnly(true)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              unprocessedOnly
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            Unprocessed ({unprocessedCount})
          </button>
          <button
            onClick={() => setUnprocessedOnly(false)}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              !unprocessedOnly
                ? "bg-indigo-600 text-white"
                : "bg-gray-800 text-gray-400 hover:text-gray-200"
            }`}
          >
            All ({ideas.length})
          </button>
          {processedCount > 0 && (
            <button
              onClick={handleClearProcessed}
              className="ml-auto px-3 py-1 rounded text-sm font-medium text-gray-400 hover:text-red-400 bg-gray-800/50 hover:bg-red-900/20 transition-colors flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Clear
            </button>
          )}
        </div>

        {/* Ideas list */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader className="w-5 h-5 text-indigo-400 animate-spin" />
            </div>
          ) : filteredIdeas.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <Inbox className="w-12 h-12 text-gray-600 mb-4" />
              <p className="text-sm">
                {unprocessedOnly
                  ? "No unprocessed ideas. All caught up!"
                  : "No ideas in inbox yet."}
              </p>
              <p className="text-xs text-gray-500 mt-2">
                Use: showrunner capture "Your idea here"
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredIdeas.map((idea) => (
                <div
                  key={idea.id}
                  className={`p-4 rounded-lg border transition-colors ${
                    idea.processed
                      ? "bg-gray-800/30 border-gray-700/30"
                      : "bg-gray-800/60 border-gray-700"
                  }`}
                >
                  {/* Status indicator & text */}
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 pt-0.5">
                      {idea.processed ? (
                        <Check className="w-5 h-5 text-green-500" />
                      ) : (
                        <div className="w-5 h-5 rounded-full border-2 border-indigo-500 flex items-center justify-center">
                          <div className="w-2 h-2 rounded-full bg-indigo-500" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-100 text-sm leading-relaxed break-words">
                        {idea.text}
                      </p>

                      {/* Tags */}
                      {idea.tags.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {idea.tags.map((tag) => (
                            <Badge
                              key={tag}
                              variant="outline"
                              className="text-xs bg-indigo-500/10 border-indigo-500/30 text-indigo-300"
                            >
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      )}

                      {/* Metadata */}
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-400">
                        <span>{new Date(idea.captured_at).toLocaleDateString()}</span>
                        {idea.converted_to && (
                          <span className="flex items-center gap-1">
                            <ArrowRight className="w-3 h-3" />
                            {idea.converted_to}
                          </span>
                        )}
                      </div>

                      {/* Actions for unprocessed */}
                      {!idea.processed && processingId !== idea.id && (
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={() => setShowContainerInput(idea.id)}
                            className="flex-1 px-3 py-2 bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-medium rounded transition-colors flex items-center justify-center gap-2"
                          >
                            <ArrowRight className="w-4 h-4" />
                            Convert
                          </button>
                          <button
                            onClick={() => handleDiscard(idea.id)}
                            className="flex-1 px-3 py-2 bg-gray-700/50 hover:bg-red-900/30 text-gray-300 hover:text-red-300 text-xs font-medium rounded transition-colors"
                          >
                            Discard
                          </button>
                        </div>
                      )}

                      {/* Processing state */}
                      {processingId === idea.id && (
                        <div className="flex items-center gap-2 mt-3 text-indigo-400 text-xs">
                          <Loader className="w-4 h-4 animate-spin" />
                          Processing...
                        </div>
                      )}

                      {/* Container ID input */}
                      {showContainerInput === idea.id && (
                        <div className="flex gap-2 mt-3">
                          <input
                            type="text"
                            value={containerInput}
                            onChange={(e) => setContainerInput(e.target.value)}
                            placeholder="e.g., idea-zara-twin"
                            className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-xs text-gray-100 placeholder-gray-500 focus:outline-none focus:border-indigo-500/50"
                            onKeyPress={(e) => {
                              if (e.key === "Enter") {
                                handleConvert(idea.id, containerInput);
                              }
                            }}
                            autoFocus
                          />
                          <button
                            onClick={() => {
                              handleConvert(idea.id, containerInput);
                            }}
                            disabled={!containerInput.trim()}
                            className="px-3 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-xs font-medium rounded transition-colors"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setShowContainerInput(null);
                              setContainerInput("");
                            }}
                            className="px-3 py-2 bg-gray-700 hover:bg-gray-600 text-gray-300 text-xs font-medium rounded transition-colors"
                          >
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="border-t border-gray-700 px-6 py-3 bg-gray-800/30 text-xs text-gray-400">
          💡 Use <code className="bg-gray-900 px-2 py-1 rounded">showrunner capture</code> to add ideas from the CLI
        </div>
      </div>
    </div>
  );
}
