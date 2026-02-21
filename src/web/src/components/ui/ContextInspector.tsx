"use client";

import React, { useState } from "react";
import {
  ChevronDown,
  ChevronRight,
  Brain,
  Database,
  Cpu,
  Hash,
  Eye,
  EyeOff,
} from "lucide-react";

export interface ContextBucket {
  id: string;
  name: string;
  type: string;
  summary: string;
}

export interface AIOperationContext {
  agentName: string;
  agentId: string;
  modelUsed: string;
  contextBuckets: ContextBucket[];
  tokenCount?: number;
  promptPreview?: string;
}

interface ContextInspectorProps {
  operation: AIOperationContext | null;
  className?: string;
}

export function ContextInspector({ operation, className = "" }: ContextInspectorProps) {
  const [expanded, setExpanded] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);

  if (!operation) return null;

  return (
    <div className={`bg-gray-900/80 border border-gray-800 rounded-lg overflow-hidden ${className}`}>
      {/* Header — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-gray-800/50 transition-colors"
      >
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <Eye className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-medium text-gray-300">Glass Box</span>
          <span className="text-gray-600">|</span>
          <span className="text-indigo-400">{operation.agentName}</span>
          <span className="text-gray-600">|</span>
          <Cpu className="w-3 h-3" />
          <span>{operation.modelUsed}</span>
          {operation.tokenCount && (
            <>
              <span className="text-gray-600">|</span>
              <Hash className="w-3 h-3" />
              <span>{operation.tokenCount.toLocaleString()} tokens</span>
            </>
          )}
        </div>
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-500" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
        )}
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-3 pb-3 space-y-3 border-t border-gray-800/50">
          {/* Agent info */}
          <div className="pt-2">
            <div className="flex items-center gap-2 text-xs mb-1">
              <Brain className="w-3.5 h-3.5 text-purple-400" />
              <span className="font-medium text-gray-300">Agent</span>
            </div>
            <div className="ml-5 text-xs text-gray-400">
              <span className="text-purple-300">{operation.agentName}</span>
              <span className="text-gray-600 ml-2">({operation.agentId})</span>
            </div>
          </div>

          {/* Model info */}
          <div>
            <div className="flex items-center gap-2 text-xs mb-1">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-medium text-gray-300">Model</span>
            </div>
            <div className="ml-5 text-xs">
              <span className="px-2 py-0.5 rounded bg-emerald-900/30 border border-emerald-800/50 text-emerald-300">
                {operation.modelUsed}
              </span>
              {operation.tokenCount && (
                <span className="ml-2 text-gray-500">
                  {operation.tokenCount.toLocaleString()} tokens used
                </span>
              )}
            </div>
          </div>

          {/* Context buckets */}
          {operation.contextBuckets.length > 0 && (
            <div>
              <div className="flex items-center gap-2 text-xs mb-2">
                <Database className="w-3.5 h-3.5 text-amber-400" />
                <span className="font-medium text-gray-300">
                  Context Injected ({operation.contextBuckets.length} buckets)
                </span>
              </div>
              <div className="ml-5 space-y-1.5">
                {operation.contextBuckets.map((bucket) => (
                  <div
                    key={bucket.id}
                    className="flex items-start gap-2 text-xs p-1.5 rounded bg-gray-800/40"
                  >
                    <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-gray-800 text-gray-500 uppercase shrink-0">
                      {bucket.type}
                    </span>
                    <div className="min-w-0">
                      <div className="text-gray-300 font-medium truncate">
                        {bucket.name}
                      </div>
                      {bucket.summary && (
                        <div className="text-gray-500 truncate">
                          {bucket.summary}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Prompt preview */}
          {operation.promptPreview && (
            <div>
              <button
                onClick={() => setShowPrompt(!showPrompt)}
                className="flex items-center gap-2 text-xs mb-1 hover:text-gray-200 transition-colors"
              >
                {showPrompt ? (
                  <EyeOff className="w-3.5 h-3.5 text-gray-500" />
                ) : (
                  <Eye className="w-3.5 h-3.5 text-gray-500" />
                )}
                <span className="font-medium text-gray-300">
                  {showPrompt ? "Hide Prompt" : "Show Prompt"}
                </span>
              </button>
              {showPrompt && (
                <pre className="ml-5 text-[11px] text-gray-500 bg-gray-950 border border-gray-800 rounded p-2 max-h-48 overflow-auto whitespace-pre-wrap font-mono">
                  {operation.promptPreview}
                </pre>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
