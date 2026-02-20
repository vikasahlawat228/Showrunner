"use client";

import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { User, FileText } from "lucide-react";
import { cn } from "@/lib/cn";

interface SidebarItemProps {
  id: string;
  type: "character" | "scene";
  name: string;
  subtitle?: string;
  selected?: boolean;
  onClick: () => void;
}

export function SidebarItem({ id, type, name, subtitle, selected, onClick }: SidebarItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
  } = useDraggable({
    id: `sidebar-${id}`,
    data: { type, name, id, source: "sidebar" },
  });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  const Icon = type === "character" ? User : FileText;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-md cursor-pointer transition-colors text-sm",
        selected
          ? "bg-blue-600/20 border border-blue-500/30 text-white"
          : "hover:bg-gray-800 text-gray-300"
      )}
    >
      <Icon className="w-4 h-4 shrink-0 text-gray-500" />
      <div className="min-w-0 flex-1">
        <div className="font-medium truncate">{name}</div>
        {subtitle && (
          <div className="text-xs text-gray-500 truncate">{subtitle}</div>
        )}
      </div>
    </div>
  );
}
