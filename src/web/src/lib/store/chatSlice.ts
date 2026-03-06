export interface ChatEvent {
    event_type: string;
    data: any;
}

export interface ChatMessage {
    role: string;
    content: string;
}

export interface ChatActionTrace {
    agent: string;
    action: string;
}

export interface ChatArtifact {
    id: string;
    content: string;
}

export interface ChatSessionSummary { id: string; name?: string; updated_at?: string; [key: string]: any; }
