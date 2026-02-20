"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Database,
  Plus,
  Loader2,
  Trash2,
} from "lucide-react";
import { cn } from "@/lib/cn";
import { api } from "@/lib/api";
import type { ContainerSchema } from "@/lib/api";
import { SchemaEditor } from "./SchemaEditor";

function makeEmptySchema(): ContainerSchema {
  return {
    id: `new_${Date.now()}`,
    name: "",
    display_name: "",
    description: "",
    fields: [],
  };
}

export function SchemaBuilderPanel() {
  const [schemas, setSchemas] = useState<ContainerSchema[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<ContainerSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const schemaNames = schemas.map((s) => s.name).filter(Boolean);

  // Fetch schemas on mount
  const fetchSchemas = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getSchemas();
      setSchemas(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load schemas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSchemas();
  }, [fetchSchemas]);

  // Select a schema for editing
  function selectSchema(schema: ContainerSchema) {
    setSelectedId(schema.id);
    setDraft({ ...schema, fields: schema.fields.map((f) => ({ ...f })) });
    setError(null);
  }

  // Create new schema
  function handleNew() {
    const empty = makeEmptySchema();
    setSelectedId(empty.id);
    setDraft(empty);
    setError(null);
  }

  // Save schema (create or update)
  async function handleSave() {
    if (!draft) return;
    setSaving(true);
    setError(null);
    try {
      const isNew = !draft.created_at;
      let saved: ContainerSchema;
      if (isNew) {
        saved = await api.createSchema({
          name: draft.name,
          display_name: draft.display_name,
          description: draft.description,
          fields: draft.fields,
        });
      } else {
        saved = await api.updateSchema(draft.id, {
          name: draft.name,
          display_name: draft.display_name,
          description: draft.description,
          fields: draft.fields,
        });
      }
      setDraft(saved);
      setSelectedId(saved.id);
      await fetchSchemas();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  // Delete schema
  async function handleDelete(id: string) {
    try {
      await api.deleteSchema(id);
      if (selectedId === id) {
        setSelectedId(null);
        setDraft(null);
      }
      await fetchSchemas();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    }
  }

  return (
    <div className="flex h-full bg-gray-950 text-gray-100">
      {/* Left sidebar — Schema list */}
      <aside className="w-64 border-r border-gray-800 flex flex-col bg-gray-900/50 shrink-0">
        <div className="px-4 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <Database className="w-4 h-4 text-sky-400" />
            <h2 className="text-sm font-semibold text-gray-200">
              Schema Builder
            </h2>
          </div>
        </div>

        {/* Schema list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-600 animate-spin" />
            </div>
          ) : schemas.length === 0 ? (
            <p className="text-xs text-gray-600 text-center py-8">
              No schemas yet
            </p>
          ) : (
            schemas.map((s) => (
              <div
                key={s.id}
                className={cn(
                  "group flex items-center justify-between rounded-md px-3 py-2 cursor-pointer transition-colors",
                  selectedId === s.id
                    ? "bg-sky-500/10 text-sky-400"
                    : "text-gray-400 hover:bg-gray-800 hover:text-gray-200"
                )}
              >
                <button
                  onClick={() => selectSchema(s)}
                  className="flex-1 text-left"
                >
                  <p className="text-sm font-medium truncate">
                    {s.display_name}
                  </p>
                  <p className="text-xs text-gray-600 font-mono truncate">
                    {s.fields.length} field{s.fields.length !== 1 ? "s" : ""}
                  </p>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(s.id);
                  }}
                  className="p-1 rounded text-gray-700 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            ))
          )}
        </div>

        {/* New schema button */}
        <div className="p-3 border-t border-gray-800">
          <button
            onClick={handleNew}
            className="flex items-center justify-center gap-1.5 w-full px-3 py-2 rounded-lg border border-dashed border-gray-700 text-gray-500 text-sm hover:border-sky-600 hover:text-sky-400 transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            New Schema
          </button>
        </div>
      </aside>

      {/* Right panel — Editor or empty state */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Error banner */}
        {error && (
          <div className="mx-6 mt-3 p-3 bg-red-900/30 border border-red-800 rounded-lg text-red-300 text-sm flex justify-between items-center shrink-0">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-200 ml-4 text-xs"
            >
              Dismiss
            </button>
          </div>
        )}

        {draft ? (
          <SchemaEditor
            schema={draft}
            schemaNames={schemaNames}
            saving={saving}
            onChange={setDraft}
            onSave={handleSave}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-gray-600">
            <Database className="w-12 h-12 mb-4 text-gray-800" />
            <p className="text-lg font-medium text-gray-500">
              Select or create a schema
            </p>
            <p className="text-sm mt-1">
              Define custom container types for your story world
            </p>
            <button
              onClick={handleNew}
              className="mt-6 flex items-center gap-1.5 px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-500 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Schema
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
