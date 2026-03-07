"use client";

import { useEffect, useState } from "react";
import { ExportModal } from "@/components/ui/ExportModal";

export function GlobalExportModal() {
    const [exportOpen, setExportOpen] = useState(false);

    useEffect(() => {
        const handler = () => setExportOpen(true);
        window.addEventListener('open:export', handler);
        return () => window.removeEventListener('open:export', handler);
    }, []);

    return <ExportModal isOpen={exportOpen} onClose={() => setExportOpen(false)} />;
}
