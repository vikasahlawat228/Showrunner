"use client";

import { useCallback } from "react";
import { Plus, Save, Loader2 } from "lucide-react";
import type { ContainerSchema, FieldDefinition } from "@/lib/api";
import { FieldRow } from "./FieldRow";
import { NLWizardInput } from "./NLWizardInput";
import { SchemaPreview } from "./SchemaPreview";

interface SchemaEditorProps {
  schema: ContainerSchema;
  schemaNames: string[];
  saving: boolean;
  onChange: (schema: ContainerSchema) => void;
  onSave: () => void;
}

function toSnakeCase(str: string): string {
  return str
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function makeFieldId(): string {
  return `f_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

export function SchemaEditor({
  schema,
  schemaNames,
  saving,
  onChange,
  onSave,
}: SchemaEditorProps) {
  function updateSchema(patch: Partial<ContainerSchema>) {
    onChange({ ...schema, ...patch });
  }

  function handleDisplayNameChange(display_name: string) {
    updateSchema({
      display_name,
      name: toSnakeCase(display_name),
    });
  }

  function updateField(idx: number, updated: FieldDefinition) {
    const fields = [...schema.fields];
    fields[idx] = updated;
    updateSchema({ fields });
  }

  function deleteField(idx: number) {
    updateSchema({ fields: schema.fields.filter((_, i) => i !== idx) });
  }

  function addField() {
    const newField: FieldDefinition = {
      id: makeFieldId(),
      name: "",
      field_type: "string",
      required: false,
    };
    updateSchema({ fields: [...schema.fields, newField] });
  }

  const handleFieldsGenerated = useCallback(
    (fields: FieldDefinition[]) => {
      const withIds = fields.map((f) => ({
        ...f,
        id: f.id || makeFieldId(),
      }));
      updateSchema({ fields: [...schema.fields, ...withIds] });
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [schema.fields]
  );

  const isNew = !schema.created_at;
  const hasName = schema.display_name.trim().length > 0;

  return (
    <div className="flex h-full">
      {/* Editor panel */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-800 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              {/* Display name */}
              <input
                type="text"
                value={schema.display_name}
                onChange={(e) => handleDisplayNameChange(e.target.value)}
                placeholder="Schema Name"
                className="w-full bg-transparent text-xl font-bold text-gray-100 placeholder-gray-600 focus:outline-none"
              />

              {/* Derived name */}
              {schema.display_name && (
                <p className="text-xs text-gray-600 font-mono">
                  {schema.name || "..."}
                </p>
              )}

              {/* Description */}
              <textarea
                value={schema.description ?? ""}
                onChange={(e) =>
                  updateSchema({
                    description: e.target.value || undefined,
                  })
                }
                placeholder="Describe this container type..."
                rows={2}
                className="w-full bg-transparent text-sm text-gray-400 placeholder-gray-700 resize-none focus:outline-none border-b border-gray-800 focus:border-gray-600 transition-colors"
              />
            </div>

            {/* Save button */}
            <button
              onClick={onSave}
              disabled={saving || !hasName}
              className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Save className="w-4 h-4" />
              )}
              {isNew ? "Create" : "Save"}
            </button>
          </div>

          {/* NL Wizard */}
          <NLWizardInput
            schemaNames={schemaNames}
            onFieldsGenerated={handleFieldsGenerated}
          />
        </div>

        {/* Field list */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Fields ({schema.fields.length})
            </h3>
          </div>

          {schema.fields.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-600">
              <p className="text-sm mb-1">No fields yet</p>
              <p className="text-xs">
                Add fields manually or use the AI generator above
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {schema.fields.map((field, idx) => (
                <FieldRow
                  key={field.id}
                  field={field}
                  schemaNames={schemaNames}
                  onChange={(updated) => updateField(idx, updated)}
                  onDelete={() => deleteField(idx)}
                />
              ))}
            </div>
          )}

          {/* Add field */}
          <button
            onClick={addField}
            className="mt-3 flex items-center gap-1.5 px-3 py-2 rounded-lg border border-dashed border-gray-700 text-gray-500 text-sm hover:border-gray-600 hover:text-gray-400 transition-colors w-full justify-center"
          >
            <Plus className="w-3.5 h-3.5" />
            Add Field
          </button>
        </div>
      </div>

      {/* YAML Preview sidebar */}
      <div className="w-72 border-l border-gray-800 bg-gray-950/50 hidden lg:flex flex-col">
        <SchemaPreview schema={schema} />
      </div>
    </div>
  );
}
