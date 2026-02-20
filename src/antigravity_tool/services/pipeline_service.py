"""Core service logic for the SSE event pipeline engine."""

import asyncio
import json
from typing import AsyncGenerator
import ulid

from antigravity_tool.schemas.pipeline import PipelineState, PipelineRun

class PipelineService:
    """Manages state-machine pipelines and Server-Sent Events (SSE) streaming."""
    
    # Simple in-memory storage for active runs
    _runs: dict[str, PipelineRun] = {}
    
    # asyncio Events to handle pausing/resuming
    _events: dict[str, asyncio.Event] = {}

    @classmethod
    async def start_pipeline(cls, initial_payload: dict) -> str:
        """Initializes a run, starts the background task, and returns its ID."""
        run_id = str(ulid.ULID())
        run = PipelineRun(
            id=run_id,
            current_state=PipelineState.CONTEXT_GATHERING,
            payload=initial_payload
        )
        cls._runs[run_id] = run
        cls._events[run_id] = asyncio.Event()

        # Start the pipeline background task
        asyncio.create_task(cls._run_pipeline_logic(run_id))
        
        return run_id

    @classmethod
    async def _run_pipeline_logic(cls, run_id: str):
        """Simulates/Runs the state machine transitions."""
        run = cls._runs.get(run_id)
        if not run:
            return

        try:
            # State: CONTEXT_GATHERING
            # (Run begins here)
            await asyncio.sleep(1) # Simulate real work
            
            # Transite to -> PROMPT_ASSEMBLY
            run.current_state = PipelineState.PROMPT_ASSEMBLY
            await asyncio.sleep(1) # Simulate real work

            # Populate the payload with assembled prompt before pausing.
            # In a real pipeline, the context compiler would populate this
            # with the actual assembled LLM prompt from gathered containers.
            run.payload = {
                **run.payload,
                "prompt_text": (
                    f"[Assembled prompt for pipeline run {run_id}]\n\n"
                    "You are a creative writing assistant working on a manga/manhwa story.\n\n"
                    "## Gathered Context\n"
                    "- Characters, scenes, and world data have been compiled.\n\n"
                    "## Instructions\n"
                    "Review and edit this prompt before AI execution begins."
                ),
                "step_name": "Prompt Assembly",
            }

            # Transite to -> PAUSED_FOR_USER
            # Waiting for the frontend user to review the system prompt
            run.current_state = PipelineState.PAUSED_FOR_USER
            
            # Block execution until resumed
            event = cls._events.get(run_id)
            if event:
                await event.wait()
            
            # Transite to -> EXECUTING
            # AI generation phase
            run.current_state = PipelineState.EXECUTING
            await asyncio.sleep(2) # Simulate AI inference
            
            # Transite to -> COMPLETED
            run.current_state = PipelineState.COMPLETED
            
        except Exception as e:
            run.current_state = PipelineState.FAILED
            run.error = str(e)
            
        finally:
            # Clean up asyncio.Event, keep run for historical tracking or cleanup later
            if run_id in cls._events:
                del cls._events[run_id]

    @classmethod
    async def stream_pipeline(cls, run_id: str) -> AsyncGenerator[str, None]:
        """Provides SSE stream for the given run_id's state changes."""
        run = cls._runs.get(run_id)
        if not run:
            yield f"data: {json.dumps({'error': 'Run not found'})}\n\n"
            return
            
        last_state = None
        while True:
            # Double check existence 
            run = cls._runs.get(run_id)
            if not run:
                break
                
            if run.current_state != last_state:
                last_state = run.current_state
                
                # yield SSE data payload
                # Note: `model_dump_json` correctly serializes enum and datetime types for pydantic v2
                data = run.model_dump_json()
                yield f"data: {data}\n\n"
                
                # Terminal states stop the stream
                if run.current_state in [PipelineState.COMPLETED, PipelineState.FAILED]:
                    break
            
            # Avoid busy blocking, realistically this could use its own asyncio.Condition 
            # to wake exactly when state is updated, but short polling is acceptable here for simplicity
            await asyncio.sleep(0.1)

    @classmethod
    async def resume_pipeline(cls, run_id: str, new_payload: dict):
        """Resume a paused pipeline run with user edits/updates."""
        run = cls._runs.get(run_id)
        if not run:
            raise ValueError(f"Pipeline Run {run_id} not found")
            
        if run.current_state != PipelineState.PAUSED_FOR_USER:
            raise ValueError(f"Pipeline Run {run_id} is not paused (currently {run.current_state})")
            
        # Update payload 
        run.payload = new_payload
        
        # Unblock the background task
        event = cls._events.get(run_id)
        if event:
            event.set()
