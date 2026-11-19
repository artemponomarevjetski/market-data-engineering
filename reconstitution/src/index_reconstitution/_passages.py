"""Narrow exclusion rules for personnel headings and career biographies."""

import re

def _is_personnel_section_heading(section: str) -> bool:
    """Exclude personnel biographies and governance profiles, not operating evidence."""
    heading = " ".join(section.split()).casefold().strip(" .:-")
    heading = re.sub(r"^item\s+\d+[a-z]?\s*[.:\-–—]?\s*", "", heading)
    if len(heading) > 180:
        return False
    if heading in {"management", "our management", "executive and director compensation"}:
        return True
    if re.fullmatch(r"information about (?:our )?executive officers", heading):
        return True
    return bool(re.match(
        r"^(?:board\s+of\s+directors?\b|directors?\b|"
        r"(?:executive\s+)?officers?(?:\s+(?:and|&)\s+directors?)?\b|"
        r"(?:senior|executive|corporate)\s+(?:leadership|management|biograph(?:y|ies)|profiles?)\b|"
        r"(?:our\s+)?management\s+(?:team|biograph(?:y|ies)|profiles?)\b|"
        r"(?:our\s+)?leadership\s+(?:team|biograph(?:y|ies)|profiles?)\b|"
        r"(?:ceo|chief\s+executive\s+officer)\s+(?:biograph(?:y|ies)|profiles?|background)\b|"
        r"biograph(?:ical|y|ies)\b)", heading
    ))


def _is_personnel_career_paragraph(text: str) -> bool:
    """Withhold an explicit named career profile without closing financial scope.

    Related-party notes can contain executive appointment histories without a
    biography heading. Such whole paragraphs remain in the original source but
    are not thematic evidence. A transaction merely naming an officer is not a
    career profile and does not satisfy this narrow opening syntax.
    """
    compact = " ".join(text.split())
    career = re.match(
        r"(?i)^(?:mr|mrs|ms|dr)\.\s+[\w.'’\- ]{1,80}\s+"
        r"(?:joined\b|has(?:\s+(?:also|previously))?\s+(?:been|served)\b|"
        r"(?:was|is)\s+(?:appointed|elected|named)\b|(?:previously\s+)?served\b)", compact
    )
    if not career:
        career = re.match(
            r"^On (?:January|February|March|April|May|June|July|August|September|October|November|December) "
            r"\d{1,2}, \d{4}, [A-Z][\w.'’\-]*(?: [A-Z][\w.'’\-]*){1,3} "
            r"was appointed (?:as )?", compact,
        )
    return bool(career and re.search(
        r"(?i)\b(?:directors?|president|executive|officer|chairman|chairperson|ceo|cfo)\b",
        compact[:500],
    ))
