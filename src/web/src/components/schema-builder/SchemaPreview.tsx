"use client";

import { useMemo } from "react";
import { FileCode } from "lucide-react";
import yaml from "js-yaml";
import type { ContainerSchema } from "@/lib/api";

interface SchemaPreviewProps {
  schema: Omit<ContainerSchema, "id" | "created_at" | "updated_at">;
}

export function SchemaPreview({ schema }: SchemaPreviewProps) {
  const yamlText = useMemo(() => {
    const doc = {
      name: schema.name,
      display_name: schema.display_name,
      ...(schema.description ? { description: schema.description } : {}),
      fields: schema.fields.map((f) => {
        const field: Record<string, unknown> = {
          name: f.name,
          field_type: f.field_type,
          required: f.required,
        };
        if (f.description) field.description = f.description;
        if (f.options?.length) field.options = f.options;
        if (f.target_type) field.target_type = f.target_type;
        if (f.default !== undefined && f.default !== null)
          field.default = f.default;
        return field;
      }),
    };
    return yaml.dump(doc, { indent: 2, lineWidth: 80, noRefs: true });
  }, [schema]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-2 px-3 py-2 border-b border-gray-800">
        <FileCode className="w-3.5 h-3.5 text-gray-500" />
        <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
          YAML Preview
        </span>
      </div>
      <pre className="flex-1 overflow-auto p-3 text-xs text-gray-400 font-mono leading-relaxed">
        {yamlText}
      </pre>
    </div>
  );
}
