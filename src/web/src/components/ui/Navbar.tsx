"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  PenTool,
  Workflow,
  Film,
  Clock,
  Lightbulb,
  BookOpen,
  Globe,
  Smartphone,
  Command,
  MessageSquare,
  Circle,
  Square,
  Loader2
} from "lucide-react";
import { useStudioStore } from "@/lib/store";
import { useRecorderStore } from "@/lib/store/recorderSlice";
import { CloudSyncIndicator } from "@/components/shared/CloudSyncIndicator";
import { toast } from "sonner";
import { RecordingReviewPanel } from "@/components/workflow/RecordingReviewPanel";
import { BackgroundJobsWidget } from "@/components/ui/BackgroundJobsWidget";

const navItems = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Zen", href: "/zen", icon: PenTool },
  { name: "Pipelines", href: "/pipelines", icon: Workflow },
  { name: "Storyboard", href: "/storyboard", icon: Film },
  { name: "Timeline", href: "/timeline", icon: Clock },
  { name: "Brainstorm", href: "/brainstorm", icon: Lightbulb },
  { name: "Research", href: "/research", icon: BookOpen },
  { name: "Translation", href: "/translation", icon: Globe },
  { name: "Preview", href: "/preview", icon: Smartphone },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { isChatSidebarOpen, setChatSidebarOpen } = useStudioStore();
  const {
    isRecording,
    startRecording,
    stopRecording,
    actions,
    isCompiling,
    setShowReviewPanel,
  } = useRecorderStore();

  const handleCommandPaletteClick = () => {
    // Trigger custom event to open the command palette
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }));
    // As a fallback for different OS/browsers, also dispatch a custom event
    window.dispatchEvent(new CustomEvent('open:command-palette'));
  };

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === 'c') {
        e.preventDefault();
        setChatSidebarOpen(!isChatSidebarOpen);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isChatSidebarOpen, setChatSidebarOpen]);

  const handleToggleRecording = () => {
    if (isRecording) {
      // Stop recording and show the review panel
      stopRecording();

      if (actions.length === 0) {
        toast.info("Recording stopped (No actions captured)");
        return;
      }

      setShowReviewPanel(true);
    } else {
      // Start recording
      startRecording();
      toast.info("Recording Started", {
        description: "Your AI actions will be captured and compiled into a reusable pipeline.",
        icon: <Circle className="w-4 h-4 text-red-500 fill-red-500" />
      });
    }
  };

  return (
    <>
      <nav className="fixed top-0 left-0 right-0 h-12 bg-gray-950/95 backdrop-blur-sm border-b border-gray-800 z-50 flex items-center justify-between px-4">
        {/* Left: Brand */}
        <div className="flex items-center gap-4">
          <span className="font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-purple-500">
            Showrunner
          </span>
          <CloudSyncIndicator />
        </div>

        {/* Center: Tabs */}
        <div className="flex items-center gap-1 overflow-x-auto no-scrollbar max-w-[60%] lg:max-w-[70%]">
          {navItems.map((item) => {
            const isActive = pathname?.startsWith(item.href);
            const Icon = item.icon;

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md whitespace-nowrap transition-colors ${isActive
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                  : "text-gray-500 hover:text-gray-300 hover:bg-gray-800/50 border border-transparent"
                  }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-400" : "text-gray-500"}`} />
                <span className="hidden sm:inline">{item.name}</span>
              </Link>
            );
          })}
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-3">
          <BackgroundJobsWidget />

          {/* Record Workflow Toggle */}
          <button
            onClick={handleToggleRecording}
            disabled={isCompiling}
            className={`relative flex items-center gap-2 px-3 py-1.5 border rounded-md transition-all text-xs font-semibold uppercase tracking-wider
              ${isRecording
                ? "bg-red-500/10 text-red-500 border-red-500/30 hover:bg-red-500/20 animate-pulse"
                : "bg-gray-900 text-gray-400 border-gray-700 hover:text-gray-200 hover:border-gray-500"}
              ${isCompiling ? "opacity-50 cursor-not-allowed" : ""}
            `}
            title={isRecording ? "Stop Recording & Review Pipeline" : "Record AI Workflow"}
          >
            {isCompiling ? (
              <Loader2 className="w-4 h-4 animate-spin text-indigo-400" />
            ) : isRecording ? (
              <>
                <Square className="w-3.5 h-3.5 fill-red-500 text-red-500" />
                <span>Recording...</span>
              </>
            ) : (
              <>
                <Circle className="w-3.5 h-3.5 text-gray-400" />
                <span>Record</span>
              </>
            )}

            {/* Action count badge */}
            {isRecording && actions.length > 0 && (
              <span className="absolute -top-1.5 -right-1.5 min-w-[18px] h-[18px] flex items-center justify-center px-1 rounded-full bg-red-500 text-white text-[10px] font-bold shadow-lg shadow-red-500/30">
                {actions.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setChatSidebarOpen(!isChatSidebarOpen)}
            className={`flex items-center justify-center p-1.5 border hover:border-gray-600 rounded-md transition-colors ${isChatSidebarOpen
              ? "bg-indigo-600/20 text-indigo-300 border-indigo-500/30"
              : "bg-gray-900 border-gray-700 text-gray-400"
              }`}
            title="Toggle Agentic Chat (Cmd+Shift+C)"
          >
            <MessageSquare className="w-4 h-4" />
          </button>

          <button
            onClick={handleCommandPaletteClick}
            className="flex items-center gap-1.5 px-2 py-1 bg-gray-900 hover:bg-gray-800 border border-gray-700 hover:border-gray-600 rounded-md text-gray-400 transition-colors"
            title="Open Command Palette (Cmd+K)"
          >
            <Command className="w-3.5 h-3.5" />
            <span className="text-[10px] font-semibold tracking-wider">⌘K</span>
          </button>
        </div>
      </nav>

      {/* Recording review panel (rendered as portal-like overlay) */}
      <RecordingReviewPanel />
    </>
  );
}
