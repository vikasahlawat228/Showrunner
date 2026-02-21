# Phase F, Track 3: The Model Configuration Cascade

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 3 of Phase F**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Build `ModelConfig` Schemas**
   - Create `src/antigravity_tool/schemas/model_config.py`.
   - Implement `ModelConfig`: fields for `model` (str), `temperature` (float, default 0.7), `max_tokens` (int, default 2048), `fallback_model` (Optional[str]).
   - Implement `ProjectModelConfig`: a `default_model` (str) and a dictionary of `model_overrides` mapping agent IDs to `ModelConfig` instances.

2. **Implement `ModelConfigRegistry`**
   - Create `src/antigravity_tool/services/model_config_registry.py`.
   - This service reads the `antigravity.yaml` file from the Workspace to seed project-level defaults.
   - Implement `.resolve(step_config: dict, bucket: GenericContainer, agent_id: str) -> ModelConfig`.
   - Enforce the cascade priority order: **Step Config > Bucket Preference > Agent Default > Project Default**.

3. **Update Dependency Injection (`deps.py`)**
   - Open `src/antigravity_tool/server/deps.py`.
   - Add an LRU-cached provider for `get_model_config_registry()`.
   - Inject the new registry singleton into `get_pipeline_service()` and `get_agent_dispatcher()`.

4. **Build the Models Router**
   - Create a new FastAPI router: `src/antigravity_tool/server/routers/models.py`.
   - `GET /api/v1/models/available`: List available models (e.g., using LiteLLM).
   - `GET /api/v1/models/config`: Get the current `ProjectModelConfig`.
   - `PUT /api/v1/models/config`: Overwrite the user's `antigravity.yaml` model configurations.

Please write tests in a new file `tests/test_model_registry.py` explicitly testing that the cascade priority logic functions properly. Run the tests.
