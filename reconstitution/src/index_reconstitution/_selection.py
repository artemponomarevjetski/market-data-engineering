"""Deterministic, role-preserving selection of already admitted passages."""

_REVIEW_ROLE_RANK = {"BUSINESS": 0, "FINANCIAL_NOTES": 1, "OPERATING_FINANCIAL": 2}

def _review_priority(record: dict, query_terms: tuple[str, ...]) -> tuple:
    """Deterministic reviewer ranking; eligibility and boundaries are decided upstream."""
    text = str(record.get("quote", "")).casefold()
    relevance = -sum(text.count(term.casefold()) for term in query_terms if term.strip())
    return (_REVIEW_ROLE_RANK.get(record.get("section_role"), 99), relevance,
            str(record.get("passage_id", "")), str(record.get("source_start", "")))


def _select_review_records(mapped: list[dict], limit: int, query_terms: tuple[str, ...]) -> list[dict]:
    """Reserve one deterministic representative for every available permitted role."""
    ranked = sorted(mapped, key=lambda row: _review_priority(row, query_terms))
    roles = ("BUSINESS", "FINANCIAL_NOTES", "OPERATING_FINANCIAL")
    selected = []
    for role in roles:
        candidate = next((row for row in ranked if row.get("section_role") == role), None)
        if candidate is not None:
            selected.append(candidate)
    selected_ids = {row.get("passage_id") for row in selected}
    selected.extend(row for row in ranked if row.get("passage_id") not in selected_ids)
    return selected[:limit]
