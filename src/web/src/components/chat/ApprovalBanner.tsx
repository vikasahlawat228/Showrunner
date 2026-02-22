import React from "react";
import { AlertTriangle, Check, X } from "lucide-react";

export interface ApprovalData {
    intent?: string;
    params?: any;
    message?: string;
}

interface ApprovalBannerProps {
    data: ApprovalData;
    onApprove: () => void;
    onReject: () => void;
}

export function ApprovalBanner({ data, onApprove, onReject }: ApprovalBannerProps) {
    return (
        <div className="bg-yellow-900/30 border border-yellow-700/50 rounded-lg p-3 my-2 shadow-inner">
            <div className="flex items-start gap-3">
                <div className="mt-0.5">
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                </div>
                <div className="flex-1 min-w-0">
                    <h4 className="text-sm font-semibold text-yellow-400">Approval Required</h4>
                    <p className="text-sm text-yellow-200/80 mt-1">
                        {data.message || `Action ${data.intent || 'requested'} requires your approval.`}
                    </p>

                    {data.params && Object.keys(data.params).length > 0 && (
                        <div className="mt-2 text-xs text-yellow-300/60 bg-black/20 rounded p-2 overflow-x-auto">
                            <pre>{JSON.stringify(data.params, null, 2)}</pre>
                        </div>
                    )}

                    <div className="flex gap-2 mt-3">
                        <button
                            onClick={onApprove}
                            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded text-xs font-semibold transition-colors"
                        >
                            <Check className="w-4 h-4" />
                            Approve
                        </button>
                        <button
                            onClick={onReject}
                            className="flex items-center justify-center gap-1.5 px-3 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded text-xs font-semibold transition-colors"
                        >
                            <X className="w-4 h-4" />
                            Reject
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
