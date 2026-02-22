import React from "react";
import { ChatSessionSummary } from "../../lib/store/chatSlice";
import { Activity } from "lucide-react";

interface TokenIndicatorProps {
    session: ChatSessionSummary;
}

export function TokenIndicator({ session }: TokenIndicatorProps) {
    const usageStr = (session.token_usage / 1000).toFixed(1) + "k";
    const budgetStr = (session.context_budget / 1000).toFixed(1) + "k";
    const percent = Math.min(100, (session.token_usage / Math.max(1, session.context_budget)) * 100);

    let colorClass = "bg-emerald-500";
    if (percent > 75) colorClass = "bg-yellow-500";
    if (percent > 90) colorClass = "bg-red-500";

    return (
        <div className="flex flex-col gap-1 w-full mt-1">
            <div className="flex justify-between items-center text-[10px] text-gray-500 font-medium">
                <span className="flex items-center gap-1">
                    <Activity className="w-3 h-3" /> Context Budget
                </span>
                <span>{usageStr} / {budgetStr} tokens</span>
            </div>
            <div className="h-1.5 w-full bg-gray-800 rounded-full overflow-hidden">
                <div
                    className={`h-full ${colorClass} transition-all duration-300`}
                    style={{ width: `${Math.max(2, percent)}%` }}
                />
            </div>
        </div>
    );
}
