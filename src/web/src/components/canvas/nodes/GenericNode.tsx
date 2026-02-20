import React, { memo } from "react";
import { Handle, Position } from "@xyflow/react";
import { useStudioStore } from "@/lib/store";

interface GenericNodeData {
    label: string;
    containerType: string;
    payload: any;
}

const GenericNode = ({ data, id }: { data: GenericNodeData; id: string }) => {
    const { selectItem, selectedItem } = useStudioStore();
    const isSelected = selectedItem?.id === id;

    let bgColor = "bg-slate-800";
    let icon = "📦";

    if (data.containerType === "character") {
        bgColor = "bg-blue-900";
        icon = "👤";
    } else if (data.containerType === "scene") {
        bgColor = "bg-emerald-900";
        icon = "🎬";
    } else if (data.containerType === "world" || data.containerType === "location") {
        bgColor = "bg-amber-900";
        icon = "🌍";
    } else if (data.containerType === "faction") {
        bgColor = "bg-purple-900";
        icon = "🛡️";
    }

    return (
        <div
            onClick={() => selectItem({ id, type: data.containerType as any, name: data.label })}
            className={`relative rounded-lg shadow-xl border-2 transition-all cursor-pointer ${isSelected ? "border-sky-400 ring-2 ring-sky-400/50 shadow-sky-500/20" : "border-slate-700 hover:border-slate-500"
                } ${bgColor}`}
            style={{ width: "220px" }}
        >
            <Handle type="target" position={Position.Left} className="w-3 h-3 bg-slate-400" />

            <div className="p-3">
                <div className="flex items-center gap-2 mb-2">
                    <span className="text-xl">{icon}</span>
                    <h3 className="text-sm font-semibold text-white truncate" title={data.label}>
                        {data.label}
                    </h3>
                </div>

                <div className="text-xs text-slate-300">
                    <span className="uppercase tracking-wider font-mono opacity-60 text-[10px]">
                        {data.containerType}
                    </span>
                </div>
            </div>

            {/* Node specific dynamic details based on schema */}
            <div className="px-3 pb-3 text-xs text-slate-400">
                {data.containerType === "character" && data.payload.role && (
                    <p className="truncate">Role: {data.payload.role}</p>
                )}
                {data.containerType === "scene" && data.payload.setting && (
                    <p className="truncate">Loc: {data.payload.setting}</p>
                )}
            </div>

            <Handle type="source" position={Position.Right} className="w-3 h-3 bg-slate-400" />
        </div>
    );
};

export default memo(GenericNode);
