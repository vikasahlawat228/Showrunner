"""Project router -- project metadata and status."""

from fastapi import APIRouter, Depends

from antigravity_tool.core.project import Project
from antigravity_tool.core.workflow import WorkflowState
from antigravity_tool.server.api_schemas import ProjectResponse, HealthResponse
from antigravity_tool.server.deps import get_project

router = APIRouter(prefix="/api/v1/project", tags=["project"])


@router.get("/", response_model=ProjectResponse)
async def get_project_info(project: Project = Depends(get_project)):
    wf = WorkflowState(project.path)
    return ProjectResponse(
        name=project.name,
        path=str(project.path),
        variables=project.variables,
        workflow_step=wf.get_current_step(),
    )


@router.get("/health", response_model=HealthResponse)
async def health_check(project: Project = Depends(get_project)):
    return HealthResponse(status="ok", project=project.name)
