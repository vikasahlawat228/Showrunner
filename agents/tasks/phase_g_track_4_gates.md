# Phase G, Track 4: Enhanced Approval Gates & UI

You are a Lead Software Engineer working on "Showrunner", an AI-augmented writing tool.
You are executing **Track 4 of Phase G**. Please read `docs/LOW_LEVEL_DESIGN.md` for full context on the architecture.

## Your Task

1. **Enhance `PromptReviewModal.tsx`**
   - Open `src/web/src/components/pipeline/PromptReviewModal.tsx`.
   - Add a dropdown for model selection using the `/api/v1/models/available` endpoint. When the user changes the model, include that selection in the payload back to the server.
   - Add a "Refine" text area that allows the user to append follow-up instructions to the AI prompt without manually modifying the generated output text.

2. **Backend Processing for "Chat-to-Refine"**
   - Update `src/showrunner_tool/services/pipeline_service.py` to handle the `model` and `refine_instructions` keys from the `resume_pipeline` payload.
   - If `refine_instructions` are provided, the state machine should NOT proceed to the next step. Instead, it should re-run the previous LLM generation step, appending the instructions to the user prompt.

3. **Backend Tests**
   - Create `tests/test_approval_gates.py`.
   - Write tests verifying that resuming a paused pipeline with `refine_instructions` loops back to generation with the updated prompt.
   - Write tests verifying that resuming with a `model` override correctly uses the selected model (check ModelConfigRegistry integration).

Please execute these changes and ensure all existing tests still pass.
