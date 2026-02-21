"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
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
    Plus,
    Play,
    Download,
    Moon,
    User,
    FileText,
    Image as ImageIcon,
    File
} from "lucide-react";


export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const router = useRouter();

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };

        document.addEventListener("keydown", down);

        // Listen for custom event from Navbar
        const handleCustomOpen = () => setOpen(true);
        window.addEventListener("open:command-palette", handleCustomOpen);

        return () => {
            document.removeEventListener("keydown", down);
            window.removeEventListener("open:command-palette", handleCustomOpen);
        };
    }, []);

    const runCommand = (command: () => void) => {
        setOpen(false);
        command();
    };

    return (
        <Command.Dialog
            open={open}
            onOpenChange={setOpen}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[20vh]"
        >
            <div className="w-full max-w-lg bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <Command.Input
                    placeholder="Search pages, actions..."
                    className="w-full bg-transparent px-4 py-3 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none border-b border-gray-800"
                />
                <Command.List className="max-h-[300px] overflow-y-auto p-2 no-scrollbar">
                    <Command.Empty className="py-6 text-center text-sm text-gray-500">
                        No results found.
                    </Command.Empty>

                    <Command.Group heading="Pages" className="text-[10px] uppercase text-gray-600 font-semibold px-2 py-1.5 [&_[cmdk-item]]:px-3 [&_[cmdk-item]]:py-2 [&_[cmdk-item]]:text-sm [&_[cmdk-item]]:flex [&_[cmdk-item]]:items-center [&_[cmdk-item]]:gap-3 [&_[cmdk-item]]:rounded-md [&_[cmdk-item]]:text-gray-300 [&_[cmdk-item]]:cursor-pointer [&_[cmdk-item][data-selected='true']]:bg-indigo-600/20 [&_[cmdk-item][data-selected='true']]:text-white">
                        <Command.Item onSelect={() => runCommand(() => router.push("/dashboard"))}>
                            <LayoutDashboard className="w-4 h-4 text-gray-400" />
                            Dashboard
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/zen"))}>
                            <PenTool className="w-4 h-4 text-gray-400" />
                            Zen Mode
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/pipelines"))}>
                            <Workflow className="w-4 h-4 text-gray-400" />
                            Pipelines
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/storyboard"))}>
                            <Film className="w-4 h-4 text-gray-400" />
                            Storyboard
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/timeline"))}>
                            <Clock className="w-4 h-4 text-gray-400" />
                            Timeline
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/brainstorm"))}>
                            <Lightbulb className="w-4 h-4 text-gray-400" />
                            Brainstorm
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/research"))}>
                            <BookOpen className="w-4 h-4 text-gray-400" />
                            Research
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/translation"))}>
                            <Globe className="w-4 h-4 text-gray-400" />
                            Translation
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/preview"))}>
                            <Smartphone className="w-4 h-4 text-gray-400" />
                            Preview
                        </Command.Item>
                    </Command.Group>

                    <Command.Separator className="h-px bg-gray-800 my-1" />

                    <Command.Group heading="Create" className="text-[10px] uppercase text-gray-600 font-semibold px-2 py-1.5 [&_[cmdk-item]]:px-3 [&_[cmdk-item]]:py-2 [&_[cmdk-item]]:text-sm [&_[cmdk-item]]:flex [&_[cmdk-item]]:items-center [&_[cmdk-item]]:gap-3 [&_[cmdk-item]]:rounded-md [&_[cmdk-item]]:text-gray-300 [&_[cmdk-item]]:cursor-pointer [&_[cmdk-item][data-selected='true']]:bg-indigo-600/20 [&_[cmdk-item][data-selected='true']]:text-white">
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'scene' } })))}>
                            <FileText className="w-4 h-4 text-gray-400" />
                            Create Scene
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'character' } })))}>
                            <User className="w-4 h-4 text-gray-400" />
                            Create Character
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'idea_card' } })))}>
                            <ImageIcon className="w-4 h-4 text-gray-400" />
                            Create Idea Card
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:quick-add', { detail: { type: 'research_topic' } })))}>
                            <File className="w-4 h-4 text-gray-400" />
                            Create Research Topic
                        </Command.Item>
                    </Command.Group>

                    <Command.Separator className="h-px bg-gray-800 my-1" />

                    <Command.Group heading="Actions" className="text-[10px] uppercase text-gray-600 font-semibold px-2 py-1.5 [&_[cmdk-item]]:px-3 [&_[cmdk-item]]:py-2 [&_[cmdk-item]]:text-sm [&_[cmdk-item]]:flex [&_[cmdk-item]]:items-center [&_[cmdk-item]]:gap-3 [&_[cmdk-item]]:rounded-md [&_[cmdk-item]]:text-gray-300 [&_[cmdk-item]]:cursor-pointer [&_[cmdk-item][data-selected='true']]:bg-indigo-600/20 [&_[cmdk-item][data-selected='true']]:text-white">
                        <Command.Item onSelect={() => runCommand(() => router.push("/pipelines"))}>
                            <Plus className="w-4 h-4 text-gray-400" />
                            Create New Pipeline
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => { /* TODO: trigger director */ })}>
                            <Play className="w-4 h-4 text-gray-400" />
                            Start AI Director
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:export')))}>
                            <Download className="w-4 h-4 text-gray-400" />
                            Export Project
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/zen"))}>
                            <Moon className="w-4 h-4 text-gray-400" />
                            Open Zen Mode
                        </Command.Item>
                    </Command.Group>
                </Command.List>
            </div>
        </Command.Dialog>
    );
}
