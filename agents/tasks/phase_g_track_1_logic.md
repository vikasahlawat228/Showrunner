# Phase G, Track 1: Logic Nodes & Pipeline Evolution

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 1 of Phase G**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Extend Pipeline Schemas**
   - Open `src/antigravity_tool/schemas/pipeline_steps.py`.
   - Add `IF_ELSE`, `LOOP`, and `MERGE_OUTPUTS` to the `StepType` enum.
   - Add `LOGIC` to the `StepCategory` enum.
   - Ensure `PipelineStepDef.config` is flexible enough to store logic-specific fields like `condition` (str), `true_target` (str), `false_target` (str), and `loop_back_to` (str).

2. **Implement Logic Execution in `PipelineService`**
   - Open `src/antigravity_tool/services/pipeline_service.py`.
   - Update `_run_composable_pipeline` to handle the new logic steps:
     - **`IF_ELSE`**: Use `jsonpath-ng` (or a similar lightweight logic) to evaluate the `condition` against the current payload. Route the state machine to the correct next step based on the boolean result.
     - **`LOOP`**: Implement a simple iteration counter. If the `condition` is not met and `max_iterations` hasn't been reached, route the state machine back to the `loop_back_to` step ID.
     - **`MERGE_OUTPUTS`**: Collect outputs from parallel branches into a single merged dictionary.

3. **Backend Tests**
   - Create `tests/test_pipeline_logic.py`.
   - Write tests for a branching pipeline (If X > 5 then A else B) and a looping pipeline (Run step A until 'ready' == true).

Please execute these changes and ensure all existing pipeline tests still pass.
