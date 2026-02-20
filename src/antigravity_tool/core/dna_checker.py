"""DNA drift detection: compares character DNA against generated image prompts."""

from __future__ import annotations

from typing import Optional

from antigravity_tool.core.project import Project
from antigravity_tool.schemas.continuity import (
    DNADriftIssue,
    DNADriftReport,
    IssueSeverity,
)
from antigravity_tool.schemas.character import Character


class DNADriftChecker:
    """Detects when image prompts deviate from canonical character DNA blocks."""

    def __init__(self, project: Project):
        self.project = project

    def check_character(
        self, character_name: str, chapter_num: Optional[int] = None
    ) -> DNADriftReport:
        """Check a single character's DNA against all their panel appearances."""
        char = self.project.load_character(character_name)
        if not char:
            return DNADriftReport(character_name=character_name, panels_checked=0)

        chapters = self._get_chapters(chapter_num)
        issues: list[DNADriftIssue] = []
        panels_checked = 0

        for ch in chapters:
            panels = self.project.load_panels(ch)
            for panel in panels:
                for char_in_panel in panel.characters:
                    if char_in_panel.character_name != character_name:
                        continue
                    panels_checked += 1
                    loc = f"Chapter {ch}, Page {panel.page_number}, Panel {panel.panel_number}"

                    if panel.image_prompt:
                        drift = self._check_prompt_against_dna(
                            char, panel.image_prompt, loc
                        )
                        issues.extend(drift)

        return DNADriftReport(
            character_name=character_name,
            issues=issues,
            panels_checked=panels_checked,
        )

    def check_all(self, chapter_num: Optional[int] = None) -> DNADriftReport:
        """Check all characters' DNA against their panel appearances."""
        characters = self.project.load_all_characters(filter_secrets=False)
        all_issues: list[DNADriftIssue] = []
        total_panels = 0

        for char in characters:
            report = self.check_character(char.name, chapter_num)
            all_issues.extend(report.issues)
            total_panels += report.panels_checked

        return DNADriftReport(
            character_name=None,
            issues=all_issues,
            panels_checked=total_panels,
        )

    def _check_prompt_against_dna(
        self, char: Character, prompt: str, location: str
    ) -> list[DNADriftIssue]:
        """Compare a single image prompt against the character's canonical DNA."""
        issues: list[DNADriftIssue] = []
        prompt_lower = prompt.lower()
        dna = char.dna

        # Check hair color
        if dna.hair.color:
            canonical = dna.hair.color.lower()
            # Look for contradicting hair color mentions
            hair_colors = [
                "black", "brown", "blonde", "red", "white", "silver",
                "blue", "green", "pink", "purple", "orange", "gray", "grey",
            ]
            for color in hair_colors:
                if color in prompt_lower and color not in canonical and "hair" in prompt_lower:
                    # Check if this color is near "hair" in the prompt
                    hair_idx = prompt_lower.find("hair")
                    color_idx = prompt_lower.find(color)
                    if abs(hair_idx - color_idx) < 30:
                        issues.append(DNADriftIssue(
                            character_name=char.name,
                            panel_location=location,
                            dna_field="hair.color",
                            canonical_value=dna.hair.color,
                            prompt_value=color,
                            severity=IssueSeverity.WARNING,
                        ))

        # Check eye color
        if dna.face.eye_color:
            canonical = dna.face.eye_color.lower()
            eye_colors = [
                "black", "brown", "blue", "green", "hazel", "amber",
                "red", "purple", "gold", "silver", "grey", "gray",
            ]
            for color in eye_colors:
                if color in prompt_lower and color not in canonical and "eye" in prompt_lower:
                    eye_idx = prompt_lower.find("eye")
                    color_idx = prompt_lower.find(color)
                    if abs(eye_idx - color_idx) < 30:
                        issues.append(DNADriftIssue(
                            character_name=char.name,
                            panel_location=location,
                            dna_field="face.eye_color",
                            canonical_value=dna.face.eye_color,
                            prompt_value=color,
                            severity=IssueSeverity.WARNING,
                        ))

        # Check skin tone
        if dna.face.skin_tone:
            canonical = dna.face.skin_tone.lower()
            skin_terms = [
                "pale", "fair", "light", "olive", "tan", "brown",
                "dark", "ebony", "porcelain",
            ]
            for term in skin_terms:
                if term in prompt_lower and term not in canonical and "skin" in prompt_lower:
                    skin_idx = prompt_lower.find("skin")
                    term_idx = prompt_lower.find(term)
                    if abs(skin_idx - term_idx) < 30:
                        issues.append(DNADriftIssue(
                            character_name=char.name,
                            panel_location=location,
                            dna_field="face.skin_tone",
                            canonical_value=dna.face.skin_tone,
                            prompt_value=term,
                            severity=IssueSeverity.WARNING,
                        ))

        # Check distinguishing marks
        for mark in dna.face.distinguishing_marks:
            mark_lower = mark.lower()
            # Key mark words that should appear in prompts
            mark_keywords = mark_lower.split()
            if len(mark_keywords) >= 2:
                key_word = max(mark_keywords, key=len)
                if key_word not in prompt_lower and len(key_word) > 3:
                    issues.append(DNADriftIssue(
                        character_name=char.name,
                        panel_location=location,
                        dna_field="face.distinguishing_marks",
                        canonical_value=mark,
                        prompt_value="(missing from prompt)",
                        severity=IssueSeverity.INFO,
                    ))

        return issues

    def generate_correction_prompt(self, report: DNADriftReport) -> str:
        """Generate a prompt to help fix DNA drift issues."""
        if not report.issues:
            return "No DNA drift issues found."

        lines = ["# DNA Drift Correction Needed\n"]
        lines.append(f"Found {len(report.issues)} drift issues.\n")

        by_character: dict[str, list[DNADriftIssue]] = {}
        for issue in report.issues:
            by_character.setdefault(issue.character_name, []).append(issue)

        for char_name, char_issues in by_character.items():
            lines.append(f"\n## {char_name}\n")
            for issue in char_issues:
                lines.append(f"- **{issue.dna_field}** at {issue.panel_location}")
                lines.append(f"  - Canonical: `{issue.canonical_value}`")
                lines.append(f"  - In prompt: `{issue.prompt_value}`")

        lines.append("\n## Instructions\n")
        lines.append("Regenerate the image prompts for the panels listed above,")
        lines.append("ensuring the character DNA values match the canonical definitions.")

        return "\n".join(lines)

    def _get_chapters(self, chapter_num: Optional[int] = None) -> list[int]:
        """Get list of chapter numbers to check."""
        if chapter_num:
            return [chapter_num]
        chapters = []
        if self.project.chapters_dir.exists():
            for d in sorted(self.project.chapters_dir.iterdir()):
                if d.is_dir() and d.name.startswith("chapter-"):
                    try:
                        chapters.append(int(d.name.split("-")[1]))
                    except (IndexError, ValueError):
                        pass
        return chapters
