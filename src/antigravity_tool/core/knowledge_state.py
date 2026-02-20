"""Reader knowledge state tracking utilities."""

from __future__ import annotations

from antigravity_tool.schemas.creative_room import ReaderKnowledgeState


def merge_knowledge_states(
    previous: ReaderKnowledgeState | None,
    new_reveals: dict,
) -> ReaderKnowledgeState:
    """Merge new knowledge into the existing reader knowledge state.

    new_reveals should be a dict with keys matching ReaderKnowledgeState fields,
    containing lists of new items to add.
    """
    if previous is None:
        return ReaderKnowledgeState(**new_reveals)

    merged = previous.model_copy(deep=True)

    for field in [
        "known_characters", "known_locations", "known_world_rules",
        "known_relationships", "revealed_secrets", "active_questions",
        "false_beliefs",
    ]:
        existing = getattr(merged, field, [])
        new_items = new_reveals.get(field, [])
        # Deduplicate while preserving order
        seen = set(existing)
        for item in new_items:
            if item not in seen:
                existing.append(item)
                seen.add(item)
        setattr(merged, field, existing)

    # Merge known_character_traits (dict of lists)
    for char_id, traits in new_reveals.get("known_character_traits", {}).items():
        if char_id not in merged.known_character_traits:
            merged.known_character_traits[char_id] = []
        existing_traits = set(merged.known_character_traits[char_id])
        for trait in traits:
            if trait not in existing_traits:
                merged.known_character_traits[char_id].append(trait)

    # Remove resolved questions
    resolved = set(new_reveals.get("resolved_questions", []))
    if resolved:
        merged.active_questions = [
            q for q in merged.active_questions if q not in resolved
        ]

    # Remove corrected false beliefs
    corrected = set(new_reveals.get("corrected_beliefs", []))
    if corrected:
        merged.false_beliefs = [
            b for b in merged.false_beliefs if b not in corrected
        ]

    return merged
