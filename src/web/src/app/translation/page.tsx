import { TranslationPanel } from "@/components/translation/TranslationPanel";
import Link from "next/link";
import { ChevronLeft } from "lucide-react";

export default function TranslationPage() {
    return (
        <div className="min-h-screen bg-gray-950 text-gray-100">
            <div className="max-w-6xl mx-auto px-6 py-8">
                <div className="flex items-center gap-3 mb-6">
                    <Link href="/dashboard" className="text-gray-500 hover:text-gray-300 flex items-center transition-colors">
                        <ChevronLeft className="w-4 h-4 mr-1" /> Dashboard
                    </Link>
                    <span className="text-gray-700">|</span>
                    <h1 className="text-2xl font-bold text-gray-100 tracking-tight">Translation Studio</h1>
                </div>

                <div className="mb-6 text-gray-400 text-sm max-w-3xl">
                    Use the translation agent to safely translate prose into different languages.
                    The agent automatically adapts cultural idioms safely while preserving character voices and applying the project glossary.
                </div>

                <TranslationPanel />
            </div>
        </div>
    );
}
