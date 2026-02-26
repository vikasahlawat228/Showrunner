"""Creative room service -- author-only data with access-level enforcement."""

from __future__ import annotations

from typing import Optional

from showrunner_tool.core.creative_room import CreativeRoomManager
from showrunner_tool.errors import ContextIsolationError
from showrunner_tool.schemas.creative_room import (
    CreativeRoom,
    PlotTwist,
    CharacterSecret,
    ForeshadowingEntry,
    ReaderKnowledgeState,
)
from showrunner_tool.services.base import ServiceContext


class CreativeRoomService:
    """Access to creative room data with isolation enforcement.

    All methods here provide author-level access. Callers must ensure
    they are in an appropriate context (evaluation, creative-room commands).
    """

    def __init__(self, ctx: ServiceContext):
        self.ctx = ctx
        self._manager = CreativeRoomManager(ctx.project)

    def get_room(self) -> Optional[CreativeRoom]:
        """Load the full creative room."""
        return self.ctx.project.load_creative_room()

    def add_plot_twist(self, twist: PlotTwist) -> None:
        """Add a plot twist to the creative room."""
        self._manager.add_plot_twist(twist)

    def list_plot_twists(self) -> list[PlotTwist]:
        """List all plot twists."""
        return self._manager.list_plot_twists()

    def add_character_secret(self, secret: CharacterSecret) -> None:
        """Add a character secret to the creative room."""
        self._manager.add_character_secret(secret)

    def list_character_secrets(self) -> list[CharacterSecret]:
        """List all character secrets."""
        return self._manager.list_character_secrets()

    def list_foreshadowing(self) -> list[ForeshadowingEntry]:
        """List all foreshadowing entries."""
        return self._manager.list_foreshadowing()

    def get_reader_knowledge(
        self, chapter_id: str, scene_id: str | None = None
    ) -> Optional[ReaderKnowledgeState]:
        """Load reader knowledge state."""
        return self.ctx.project.load_reader_knowledge(chapter_id, scene_id)
