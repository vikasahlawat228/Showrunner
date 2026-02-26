"""WEBTOON export: stitch panels into vertical scroll strips.

WEBTOON specs: 800px wide, max 1280px per slice.
Requires Pillow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from showrunner_tool.core.project import Project
from showrunner_tool.utils.io import ensure_dir


class WebtoonExporter:
    """Exports composited panels as WEBTOON-format vertical strips."""

    WEBTOON_WIDTH = 800
    MAX_SLICE_HEIGHT = 1280

    def __init__(self, project: Project):
        self.project = project

    def export_chapter(
        self,
        chapter_num: int,
        *,
        output_dir: Optional[Path] = None,
        use_composited: bool = True,
    ) -> list[Path]:
        """Export a chapter as WEBTOON vertical scroll strips."""
        try:
            from PIL import Image
        except ImportError:
            raise RuntimeError("Pillow required. Install: pip install Pillow>=10.0.0")

        # Find source images
        ch_dir = self.project.chapters_dir / f"chapter-{chapter_num:02d}"
        if use_composited and (ch_dir / "composited").exists():
            img_dir = ch_dir / "composited"
        else:
            img_dir = ch_dir / "images"

        if not img_dir.exists():
            return []

        # Load all panel images in order
        image_files = sorted(img_dir.glob("*.png"))
        if not image_files:
            return []

        images = []
        for f in image_files:
            img = Image.open(f)
            # Resize to WEBTOON width
            if img.width != self.WEBTOON_WIDTH:
                ratio = self.WEBTOON_WIDTH / img.width
                new_h = int(img.height * ratio)
                img = img.resize((self.WEBTOON_WIDTH, new_h), Image.LANCZOS)
            images.append(img)

        # Calculate total height
        total_height = sum(img.height for img in images)

        # Create one tall strip
        strip = Image.new("RGB", (self.WEBTOON_WIDTH, total_height), (255, 255, 255))
        y_offset = 0
        for img in images:
            strip.paste(img, (0, y_offset))
            y_offset += img.height

        # Slice into max-height pieces
        if output_dir is None:
            output_dir = ensure_dir(self.project.exports_dir / "webtoon" / f"chapter-{chapter_num:02d}")
        else:
            output_dir = ensure_dir(Path(output_dir))

        slices = []
        slice_num = 1
        y = 0
        while y < total_height:
            slice_h = min(self.MAX_SLICE_HEIGHT, total_height - y)
            slice_img = strip.crop((0, y, self.WEBTOON_WIDTH, y + slice_h))
            slice_path = output_dir / f"slice-{slice_num:03d}.jpg"
            slice_img.save(slice_path, "JPEG", quality=90)
            slices.append(slice_path)
            y += slice_h
            slice_num += 1

        return slices
