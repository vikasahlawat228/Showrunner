export interface AgentConfig {
    id: string;
    name: string;
    description: string;
    icon: string;
    color: string;
    bgClass?: string;
    borderClass?: string;
    textClass?: string;
    [key: string]: any;
}

export function getAgentConfig(id: string): AgentConfig {
    return {
        id,
        name: `Agent ${id}`,
        description: `Fallback config for ${id}`,
        icon: "Bot",
        color: "bg-gray-500",
        bgClass: "bg-gray-500/20",
        borderClass: "border-gray-500/50",
        textClass: "text-gray-400",
    };
}
