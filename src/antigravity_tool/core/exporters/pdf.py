"""PDF export: print-ready PDFs with page layouts.

Requires fpdf2. Install: pip install fpdf2>=2.7.0
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.utils.io import ensure_dir


class PDFExporter:
    """Exports chapters or full story as print-ready PDF."""

    def __init__(self, project: Project):
        self.project = project

    def export_chapter(
        self,
        chapter_num: int,
        *,
        output_path: Optional[Path] = None,
        layout: str = "vertical",  # "vertical" or "page_based"
        use_composited: bool = True,
    ) -> Optional[Path]:
        """Export a single chapter as PDF."""
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("fpdf2 required. Install: pip install fpdf2>=2.7.0")

        ch_dir = self.project.chapters_dir / f"chapter-{chapter_num:02d}"
        if use_composited and (ch_dir / "composited").exists():
            img_dir = ch_dir / "composited"
        else:
            img_dir = ch_dir / "images"

        if not img_dir.exists():
            return None

        image_files = sorted(img_dir.glob("*.png"))
        if not image_files:
            return None

        if output_path is None:
            export_dir = ensure_dir(self.project.exports_dir / "pdf")
            output_path = export_dir / f"chapter-{chapter_num:02d}.pdf"

        if layout == "vertical":
            return self._export_vertical(image_files, output_path)
        else:
            return self._export_page_based(image_files, output_path)

    def export_full(
        self,
        *,
        output_path: Optional[Path] = None,
        layout: str = "page_based",
    ) -> Optional[Path]:
        """Export all chapters as a single PDF."""
        try:
            from fpdf import FPDF
        except ImportError:
            raise RuntimeError("fpdf2 required. Install: pip install fpdf2>=2.7.0")

        all_images = []
        if self.project.chapters_dir.exists():
            for d in sorted(self.project.chapters_dir.iterdir()):
                if d.is_dir() and d.name.startswith("chapter-"):
                    img_dir = d / "composited" if (d / "composited").exists() else d / "images"
                    if img_dir.exists():
                        all_images.extend(sorted(img_dir.glob("*.png")))

        if not all_images:
            return None

        if output_path is None:
            export_dir = ensure_dir(self.project.exports_dir / "pdf")
            output_path = export_dir / f"{self.project.name.lower().replace(' ', '-')}-full.pdf"

        if layout == "vertical":
            return self._export_vertical(all_images, output_path)
        else:
            return self._export_page_based(all_images, output_path)

    def _export_vertical(self, image_files: list[Path], output_path: Path) -> Path:
        """Vertical scroll layout (one long page per panel)."""
        from fpdf import FPDF

        pdf = FPDF(unit="mm")
        pdf.set_auto_page_break(auto=False)

        for img_path in image_files:
            from PIL import Image
            img = Image.open(img_path)
            w_mm = 190  # Leave margins
            h_mm = w_mm * img.height / img.width

            pdf.add_page(format=(210, max(h_mm + 20, 297)))
            pdf.image(str(img_path), x=10, y=10, w=w_mm)

        pdf.output(str(output_path))
        return output_path

    def _export_page_based(self, image_files: list[Path], output_path: Path) -> Path:
        """Standard page-based layout (A4 pages, 1-2 panels per page)."""
        from fpdf import FPDF

        pdf = FPDF(unit="mm", format="A4")
        pdf.set_auto_page_break(auto=False)

        page_w = 210
        page_h = 297
        margin = 10
        usable_w = page_w - 2 * margin
        usable_h = page_h - 2 * margin

        for img_path in image_files:
            pdf.add_page()
            from PIL import Image
            img = Image.open(img_path)
            ratio = img.width / img.height

            if ratio > 1:
                # Landscape: full width
                w = usable_w
                h = w / ratio
            else:
                # Portrait: fit height
                h = usable_h
                w = h * ratio
                if w > usable_w:
                    w = usable_w
                    h = w / ratio

            x = margin + (usable_w - w) / 2
            y = margin + (usable_h - h) / 2

            pdf.image(str(img_path), x=x, y=y, w=w, h=h)

        pdf.output(str(output_path))
        return output_path
