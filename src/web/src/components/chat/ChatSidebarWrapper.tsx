"use client";

import { useEffect } from "react";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { useStudioStore } from "@/lib/store";
import { useProjectEvents } from "@/hooks/useProjectEvents";

export function ChatSidebarWrapper() {
  const { isChatSidebarOpen, setChatSidebarOpen } = useStudioStore();

  // Listen for global project file changes (SSE) to keep stores synced
  useProjectEvents();

  // Set up keyboard shortcuts for chat sidebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+K (or Cmd+K on Mac) to toggle chat sidebar
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setChatSidebarOpen(!isChatSidebarOpen);
      }
      // Escape to close chat sidebar
      if (e.key === "Escape" && isChatSidebarOpen) {
        setChatSidebarOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isChatSidebarOpen, setChatSidebarOpen]);

  // Persist sidebar state to localStorage
  useEffect(() => {
    localStorage.setItem("showrunner-chat-sidebar-open", String(isChatSidebarOpen));
  }, [isChatSidebarOpen]);

  return (
    <ChatSidebar
      isOpen={isChatSidebarOpen}
      onClose={() => setChatSidebarOpen(false)}
    />
  );
}
