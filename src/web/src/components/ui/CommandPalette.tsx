"use client";

import React, { useEffect, useState, useCallback } from "react";
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
    File,
    Search,
    Sparkles,
    Users
} from "lucide-react";
import { api } from "@/lib/api";
import { useStudioStore } from "@/lib/store";
import { toast } from "sonner";

const groupStyles = "text-[10px] uppercase text-gray-600 font-semibold px-2 py-1.5 [&_[cmdk-item]]:px-3 [&_[cmdk-item]]:py-2 [&_[cmdk-item]]:text-sm [&_[cmdk-item]]:flex [&_[cmdk-item]]:items-center [&_[cmdk-item]]:gap-3 [&_[cmdk-item]]:rounded-md [&_[cmdk-item]]:text-gray-300 [&_[cmdk-item]]:cursor-pointer [&_[cmdk-item][data-selected='true']]:bg-indigo-600/20 [&_[cmdk-item][data-selected='true']]:text-white";

export function CommandPalette() {
    const [open, setOpen] = useState(false);
    const [search, setSearch] = useState("");
    const router = useRouter();

    // Dynamic search results
    const [characters, setCharacters] = useState<Array<{ id: string; name: string; role: string }>>([]);
    const [scenes, setScenes] = useState<Array<{ id: string; title: string; chapter: number; scene_number: number }>>([]);
    const [searchResults, setSearchResults] = useState<Array<{ id: string; name: string; container_type: string }>>([]);

    useEffect(() => {
        const down = (e: KeyboardEvent) => {
            if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
                e.preventDefault();
                setOpen((open) => !open);
            }
        };

        document.addEventListener("keydown", down);
        const handleCustomOpen = () => setOpen(true);
        window.addEventListener("open:command-palette", handleCustomOpen);

        return () => {
            document.removeEventListener("keydown", down);
            window.removeEventListener("open:command-palette", handleCustomOpen);
        };
    }, []);

    // Load characters and scenes when palette opens
    useEffect(() => {
        if (!open) return;
        api.getCharacters()
            .then((chars) => setCharacters(chars.map((c: any) => ({ id: c.id, name: c.name, role: c.role || "" }))))
            .catch(() => { });
        api.getScenes(1)
            .then((s) => setScenes(s.map((sc: any) => ({ id: sc.id, title: sc.title, chapter: sc.chapter, scene_number: sc.scene_number }))))
            .catch(() => { });
    }, [open]);

    // Dynamic search
    useEffect(() => {
        if (!search || search.length < 2) {
            setSearchResults([]);
            return;
        }
        const timer = setTimeout(() => {
            api.searchEntities(search, 6)
                .then((results) => setSearchResults(results))
                .catch(() => { });
        }, 250);
        return () => clearTimeout(timer);
    }, [search]);

    const runCommand = (command: () => void) => {
        setOpen(false);
        setSearch("");
        command();
    };

    const handleStartDirector = async () => {
        setOpen(false);
        setSearch("");
        try {
            toast.info("Starting AI Director...", { description: "The Director will advance your story workflow." });
            const result = await api.directorAct();
            toast.success(`Director: ${result.message}`, {
                description: `Step: ${result.step_executed} → Next: ${result.next_step || "done"}`,
            });
        } catch (err) {
            toast.error("AI Director failed", { description: String(err) });
        }
    };

    return (
        <Command.Dialog
            open={open}
            onOpenChange={setOpen}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[20vh]"
        >
            <div className="w-full max-w-lg bg-gray-900 border border-gray-700 rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <Command.Input
                    placeholder="Search pages, scenes, characters..."
                    value={search}
                    onValueChange={setSearch}
                    className="w-full bg-transparent px-4 py-3 text-sm text-gray-100 placeholder:text-gray-500 focus:outline-none border-b border-gray-800"
                />
                <Command.List className="max-h-[400px] overflow-y-auto p-2 no-scrollbar">
                    <Command.Empty className="py-6 text-center text-sm text-gray-500">
                        No results found.
                    </Command.Empty>

                    {/* Dynamic Search Results */}
                    {searchResults.length > 0 && (
                        <>
                            <Command.Group heading="Search Results" className={groupStyles}>
                                {searchResults.map((result) => (
                                    <Command.Item
                                        key={result.id}
                                        value={`search-${result.name}`}
                                        onSelect={() => runCommand(() => {
                                            if (result.container_type === "scene") {
                                                router.push(`/zen?scene=${result.id}`);
                                            } else if (result.container_type === "character") {
                                                router.push(`/dashboard`);
                                            } else {
                                                router.push(`/dashboard`);
                                            }
                                        })}
                                    >
                                        <Search className="w-4 h-4 text-gray-400" />
                                        <div className="flex flex-col">
                                            <span>{result.name}</span>
                                            <span className="text-[10px] text-gray-600 capitalize">{result.container_type}</span>
                                        </div>
                                    </Command.Item>
                                ))}
                            </Command.Group>
                            <Command.Separator className="h-px bg-gray-800 my-1" />
                        </>
                    )}

                    {/* Characters */}
                    {characters.length > 0 && (
                        <>
                            <Command.Group heading="Characters" className={groupStyles}>
                                {characters.slice(0, 5).map((char) => (
                                    <Command.Item
                                        key={char.id}
                                        value={`character-${char.name}`}
                                        onSelect={() => runCommand(() => router.push(`/dashboard`))}
                                    >
                                        <Users className="w-4 h-4 text-violet-400" />
                                        <div className="flex flex-col">
                                            <span>{char.name}</span>
                                            <span className="text-[10px] text-gray-600 capitalize">{char.role}</span>
                                        </div>
                                    </Command.Item>
                                ))}
                            </Command.Group>
                            <Command.Separator className="h-px bg-gray-800 my-1" />
                        </>
                    )}

                    {/* Scenes */}
                    {scenes.length > 0 && (
                        <>
                            <Command.Group heading="Scenes" className={groupStyles}>
                                {scenes.slice(0, 5).map((scene) => (
                                    <Command.Item
                                        key={scene.id}
                                        value={`scene-${scene.title}`}
                                        onSelect={() => runCommand(() => router.push(`/zen?scene=${scene.id}`))}
                                    >
                                        <FileText className="w-4 h-4 text-blue-400" />
                                        <div className="flex flex-col">
                                            <span>{scene.title}</span>
                                            <span className="text-[10px] text-gray-600">Ch.{scene.chapter} Sc.{scene.scene_number}</span>
                                        </div>
                                    </Command.Item>
                                ))}
                            </Command.Group>
                            <Command.Separator className="h-px bg-gray-800 my-1" />
                        </>
                    )}

                    {/* Pages */}
                    <Command.Group heading="Pages" className={groupStyles}>
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

                    <Command.Group heading="Create" className={groupStyles}>
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

                    <Command.Group heading="Actions" className={groupStyles}>
                        <Command.Item onSelect={() => runCommand(() => router.push("/pipelines"))}>
                            <Plus className="w-4 h-4 text-gray-400" />
                            Create New Pipeline
                        </Command.Item>
                        <Command.Item onSelect={handleStartDirector}>
                            <Play className="w-4 h-4 text-emerald-400" />
                            <div className="flex flex-col">
                                <span>Start AI Director</span>
                                <span className="text-[10px] text-gray-600">Advance story workflow to next step</span>
                            </div>
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:export')))}>
                            <Download className="w-4 h-4 text-gray-400" />
                            Export Project
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => router.push("/zen"))}>
                            <Moon className="w-4 h-4 text-gray-400" />
                            Open Zen Mode
                        </Command.Item>
                        <Command.Item onSelect={() => runCommand(() => window.dispatchEvent(new CustomEvent('open:onboarding')))}>
                            <Sparkles className="w-4 h-4 text-gray-400" />
                            Re-run Onboarding
                        </Command.Item>
                    </Command.Group>
                </Command.List>
            </div>
        </Command.Dialog>
    );
}
