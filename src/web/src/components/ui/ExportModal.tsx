"use client";

import { useEffect, useState, useRef } from "react";
import { X, FileText, Package, Clapperboard, Printer, Download, Loader2 } from "lucide-react";
import { api, ExportFormat } from "@/lib/api";
import { toast } from "sonner";

interface ExportModalProps {
    isOpen: boolean;
    onClose: () => void;
}

const FORMATS: { id: ExportFormat; icon: any; label: string; ext: string }[] = [
    { id: "markdown", icon: FileText, label: "Markdown", ext: ".md" },
    { id: "json", icon: Package, label: "JSON", ext: ".json" },
    { id: "fountain", icon: Clapperboard, label: "Fountain", ext: ".fountain" },
    { id: "html", icon: Printer, label: "HTML", ext: "(PDF)" },
];

export function ExportModal({ isOpen, onClose }: ExportModalProps) {
    const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("markdown");
    const [previewContent, setPreviewContent] = useState<string>("");
    const [isLoadingPreview, setIsLoadingPreview] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);

    // Initial fetch when opened
    useEffect(() => {
        if (isOpen) {
            setSelectedFormat("markdown");
            fetchPreview("markdown");
        }
    }, [isOpen]);

    const fetchPreview = async (format: ExportFormat) => {
        setIsLoadingPreview(true);
        setPreviewContent("");
        try {
            if (format === "html") {
                const html = await api.exportPreview();
                setPreviewContent(html);
            } else if (format === "markdown") {
                const blob = await api.exportManuscript();
                const text = await blob.text();
                setPreviewContent(text);
            } else if (format === "json") {
                const data = await api.exportBundle();
                setPreviewContent(JSON.stringify(data, null, 2));
            } else if (format === "fountain") {
                const blob = await api.exportScreenplay();
                const text = await blob.text();
                setPreviewContent(text);
            }
        } catch (error) {
            console.error(error);
            setPreviewContent("Error loading preview.");
        } finally {
            setIsLoadingPreview(false);
        }
    };

    const handleFormatSelect = (format: ExportFormat) => {
        if (format === selectedFormat) return;
        setSelectedFormat(format);
        fetchPreview(format);
    };

    const handleDownload = async () => {
        setIsDownloading(true);
        let blob: Blob;
        let filename: string;

        try {
            switch (selectedFormat) {
                case "markdown":
                    blob = await api.exportManuscript();
                    filename = "manuscript.md";
                    break;
                case "json":
                    const data = await api.exportBundle();
                    blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                    filename = "project-bundle.json";
                    break;
                case "fountain":
                    blob = await api.exportScreenplay();
                    filename = "screenplay.fountain";
                    break;
                case "html":
                    blob = await api.exportHTML();
                    filename = "manuscript.html";
                    break;
                default:
                    throw new Error("Invalid format");
            }

            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            toast.success(`Exported as ${filename}`);
            onClose();
        } catch (error) {
            console.error("Export error", error);
            toast.error("Export failed");
        } finally {
            setIsDownloading(false);
        }
    };

    const handlePrint = async () => {
        try {
            const html = await api.exportPreview();
            const printWindow = window.open("", "_blank");
            if (printWindow) {
                printWindow.document.write(html);
                printWindow.document.close();
                printWindow.focus();
                // Adding slight delay before printing to ensure it renders
                setTimeout(() => {
                    printWindow.print();
                }, 200);
            }
        } catch (error) {
            toast.error("Preparing print failed");
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[90] flex items-center justify-center">
            {/* Backdrop click to close */}
            <div className="absolute inset-0" onClick={onClose} />

            <div className="bg-gray-900 border border-gray-700 rounded-xl shadow-2xl max-w-2xl w-full mx-4 max-h-[85vh] overflow-hidden flex flex-col relative z-10">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-gray-800">
                    <h2 className="text-lg font-semibold text-white">Export Project</h2>
                    <button onClick={onClose} className="p-1 text-gray-400 hover:text-white rounded-md hover:bg-gray-800">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 flex flex-col flex-1 overflow-hidden min-h-0">
                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-300 mb-2">Select Format:</label>
                        <div className="grid grid-cols-4 gap-4">
                            {FORMATS.map((f) => {
                                const Icon = f.icon;
                                const isSelected = selectedFormat === f.id;
                                return (
                                    <button
                                        key={f.id}
                                        onClick={() => handleFormatSelect(f.id)}
                                        className={`w-full h-24 rounded-lg flex flex-col items-center justify-center gap-2 border transition-all ${isSelected
                                                ? "border-indigo-500 bg-indigo-600/10 text-indigo-400"
                                                : "border-gray-700 bg-gray-800/50 text-gray-400 hover:bg-gray-800 hover:border-gray-600"
                                            }`}
                                    >
                                        <Icon className="w-6 h-6" />
                                        <span className={`text-sm font-medium ${isSelected ? "text-indigo-300" : "text-gray-300"}`}>{f.label}</span>
                                        <span className="text-xs opacity-70">{f.ext}</span>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    {/* Preview Area */}
                    <div className="flex-1 min-h-0 flex flex-col border border-gray-800 rounded-lg overflow-hidden bg-gray-950 relative">
                        {isLoadingPreview ? (
                            <div className="flex-1 flex items-center justify-center text-gray-500">
                                <span className="flex items-center gap-2">
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Loading preview...
                                </span>
                            </div>
                        ) : selectedFormat === "html" ? (
                            <iframe
                                className="w-full h-64 bg-white"
                                srcDoc={previewContent}
                                title="HTML Preview"
                            />
                        ) : (
                            <pre className="flex-1 p-4 font-mono text-xs text-gray-300 overflow-auto max-h-64 whitespace-pre-wrap">
                                {previewContent}
                            </pre>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-gray-800 bg-gray-950 flex items-center justify-between shrink-0">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-400 hover:text-white transition-colors"
                    >
                        Cancel
                    </button>
                    <div className="flex gap-3">
                        {selectedFormat === "html" && (
                            <button
                                onClick={handlePrint}
                                disabled={isDownloading || isLoadingPreview}
                                className="px-4 py-2 text-sm font-medium text-white bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                            >
                                <Printer className="w-4 h-4" />
                                Print to PDF
                            </button>
                        )}
                        <button
                            onClick={handleDownload}
                            disabled={isDownloading || isLoadingPreview}
                            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50"
                        >
                            {isDownloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                            Download {FORMATS.find(f => f.id === selectedFormat)?.ext.replace(/[()]/g, '')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
