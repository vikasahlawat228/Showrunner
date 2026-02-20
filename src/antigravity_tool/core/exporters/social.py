"""Social media export: panels optimized for Instagram, Twitter, TikTok.

Requires Pillow.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.utils.io import ensure_dir


SOCIAL_FORMATS = {
    "instagram_square": (1080, 1080),
    "instagram_portrait": (1080, 1350),
    "twitter": (1200, 675),
    "tiktok": (1080, 1920),
}


class SocialExporter:
    """Exports panels optimized for social media platforms."""

    def __init__(self, project: Project):
        self.project = project

    def export_panel(
        self,
        chapter_num: int,
        page_num: int,
        panel_num: int,
        *,
        format_name: str = "instagram_square",
        output_dir: Optional[Path] = None,
        watermark_text: Optional[str] = None,
    ) -> Optional[Path]:
        """Export a single panel optimized for a social media format."""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            raise RuntimeError("Pillow required. Install: pip install Pillow>=10.0.0")

        dims = SOCIAL_FORMATS.get(format_name)
        if not dims:
            raise ValueError(f"Unknown format: {format_name}. Options: {', '.join(SOCIAL_FORMATS.keys())}")

        target_w, target_h = dims

        # Find source image
        ch_dir = self.project.chapters_dir / f"chapter-{chapter_num:02d}"
        img_dir = ch_dir / "composited" if (ch_dir / "composited").exists() else ch_dir / "images"
        filename = f"page-{page_num:02d}-panel-{panel_num:02d}.png"
        source = img_dir / filename

        if not source.exists():
            return None

        img = Image.open(source)

        # Resize and crop to target dimensions
        img = self._smart_crop(img, target_w, target_h)

        # Add watermark if specified
        if watermark_text:
            img = self._add_watermark(img, watermark_text)

        # Save
        if output_dir is None:
            output_dir = ensure_dir(
                self.project.exports_dir / "social" / format_name
            )
        else:
            output_dir = ensure_dir(Path(output_dir))

        output_path = output_dir / f"ch{chapter_num:02d}-p{page_num:02d}-panel{panel_num:02d}-{format_name}.jpg"
        img.save(output_path, "JPEG", quality=92)
        return output_path

    def export_chapter_batch(
        self,
        chapter_num: int,
        *,
        format_name: str = "instagram_square",
        watermark_text: Optional[str] = None,
    ) -> list[Path]:
        """Export all panels in a chapter for a social media format."""
        panels = self.project.load_panels(chapter_num)
        results = []

        for panel in panels:
            result = self.export_panel(
                chapter_num,
                panel.page_number,
                panel.panel_number,
                format_name=format_name,
                watermark_text=watermark_text,
            )
            if result:
                results.append(result)

        return results

    def _smart_crop(self, img, target_w: int, target_h: int):
        """Resize and center-crop to target dimensions."""
        from PIL import Image

        src_ratio = img.width / img.height
        target_ratio = target_w / target_h

        if src_ratio > target_ratio:
            # Source is wider: fit height, crop width
            new_h = target_h
            new_w = int(img.width * target_h / img.height)
        else:
            # Source is taller: fit width, crop height
            new_w = target_w
            new_h = int(img.height * target_w / img.width)

        img = img.resize((new_w, new_h), Image.LANCZOS)

        # Center crop
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img = img.crop((left, top, left + target_w, top + target_h))

        return img

    def _add_watermark(self, img, text: str):
        """Add a semi-transparent watermark to the bottom-right corner."""
        from PIL import ImageDraw, ImageFont

        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except (OSError, IOError):
            font = ImageFont.load_default()

        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x = img.width - text_w - 15
        y = img.height - text_h - 15

        # Semi-transparent background
        draw.rectangle(
            [x - 5, y - 3, x + text_w + 5, y + text_h + 3],
            fill=(0, 0, 0, 128),
        )
        draw.text((x, y), text, fill=(255, 255, 255, 200), font=font)

        return img
