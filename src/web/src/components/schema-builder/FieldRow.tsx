"use client";

import { useState } from "react";
import { Trash2, Star, ChevronDown, X } from "lucide-react";
import { cn } from "@/lib/cn";
import type { FieldDefinition, FieldType } from "@/lib/api";
import { FieldTypeSelector, fieldTypeLabel } from "./FieldTypeSelector";

interface FieldRowProps {
  field: FieldDefinition;
  schemaNames: string[];
  onChange: (updated: FieldDefinition) => void;
  onDelete: () => void;
}

export function FieldRow({
  field,
  schemaNames,
  onChange,
  onDelete,
}: FieldRowProps) {
  const [showTypePicker, setShowTypePicker] = useState(false);
  const [tagInput, setTagInput] = useState("");

  function update(patch: Partial<FieldDefinition>) {
    onChange({ ...field, ...patch });
  }

  function handleTypeChange(type: FieldType) {
    const patch: Partial<FieldDefinition> = { field_type: type };
    if (type !== "enum") patch.options = undefined;
    if (type !== "reference") patch.target_type = undefined;
    if (type === "enum" && !field.options) patch.options = [];
    update(patch);
  }

  function addOption(value: string) {
    const trimmed = value.trim();
    if (!trimmed || field.options?.includes(trimmed)) return;
    update({ options: [...(field.options ?? []), trimmed] });
  }

  function removeOption(idx: number) {
    update({ options: (field.options ?? []).filter((_, i) => i !== idx) });
  }

  function handleTagKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addOption(tagInput);
      setTagInput("");
    }
  }

  return (
    <div className="group rounded-lg border border-gray-800 bg-gray-900/50 p-3 transition-all duration-150 hover:border-gray-700">
      {/* Main row */}
      <div className="flex items-center gap-2">
        {/* Name */}
        <input
          type="text"
          value={field.name}
          onChange={(e) => update({ name: e.target.value })}
          placeholder="field_name"
          className="w-36 bg-transparent border-b border-gray-700 px-1 py-0.5 text-sm text-gray-200 placeholder-gray-600 focus:border-sky-500 focus:outline-none transition-colors font-mono"
        />

        {/* Type badge */}
        <div className="relative">
          <button
            onClick={() => setShowTypePicker(!showTypePicker)}
            className={cn(
              "flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-colors",
              "bg-gray-800 text-gray-300 hover:bg-gray-700 hover:text-gray-100"
            )}
          >
            {fieldTypeLabel(field.field_type)}
            <ChevronDown className="w-3 h-3" />
          </button>
          {showTypePicker && (
            <FieldTypeSelector
              current={field.field_type}
              onSelect={handleTypeChange}
              onClose={() => setShowTypePicker(false)}
            />
          )}
        </div>

        {/* Required toggle */}
        <button
          onClick={() => update({ required: !field.required })}
          title={field.required ? "Required" : "Optional"}
          className={cn(
            "p-1 rounded transition-colors",
            field.required
              ? "text-amber-400 hover:text-amber-300"
              : "text-gray-600 hover:text-gray-400"
          )}
        >
          <Star
            className="w-3.5 h-3.5"
            fill={field.required ? "currentColor" : "none"}
          />
        </button>

        {/* Description */}
        <input
          type="text"
          value={field.description ?? ""}
          onChange={(e) => update({ description: e.target.value || undefined })}
          placeholder="Description..."
          className="flex-1 bg-transparent border-b border-gray-800 px-1 py-0.5 text-sm text-gray-400 placeholder-gray-700 focus:border-gray-600 focus:outline-none transition-colors"
        />

        {/* Delete */}
        <button
          onClick={onDelete}
          className="p-1 rounded text-gray-700 hover:text-red-400 hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all"
        >
          <Trash2 className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Enum options */}
      {field.field_type === "enum" && (
        <div className="mt-2 pl-1">
          <div className="flex flex-wrap gap-1 mb-1.5">
            {(field.options ?? []).map((opt, i) => (
              <span
                key={i}
                className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-900/30 text-emerald-400 text-xs border border-emerald-800/40"
              >
                {opt}
                <button
                  onClick={() => removeOption(i)}
                  className="hover:text-emerald-200"
                >
                  <X className="w-2.5 h-2.5" />
                </button>
              </span>
            ))}
          </div>
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleTagKeyDown}
            onBlur={() => {
              if (tagInput.trim()) {
                addOption(tagInput);
                setTagInput("");
              }
            }}
            placeholder="Add option, press Enter..."
            className="w-48 bg-transparent border-b border-gray-800 px-1 py-0.5 text-xs text-gray-400 placeholder-gray-700 focus:border-emerald-600 focus:outline-none transition-colors"
          />
        </div>
      )}

      {/* Reference target */}
      {field.field_type === "reference" && (
        <div className="mt-2 pl-1 flex items-center gap-2">
          <span className="text-xs text-gray-500">Target:</span>
          <select
            value={field.target_type ?? ""}
            onChange={(e) =>
              update({ target_type: e.target.value || undefined })
            }
            className="bg-gray-800 border border-gray-700 rounded px-2 py-0.5 text-xs text-gray-300 focus:border-sky-500 focus:outline-none transition-colors"
          >
            <option value="">Select schema...</option>
            {schemaNames.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
