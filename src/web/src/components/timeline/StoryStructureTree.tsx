"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import {
    DndContext,
    closestCenter,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    type DragEndEvent,
} from "@dnd-kit/core";
import {
    SortableContext,
    verticalListSortingStrategy,
    useSortable,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { ChevronRight, ChevronDown, GripVertical, FileText, LayoutList, Layers, LayoutTemplate, Plus, Edit, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { api, type StructureNode } from "@/lib/api";
import { useStudioStore } from "@/lib/store";

// ── Icons by type ──────────────────────────────────────────

function getTypeIcon(type: string) {
    switch (type) {
        case "season":
            return <LayoutTemplate className="w-4 h-4 text-emerald-500" />;
        case "arc":
            return <Layers className="w-4 h-4 text-blue-500" />;
        case "chapter":
            return <LayoutList className="w-4 h-4 text-indigo-500" />;
        case "scene":
            return <FileText className="w-4 h-4 text-purple-500" />;
        default:
            return <FileText className="w-4 h-4 text-slate-500" />;
    }
}

const CHILD_TYPES: Record<string, string> = {
    season: "arc",
    arc: "act",
    act: "chapter",
    chapter: "scene",
};

// ── Sortable Tree Item ─────────────────────────────────────

interface SortableTreeItemProps {
    node: StructureNode & { attributes?: Record<string, any> };
    depth: number;
    expandedIds: Set<string>;
    toggleExpand: (id: string) => void;
    onRename: (id: string, newName: string) => void;
    onAddChild: (node: StructureNode) => void;
    onDelete: (node: StructureNode) => void;
    onOpenZen: (id: string) => void;
    childrenNodes?: React.ReactNode;
}

function SortableTreeItem({ node, depth, expandedIds, toggleExpand, onRename, onAddChild, onDelete, onOpenZen, childrenNodes }: SortableTreeItemProps) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({ id: node.id });

    const style = {
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.4 : 1,
    };

    const isExpanded = expandedIds.has(node.id);
    const hasChildren = node.children && node.children.length > 0;

    const [isEditing, setIsEditing] = useState(false);
    const [editValue, setEditValue] = useState(node.name);

    const handleRenameSubmit = () => {
        setIsEditing(false);
        if (editValue.trim() && editValue.trim() !== node.name) {
            onRename(node.id, editValue.trim());
        } else {
            setEditValue(node.name); // revert
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") handleRenameSubmit();
        if (e.key === "Escape") {
            setIsEditing(false);
            setEditValue(node.name);
        }
    };

    const status = node.attributes?.status as string | undefined;
    let borderClass = "border-l-[3px] border-transparent";
    if (status === "complete") borderClass = "border-l-[3px] border-emerald-500";
    else if (status === "in_progress") borderClass = "border-l-[3px] border-amber-500";
    else if (status === "draft") borderClass = "border-l-[3px] border-blue-500";
    else if (node.attributes && "status" in node.attributes) borderClass = "border-l-[3px] border-slate-300 dark:border-slate-700";

    return (
        <div ref={setNodeRef} style={style} className="flex flex-col">
            <div
                className={`flex items-center group py-1.5 px-2 hover:bg-slate-100 dark:hover:bg-slate-800/50 transition-colors ${borderClass}`}
                style={{ paddingLeft: `${depth * 16 + 4}px` }}
            >
                {/* Drag Handle */}
                <div
                    {...attributes}
                    {...listeners}
                    className="cursor-grab opacity-0 group-hover:opacity-100 text-slate-400 hover:text-slate-600 mr-1 p-0.5 rounded transition-opacity"
                >
                    <GripVertical className="w-3.5 h-3.5" />
                </div>

                {/* Expand/Collapse Toggle */}
                <div
                    className={`w-5 h-5 flex items-center justify-center cursor-pointer text-slate-400 hover:text-slate-600 ${!hasChildren ? 'invisible' : ''}`}
                    onClick={(e) => { e.stopPropagation(); toggleExpand(node.id); }}
                >
                    {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                </div>

                {/* Icon */}
                <div className="mr-2 ml-1">
                    {getTypeIcon(node.container_type)}
                </div>

                {/* Name / Editor */}
                {isEditing ? (
                    <input
                        autoFocus
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        onBlur={handleRenameSubmit}
                        onKeyDown={handleKeyDown}
                        className="flex-1 min-w-0 bg-white dark:bg-slate-900 border border-blue-400 rounded px-1.5 py-0.5 text-sm outline-none"
                        onClick={(e) => e.stopPropagation()}
                        onPointerDown={(e) => e.stopPropagation()}
                    />
                ) : (
                    <span
                        className="flex-1 min-w-0 text-sm text-slate-700 dark:text-slate-200 truncate select-none cursor-pointer"
                        onDoubleClick={(e) => {
                            e.stopPropagation();
                            setIsEditing(true);
                        }}
                    >
                        {node.name}
                    </span>
                )}

                {/* Actions */}
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity ml-2">
                    {CHILD_TYPES[node.container_type] && (
                        <button onClick={(e) => { e.stopPropagation(); onAddChild(node); }} className="p-1 text-slate-400 hover:text-blue-500" title={`Add ${CHILD_TYPES[node.container_type]}`}>
                            <Plus className="w-3.5 h-3.5" />
                        </button>
                    )}
                    {node.container_type === "scene" && (
                        <button onClick={(e) => { e.stopPropagation(); onOpenZen(node.id); }} className="p-1 text-slate-400 hover:text-emerald-500" title="Open in Zen Editor">
                            <Edit className="w-3.5 h-3.5" />
                        </button>
                    )}
                    <button onClick={(e) => { e.stopPropagation(); onDelete(node); }} className="p-1 text-slate-400 hover:text-red-500" title="Delete">
                        <Trash2 className="w-3.5 h-3.5" />
                    </button>
                </div>
            </div>

            {/* Render Children if expanded */}
            {isExpanded && hasChildren && (
                <div className="flex flex-col">
                    {childrenNodes}
                </div>
            )}
        </div>
    );
}

// ── Recursive Sortable List ────────────────────────────────

interface SortableListProps {
    items: (StructureNode & { attributes?: Record<string, any> })[];
    depth: number;
    expandedIds: Set<string>;
    toggleExpand: (id: string) => void;
    onRename: (id: string, newName: string) => void;
    onAddChild: (node: StructureNode) => void;
    onDelete: (node: StructureNode) => void;
    onOpenZen: (id: string) => void;
}

function SortableList({ items, depth, expandedIds, toggleExpand, onRename, onAddChild, onDelete, onOpenZen }: SortableListProps) {
    return (
        <SortableContext
            items={items.map(i => i.id)}
            strategy={verticalListSortingStrategy}
        >
            <div className="flex flex-col">
                {items.map((node) => (
                    <SortableTreeItem
                        key={node.id}
                        node={node}
                        depth={depth}
                        expandedIds={expandedIds}
                        toggleExpand={toggleExpand}
                        onRename={onRename}
                        onAddChild={onAddChild}
                        onDelete={onDelete}
                        onOpenZen={onOpenZen}
                        childrenNodes={
                            node.children && node.children.length > 0 ? (
                                <SortableList
                                    items={node.children}
                                    depth={depth + 1}
                                    expandedIds={expandedIds}
                                    toggleExpand={toggleExpand}
                                    onRename={onRename}
                                    onAddChild={onAddChild}
                                    onDelete={onDelete}
                                    onOpenZen={onOpenZen}
                                />
                            ) : null
                        }
                    />
                ))}
            </div>
        </SortableContext>
    );
}

// ── Main Component ─────────────────────────────────────────

export function StoryStructureTree() {
    const activeProjectId = useStudioStore(s => (s as any).activeProjectId || "default");
    const [tree, setTree] = useState<StructureNode[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

    const router = useRouter();
    const [nodeToDelete, setNodeToDelete] = useState<StructureNode | null>(null);

    const loadTree = useCallback(async () => {
        try {
            setLoading(true);
            const data = await api.getProjectStructure();
            // Sort each level by sort_order
            const sortRecursive = (nodes: StructureNode[]): StructureNode[] => {
                const sorted = [...nodes].sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
                return sorted.map(n => ({
                    ...n,
                    children: n.children ? sortRecursive(n.children) : [],
                }));
            };

            const sortedData = sortRecursive(data || []);
            setTree(sortedData);

            // Auto-expand top level items on initial load
            if (sortedData.length > 0 && expandedIds.size === 0) {
                const initialExpanded = new Set<string>();
                sortedData.forEach(node => initialExpanded.add(node.id));
                setExpandedIds(initialExpanded);
            }
        } catch (err: any) {
            setError(err.message || "Failed to load structure");
        } finally {
            setLoading(false);
        }
    }, [activeProjectId, expandedIds.size]);

    useEffect(() => {
        loadTree();
    }, [loadTree]);

    const toggleExpand = useCallback((id: string) => {
        setExpandedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    }, []);

    const handleRename = async (id: string, newName: string) => {
        // Optimistically update
        const updateRecursive = (nodes: StructureNode[]): StructureNode[] => {
            return nodes.map(n => {
                if (n.id === id) return { ...n, name: newName };
                if (n.children) return { ...n, children: updateRecursive(n.children) };
                return n;
            });
        };
        setTree(updateRecursive);

        try {
            await api.updateContainer(id, { name: newName });
        } catch (err: any) {
            console.error("Failed to rename:", err);
            loadTree(); // revert on fail
        }
    };

    const handleAddChild = async (parentNode: StructureNode) => {
        const childType = CHILD_TYPES[parentNode.container_type];
        if (!childType) return;
        const name = prompt(`Enter name for new ${childType}:`);
        if (!name?.trim()) return;

        try {
            await api.createContainer({
                container_type: childType,
                name: name.trim(),
                parent_id: parentNode.id,
                sort_order: (parentNode.children?.length || 0)
            });
            toast.success(`Created ${childType} ${name}`);
            setExpandedIds(prev => new Set(prev).add(parentNode.id));
            loadTree();
        } catch (err: any) {
            toast.error(err.message || "Failed to create container");
        }
    };

    const handleDeleteConfirm = async () => {
        if (!nodeToDelete) return;
        try {
            await api.deleteContainer(nodeToDelete.id);
            toast.success("Deleted successfully");
            loadTree();
        } catch (err: any) {
            toast.error(err.message || "Failed to delete");
        } finally {
            setNodeToDelete(null);
        }
    };

    const handleOpenZen = (id: string) => {
        router.push(`/zen?scene_id=${id}`);
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over || active.id === over.id) return;

        // Find the sibling list that contains active and over
        let activeList: StructureNode[] | null = null;

        const findList = (nodes: StructureNode[]): StructureNode[] | null => {
            if (nodes.some(n => n.id === active.id) && nodes.some(n => n.id === over.id)) {
                return nodes;
            }
            for (const n of nodes) {
                if (n.children) {
                    const found = findList(n.children);
                    if (found) return found;
                }
            }
            return null;
        };

        activeList = findList(tree);

        if (!activeList) {
            // They are not in the same sibling list => reject cross-level drag for now
            return;
        }

        const oldIndex = activeList.findIndex(n => n.id === active.id);
        const newIndex = activeList.findIndex(n => n.id === over.id);

        if (oldIndex === -1 || newIndex === -1) return;

        // Optimistically reorder Locally
        const reorderRecursive = (nodes: StructureNode[]): StructureNode[] => {
            if (nodes === activeList) {
                const newNodes = [...nodes];
                const [moved] = newNodes.splice(oldIndex, 1);
                newNodes.splice(newIndex, 0, moved);
                // Update sort_order for all siblings
                return newNodes.map((n, i) => ({ ...n, sort_order: i }));
            }
            return nodes.map(n => ({
                ...n,
                children: n.children ? reorderRecursive(n.children) : []
            }));
        };

        setTree(reorderRecursive(tree));

        // Sync with API
        try {
            const reorderedNodes = [...activeList];
            const [moved] = reorderedNodes.splice(oldIndex, 1);
            reorderedNodes.splice(newIndex, 0, moved);

            const itemsToReorder = reorderedNodes.map((n, i) => ({ id: n.id, sort_order: i }));
            await api.reorderContainers(itemsToReorder);
        } catch (err) {
            console.error("Failed to reorder:", err);
            toast.error("Failed to save reorder");
            loadTree(); // revert on fail
        }
    };

    const sensors = useSensors(
        useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
        useSensor(KeyboardSensor)
    );

    if (loading && tree.length === 0) {
        return <div className="p-4 text-sm text-slate-500">Loading structure...</div>;
    }

    if (error) {
        return <div className="p-4 text-sm text-red-500">{error}</div>;
    }

    if (tree.length === 0) {
        return (
            <div className="p-8 text-center text-sm text-slate-500">
                <p>No story structure found.</p>
                <p className="text-xs mt-1">Create seasons, arcs, or chapters to see them here.</p>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full w-full bg-slate-50/50 dark:bg-slate-900 overflow-y-auto override-scrollbar">
            <div className="sticky top-0 z-10 p-4 pb-2 bg-slate-50/90 dark:bg-slate-900/90 backdrop-blur border-b border-slate-200 dark:border-slate-800 flex justify-between items-center">
                <div>
                    <h2 className="text-sm font-semibold text-slate-800 dark:text-slate-200 leading-tight">Story Structure</h2>
                    <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">Drag to reorder siblings. Double-click to rename.</p>
                </div>
                <button
                    onClick={() => handleAddChild({ id: 'root', container_type: 'root' } as any)}
                    className="p-1.5 text-slate-400 hover:text-emerald-500 hover:bg-emerald-50 dark:hover:bg-slate-800 rounded-md transition-colors"
                >
                    <Plus className="w-4 h-4" />
                </button>
            </div>

            <div className="p-2">
                <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
                    <SortableList
                        items={tree as any}
                        depth={0}
                        expandedIds={expandedIds}
                        toggleExpand={toggleExpand}
                        onRename={handleRename}
                        onAddChild={handleAddChild}
                        onDelete={setNodeToDelete}
                        onOpenZen={handleOpenZen}
                    />
                </DndContext>
            </div>

            <ConfirmDialog
                isOpen={!!nodeToDelete}
                title="Delete Container"
                message={`Are you sure you want to delete ${nodeToDelete?.name}? This action cannot be undone.`}
                onConfirm={handleDeleteConfirm}
                onCancel={() => setNodeToDelete(null)}
                variant="danger"
            />
        </div>
    );
}
