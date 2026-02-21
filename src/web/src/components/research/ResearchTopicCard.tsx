import React from "react";
import { ResearchResult } from "@/lib/api";
import { Star } from "lucide-react";

interface ResearchTopicCardProps {
    topic: ResearchResult;
    isSelected: boolean;
    onClick: () => void;
}

export function ResearchTopicCard({ topic, isSelected, onClick }: ResearchTopicCardProps) {
    // Parse confidence score to a number of stars
    const getStars = (score: string) => {
        switch (score?.toLowerCase()) {
            case "high":
            case "★★★★★":
            case "★★★★☆":
                return 5;
            case "medium":
            case "★★★☆☆":
                return 3;
            case "low":
            case "★★☆☆☆":
            case "★☆☆☆☆":
                return 1;
            default:
                return 0; // Unknown
        }
    };

    const stars = getStars(topic.confidence_score);

    return (
        <button
            onClick={onClick}
            className={`w-full text-left p-4 border-b border-gray-800 transition-colors ${isSelected ? "bg-indigo-900/20 border-l-4 border-l-indigo-500" : "hover:bg-gray-800/40 border-l-4 border-l-transparent"
                }`}
        >
            <div className="flex justify-between items-start mb-1">
                <h3 className={`font-semibold text-sm ${isSelected ? "text-indigo-300" : "text-gray-200"}`}>
                    {topic.name}
                </h3>
                {stars > 0 && (
                    <div className="flex gap-0.5 text-amber-400">
                        {Array.from({ length: 5 }).map((_, i) => (
                            <Star
                                key={i}
                                className={`w-3 h-3 ${i < stars ? "fill-current" : "text-gray-600"}`}
                            />
                        ))}
                    </div>
                )}
            </div>
            <p className="text-xs text-gray-400 line-clamp-2 leading-relaxed">
                {topic.summary}
            </p>
        </button>
    );
}
