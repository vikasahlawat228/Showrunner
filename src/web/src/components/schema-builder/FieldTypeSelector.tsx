"use client";

import { useEffect, useRef } from "react";
import {
  Type,
  Hash,
  ToggleLeft,
  Tags,
  Braces,
  List,
  Link,
  CircleDot,
} from "lucide-react";
import { cn } from "@/lib/cn";
import type { FieldType } from "@/lib/api";

interface FieldTypeOption {
  value: FieldType;
  label: string;
  icon: React.ReactNode;
}

const FIELD_TYPES: FieldTypeOption[] = [
  { value: "string", label: "Text", icon: <Type className="w-4 h-4" /> },
  { value: "integer", label: "Number", icon: <Hash className="w-4 h-4" /> },
  {
    value: "float",
    label: "Decimal",
    icon: <CircleDot className="w-4 h-4" />,
  },
  {
    value: "boolean",
    label: "Toggle",
    icon: <ToggleLeft className="w-4 h-4" />,
  },
  {
    value: "list[string]",
    label: "Tags",
    icon: <Tags className="w-4 h-4" />,
  },
  { value: "json", label: "Rich Data", icon: <Braces className="w-4 h-4" /> },
  { value: "enum", label: "Dropdown", icon: <List className="w-4 h-4" /> },
  { value: "reference", label: "Link", icon: <Link className="w-4 h-4" /> },
];

interface FieldTypeSelectorProps {
  current: FieldType;
  onSelect: (type: FieldType) => void;
  onClose: () => void;
}

export function FieldTypeSelector({
  current,
  onSelect,
  onClose,
}: FieldTypeSelectorProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="absolute z-50 mt-1 w-64 p-2 bg-gray-900 border border-gray-700 rounded-lg shadow-xl backdrop-blur-sm"
    >
      <div className="grid grid-cols-2 gap-1.5">
        {FIELD_TYPES.map((ft) => (
          <button
            key={ft.value}
            onClick={() => {
              onSelect(ft.value);
              onClose();
            }}
            className={cn(
              "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-all duration-150",
              current === ft.value
                ? "bg-sky-500/20 text-sky-400 border border-sky-500/30"
                : "text-gray-400 hover:bg-gray-800 hover:text-gray-200 border border-transparent"
            )}
          >
            {ft.icon}
            <span>{ft.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

/** Returns the display label for a FieldType value. */
export function fieldTypeLabel(type: FieldType): string {
  return FIELD_TYPES.find((ft) => ft.value === type)?.label ?? type;
}
