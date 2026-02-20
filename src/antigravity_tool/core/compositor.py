"""Panel compositor: overlay speech bubbles, SFX, and narration on panel images.

Requires Pillow (optional dependency). Install with: pip install Pillow>=10.0.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.panel import Panel
from antigravity_tool.utils.io import ensure_dir


def _check_pillow():
    """Verify Pillow is installed."""
    try:
        from PIL import Image, ImageDraw, ImageFont
        return True
    except ImportError:
        return False


class PanelCompositor:
    """Overlays text elements onto generated panel images."""

    def __init__(self, project: Project):
        self.project = project

    def composite_panel(
        self,
        chapter_num: int,
        page_num: int,
        panel_num: int,
        *,
        output_path: Optional[Path] = None,
    ) -> Optional[Path]:
        """Composite a single panel with speech bubbles, SFX, and narration."""
        if not _check_pillow():
            raise RuntimeError("Pillow is required for compositing. Install with: pip install Pillow>=10.0.0")

        from PIL import Image, ImageDraw, ImageFont

        # Find the source image
        images_dir = self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "images"
        filename = f"page-{page_num:02d}-panel-{panel_num:02d}.png"
        source = images_dir / filename

        if not source.exists():
            return None

        # Find the panel data
        panels = self.project.load_panels(chapter_num)
        panel = next(
            (p for p in panels if p.page_number == page_num and p.panel_number == panel_num),
            None,
        )
        if not panel:
            return None

        # Open image
        img = Image.open(source)
        draw = ImageDraw.Draw(img)

        # Try to load a font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
            font_sfx = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except (OSError, IOError):
            font = ImageFont.load_default()
            font_small = font
            font_sfx = font

        # Draw speech bubbles
        for bubble in panel.dialogue_bubbles:
            self._draw_speech_bubble(draw, img, bubble, font)

        # Draw SFX
        for i, sfx in enumerate(panel.sound_effects):
            self._draw_sfx(draw, img, sfx, i, font_sfx)

        # Draw narration box
        if panel.narration_box:
            self._draw_narration_box(draw, img, panel.narration_box, font_small)

        # Save
        if output_path is None:
            comp_dir = ensure_dir(
                self.project.chapters_dir / f"chapter-{chapter_num:02d}" / "composited"
            )
            output_path = comp_dir / filename

        img.save(output_path)
        return output_path

    def composite_chapter(self, chapter_num: int) -> list[Path]:
        """Composite all panels in a chapter."""
        panels = self.project.load_panels(chapter_num)
        results = []

        for panel in panels:
            result = self.composite_panel(
                chapter_num, panel.page_number, panel.panel_number
            )
            if result:
                results.append(result)

        return results

    def _draw_speech_bubble(self, draw, img, bubble, font):
        """Draw a speech bubble with tail onto the image."""
        from PIL import Image, ImageDraw

        w, h = img.size
        text = f"{bubble.character_name}: {bubble.text}" if bubble.text else ""
        if not text:
            return

        # Calculate text size
        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Position based on hint
        padding = 16
        bubble_w = min(text_w + padding * 2, w - 40)
        bubble_h = text_h + padding * 2

        pos = bubble.position_hint.lower()
        if "top" in pos and "left" in pos:
            x, y = 20, 20
        elif "top" in pos and "right" in pos:
            x, y = w - bubble_w - 20, 20
        elif "bottom" in pos and "left" in pos:
            x, y = 20, h - bubble_h - 40
        elif "bottom" in pos and "right" in pos:
            x, y = w - bubble_w - 20, h - bubble_h - 40
        elif "top" in pos:
            x, y = (w - bubble_w) // 2, 20
        elif "bottom" in pos:
            x, y = (w - bubble_w) // 2, h - bubble_h - 40
        else:
            x, y = (w - bubble_w) // 2, 20

        # Draw bubble
        bubble_type = bubble.bubble_type.lower()
        if bubble_type == "thought":
            # Thought bubble: rounded with cloud-like edges
            draw.rounded_rectangle(
                [x, y, x + bubble_w, y + bubble_h],
                radius=bubble_h // 2,
                fill=(255, 255, 255, 230),
                outline=(100, 100, 100),
                width=2,
            )
        else:
            # Speech bubble: rounded rectangle
            draw.rounded_rectangle(
                [x, y, x + bubble_w, y + bubble_h],
                radius=12,
                fill=(255, 255, 255, 240),
                outline=(0, 0, 0),
                width=2,
            )

        # Draw text (wrap if needed)
        draw.text(
            (x + padding, y + padding),
            text[:bubble_w // 8],  # Basic truncation
            fill=(0, 0, 0),
            font=font,
        )

    def _draw_sfx(self, draw, img, sfx_text: str, index: int, font):
        """Draw a sound effect text with stylized appearance."""
        w, h = img.size

        # Position SFX in different areas based on index
        positions = [
            (w * 0.6, h * 0.3),
            (w * 0.2, h * 0.6),
            (w * 0.7, h * 0.7),
            (w * 0.4, h * 0.2),
        ]
        x, y = positions[index % len(positions)]

        # Draw with outline effect
        outline_color = (0, 0, 0)
        text_color = (255, 50, 50)

        for dx in [-2, -1, 0, 1, 2]:
            for dy in [-2, -1, 0, 1, 2]:
                if dx == 0 and dy == 0:
                    continue
                draw.text((x + dx, y + dy), sfx_text.upper(), fill=outline_color, font=font)

        draw.text((x, y), sfx_text.upper(), fill=text_color, font=font)

    def _draw_narration_box(self, draw, img, text: str, font):
        """Draw a narration box (typically at top or bottom of panel)."""
        w, h = img.size

        bbox = font.getbbox(text)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        padding = 12
        box_w = min(text_w + padding * 2, w - 20)
        box_h = text_h + padding * 2

        # Narration boxes go at the top
        x = (w - box_w) // 2
        y = 10

        # Semi-transparent dark background
        draw.rectangle(
            [x, y, x + box_w, y + box_h],
            fill=(20, 20, 40, 220),
            outline=(80, 80, 120),
            width=1,
        )

        draw.text(
            (x + padding, y + padding),
            text[:box_w // 8],
            fill=(230, 230, 255),
            font=font,
        )
