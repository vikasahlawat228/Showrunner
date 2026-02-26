"""Repository layer for file-based persistence.

All filesystem I/O for domain entities is routed through repositories.
The Project class delegates to these for backward compatibility.
"""

from showrunner_tool.repositories.base import YAMLRepository
from showrunner_tool.repositories.character_repo import CharacterRepository
from showrunner_tool.repositories.world_repo import WorldRepository
from showrunner_tool.repositories.chapter_repo import ChapterRepository
from showrunner_tool.repositories.story_repo import StoryRepository
from showrunner_tool.repositories.style_repo import StyleRepository
from showrunner_tool.repositories.creative_room_repo import CreativeRoomRepository

__all__ = [
    "YAMLRepository",
    "CharacterRepository",
    "WorldRepository",
    "ChapterRepository",
    "StoryRepository",
    "StyleRepository",
    "CreativeRoomRepository",
]
