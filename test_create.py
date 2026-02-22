import sys
import logging
from antigravity_tool.services.chat_tool_registry import build_tool_registry
from antigravity_tool.repositories.container_repo import ContainerRepository
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.ERROR)

project_path = "/Users/vikasahlawat/Documents/writing_tool"
container_repo = ContainerRepository(project_path)

registry = build_tool_registry(
    kg_service=None,
    container_repo=container_repo,
    project_path=project_path
)

try:
    print(registry["create"]("I want to create a dialogue style for my noir chapters.", []))
except Exception as e:
    import traceback
    traceback.print_exc()
