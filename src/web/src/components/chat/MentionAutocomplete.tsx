import React, { useEffect, useState, useRef } from "react";
import { api, ContainerSearchResult } from "@/lib/api";
import { User, Image as ImageIcon, Map, Building, Hash, Loader2 } from "lucide-react";

interface MentionAutocompleteProps {
    query: string;
    onSelect: (entityId: string, entityName: string) => void;
    activeIndex: number;
}

const getIconForType = (type: string) => {
    switch (type) {
        case "character": return User;
        case "scene": return ImageIcon;
        case "location": return Map;
        case "faction": return Building;
        default: return Hash;
    }
};

export function MentionAutocomplete({ query, onSelect, activeIndex }: MentionAutocompleteProps) {
    const [results, setResults] = useState<ContainerSearchResult[]>([]);
    const [loading, setLoading] = useState(false);

    // Debounce the search query
    useEffect(() => {
        const fetchResults = async () => {
            if (!query.trim()) {
                setResults([]);
                return;
            }

            setLoading(true);
            try {
                // Use semantic search for @mentions as requested in CUJ 13
                const searchResults = await api.semanticSearchContainers(query, 8);
                setResults(searchResults);
            } catch (err) {
                console.error("Failed to search entities for mention", err);
                setResults([]);
            } finally {
                setLoading(false);
            }
        };

        const timer = setTimeout(fetchResults, 300);
        return () => clearTimeout(timer);
    }, [query]);

    if (results.length === 0 && !loading) return null;

    return (
        <div className="absolute bottom-full left-0 mb-2 w-80 bg-gray-900 border border-gray-700 rounded-lg shadow-xl overflow-hidden z-50">
            <div className="px-3 py-2 border-b border-gray-800 text-xs font-semibold text-gray-400 flex items-center justify-between">
                <span>Mentions</span>
                {loading && <Loader2 className="w-3 h-3 animate-spin text-gray-500" />}
            </div>
            <ul className="max-h-64 overflow-y-auto python">
                {!loading && results.length === 0 && (
                    <li className="px-3 py-4 text-center text-xs text-gray-500">
                        No matches found
                    </li>
                )}
                {results.map((entity, idx) => {
                    const Icon = getIconForType(entity.container_type);
                    return (
                        <li
                            key={entity.id}
                            onClick={() => onSelect(entity.id, entity.name)}
                            className={`px-3 py-2 cursor-pointer flex items-center gap-3 ${idx === activeIndex ? "bg-indigo-600/20 text-indigo-300" : "hover:bg-gray-800 text-gray-200"
                                }`}
                        >
                            <div className={`p-1.5 rounded-md ${idx === activeIndex ? "bg-indigo-500/20" : "bg-gray-800"}`}>
                                <Icon className={`w-3.5 h-3.5 ${idx === activeIndex ? "text-indigo-400" : "text-gray-400"}`} />
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium truncate">{entity.name}</div>
                                <div className="text-xs text-gray-500 capitalize">{entity.container_type}</div>
                            </div>
                        </li>
                    );
                })}
            </ul>
        </div>
    );
}
