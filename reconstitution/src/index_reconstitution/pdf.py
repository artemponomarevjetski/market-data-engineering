"""Re-extract local annual-report PDFs and retain exact page-text locators.

Offsets address Python strings produced by the pinned layout extractor, never
PDF bytes or SEC HTML. Local hashes and receipts establish consistency, not
external source authenticity. This module performs no OCR or network calls.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping, Sequence
from datetime import date
import io
from itertools import islice
import json
import re
from typing import Any, TypedDict
from urllib.parse import urlsplit

from ._passages import _is_personnel_career_paragraph, _is_personnel_section_heading
from ._selection import _select_review_records
from ._validation import canonical_hash, ensure_sha256, require_nonempty
from .bindings import FileBinding, MAX_SOURCE_BYTES, digest, read_bound
from .filings import parse_submissions, parse_sec_header

PARSER_VERSION = "6.10.0"
PROOF_SCHEMA_VERSION = "index-reconstitution.ir-pdf.v1"
PDF_METHOD = "PDF_PAGE_LAYOUT_TEXT_OFFSETS_V1"
MAX_PDF_PAGES = 500
ROLES = frozenset({"BUSINESS", "OPERATING_FINANCIAL", "FINANCIAL_NOTES"})
_MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December")


class PdfSection(TypedDict):
    role: str
    first_page: int
    last_page: int
    start_heading: str
    next_heading: str


class PdfProof(TypedDict):
    schema_version: str
    parser_version: str
    symbol: str
    reporting_period_end: str
    form_type: str
    source_url: str
    source_origin: str
    bindings: dict[str, FileBinding]
    cik: str
    metadata_url: str
    accession_number: str
    sections: list[PdfSection]
    cover_page: int
    period_proof_page: int
    issuer_name: str
    ein: str
    sec_file_number: str


PageLoader = Callable[[bytes, Iterable[int]], Mapping[int, str]]
EvidenceRecord = dict[str, Any]


def _page_number(value: object, label: str) -> int:
    if type(value) is not int or not 1 <= value <= MAX_PDF_PAGES:
        raise ValueError(f"{label} must be an integer page within the PDF bound")
    return value


def _validate_sections(sections: Sequence[PdfSection]) -> None:
    """Validate bounds before allocating page-number ranges from a manifest."""
    if not isinstance(sections, (list, tuple)) or not 1 <= len(sections) <= MAX_PDF_PAGES:
        raise ValueError("PDF sections must be a nonempty bounded sequence")
    occupied: set[int] = set()
    for section in sections:
        if not isinstance(section, dict) or not PdfSection.__required_keys__ <= section.keys():
            raise ValueError("PDF section is missing required fields")
        if not isinstance(section["role"], str) or section["role"] not in ROLES:
            raise ValueError("inadmissible PDF section role")
        first = _page_number(section["first_page"], "first_page")
        last = _page_number(section["last_page"], "last_page")
        if first > last or last == MAX_PDF_PAGES:
            raise ValueError("PDF section must end before a retained boundary page")
        for label in ("start_heading", "next_heading"):
            require_nonempty(section[label], label)
            if len(section[label]) > 500:
                raise ValueError("PDF section heading exceeds the text bound")
        span = set(range(first, last + 1))
        if occupied & span:
            raise ValueError("overlapping PDF section ranges")
        occupied.update(span)


def page_texts(raw: bytes, numbers: Iterable[int]) -> dict[int, str]:
    """Extract selected 1-based pages with pypdf's pinned layout algorithm.

    Signature, byte, encryption and page-count guards bound ordinary inputs.
    They are not a CPU/memory sandbox for adversarial PDF files.
    """
    try:
        import pypdf
    except ImportError as exc:
        raise ValueError("PDF extraction requires the pinned pypdf dependency") from exc
    if pypdf.__version__ != PARSER_VERSION:
        raise ValueError("PDF extractor version differs from the declared parser version")
    if not isinstance(raw, bytes) or not raw.startswith(b"%PDF-") or len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("PDF original signature/byte bound failed")
    try:
        selected = tuple(islice(numbers, MAX_PDF_PAGES + 1))
    except TypeError as exc:
        raise ValueError("requested pages must be an iterable of integers") from exc
    if len(selected) > MAX_PDF_PAGES:
        raise ValueError("requested page count exceeds the PDF page bound")
    for number in selected:
        _page_number(number, "requested page")
    try:
        reader = pypdf.PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted or len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError("PDF encrypted or exceeds page bound")
        if any(number > len(reader.pages) for number in selected):
            raise ValueError("PDF page out of range")
        result = {}
        for number in sorted(set(selected)):
            page = reader.pages[number - 1]
            # A valid blank page may have no /Contents entry. It provides no
            # textual evidence; do not invent text or invoke OCR for it.
            result[number] = ("" if page.get_contents() is None
                              else page.extract_text(extraction_mode="layout"))
        return result
    except pypdf.errors.PyPdfError as exc:
        raise ValueError("PDF could not be parsed by the pinned extractor") from exc


def section_ranges(pages: Mapping[int, str], sections: Sequence[PdfSection]) -> bool:
    """Verify declared boundaries and exclude disallowed annual-report items."""
    _validate_sections(sections)
    for section in sections:
        first, last = section["first_page"], section["last_page"]
        if any(number not in pages or not isinstance(pages[number], str)
               for number in range(first, last + 2)):
            raise ValueError("PDF section or boundary page text is missing")
        if section["start_heading"].casefold() not in pages[first].casefold():
            raise ValueError("PDF section start heading absent")
        if section["next_heading"].casefold() not in pages[last + 1].casefold():
            raise ValueError("PDF section end heading absent")
        for number in range(first, last + 1):
            for line in pages[number].splitlines():
                compact = " ".join(line.split())
                if re.match(r"(?i)^Item\s+(?:1A|7A|9|10|11|12|13|14)\.", compact):
                    raise ValueError("excluded item inside declared PDF section")
    return True


def extract_page_quotes(
    pages: Mapping[int, str], sections: Sequence[PdfSection],
    identity: Mapping[str, str], terms: Sequence[str],
) -> list[EvidenceRecord]:
    """Select exact transcript paragraphs with role coverage and stable IDs.

    This standalone helper checks text boundaries and locators only. Call
    verify_ir_pdf to check the retained receipt, PDF, metadata and header.
    primary_eligible denotes a passage's permitted evidence role; it is not
    a security eligibility or index membership decision.
    """
    section_ranges(pages, sections)
    if not {"source_sha256", "source_url", "accession_number"} <= identity.keys():
        raise ValueError("PDF identity is missing source fields")
    ensure_sha256(identity["source_sha256"])
    for name in ("source_url", "accession_number"):
        require_nonempty(identity[name], name)
    if isinstance(terms, (str, bytes)):
        raise ValueError("query terms must be a sequence of strings")
    try:
        terms = tuple(terms)
    except TypeError as exc:
        raise ValueError("query terms must be a sequence of strings") from exc
    if any(not isinstance(term, str) for term in terms):
        raise ValueError("query terms must be a sequence of strings")
    records: list[EvidenceRecord] = []
    for section in sections:
        personnel = False
        for number in range(section["first_page"], section["last_page"] + 1):
            text = pages[number]
            for match in re.finditer(r"\S[^\n]*(?:\n(?!\s*\n)[^\n]+)*", text):
                quote = match.group().rstrip()
                compact = " ".join(quote.split())
                if len(compact) < 180 and _is_personnel_section_heading(compact):
                    personnel = True
                if personnel or not 100 <= len(quote) <= 3500:
                    continue
                if "\ufffd" in quote or _is_personnel_career_paragraph(compact):
                    continue
                if re.search(r"(?i)forward.looking|risks and uncertainties|risk factors", compact):
                    continue
                locator = {
                    "source_sha256": identity["source_sha256"], "page": number,
                    "start": match.start(), "end": match.start() + len(quote),
                    "parser": PARSER_VERSION, "method": PDF_METHOD,
                }
                records.append({
                    "passage_id": canonical_hash(locator), "quote": quote, "text": quote,
                    "section": section["start_heading"], "section_role": section["role"],
                    "source_sha256": identity["source_sha256"], "source_url": identity["source_url"],
                    "accession_number": identity["accession_number"],
                    "source_start": locator["start"], "source_end": locator["end"],
                    "pdf_page": number, "page_text_sha256": digest(text.encode("utf-8")),
                    "location_basis": PDF_METHOD + ":pypdf:" + PARSER_VERSION,
                    "primary_eligible": True, "verification_status": "TRANSCRIPT_LOCATOR_CHECKED",
                    "source_binding_basis": "DECLARED_PDF_IDENTITY_AND_PAGE_TEXT_LOCATOR",
                    "sec_body_byte_equivalence_verified": False,
                })
    return _select_review_records(records, 10, tuple(terms))


def _proof_inputs(proof: PdfProof, candidate_symbol: str, cutoff: str) -> date:
    if not isinstance(proof, dict) or not PdfProof.__required_keys__ <= proof.keys():
        raise ValueError("PDF proof is missing required fields")
    for name in ("symbol", "reporting_period_end", "source_url", "cik", "metadata_url",
                 "accession_number", "issuer_name", "ein", "sec_file_number",
                 "schema_version", "parser_version", "form_type", "source_origin"):
        require_nonempty(proof[name], name)
    if (proof["symbol"] != candidate_symbol or proof["schema_version"] != PROOF_SCHEMA_VERSION
            or proof["parser_version"] != PARSER_VERSION):
        raise ValueError("PDF proof scope mismatch")
    try:
        period, report_cutoff = date.fromisoformat(proof["reporting_period_end"]), date.fromisoformat(cutoff)
    except (ValueError, TypeError) as exc:
        raise ValueError("PDF reporting period and cutoff must be ISO dates") from exc
    if period > report_cutoff or proof["form_type"] != "10-K":
        raise ValueError("PDF annual reporting period inadmissible")
    url = urlsplit(proof["source_url"])
    if (url.scheme != "https" or not url.hostname or url.username is not None
            or url.password is not None or proof["source_origin"] not in {"OFFICIAL_IR", "SYNTHETIC"}):
        raise ValueError("PDF source origin and a credential-free HTTPS locator are required")
    if not re.fullmatch(r"[0-9]{2}-[0-9]{7}", proof["ein"]):
        raise ValueError("PDF proof tax identifier has an invalid format")
    if not re.fullmatch(r"[0-9]{1,3}-[0-9]{1,8}", proof["sec_file_number"]):
        raise ValueError("PDF proof SEC file number has an invalid format")
    bindings = proof["bindings"]
    if not isinstance(bindings, dict) or set(bindings) != {"pdf", "retrieval_receipt", "submissions", "header"}:
        raise ValueError("PDF proof requires exactly four named source bindings")
    _page_number(proof["cover_page"], "cover_page")
    _page_number(proof["period_proof_page"], "period_proof_page")
    _validate_sections(proof["sections"])
    return period


def verify_ir_pdf(
    proof: PdfProof, candidate_symbol: str, cutoff: str, terms: Sequence[str],
    source_bindings: MutableMapping[str, FileBinding], *, page_loader: PageLoader = page_texts,
) -> tuple[dict[str, Any], list[EvidenceRecord], str]:
    """Check retained annual-report bytes and declared SEC correspondence.

    cutoff bounds the reporting period only. Historical eligibility additionally
    requires an availability-aware review, for example check_sec_pit and the
    provenance contracts in review.py. page_loader is an explicit testing seam;
    replacing it does not constitute a run of the pinned PDF extractor.
    """
    period = _proof_inputs(proof, candidate_symbol, cutoff)
    bindings = proof["bindings"]
    raw = read_bound(bindings["pdf"])
    try:
        receipt = json.loads(read_bound(bindings["retrieval_receipt"]))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("PDF acquisition receipt is not valid JSON") from exc
    if (not isinstance(receipt, dict) or receipt.get("sha256") != digest(raw)
            or receipt.get("path") != bindings["pdf"]["path"]
            or receipt.get("final_url") != proof["source_url"]
            or type(receipt.get("bytes")) is not int or receipt["bytes"] != len(raw)):
        raise ValueError("PDF acquisition receipt differs")
    metadata_raw = read_bound(bindings["submissions"])
    header = read_bound(bindings["header"])
    metadata = parse_submissions(
        metadata_raw, expected_cik=proof["cik"], source_url=proof["metadata_url"],
        allowed_forms=frozenset({"10-K"}), on_incomplete_record=lambda row: None,
    )
    matches = [row for row in metadata if row.accession_number == proof["accession_number"]]
    if len(matches) != 1:
        raise ValueError("PDF corresponding SEC accession not unique")
    sec = parse_sec_header(header, matches[0])
    if sec.report_date != period or sec.cik != proof["cik"]:
        raise ValueError("PDF corresponding SEC identity/report-period mismatch")
    sections = proof["sections"]
    numbers = {proof["cover_page"], proof["period_proof_page"]}
    for section in sections:
        numbers.update(range(section["first_page"], section["last_page"] + 2))
    pages = page_loader(raw, numbers)
    if any(number not in pages or not isinstance(pages[number], str) for number in numbers):
        raise ValueError("PDF extractor omitted a required page")
    cover = " ".join(pages[proof["cover_page"]].split())
    period_body = " ".join(pages[proof["period_proof_page"]].split())
    date_label = _MONTH_NAMES[period.month - 1] + " " + str(period.day) + ", " + str(period.year)
    symbol_pattern = r"(?<![A-Za-z0-9])" + re.escape(proof["symbol"]) + r"(?![A-Za-z0-9])"
    if ("FORM 10-K" not in cover or proof["issuer_name"].upper() not in cover.upper()
            or date_label not in cover or not re.search(symbol_pattern, cover)
            or date_label not in period_body or "twelve-month period" not in period_body):
        raise ValueError("PDF cover/annual period corroboration failed")
    header_text = header.decode("utf-8")
    if sec.filer_claims:
        header_text = "\n".join(
            header_text[claim.source_start:claim.source_end]
            for claim in sec.filer_claims if claim.cik == sec.cik
        )
    tax_ids = set(re.findall(r"<IRS-NUMBER>\s*([0-9]+)\b", header_text))
    file_numbers = set(re.findall(r"<FILE-NUMBER>\s*([0-9]+-[0-9]+)\b", header_text))
    if (tax_ids != {proof["ein"].replace("-", "")} or proof["ein"] not in cover
            or file_numbers != {proof["sec_file_number"]} or proof["sec_file_number"] not in cover):
        raise ValueError("PDF/header tax ID or file number mismatch")
    identity = {"source_sha256": digest(raw), "source_url": proof["source_url"],
                "accession_number": proof["accession_number"]}
    evidence = extract_page_quotes(pages, sections, identity, terms)
    if not evidence or {record["section_role"] for record in evidence} != ROLES:
        raise ValueError("PDF lacks selected operating/financial coverage")
    for record in evidence:
        record["verification_status"] = "PASS"
        record["source_binding_basis"] = "RETAINED_PDF_REEXTRACTION_AND_SEC_IDENTITY_PERIOD_CORRESPONDENCE"
    for binding in bindings.values():
        source_bindings[binding["path"]] = binding
    synthetic = proof["source_origin"] == "SYNTHETIC"
    return {
        "source_status": ("SYNTHETIC_ANNUAL_PDF_VALIDATED_METADATA_CORRESPONDENCE" if synthetic
                          else "IR_ANNUAL_PDF_VALIDATED_SEC_CORRESPONDENCE"),
        "source_origin": proof["source_origin"], "source_origin_verified": False,
        "page_text_extraction": ("PINNED_PYPDF" if page_loader is page_texts
                                 else "CALLER_SUPPLIED_PAGE_LOADER"),
        "point_in_time_eligibility": "NOT_EVALUATED",
        "source_accession": sec.accession_number, "source_sha256": digest(raw),
        "source_form": sec.form_type, "reporting_period_end": period.isoformat(),
        "reporting_period_basis": "PDF_COVER_BODY_AND_SEC_METADATA_HEADER",
        "filing_date": sec.filing_date.isoformat(),
        "acceptance_timestamp": sec.availability_time.isoformat() if sec.availability_time else None,
        "availability_basis": sec.availability_basis,
        "source_format": "PDF", "sec_body_byte_equivalence_verified": False,
    }, evidence, sec.cik
