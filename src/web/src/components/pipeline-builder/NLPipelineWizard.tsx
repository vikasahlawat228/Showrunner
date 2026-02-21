import { useState } from "react";
import { api } from "@/lib/api";
import { usePipelineBuilderStore } from "@/lib/store/pipelineBuilderSlice";
import { Sparkles, X, Loader2, ArrowRight, Check } from "lucide-react";
import { toast } from "sonner";

const cn = (...classes: (string | undefined | null | false)[]) => classes.filter(Boolean).join(" ");

interface NLPipelineWizardProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated: (definitionId: string) => void;
}

const EXAMPLES = [
    "Take a scene's text content, gather character profiles, let me review the prompt, then generate panel descriptions.",
    "Research a topic, summarize findings, then draft prose.",
    "Gather character DNA, generate dialogue, review, save.",
    "Outline a chapter, expand each beat, check style."
];

export function NLPipelineWizard({ isOpen, onClose, onCreated }: NLPipelineWizardProps) {
    const [title, setTitle] = useState("");
    const [intent, setIntent] = useState("");
    const [isGenerating, setIsGenerating] = useState(false);
    const [result, setResult] = useState<any | null>(null);

    const { loadDefinition } = usePipelineBuilderStore();

    if (!isOpen) return null;

    const handleGenerate = async () => {
        if (!title.trim() || !intent.trim()) {
            toast.error("Please provide both a name and a description.");
            return;
        }

        setIsGenerating(true);
        try {
            const generated = await api.generatePipelineFromNL({ title, intent });
            setResult(generated);
        } catch (error: any) {
            toast.error(error.message || "Failed to generate pipeline");
            console.error(error);
        } finally {
            setIsGenerating(false);
        }
    };

    const handleOpenBuilder = () => {
        if (result && result.id) {
            onCreated(result.id);
            setTitle("");
            setIntent("");
            setResult(null);
        }
    };

    const handleDiscard = async () => {
        if (result && result.id) {
            try {
                await api.deletePipelineDefinition(result.id);
                toast.success("Discarded generated pipeline");
            } catch (e) {
                console.error("Failed to delete", e);
            }
        }
        setTitle("");
        setIntent("");
        setResult(null);
        onClose();
    };

    const getStepFlow = (data: any) => {
        if (!data || !data.nodes || !Array.isArray(data.nodes)) return [];

        // Attempt to reconstruct a linear progression based on edges
        // For a complex graph, this is an approximation
        const nodes = data.nodes;
        const edges = data.edges || [];

        return nodes.map((n: any) => n.data?.name || n.id);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in">
            <div className="bg-gray-900 border border-gray-800 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-800 bg-gray-900/50">
                    <div className="flex items-center gap-2">
                        <Sparkles className="w-5 h-5 text-purple-400" />
                        <h2 className="font-semibold text-gray-100">Create Pipeline from Description</h2>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-md text-gray-400 hover:text-gray-200 hover:bg-gray-800 transition-colors"
                    >
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto">
                    {!result ? (
                        <div className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">Pipeline Name</label>
                                <input
                                    type="text"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    placeholder="e.g. Scene to Panels Pipeline"
                                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-gray-100 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-purple-500"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1.5">Describe your workflow</label>
                                <textarea
                                    value={intent}
                                    onChange={(e) => setIntent(e.target.value)}
                                    rows={4}
                                    placeholder="Describe step-by-step what this pipeline should do..."
                                    className="w-full bg-gray-950 border border-gray-800 rounded-lg px-3 py-2 text-gray-100 placeholder:text-gray-600 focus:outline-none focus:ring-1 focus:ring-purple-500 resize-none"
                                />
                            </div>

                            <div>
                                <div className="flex items-center gap-2 mb-2 text-sm text-gray-400 font-medium">
                                    <span className="text-yellow-500">💡</span> Examples:
                                </div>
                                <div className="space-y-1.5">
                                    {EXAMPLES.map((ex, i) => (
                                        <button
                                            key={i}
                                            onClick={() => setIntent(ex)}
                                            className="block w-full text-left p-2 rounded-md bg-gray-800/30 hover:bg-gray-800/60 border border-transparent hover:border-gray-700 text-sm text-gray-300 transition-colors"
                                        >
                                            • "{ex}"
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="pt-4 flex justify-end">
                                <button
                                    onClick={handleGenerate}
                                    disabled={!title.trim() || !intent.trim() || isGenerating}
                                    className="flex items-center gap-2 px-6 py-2.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors font-medium shadow-lg shadow-purple-900/20 disabled:opacity-50"
                                >
                                    {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                                    {isGenerating ? "Generating pipeline..." : "Generate Pipeline"}
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6 animate-in slide-in-from-bottom-2">
                            <div className="p-4 bg-green-500/10 border border-green-500/20 rounded-lg flex items-start gap-3">
                                <div className="w-8 h-8 rounded-full bg-green-500/20 flex items-center justify-center shrink-0">
                                    <Check className="w-4 h-4 text-green-400" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-green-400">Generated successfully!</h3>
                                    <p className="text-sm text-gray-400 mt-1">
                                        {result.data?.nodes?.length || 0} steps, {result.data?.edges?.length || 0} connections
                                    </p>
                                </div>
                            </div>

                            <div className="bg-gray-950 rounded-lg border border-gray-800 p-4">
                                <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-3">Detected Flow</h4>
                                <div className="flex flex-wrap items-center gap-2 text-sm">
                                    {getStepFlow(result.data).map((stepInfo: string, i: number, arr: any[]) => (
                                        <div key={i} className="flex items-center gap-2">
                                            <span className="px-2 py-1 rounded-md bg-gray-900 border border-gray-700 text-purple-300 font-mono text-xs">
                                                {stepInfo}
                                            </span>
                                            {i < arr.length - 1 && (
                                                <ArrowRight className="w-3 h-3 text-gray-600" />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="flex items-center gap-3 pt-2">
                                <button
                                    onClick={handleOpenBuilder}
                                    className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors font-medium text-center"
                                >
                                    Open in Builder
                                </button>
                                <button
                                    onClick={handleDiscard}
                                    className="flex-1 px-4 py-2 bg-gray-800 hover:bg-red-900/80 text-gray-200 hover:text-red-200 rounded-lg transition-colors border border-gray-700 hover:border-red-800 font-medium text-center"
                                >
                                    Discard
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
