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

export interface WorkflowStepInfo {
  step: string;
  label: string;
  status: string;
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

export const api = {
  // Project
  getProject: () => request<ProjectInfo>("/api/v1/project/"),
  getHealth: () => request<HealthResponse>("/api/v1/project/health"),

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
  startPipeline: (initialPayload?: any) =>
    post<{ run_id: string }>("/api/pipeline/run", { initial_payload: initialPayload || {} }),
  resumePipeline: (runId: string, payload: any) =>
    post<{ status: string; run_id: string }>(`/api/pipeline/${runId}/resume`, { payload }),

  // Timeline & Event Sourcing
  getTimelineEvents: () => request<TimelineEvent[]>("/api/v1/timeline/events"),
  checkoutEvent: (eventId: string, branchName?: string) =>
    post<{ status: string; event_id: string; branch?: string }>("/api/v1/timeline/checkout", { event_id: eventId, branch_name: branchName }),
};
