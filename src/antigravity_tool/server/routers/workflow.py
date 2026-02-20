"""Workflow router -- workflow state and progression."""

from fastapi import APIRouter, Depends

from antigravity_tool.core.project import Project
from antigravity_tool.core.workflow import WorkflowState
from antigravity_tool.server.api_schemas import WorkflowResponse, WorkflowStepInfo
from antigravity_tool.server.deps import get_project

router = APIRouter(prefix="/api/v1/workflow", tags=["workflow"])


@router.get("/", response_model=WorkflowResponse)
async def get_workflow(project: Project = Depends(get_project)):
    wf = WorkflowState(project.path)
    steps = [
        WorkflowStepInfo(step=step, label=label, status=status)
        for step, label, status in wf.get_progress_summary()
    ]
    return WorkflowResponse(
        current_step=wf.get_current_step(),
        current_chapter=wf.get_current_chapter(),
        current_scene=wf.get_current_scene(),
        steps=steps,
    )
