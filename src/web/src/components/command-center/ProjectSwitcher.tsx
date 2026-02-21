"use client";

import { useEffect } from "react";
import { FolderOpen, Check, ChevronDown } from "lucide-react";
import { useStudioStore } from "@/lib/store";

export function ProjectSwitcher() {
    const projects = useStudioStore((s) => s.projects);
    const activeProjectId = useStudioStore((s) => s.activeProjectId);
    const projectsLoading = useStudioStore((s) => s.projectsLoading);
    const fetchProjects = useStudioStore((s) => s.fetchProjects);
    const setActiveProject = useStudioStore((s) => s.setActiveProject);

    useEffect(() => {
        fetchProjects();
    }, [fetchProjects]);

    const activeProject = projects.find((p) => p.id === activeProjectId);

    if (projectsLoading) {
        return (
            <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm p-4">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600 border-t-blue-400 animate-spin" />
                    Loading projects…
                </div>
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur-sm overflow-hidden">
            {/* Header */}
            <div className="px-4 py-3 border-b border-gray-800/60 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <FolderOpen className="w-4 h-4 text-blue-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                        Projects
                    </span>
                </div>
                <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
            </div>

            {/* Project List */}
            <div className="max-h-48 overflow-y-auto">
                {projects.length === 0 ? (
                    <div className="px-4 py-6 text-center">
                        <FolderOpen className="w-8 h-8 mx-auto text-gray-700 mb-2" />
                        <p className="text-gray-500 text-sm">No projects found</p>
                    </div>
                ) : (
                    projects.map((project) => {
                        const isActive = project.id === activeProjectId;
                        return (
                            <button
                                key={project.id}
                                onClick={() => setActiveProject(project.id)}
                                className={`w-full px-4 py-3 flex items-center gap-3 transition-all duration-150 text-left group ${isActive
                                        ? "bg-blue-500/10 border-l-2 border-blue-400"
                                        : "hover:bg-gray-800/50 border-l-2 border-transparent"
                                    }`}
                            >
                                <div
                                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${isActive
                                            ? "bg-gradient-to-br from-blue-500 to-purple-600 text-white shadow-lg shadow-blue-500/20"
                                            : "bg-gray-800 text-gray-400 group-hover:bg-gray-700"
                                        }`}
                                >
                                    {project.name.charAt(0).toUpperCase()}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p
                                        className={`text-sm font-medium truncate ${isActive ? "text-white" : "text-gray-300"
                                            }`}
                                    >
                                        {project.name}
                                    </p>
                                    <p className="text-xs text-gray-600 truncate">{project.path}</p>
                                </div>
                                {isActive && (
                                    <Check className="w-4 h-4 text-blue-400 shrink-0" />
                                )}
                            </button>
                        );
                    })
                )}
            </div>

            {/* Active indicator */}
            {activeProject && (
                <div className="px-4 py-2 border-t border-gray-800/60 bg-gray-950/40">
                    <p className="text-[10px] uppercase tracking-widest text-gray-600">
                        Active: <span className="text-blue-400">{activeProject.name}</span>
                    </p>
                </div>
            )}
        </div>
    );
}
