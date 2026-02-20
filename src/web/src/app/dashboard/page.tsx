"use client";

import { useEffect } from "react";
import { useStudioStore } from "@/lib/store";
import { WorkbenchLayout } from "@/components/workbench/WorkbenchLayout";

export default function DashboardPage() {
  const fetchAll = useStudioStore((s) => s.fetchAll);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return <WorkbenchLayout />;
}
