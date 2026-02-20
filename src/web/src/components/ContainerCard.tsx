"use client";

import React from "react";
import { useDraggable, useDroppable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";
import { FileText, User } from "lucide-react";

interface ContainerCardProps {
  id: string;
  type: "character" | "scene";
  title: string;
  subtitle?: string;
  metadata?: string;
  characterCount?: number;
}

export function ContainerCard({
  id,
  type,
  title,
  subtitle,
  metadata,
  characterCount,
}: ContainerCardProps) {
  const {
    attributes,
    listeners,
    setNodeRef: setDragRef,
    transform,
  } = useDraggable({ id, data: { type, title, id } });

  const { setNodeRef: setDropRef, isOver } = useDroppable({
    id,
    data: { type, title, id },
    disabled: type !== "scene",
  });

  const style = transform
    ? { transform: CSS.Translate.toString(transform) }
    : undefined;

  const icon =
    type === "character" ? (
      <User className="w-5 h-5" />
    ) : (
      <FileText className="w-5 h-5" />
    );

  const color =
    isOver && type === "scene"
      ? "bg-purple-600 border-purple-400 ring-4 ring-purple-400"
      : type === "character"
        ? "bg-blue-900 border-blue-700 hover:bg-blue-800"
        : "bg-purple-900 border-purple-700 hover:bg-purple-800";

  return (
    <div
      ref={(node) => {
        setDragRef(node);
        if (type === "scene") setDropRef(node);
      }}
      style={style}
      {...listeners}
      {...attributes}
      className={`p-4 rounded-lg border-2 cursor-grab active:cursor-grabbing shadow-lg transition-all ${color}`}
    >
      <div className="flex items-center gap-2 mb-1 text-white/90">
        {icon}
        <span className="font-bold text-lg">{title}</span>
      </div>

      {subtitle && (
        <p className="text-white/60 text-sm mb-1">{subtitle}</p>
      )}

      {metadata && (
        <p className="text-white/40 text-xs">{metadata}</p>
      )}

      {type === "scene" && characterCount !== undefined && characterCount > 0 && (
        <div className="mt-2 text-xs bg-purple-950/50 px-2 py-1 rounded inline-block">
          {characterCount} {characterCount === 1 ? "Character" : "Characters"}
        </div>
      )}
    </div>
  );
}
