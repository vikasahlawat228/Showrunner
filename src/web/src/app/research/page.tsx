"use client";

import React, { useState, useEffect } from "react";
import { Search, Plus, Loader2, Sparkles, AlertCircle } from "lucide-react";
import { ResearchTopicCard } from "@/components/research/ResearchTopicCard";
import { ResearchDetailPanel } from "@/components/research/ResearchDetailPanel";
import { api, ResearchResult } from "@/lib/api";

export default function ResearchPage() {
    const [topics, setTopics] = useState<ResearchResult[]>([]);
    const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState("");

    // New query state
    const [newQuery, setNewQuery] = useState("");
    const [isQuerying, setIsQuerying] = useState(false);
    const [queryError, setQueryError] = useState<string | null>(null);

    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchLibrary = async () => {
        setIsLoading(true);
        try {
            const resp = await api.getResearchLibrary();
            setTopics(resp.items);
            if (resp.items.length > 0 && !selectedTopicId) {
                setSelectedTopicId(resp.items[0].id);
            }
        } catch (err: any) {
            setError(err.message || "Failed to load research library");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchLibrary();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const handleQuery = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newQuery.trim() || isQuerying) return;

        setIsQuerying(true);
        setQueryError(null);
        try {
            const result = await api.queryResearch(newQuery);
            setTopics(prev => [result, ...prev]);
            setSelectedTopicId(result.id);
            setNewQuery("");
        } catch (err: any) {
            setQueryError(err.message || "Failed to execute research query");
        } finally {
            setIsQuerying(false);
        }
    };

    const filteredTopics = topics.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.summary.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const selectedTopic = topics.find(t => t.id === selectedTopicId) || null;

    return (
        <div className="flex flex-col h-full overflow-hidden bg-gray-950">
            {/* Header */}
            <header className="px-6 py-4 border-b border-gray-800 flex items-center justify-between shrink-0 bg-gray-900/50 backdrop-blur-md z-10">
                <div>
                    <h1 className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-emerald-400" />
                        Research Agent Library
                    </h1>
                    <p className="text-xs text-gray-500 mt-1">
                        Query the AI agent or browse saved topic deep-dives
                    </p>
                </div>
            </header>

            <div className="flex flex-1 overflow-hidden">
                {/* Left Panel: Library List */}
                <div className="w-80 flex flex-col border-r border-gray-800 bg-gray-900/30">
                    <div className="p-4 border-b border-gray-800/50">
                        <div className="relative">
                            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                            <input
                                type="text"
                                placeholder="Search research..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-9 pr-4 py-2 bg-gray-900 border border-gray-800 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/50 transition-all placeholder:text-gray-600"
                            />
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto">
                        {isLoading ? (
                            <div className="p-8 flex items-center justify-center">
                                <Loader2 className="w-6 h-6 animate-spin text-gray-600" />
                            </div>
                        ) : error ? (
                            <div className="p-6 text-center text-sm text-red-400">
                                <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                {error}
                            </div>
                        ) : filteredTopics.length === 0 ? (
                            <div className="p-8 text-center">
                                <div className="w-12 h-12 rounded-full bg-gray-800/50 flex items-center justify-center mx-auto mb-3">
                                    <Search className="w-5 h-5 text-gray-500" />
                                </div>
                                <h3 className="text-sm font-medium text-gray-400 mb-1">No research found</h3>
                                <p className="text-xs text-gray-600">Try a different search or query new topics below.</p>
                            </div>
                        ) : (
                            <div className="divide-y divide-gray-800/30">
                                {filteredTopics.map((topic) => (
                                    <ResearchTopicCard
                                        key={topic.id}
                                        topic={topic}
                                        isSelected={selectedTopicId === topic.id}
                                        onClick={() => setSelectedTopicId(topic.id)}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* New Query Bar (Bottom Left) */}
                    <div className="p-4 bg-gray-900 border-t border-gray-800">
                        <form onSubmit={handleQuery} className="relative">
                            <input
                                type="text"
                                placeholder="Ask the Research Agent..."
                                value={newQuery}
                                onChange={(e) => setNewQuery(e.target.value)}
                                disabled={isQuerying}
                                className="w-full pl-4 pr-12 py-3 bg-gray-950 border border-gray-700 rounded-xl text-sm text-gray-200 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 transition-all placeholder:text-gray-500 disabled:opacity-50"
                            />
                            <button
                                type="submit"
                                disabled={!newQuery.trim() || isQuerying}
                                className="absolute right-2 top-1/2 -translate-y-1/2 p-2 rounded-lg bg-emerald-500 text-white disabled:opacity-50 disabled:bg-gray-700 transition-colors"
                                title="Run Deep Dive"
                            >
                                {isQuerying ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <Plus className="w-4 h-4" />
                                )}
                            </button>
                        </form>
                        {queryError && (
                            <p className="text-xs text-red-400 mt-2 px-1">{queryError}</p>
                        )}
                        {isQuerying && (
                            <div className="mt-3 flex items-center gap-2 text-xs text-emerald-400/80 px-1 animate-pulse">
                                <span>Agent is researching...</span>
                                <div className="flex-1 h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-emerald-500/50 w-1/3 animate-[slide_1s_ease-in-out_infinite_alternate]" />
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel: Detail View */}
                {selectedTopic ? (
                    <ResearchDetailPanel
                        topic={selectedTopic}
                        onDeleted={() => {
                            fetchLibrary();
                            setSelectedTopicId(null);
                        }}
                    />
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center bg-gray-900/50 text-center p-8">
                        <div className="w-24 h-24 rounded-full bg-gray-800 flex items-center justify-center mb-6">
                            <Sparkles className="w-10 h-10 text-emerald-500/50" />
                        </div>
                        <h2 className="text-xl font-bold text-gray-300 mb-2">Research Library</h2>
                        <p className="text-sm text-gray-500 max-w-md leading-relaxed">
                            Select a topic from the left to view the detailed findings, or use the query input to execute a new deep-dive with the research agent.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
