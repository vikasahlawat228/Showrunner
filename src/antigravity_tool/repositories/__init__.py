"""Repository layer for file-based persistence.

All filesystem I/O for domain entities is routed through repositories.
The Project class delegates to these for backward compatibility.
"""

from antigravity_tool.repositories.base import YAMLRepository
from antigravity_tool.repositories.character_repo import CharacterRepository
from antigravity_tool.repositories.world_repo import WorldRepository
from antigravity_tool.repositories.chapter_repo import ChapterRepository
from antigravity_tool.repositories.story_repo import StoryRepository
from antigravity_tool.repositories.style_repo import StyleRepository
from antigravity_tool.repositories.creative_room_repo import CreativeRoomRepository

__all__ = [
    "YAMLRepository",
    "CharacterRepository",
    "WorldRepository",
    "ChapterRepository",
    "StoryRepository",
    "StyleRepository",
    "CreativeRoomRepository",
]
