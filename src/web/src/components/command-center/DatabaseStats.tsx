"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Database, HardDrive, RefreshCcw } from "lucide-react";

export function DatabaseStats() {
    const [stats, setStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await api.getDBStats();
            setStats(data);
        } catch (err) {
            console.error("Failed to fetch DB stats", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStats();
    }, []);

    if (!stats && loading) {
        return (
            <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 animate-pulse h-32" />
        );
    }

    if (!stats) return null;

    return (
        <div className="bg-gray-900/50 border border-gray-800/80 rounded-lg overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800 bg-gray-900/80">
                <h3 className="text-sm font-medium text-gray-200 flex items-center gap-2">
                    <Database className="w-4 h-4 text-indigo-400" />
                    System Health
                </h3>
                <button
                    onClick={fetchStats}
                    disabled={loading}
                    className="p-1 text-gray-500 hover:text-gray-300 disabled:opacity-50 transition-colors"
                >
                    <RefreshCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                </button>
            </div>
            <div className="p-4 grid grid-cols-2 gap-4">
                <div>
                    <div className="text-xs text-gray-500 mb-1 flex items-center gap-1">
                        <HardDrive className="w-3 h-3" /> Indexed Items
                    </div>
                    <div className="text-xl font-semibold text-gray-100">{stats.total_indexed || 0}</div>
                </div>
                <div>
                    <div className="text-xs text-gray-500 mb-1">YAML Source Files</div>
                    <div className="text-xl font-semibold text-gray-100">{stats.total_yaml_files || 0}</div>
                </div>
                <div className="col-span-2 border-t border-gray-800/50 pt-3 flex items-center justify-between">
                    <div className="text-xs text-gray-500">Sync Metadata Cache</div>
                    <div className="text-xs font-medium text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded-full">
                        {stats.sync_metadata_count || 0} tracking
                    </div>
                </div>
            </div>
        </div>
    );
}
