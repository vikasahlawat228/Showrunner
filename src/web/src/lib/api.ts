// ── Response Types ────────────────────────────────────────────

export interface ProjectInfo {
  name: string;
  path: string;
  variables: Record<string, unknown>;
  workflow_step: string;
}

export interface HealthResponse {
  status: string;
  project: string;
}

export interface CharacterSummary {
  id: string;
  name: string;
  role: string;
  one_line: string;
  has_dna: boolean;
}

export interface SceneSummary {
  id: string;
  title: string;
  chapter: number;
  scene_number: number;
  scene_type: string;
  tension_level: number;
  characters_present: string[];
}

export interface SceneDetail extends SceneSummary {
  pov_character_id: string | null;
  location_name: string;
  mood: string;
  summary: string;
}

export interface UpdateSceneRequest {
  characters_present?: string[];
}

export interface PanelLayoutHint {
  panel_number: number;
  panel_type: string;
  camera_angle: string;
  size_hint: 'large' | 'medium' | 'small' | 'splash';
  description_hint: string;
  composition_notes: string;
}

export interface LayoutSuggestion {
  beat_type: string;
  suggested_panel_count: number;
  layout: PanelLayoutHint[];
  reasoning: string;
  pacing_notes: string;
}

export interface WorkflowStepInfo {
  step: string;
  label: string;
  status: string;
}

export interface WorkflowTemplate {
  template_id: string;
  name: string;
  description: string;
  category: string;
  steps: any[];
  edges: any[];
}

export interface WorkflowResponse {
  current_step: string;
  current_chapter: number | null;
  current_scene: number | null;
  steps: WorkflowStepInfo[];
}

export interface DirectorResult {
  step_executed: string;
  status: string;
  files_created: string[];
  files_modified: string[];
  next_step: string | null;
  message: string;
}

export interface PromptResponse {
  prompt_text: string;
  step: string;
  template_used: string;
  context_keys: string[];
}

export interface BrainstormSuggestion {
  suggested_edges: Array<{ source: string; target: string; label: string; reasoning: string }>;
  suggested_cards: Array<{ text: string; near_card_id: string; reasoning: string }>;
  themes: Array<{ name: string; card_ids: string[] }>;
}

// ── Analysis Types ──────────────────────────────────────────

export interface VoiceProfile {
  character_id: string;
  character_name: string;
  avg_sentence_length: number;
  vocabulary_diversity: number;
  formality_score: number;
  top_phrases: string[];
  dialogue_sample_count: number;
}

export interface VoiceScorecardResponse {
  profiles: VoiceProfile[];
  similarity_matrix: Array<{ char_a: string; char_b: string; similarity: number }>;
  warnings: string[];
}

// ── Research Types ──────────────────────────────────────────

export interface ResearchResult {
  id: string;
  name: string;
  original_query: string;
  summary: string;
  confidence_score: string;
  key_facts: string[];
  constraints: string[];
  story_implications: string[];
  sources: string[];
}

export interface ResearchLibraryResponse {
  items: ResearchResult[];
  total: number;
}

// ── Character Detail Types ──────────────────────────────────

export interface FacialFeatures {
  face_shape: string;
  jaw: string;
  eyes: string;
  eye_color: string;
  nose: string;
  mouth: string;
  skin_tone: string;
  distinguishing_marks: string[];
  eyebrows?: string;
  ears?: string;
}

export interface HairDescription {
  style: string;
  length: string;
  color: string;
  texture: string;
  hairline?: string;
  notable_details?: string;
}

export interface BodyDescription {
  height: string;
  build: string;
  posture: string;
  notable_features: string[];
}

export interface OutfitCanon {
  name: string;
  description: string;
  colors: string[];
  key_items: string[];
  prompt_tokens: string;
}

export interface CharacterDNA {
  face: FacialFeatures;
  hair: HairDescription;
  body: BodyDescription;
  default_outfit: OutfitCanon;
  additional_outfits: OutfitCanon[];
  age_appearance: string;
  gender_presentation: string;
  species: string;
}

export interface Personality {
  traits: string[];
  fears: string[];
  desires: string[];
  speech_pattern: string;
  verbal_tics: string[];
  internal_conflict: string;
}

export interface CharacterArc {
  starting_state: string;
  catalyst: string;
  progression: string[];
  ending_state: string;
  arc_type: string;
}

export interface Relationship {
  target_character_id: string;
  target_character_name: string;
  relationship_type: string;
  description: string;
  dynamic: string;
  known_to_reader: boolean;
}

export interface CharacterDetail {
  id: string;
  name: string;
  aliases: string[];
  role: string;
  one_line: string;
  backstory: string;
  personality: Personality;
  dna: CharacterDNA | null;
  arc: CharacterArc | null;
  relationships: Relationship[];
  first_appearance?: string;
  tags: string[];
}

// ── World Detail Types ──────────────────────────────────────

export interface WorldLocation {
  id: string;
  name: string;
  type: string;
  description: string;
  atmosphere: string;
  visual_description: string;
  notable_features: string[];
  connected_to: string[];
  tags: string[];
}

export interface WorldRule {
  name: string;
  category: string;
  description: string;
  limitations: string[];
  known_to_reader: boolean;
}

export interface Faction {
  id: string;
  name: string;
  type: string;
  description: string;
  goals: string[];
  visual_motif: string;
  tags: string[];
}

export interface HistoricalEvent {
  name: string;
  period: string;
  description: string;
  impact: string;
  known_to_reader: boolean;
}

export interface WorldSettings {
  id: string;
  name: string;
  genre: string;
  time_period: string;
  tone: string;
  one_line: string;
  description: string;
  locations: WorldLocation[];
  rules: WorldRule[];
  factions: Faction[];
  history: HistoricalEvent[];
  technology_level: string;
  cultural_notes: string[];
}

// ── Schema Builder Types ────────────────────────────────────

export type FieldType =
  | "string"
  | "integer"
  | "float"
  | "boolean"
  | "list[string]"
  | "json"
  | "enum"
  | "reference";

export interface FieldDefinition {
  id: string;
  name: string;
  field_type: FieldType;
  description?: string;
  default?: unknown;
  required: boolean;
  options?: string[];    // For enum fields
  target_type?: string;  // For reference fields
}

export interface ContainerSchema {
  id: string;
  name: string;
  display_name: string;
  description?: string;
  fields: FieldDefinition[];
  created_at?: string;
  updated_at?: string;
}

export interface GenerateFieldsRequest {
  prompt: string;
  existing_schemas?: string[];
}

export interface GenerateFieldsResponse {
  fields: FieldDefinition[];
}

// ── Request Types ────────────────────────────────────────────

export interface CreateCharacterRequest {
  name: string;
  role?: string;
}

export interface DirectorActRequest {
  step_override?: string | null;
}

// ── API Client ───────────────────────────────────────────────

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, init);
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.error || body?.detail || `API ${res.status}: ${path}`);
  }
  return res.json();
}

function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

function put<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function patch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function del(path: string): Promise<void> {
  return request<void>(path, { method: "DELETE" });
}


export interface GraphResponse {
  nodes: any[];
  edges: any[];
}

export interface TimelineEvent {
  id: string;
  parent_event_id: string | null;
  branch_id: string;
  timestamp: string;
  event_type: string;
  container_id: string;
  payload: any;
}

export interface BranchInfo {
  id: string;
  head_event_id: string | null;
  event_count: number;
}

export interface BranchComparison {
  branch_a: string;
  branch_b: string;
  only_in_a: Array<{ container_id: string; state: Record<string, unknown> }>;
  only_in_b: Array<{ container_id: string; state: Record<string, unknown> }>;
  different: Array<{ container_id: string; state_a: Record<string, unknown>; state_b: Record<string, unknown> }>;
  same_count: number;
}

export const api = {
  // Project
  getProject: () => request<ProjectInfo>("/api/v1/project/"),
  getHealth: () => request<HealthResponse>("/api/v1/project/health"),

  // Analysis
  getVoiceScorecard: (characterIds?: string[]) =>
    request<VoiceScorecardResponse>(
      characterIds
        ? `/api/v1/analysis/voice-scorecard?character_ids=${characterIds.join(",")}`
        : "/api/v1/analysis/voice-scorecard"
    ),
  getContinuityIssues: (scope: string = "all", scopeId?: string) =>
    request<ContinuityCheckResponse[]>(
      `/api/v1/analysis/continuity-issues?scope=${encodeURIComponent(scope)}${scopeId ? `&scope_id=${encodeURIComponent(scopeId)}` : ""}`
    ),
  checkContinuity: (containerId: string, proposedChanges?: Record<string, any>) =>
    post<ContinuityCheckResponse>("/api/v1/analysis/continuity-check", { container_id: containerId, proposed_changes: proposedChanges }),
  checkContinuityScene: (sceneId: string) =>
    post<ContinuityCheckResponse[]>(`/api/v1/analysis/continuity-check/scene/${encodeURIComponent(sceneId)}`),
  checkStyle: (text: string, sceneId?: string) =>
    post<StyleCheckResponse>("/api/v1/analysis/style-check", { text, scene_id: sceneId }),

  // Characters
  getCharacters: () => request<CharacterSummary[]>("/api/v1/characters/"),
  getCharacter: (name: string) =>
    request<CharacterDetail>(`/api/v1/characters/${encodeURIComponent(name)}`),

  // World
  getWorld: () => request<WorldSettings>("/api/v1/world/"),

  // Chapters / Scenes / Panels
  getScenes: (chapter: number) =>
    request<SceneSummary[]>(`/api/v1/chapters/${chapter}/scenes`),
  getScene: (chapter: number, sceneNum: number) =>
    request<SceneDetail>(`/api/v1/chapters/${chapter}/scenes/${sceneNum}`),
  updateScene: (chapter: number, sceneNum: number, body: UpdateSceneRequest) =>
    patch<SceneDetail>(`/api/v1/chapters/${chapter}/scenes/${sceneNum}`, body),
  getPanels: (chapter: number) =>
    request<Record<string, unknown>[]>(`/api/v1/chapters/${chapter}/panels`),

  // Workflow
  getWorkflow: () => request<WorkflowResponse>("/api/v1/workflow/"),

  // Director
  directorAct: (req?: DirectorActRequest) =>
    post<DirectorResult>("/api/v1/director/act", req ?? {}),
  getDirectorStatus: () =>
    request<{ current_step: string }>("/api/v1/director/status"),
  directorDispatch: (intent: string, context?: Record<string, unknown>) =>
    post<AgentDispatchResult>("/api/v1/director/dispatch", { intent, context: context ?? {} }),
  getAgentSkills: () =>
    request<AgentSkillSummary[]>("/api/v1/director/skills"),

  // Brainstorm
  getBrainstormCards: () =>
    request<any[]>("/api/v1/director/brainstorm/cards"),
  saveBrainstormCard: (body: { text: string; position_x: number; position_y: number; color?: string; tags?: string[] }) =>
    post<any>("/api/v1/director/brainstorm/save-card", body),
  deleteBrainstormCard: (cardId: string) =>
    del(`/api/v1/director/brainstorm/cards/${encodeURIComponent(cardId)}`),
  suggestBrainstormConnections: (body: { cards: Array<{ id: string; text: string; x: number; y: number }>; intent?: string }) =>
    post<BrainstormSuggestion>("/api/v1/director/brainstorm/suggest-connections", body),

  // Schemas
  getSchemas: () => request<ContainerSchema[]>("/api/v1/schemas/"),
  getSchema: (id: string) =>
    request<ContainerSchema>(`/api/v1/schemas/${encodeURIComponent(id)}`),
  createSchema: (schema: Omit<ContainerSchema, "id" | "created_at" | "updated_at">) =>
    post<ContainerSchema>("/api/v1/schemas/", schema),
  updateSchema: (id: string, schema: Partial<ContainerSchema>) =>
    put<ContainerSchema>(`/api/v1/schemas/${encodeURIComponent(id)}`, schema),
  deleteSchema: (id: string) =>
    del(`/api/v1/schemas/${encodeURIComponent(id)}`),
  generateFields: (req: GenerateFieldsRequest) =>
    post<GenerateFieldsResponse>("/api/v1/schemas/generate", req),

  // Knowledge Graph
  getGraph: () => request<GraphResponse>("/api/v1/graph/"),

  // Pipeline execution
  startPipeline: (initialPayload?: any, definitionId?: string) =>
    post<{ run_id: string }>("/api/v1/pipeline/run", {
      initial_payload: initialPayload || {},
      definition_id: definitionId || null,
    }),
  resumePipeline: (runId: string, payload: any) =>
    post<{ status: string; run_id: string }>(`/api/v1/pipeline/${runId}/resume`, { payload }),

  // Research
  queryResearch: (query: string) =>
    post<ResearchResult>("/api/v1/research/query", { query }),
  getResearchLibrary: () =>
    request<ResearchLibraryResponse>("/api/v1/research/library"),
  getResearchTopic: (id: string) =>
    request<ResearchResult>(`/api/v1/research/library/${encodeURIComponent(id)}`),

  // Pipeline definitions (composable)
  getPipelineStepRegistry: () =>
    request<any[]>("/api/v1/pipeline/steps/registry"),
  getWorkflowTemplates: () =>
    request<WorkflowTemplate[]>("/api/v1/pipeline/templates"),
  createFromTemplate: (templateId: string) =>
    post<any>(`/api/v1/pipeline/templates/${encodeURIComponent(templateId)}/create`),
  getPipelineDefinitions: () =>
    request<any[]>("/api/v1/pipeline/definitions"),
  getPipelineDefinition: (id: string) =>
    request<any>(`/api/v1/pipeline/definitions/${encodeURIComponent(id)}`),
  createPipelineDefinition: (body: any) =>
    post<any>("/api/v1/pipeline/definitions", body),
  updatePipelineDefinition: (id: string, body: any) =>
    put<any>(`/api/v1/pipeline/definitions/${encodeURIComponent(id)}`, body),
  deletePipelineDefinition: (id: string) =>
    del(`/api/v1/pipeline/definitions/${encodeURIComponent(id)}`),

  // Timeline & Event Sourcing
  getTimelineEvents: () => request<TimelineEvent[]>("/api/v1/timeline/events"),
  checkoutEvent: (eventId: string, branchName?: string) =>
    post<{ status: string; event_id: string; branch?: string }>("/api/v1/timeline/checkout", { event_id: eventId, branch_name: branchName }),
  getBranches: () =>
    request<BranchInfo[]>("/api/v1/timeline/branches"),
  createBranch: (body: { branch_name: string; parent_event_id: string; source_branch_id?: string }) =>
    post<{ status: string; branch_name: string; parent_event_id: string }>("/api/v1/timeline/branch", body),
  getBranchEvents: (branchId: string) =>
    request<TimelineEvent[]>(`/api/v1/timeline/branch/${encodeURIComponent(branchId)}/events`),
  compareBranches: (branchA: string, branchB: string) =>
    request<BranchComparison>(`/api/v1/timeline/compare?branch_a=${encodeURIComponent(branchA)}&branch_b=${encodeURIComponent(branchB)}`),

  // Zen Mode — Writing Surface
  saveFragment: (data: FragmentCreateRequest) =>
    post<FragmentResponse>("/api/v1/writing/fragments", data),
  detectEntities: (text: string) =>
    post<EntityDetectionResponse>("/api/v1/writing/detect-entities", { text }),
  getContainerContext: (containerId: string) =>
    request<ContainerContextResponse>(`/api/v1/writing/context/${encodeURIComponent(containerId)}`),
  searchContainers: (q: string, limit = 10) =>
    request<ContainerSearchResult[]>(`/api/v1/writing/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  searchEntities: (q: string, limit = 10) =>
    request<ContainerSearchResult[]>(`/api/v1/writing/search?q=${encodeURIComponent(q)}&limit=${limit}`),
  semanticSearchContainers: (q: string, limit = 8) =>
    request<Array<ContainerSearchResult & { similarity?: number }>>(`/api/v1/writing/semantic-search?q=${encodeURIComponent(q)}&limit=${limit}`),

  // Translation
  translateText: (body: {
    text: string;
    source_language?: string;
    target_language?: string;
    character_ids?: string[];
    scene_id?: string;
  }) => post<TranslateResponse>("/api/v1/translation/translate", body),
  getGlossary: () => request<GlossaryEntry[]>("/api/v1/translation/glossary"),
  saveGlossaryEntry: (body: { term: string; translations: Record<string, string>; notes?: string }) =>
    post<GlossaryEntry>("/api/v1/translation/glossary", body),

  // Chat
  getChatSessions: (projectId?: string) =>
    request<any[]>(
      projectId
        ? `/api/v1/chat/sessions?project_id=${encodeURIComponent(projectId)}`
        : "/api/v1/chat/sessions"
    ),
  createChatSession: (body: { name?: string; project_id?: string; autonomy_level?: number; tags?: string[] }) =>
    post<any>("/api/v1/chat/sessions", body),
  getChatSession: (sessionId: string) =>
    request<any>(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`),
  deleteChatSession: (sessionId: string) =>
    del(`/api/v1/chat/sessions/${encodeURIComponent(sessionId)}`),
  getChatMessages: (sessionId: string, limit = 100, offset = 0) =>
    request<any[]>(
      `/api/v1/chat/sessions/${encodeURIComponent(sessionId)}/messages?limit=${limit}&offset=${offset}`
    ),
  // Note: sendMessage uses SSE streaming via useChatStream hook, not this API client

  // DB Maintenance
  getDBHealth: () => request<any>("/api/v1/db/health"),
  getDBStats: () => request<any>("/api/v1/db/stats"),
  runDBCheck: () => post<any>("/api/v1/db/check"),
  runDBReindex: () => post<any>("/api/v1/db/reindex"),

  // Storyboard
  getStoryboardPanels: (sceneId: string) =>
    request<any[]>(`/api/v1/storyboard/scenes/${encodeURIComponent(sceneId)}/panels`),
  createStoryboardPanel: (body: any) =>
    post<any>("/api/v1/storyboard/panels", body),
  updateStoryboardPanel: (panelId: string, body: any) =>
    put<any>(`/api/v1/storyboard/panels/${encodeURIComponent(panelId)}`, body),
  deleteStoryboardPanel: (panelId: string) =>
    del(`/api/v1/storyboard/panels/${encodeURIComponent(panelId)}`),
  reorderStoryboardPanels: (sceneId: string, panelIds: string[]) =>
    post<any[]>("/api/v1/storyboard/panels/reorder", { scene_id: sceneId, panel_ids: panelIds }),
  generateStoryboardPanels: (sceneId: string, count = 6, style = "manga") =>
    post<any[]>(`/api/v1/storyboard/scenes/${encodeURIComponent(sceneId)}/generate`, { panel_count: count, style }),
  suggestLayout: (sceneId: string) =>
    post<LayoutSuggestion>(`/api/v1/storyboard/scenes/${encodeURIComponent(sceneId)}/suggest-layout`),

  // Voice-to-Scene
  voiceToScene: (sceneText: string, sceneName?: string, panelCount?: number, style?: string) => {
    const formData = new FormData();
    formData.append("scene_text", sceneText);
    if (sceneName) formData.append("scene_name", sceneName);
    if (panelCount) formData.append("panel_count", panelCount.toString());
    if (style) formData.append("style", style);

    return request<{ layout_suggestion: LayoutSuggestion; panels: any[]; scene_text: string }>(
      "/api/v1/storyboard/voice-to-scene",
      {
        method: "POST",
        body: formData, // Don't use standard post() helper because this needs multipart/form-data
      }
    );
  },

  // Models
  getAvailableModels: () => request<string[]>("/api/v1/models/available"),
  getModelConfig: () => request<ProjectModelConfig>("/api/v1/models/config"),
  updateModelConfig: (body: ProjectModelConfig) =>
    put<ProjectModelConfig>("/api/v1/models/config", body),

  // Projects (multi-project)
  listProjects: () => request<ProjectSummary[]>("/api/v1/projects/"),
  getProjectStructure: async () => {
    const res = await request<{ roots: StructureNode[] }>("/api/v1/projects/structure");
    return res.roots;
  },

  // Analysis
  getEmotionalArc: (chapter?: number) =>
    request<EmotionalArcResponse>(
      chapter ? `/api/v1/analysis/emotional-arc?chapter=${chapter}` : "/api/v1/analysis/emotional-arc"
    ),
  getCharacterRibbons: (chapter?: number) =>
    request<CharacterRibbonResponse[]>(
      chapter ? `/api/v1/analysis/ribbons?chapter=${chapter}` : "/api/v1/analysis/ribbons"
    ),

  // Pipeline runs (query)
  getPipelineRuns: (state?: string) =>
    request<PipelineRunSummary[]>(
      state
        ? `/api/v1/pipeline/runs?state=${encodeURIComponent(state)}`
        : "/api/v1/pipeline/runs"
    ),

  // Pipeline definition tools
  generatePipelineFromNL: (body: { intent: string; title: string }) =>
    post<PipelineDefinitionResponse>("/api/v1/pipeline/definitions/generate", body),

  // Containers
  createContainer: (body: { container_type: string; name: string; parent_id?: string; attributes?: Record<string, unknown>; sort_order?: number }) =>
    post<any>("/api/v1/containers", body),
  getContainer: (id: string) =>
    request<any>(`/api/v1/containers/${encodeURIComponent(id)}`),
  updateContainer: (id: string, body: any) =>
    put<any>(`/api/v1/containers/${encodeURIComponent(id)}`, body),
  deleteContainer: (id: string) =>
    del(`/api/v1/containers/${encodeURIComponent(id)}`),
  reorderContainers: (items: Array<{ id: string; sort_order: number }>) =>
    post("/api/v1/containers/reorder", { items }),

  // Character Progressions
  getCharacterProgressions: (characterId: string) =>
    request<CharacterProgression[]>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions`),
  addCharacterProgression: (characterId: string, body: ProgressionCreateRequest) =>
    post<CharacterProgression>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions`, body),
  updateCharacterProgression: (characterId: string, progressionId: string, body: Partial<ProgressionCreateRequest>) =>
    put<CharacterProgression>(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions/${encodeURIComponent(progressionId)}`, body),
  deleteCharacterProgression: (characterId: string, progressionId: string) =>
    del(`/api/v1/characters/${encodeURIComponent(characterId)}/progressions/${encodeURIComponent(progressionId)}`),
  getDNAAtChapter: (characterId: string, chapter: number) =>
    request<ResolvedDNAResponse>(`/api/v1/characters/${encodeURIComponent(characterId)}/dna-at-chapter/${chapter}`),

  // Reader Preview
  getReadingSimScene: (sceneId: string) =>
    request<ReadingSimResult>(`/api/v1/preview/scene/${encodeURIComponent(sceneId)}`),
  getReadingSimChapter: (chapter: number) =>
    request<ReadingSimResult[]>(`/api/v1/preview/chapter/${chapter}`),

  // Export
  exportManuscript: async (): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/v1/export/manuscript`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
  },
  exportBundle: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/api/v1/export/bundle`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.json();
  },
  exportScreenplay: async (): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/v1/export/screenplay`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
  },
  exportHTML: async (): Promise<Blob> => {
    const res = await fetch(`${API_BASE}/api/v1/export/html`, { method: 'POST' });
    if (!res.ok) throw new Error('Export failed');
    return res.blob();
  },
  exportPreview: async (): Promise<string> => {
    const res = await fetch(`${API_BASE}/api/v1/export/preview`, { method: 'POST' });
    if (!res.ok) throw new Error('Export preview failed');
    return res.text();
  },
};

// ── Zen Mode Types ──────────────────────────────────────────

export interface FragmentCreateRequest {
  text: string;
  title?: string;
  scene_id?: string;
  chapter?: number;
  branch_id?: string;
  associated_containers?: string[];
  metadata?: Record<string, unknown>;
}

export interface FragmentResponse {
  id: string;
  text: string;
  title?: string;
  associated_containers: string[];
  detected_entities: EntityDetection[];
  word_count: number;
}

export interface EntityDetection {
  mention: string;
  container_id: string;
  container_type: string;
  container_name: string;
  confidence: number;
}

export interface EntityDetectionResponse {
  entities: EntityDetection[];
}

export interface ContainerContextResponse {
  container_id: string;
  container_type: string;
  name: string;
  context_text: string;
  attributes: Record<string, unknown>;
  related_count: number;
}

export interface ContainerSearchResult {
  id: string;
  name: string;
  container_type: string;
  attributes: Record<string, unknown>;
  score: number;
}

// ── Project & Model Config Types ────────────────────────────

export interface ProjectSummary {
  id: string;
  name: string;
  path: string;
  created_at?: string;
}

export interface StructureNode {
  id: string;
  name: string;
  container_type: string;
  parent_id: string | null;
  sort_order: number;
  children?: StructureNode[];
}

export interface ModelConfigEntry {
  model: string;
  temperature: number;
  max_tokens: number;
  fallback_model?: string | null;
}

export interface ProjectModelConfig {
  default_model: string;
  model_overrides: Record<string, ModelConfigEntry>;
}

export interface PipelineRunSummary {
  id: string;
  definition_id: string | null;
  title: string;
  state: string;
  current_step_name: string | null;
  created_at: string;
  updated_at: string;
}

// ── Agent Dispatch Types ─────────────────────────────────────

export interface AgentDispatchResult {
  skill_used: string;
  response: string;
  actions: Record<string, unknown>[];
  success: boolean;
  error?: string | null;
  model_used: string;
  context_used: string[];
}

export interface AgentSkillSummary {
  id: string;
  name: string;
  description: string;
  keywords: string[];
}

// ── Analysis Types ───────────────────────────────────────────

export interface EmotionalScoreResponse {
  scene_id: string;
  scene_name: string;
  chapter: number;
  scene_number: number;
  hope: number;
  conflict: number;
  tension: number;
  sadness: number;
  joy: number;
  dominant_emotion: string;
  summary: string;
}

export interface EmotionalArcResponse {
  scores: EmotionalScoreResponse[];
  flat_zones: Record<string, any>[];
  peak_moments: Record<string, any>[];
  pacing_grade: string;
  recommendations: string[];
}

export interface CharacterRibbonResponse {
  scene_id: string;
  scene_name: string;
  chapter: number;
  scene_number: number;
  characters: Record<string, any>[];
}

// ── Character Progressions ───────────────────────────────────

export interface CharacterProgression {
  id: string;
  chapter: number;
  label: string;
  changes: Record<string, any>;
  notes: string;
}

export interface ProgressionCreateRequest {
  chapter: number;
  label: string;
  changes: Record<string, any>;
  notes: string;
}

export interface ResolvedDNAResponse {
  character_id: string;
  character_name: string;
  chapter: number;
  resolved_dna: Record<string, any>;
  progressions_applied: string[];
}

// ── Reader Simulator ─────────────────────────────────────────

export interface PanelReadingMetrics {
  panel_id: string;
  panel_number: number;
  panel_type: string;
  estimated_reading_seconds: number;
  text_density: number;
  is_info_dense: boolean;
  pacing_type: string;
}

export interface ReadingSimResult {
  scene_id: string;
  scene_name: string;
  total_reading_seconds: number;
  panels: PanelReadingMetrics[];
  pacing_dead_zones: Array<Record<string, any>>;
  info_overload_warnings: Array<Record<string, any>>;
  engagement_score: number;
  recommendations: string[];
}

// ── Continuity Checker ───────────────────────────────────────

export interface ContinuityCheckResponse {
  status: string;
  reasoning: string;
  suggestions: string;
  affected_entities: string[];
  severity: string;
}

// ── Style Checker ────────────────────────────────────────────

export interface StyleIssueResponse {
  category: string;
  severity: string;
  location: string;
  description: string;
  suggestion: string;
}

export interface StyleCheckResponse {
  status: string;
  overall_score: number;
  issues: StyleIssueResponse[];
  strengths: string[];
  summary: string;
}

// ── Translation & Pipeline Definition generated types ───────

export interface PipelineDefinitionResponse {
  id: string;
  name: string;
  description: string;
  data: any; // pipeline dag
}

export interface AdaptationNote {
  original: string;
  adapted: string;
  reason: string;
}

export interface CulturalFlag {
  location: string;
  flag: string;
  action_taken: string;
}

export interface TranslateResponse {
  translated_text: string;
  source_language: string;
  target_language: string;
  adaptation_notes: AdaptationNote[];
  cultural_flags: CulturalFlag[];
  glossary_applied: Record<string, string>;
  confidence: number;
}

export interface GlossaryEntry {
  id: string;
  term: string;
  translations: Record<string, string>;
  notes: string;
}

// ── Export Types ─────────────────────────────────────────────

export type ExportFormat = 'markdown' | 'json' | 'fountain' | 'html';
