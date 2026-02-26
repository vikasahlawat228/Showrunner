"""Intent Classifier — classifies user messages into tool intents (Phase J-3).

Maps user messages to one of the available tool intents:
  CHAT, SEARCH, CREATE, UPDATE, DELETE, PIPELINE, NAVIGATE,
  EVALUATE, RESEARCH, PLAN, DECIDE

Uses keyword matching as a baseline, with LLM-based classification planned.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional

from showrunner_tool.schemas.chat import ToolIntent

logger = logging.getLogger(__name__)

# Keyword patterns for each intent
_INTENT_PATTERNS: Dict[str, List[str]] = {
    "SEARCH": [
        r"\bfind\b", r"\bsearch\b", r"\blook\s+(?:up|for)\b",
        r"\bwhere\s+is\b", r"\bwhat\s+is\b", r"\bshow\s+me\b",
        r"\blist\s+all\b",
    ],
    "UNRESOLVED_THREADS": [
        r"\bunresolved\s+threads\b", r"\bopen\s+plot\b", r"\bunfinished\s+storylines\b",
        r"\bwhat\s+plots\s+are\s+open\b", r"\bshow\s+unresolved\b", r"\bloose\s+ends\b"
    ],
    "CREATE": [
        r"\bcreate\b", r"\bnew\b", r"\badd\b", r"\bgenerate\b",
        r"\bwrite\s+(?:a|an|the)\b", r"\bdraft\b", r"\bcompose\b",
    ],
    "UPDATE": [
        r"\bupdate\b", r"\bedit\b", r"\bchange\b", r"\bmodify\b",
        r"\brefine\b", r"\brevise\b", r"\brename\b",
    ],
    "DELETE": [
        r"\bdelete\b", r"\bremove\b", r"\bdrop\b",
    ],
    "PIPELINE": [
        r"\brun\s+pipeline\b", r"\bstart\s+pipeline\b",
        r"\bpipeline\b", r"\bworkflow\b", r"\bbatch\b",
    ],
    "NAVIGATE": [
        r"\bopen\b", r"\bgo\s+to\b", r"\bnavigate\b",
        r"\bswitch\s+to\b", r"\bshow\b(?!\s+me)",
    ],
    "EVALUATE": [
        r"\bevaluate\b", r"\breview\b", r"\bcheck\s+quality\b",
        r"\bcritique\b", r"\bfeedback\b", r"\bgrade\b",
    ],
    "RESEARCH": [
        r"\bresearch\b", r"\binvestigate\b", r"\bdig\s+into\b",
        r"\bexplore\b(?!\s+the\s+code)",
    ],
    "PLAN": [
        r"\bplan\b", r"\boutline\b", r"\bstrategy\b",
        r"\barchitect\b", r"\bdesign\b",
    ],
    "DECIDE": [
        r"\bdecide\b", r"\bdecision\b", r"\bpreference\b",
        r"\brule\b", r"\balways\b.*\buse\b", r"\bnever\b.*\buse\b",
        r"\bremember\s+that\b",
    ],
    "PLAUSIBILITY_CHECK": [
        r"\brealistic\b", r"\bmake\s+sense\b", r"\bfact\s+check\b",
        r"\bplausible\b", r"\baccurate\b",
    ],
}

# Intents that require approval before execution
_APPROVAL_REQUIRED = {"DELETE", "PIPELINE", "UPDATE"}


class IntentClassifier:
    """Classifies user messages into tool intents.

    Uses keyword pattern matching as baseline. LLM-based classification
    can be wired in later by subclassing or replacing `classify()`.
    """

    def classify(self, message: str) -> ToolIntent:
        """Classify a user message into a ToolIntent.

        Returns the highest-confidence match, or CHAT as default.
        """
        message_lower = message.lower().strip()

        best_intent = "CHAT"
        best_confidence = 0.0
        best_params: Dict = {}

        for intent, patterns in _INTENT_PATTERNS.items():
            hits = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    hits += 1

            if hits > 0:
                confidence = min(0.9, 0.3 + (hits * 0.2))
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_intent = intent
                    best_params = self._extract_params(intent, message)

        # Default CHAT confidence
        if best_intent == "CHAT":
            best_confidence = 0.5

        return ToolIntent(
            tool=best_intent,
            confidence=best_confidence,
            params=best_params,
            requires_approval=best_intent in _APPROVAL_REQUIRED,
        )

    def _extract_params(self, intent: str, message: str) -> Dict:
        """Extract parameters from the message based on intent type."""
        params: Dict = {}

        if intent == "CREATE":
            # Try to extract entity type
            for entity_type in ["character", "scene", "chapter", "world", "panel"]:
                if entity_type in message.lower():
                    params["entity_type"] = entity_type
                    break

        elif intent == "SEARCH":
            # The search query is essentially the message itself
            params["query"] = message

        elif intent == "NAVIGATE":
            # Try to extract target (check longer names first to avoid partial matches)
            for target in ["storyboard", "characters", "timeline", "pipeline",
                          "scenes", "panels", "world", "story", "zen"]:
                if target in message.lower():
                    params["target"] = target
                    break

        return params

    def classify_batch(self, messages: List[str]) -> List[ToolIntent]:
        """Classify multiple messages at once."""
        return [self.classify(msg) for msg in messages]
