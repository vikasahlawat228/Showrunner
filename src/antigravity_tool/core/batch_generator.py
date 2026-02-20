"""Batch image generation: generate images for all panels in a chapter."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from antigravity_tool.agent.image_provider import (
    ImageProvider,
    ImageProviderType,
    ImageResult,
    get_provider,
)
from antigravity_tool.core.project import Project
from antigravity_tool.schemas.panel import Panel
from antigravity_tool.utils.io import ensure_dir


class BatchResult(BaseModel):
    """Result of a batch image generation operation."""

    chapter_num: int
    total_panels: int = 0
    generated: int = 0
    failed: int = 0
    skipped: int = 0
    results: list[ImageResult] = Field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.total_panels == 0:
            return 0.0
        return self.generated / self.total_panels


class BatchGenerator:
    """Generates images for all panels in a chapter."""

    def __init__(self, project: Project, provider: ImageProvider):
        self.project = project
        self.provider = provider

    def generate_chapter(
        self,
        chapter_num: int,
        *,
        dry_run: bool = False,
        skip_existing: bool = True,
        width: int = 1024,
        height: int = 1820,  # 9:16 default for manhwa
    ) -> BatchResult:
        """Generate images for all panels in a chapter."""
        panels = self.project.load_panels(chapter_num)
        characters = self.project.load_all_characters(filter_secrets=False)
        style = self.project.load_visual_style_guide()

        # Build DNA block map
        dna_blocks = {}
        for char in characters:
            if char.dna.face.face_shape:
                dna_blocks[char.id] = char.dna.to_prompt_block()
                dna_blocks[char.name] = char.dna.to_prompt_block()

        style_tokens = style.prompt_style_tokens if style else ""

        output_dir = ensure_dir(
            self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "images"
        )

        result = BatchResult(chapter_num=chapter_num, total_panels=len(panels))

        for panel in panels:
            filename = f"page-{panel.page_number:02d}-panel-{panel.panel_number:02d}.png"
            output_path = output_dir / filename

            if skip_existing and output_path.exists():
                result.skipped += 1
                continue

            # Compile image prompt
            prompt = panel.compile_image_prompt(dna_blocks, style_tokens)

            if dry_run:
                result.results.append(ImageResult(
                    provider=self.provider.provider_type,
                    prompt_used=prompt,
                    negative_prompt=panel.negative_prompt or "",
                    status="dry_run",
                ))
                result.skipped += 1
                continue

            # Generate
            img_result = self.provider.generate(
                prompt,
                negative_prompt=panel.negative_prompt or "",
                width=width,
                height=height,
                seed=panel.seed_suggestion,
                output_path=output_path,
            )

            result.results.append(img_result)

            if img_result.status == "success":
                result.generated += 1
            else:
                result.failed += 1

        return result

    def generate_single(
        self,
        chapter_num: int,
        page_num: int,
        panel_num: int,
        *,
        width: int = 1024,
        height: int = 1820,
    ) -> ImageResult:
        """Generate a single panel image."""
        panels = self.project.load_panels(chapter_num)
        target = next(
            (p for p in panels if p.page_number == page_num and p.panel_number == panel_num),
            None,
        )
        if not target:
            return ImageResult(
                provider=self.provider.provider_type,
                status="failed",
                error_message=f"Panel not found: Page {page_num}, Panel {panel_num}",
            )

        characters = self.project.load_all_characters(filter_secrets=False)
        style = self.project.load_visual_style_guide()

        dna_blocks = {}
        for char in characters:
            if char.dna.face.face_shape:
                dna_blocks[char.id] = char.dna.to_prompt_block()
                dna_blocks[char.name] = char.dna.to_prompt_block()

        style_tokens = style.prompt_style_tokens if style else ""
        prompt = target.compile_image_prompt(dna_blocks, style_tokens)

        output_dir = ensure_dir(
            self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "images"
        )
        filename = f"page-{page_num:02d}-panel-{panel_num:02d}.png"

        return self.provider.generate(
            prompt,
            negative_prompt=target.negative_prompt or "",
            width=width,
            height=height,
            seed=target.seed_suggestion,
            output_path=output_dir / filename,
        )

    def retry_failed(
        self, chapter_num: int, previous_result: BatchResult
    ) -> BatchResult:
        """Retry only the failed panels from a previous batch."""
        failed_prompts = [
            r for r in previous_result.results if r.status == "failed"
        ]

        result = BatchResult(
            chapter_num=chapter_num, total_panels=len(failed_prompts)
        )

        for failed in failed_prompts:
            output_dir = ensure_dir(
                self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "images"
            )

            img_result = self.provider.generate(
                failed.prompt_used,
                negative_prompt=failed.negative_prompt,
            )

            result.results.append(img_result)
            if img_result.status == "success":
                result.generated += 1
            else:
                result.failed += 1

        return result

    def get_status(self, chapter_num: int) -> dict:
        """Get generation status for a chapter."""
        panels = self.project.load_panels(chapter_num)
        images_dir = self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "images"

        total = len(panels)
        existing = 0
        missing = []

        for panel in panels:
            filename = f"page-{panel.page_number:02d}-panel-{panel.panel_number:02d}.png"
            if (images_dir / filename).exists():
                existing += 1
            else:
                missing.append(f"Page {panel.page_number}, Panel {panel.panel_number}")

        return {
            "chapter": chapter_num,
            "total_panels": total,
            "images_generated": existing,
            "images_missing": len(missing),
            "missing_panels": missing,
            "completion_pct": (existing / total * 100) if total > 0 else 0,
        }
