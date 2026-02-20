"use client";

import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { FieldDefinition } from "@/lib/api";

interface NLWizardInputProps {
  schemaNames: string[];
  onFieldsGenerated: (fields: FieldDefinition[]) => void;
}

export function NLWizardInput({
  schemaNames,
  onFieldsGenerated,
}: NLWizardInputProps) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await api.generateFields({
        prompt: prompt.trim(),
        existing_schemas: schemaNames,
      });
      onFieldsGenerated(result.fields);
      setPrompt("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Generation failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleGenerate();
          }}
          placeholder='Describe your schema, e.g. "A spell with mana cost, element type, and cooldown"'
          className="flex-1 bg-gray-900/50 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-sky-500 focus:outline-none transition-colors"
        />
        <button
          onClick={handleGenerate}
          disabled={!prompt.trim() || loading}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-gradient-to-r from-sky-600 to-emerald-600 text-white text-sm font-medium hover:from-sky-500 hover:to-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200"
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Sparkles className="w-4 h-4" />
          )}
          Generate Fields
        </button>
      </div>
      {error && (
        <p className="text-xs text-red-400">{error}</p>
      )}
    </div>
  );
}
