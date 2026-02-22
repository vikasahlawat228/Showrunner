"use client";

import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { useStudioStore } from "@/lib/store";
import { useProjectEvents } from "@/hooks/useProjectEvents";

export function ChatSidebarWrapper() {
  const { isChatSidebarOpen, setChatSidebarOpen } = useStudioStore();

  // Listen for global project file changes (SSE) to keep stores synced
  useProjectEvents();

  return (
    <ChatSidebar
      isOpen={isChatSidebarOpen}
      onClose={() => setChatSidebarOpen(false)}
    />
  );
}
