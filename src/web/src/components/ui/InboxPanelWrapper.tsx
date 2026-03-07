"use client";

import { InboxPanel } from "@/components/ui/InboxPanel";
import { useStudioStore } from "@/lib/store";

export function InboxPanelWrapper() {
  const { isInboxPanelOpen, setInboxPanelOpen } = useStudioStore();

  return (
    <InboxPanel
      isOpen={isInboxPanelOpen}
      onClose={() => setInboxPanelOpen(false)}
    />
  );
}
