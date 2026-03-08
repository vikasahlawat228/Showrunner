"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
    PenTool, TrendingUp, Clock, Flame, BookOpen,
    ChevronRight, FileText, Sparkles, BarChart3, Target
} from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { useZenStore } from "@/lib/store/zenSlice";
import { OnboardingChecklist } from "@/components/ui/OnboardingChecklist";
import { api } from "@/lib/api";

interface SessionHistory {
    date: string;
    words: number;
}

export function WriterDashboard() {
    const router = useRouter();
    const characters = useStudioStore((s) => s.characters);
    const scenes = useStudioStore((s) => s.scenes);
    const fetchAll = useStudioStore((s) => s.fetchAll);

    const sessionWordsWritten = useZenStore((s) => s.sessionWordsWritten);

    const [projectName, setProjectName] = useState("Your Story");
    const [wordHistory, setWordHistory] = useState<SessionHistory[]>([]);
    const [streak, setStreak] = useState(0);
    const [lastScene, setLastScene] = useState<string | null>(null);
    const [totalWords, setTotalWords] = useState(0);

    useEffect(() => {
        fetchAll();

        // Load project info
        api.getProject()
            .then((p) => setProjectName(p.name || "Your Story"))
            .catch(() => { });

        // Load writing history from localStorage
        const history: SessionHistory[] = JSON.parse(
            localStorage.getItem("showrunner:wordHistory") || "[]"
        );
        setWordHistory(history.slice(-7));

        // Calculate streak
        let s = 0;
        const today = new Date().toDateString();
        for (let i = history.length - 1; i >= 0; i--) {
            const d = new Date(history[i].date).toDateString();
            const expected = new Date(Date.now() - s * 86400000).toDateString();
            if (d === expected) { s++; } else break;
        }
        setStreak(s);

        // Total words
        setTotalWords(history.reduce((acc, h) => acc + h.words, 0));

        // Last edited scene
        setLastScene(localStorage.getItem("showrunner:lastScene"));
    }, [fetchAll]);

    const maxWords = Math.max(...wordHistory.map((h) => h.words), 1);

    return (
        <div className="h-full overflow-y-auto p-6 space-y-6">
            {/* Welcome Header */}
            <div className="bg-gradient-to-br from-indigo-600/10 via-purple-600/5 to-transparent border border-indigo-500/20 rounded-xl p-6">
                <h1 className="text-2xl font-bold text-white mb-1">
                    Welcome back
                </h1>
                <p className="text-gray-400 text-sm mb-5">
                    Working on <span className="text-indigo-300 font-medium">{projectName}</span>
                    {scenes && scenes.length > 0 && (
                        <> · {scenes.length} scene{scenes.length !== 1 ? "s" : ""} created</>
                    )}
                </p>

                <button
                    onClick={() => router.push("/zen")}
                    className="flex items-center gap-2 px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-lg transition-colors shadow-lg shadow-indigo-600/20"
                >
                    <PenTool className="w-4 h-4" />
                    Continue Writing
                    <ChevronRight className="w-4 h-4" />
                </button>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-gray-500 text-xs font-medium mb-2">
                        <Flame className="w-3.5 h-3.5 text-orange-400" /> STREAK
                    </div>
                    <div className="text-2xl font-bold text-white">{streak}</div>
                    <div className="text-xs text-gray-600">day{streak !== 1 ? "s" : ""}</div>
                </div>
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-gray-500 text-xs font-medium mb-2">
                        <BarChart3 className="w-3.5 h-3.5 text-indigo-400" /> TOTAL WORDS
                    </div>
                    <div className="text-2xl font-bold text-white">{totalWords.toLocaleString()}</div>
                    <div className="text-xs text-gray-600">all sessions</div>
                </div>
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <div className="flex items-center gap-2 text-gray-500 text-xs font-medium mb-2">
                        <Target className="w-3.5 h-3.5 text-emerald-400" /> TODAY
                    </div>
                    <div className="text-2xl font-bold text-white">{sessionWordsWritten.toLocaleString()}</div>
                    <div className="text-xs text-gray-600">words written</div>
                </div>
            </div>

            {/* Word Count Chart */}
            {wordHistory.length > 0 && (
                <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-4">
                        <span className="text-sm font-semibold text-gray-300 flex items-center gap-2">
                            <TrendingUp className="w-4 h-4 text-indigo-400" /> Last 7 Sessions
                        </span>
                    </div>
                    <div className="flex items-end gap-1.5 h-20">
                        {wordHistory.map((h, i) => {
                            const height = Math.max(4, (h.words / maxWords) * 100);
                            return (
                                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                                    <div
                                        className="w-full bg-indigo-500/30 rounded-sm transition-all hover:bg-indigo-500/50"
                                        style={{ height: `${height}%` }}
                                        title={`${h.words} words on ${new Date(h.date).toLocaleDateString()}`}
                                    />
                                    <span className="text-[9px] text-gray-600">
                                        {new Date(h.date).toLocaleDateString("en", { weekday: "short" })}
                                    </span>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Onboarding Checklist */}
            <OnboardingChecklist />

            {/* Quick Links */}
            <div className="grid grid-cols-2 gap-3">
                <Link
                    href="/brainstorm"
                    className="flex items-center gap-3 bg-gray-900/50 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors group"
                >
                    <Sparkles className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
                    <div>
                        <span className="text-sm font-medium text-gray-200">Brainstorm</span>
                        <span className="block text-xs text-gray-600">Generate new ideas</span>
                    </div>
                </Link>
                <Link
                    href="/storyboard"
                    className="flex items-center gap-3 bg-gray-900/50 border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition-colors group"
                >
                    <BookOpen className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                    <div>
                        <span className="text-sm font-medium text-gray-200">Storyboard</span>
                        <span className="block text-xs text-gray-600">Visualize your scenes</span>
                    </div>
                </Link>
            </div>
        </div>
    );
}
