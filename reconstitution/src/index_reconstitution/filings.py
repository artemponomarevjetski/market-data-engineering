"""Parse locally retained SEC metadata and original submission headers.

No function in this module retrieves a URL. SEC acceptance is a research
availability proxy, not proof of the first instant of public dissemination.
"""

from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
import hashlib
import json
import re
from typing import Callable
from urllib.parse import unquote, urlsplit
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .review import ReviewCutoff, AvailabilityResult, Status, check_observation_availability
from ._validation import ensure_aware, ensure_date, ensure_sha256, normalize_cik, require_nonempty

ANNUAL_FORMS = frozenset(("10-K", "20-F", "40-F"))


REGISTRATION_FORMS = frozenset(("S-1", "S-1/A", "F-1", "F-1/A", "S-4", "S-4/A",
                                "F-4", "F-4/A", "424B3", "424B4", "20FR12B", "20FR12B/A"))


UPDATE_FORMS = frozenset(("10-K/A", "20-F/A", "40-F/A", "8-K", "8-K/A", "6-K", "6-K/A"))


SOURCE_FORMS = ANNUAL_FORMS | REGISTRATION_FORMS | UPDATE_FORMS


AVAILABILITY_BASIS = "SEC_ACCEPTANCE_PROXY"


PUBLIC_VISIBILITY_CAVEAT = (
    "SEC acceptance is not a first-public-visibility timestamp. SEC reports "
    "dissemination lag and possible next-business-day dissemination; exact "
    "public availability remains unknown."
)


_ACCESSION = re.compile(r"[0-9]{10}-[0-9]{2}-[0-9]{6}\Z")


_DOCUMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")


class SecEdgarError(ValueError):
    """Malformed, conflicting, unsafe, or out-of-bounds SEC source."""


@dataclass(frozen=True)
class SecFilerClaim:
    cik: str
    issuer_name: str
    source_start: int
    source_end: int
    representation: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "cik", _cik(self.cik))
        require_nonempty(self.issuer_name, "issuer_name")
        if (isinstance(self.source_start, bool) or not isinstance(self.source_start, int)
                or isinstance(self.source_end, bool) or not isinstance(self.source_end, int)
                or self.source_start < 0 or self.source_end <= self.source_start
                or self.representation not in {"TAGGED_FILER", "READABLE_FILER"}):
            raise SecEdgarError("SEC filer claim requires an exact ordered original header block")


@dataclass(frozen=True)
class SecFilingMetadata:
    cik: str
    issuer_name: str
    form_type: str
    accession_number: str
    primary_document: str
    filing_date: date
    report_date: date | None
    acceptance_time: datetime | None
    acceptance_raw_json: str | None
    acceptance_raw_header: str | None
    availability_basis: str
    metadata_source_url: str
    metadata_sha256: str
    header_source_url: str | None = None
    header_sha256: str | None = None
    post_acceptance_change_date: date | None = None
    private_to_public: bool = False
    public_delay_flag: bool = False
    acceptance_claim_status: str = "NOT_PRESENT"
    acceptance_source_conflict: bool = False
    filer_claims: tuple[SecFilerClaim, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "cik", _cik(self.cik))
        require_nonempty(self.issuer_name, "issuer_name")
        if not isinstance(self.filer_claims, tuple) or any(not isinstance(claim, SecFilerClaim) for claim in self.filer_claims):
            raise SecEdgarError("SEC filer claims must retain immutable typed original header blocks")
        if self.filer_claims and not any(claim.cik == self.cik and claim.issuer_name == self.issuer_name for claim in self.filer_claims):
            raise SecEdgarError("SEC retained filer claims do not include the expected issuer")
        if not isinstance(self.form_type, str) or self.form_type not in SOURCE_FORMS:
            raise SecEdgarError("SEC metadata form is not a supported evidence filing")
        archive_url(self.cik, self.accession_number, self.primary_document)
        ensure_date(self.filing_date, "filing_date")
        if self.report_date is not None:
            ensure_date(self.report_date, "report_date")
            if self.report_date > self.filing_date:
                raise SecEdgarError("SEC reporting period follows the filing date")
        if self.post_acceptance_change_date is not None:
            ensure_date(self.post_acceptance_change_date, "post_acceptance_change_date")
        if not isinstance(self.private_to_public, bool) or not isinstance(self.public_delay_flag, bool):
            raise SecEdgarError("SEC public-delay markers must be Boolean")
        if (self.private_to_public or (self.post_acceptance_change_date is not None
                and self.post_acceptance_change_date > self.filing_date)) and not self.public_delay_flag:
            raise SecEdgarError("SEC public-delay evidence cannot be silently ignored")
        if self.acceptance_time is not None:
            ensure_aware(self.acceptance_time, "acceptance_time")
            if (self.acceptance_raw_header is None or self.header_source_url is None
                    or self.header_sha256 is None):
                raise SecEdgarError("SEC accepted time requires original header timestamp, URL and hash")
            if _accepted_utc(self.acceptance_raw_header) != self.acceptance_time:
                raise SecEdgarError("SEC accepted time does not match its original Eastern header timestamp")
        for name in ("acceptance_raw_json", "acceptance_raw_header"):
            if getattr(self, name) is not None:
                require_nonempty(getattr(self, name), name)
        expected_claim = _acceptance_claim_status(self.acceptance_raw_json, self.acceptance_time)
        if self.acceptance_claim_status != expected_claim:
            raise SecEdgarError("SEC acceptance claim status does not match retained source claims")
        if (not isinstance(self.acceptance_source_conflict, bool)
                or self.acceptance_source_conflict != (expected_claim in {"CONFLICT", "UNRESOLVED"})):
            raise SecEdgarError("SEC acceptance source conflict cannot be silently ignored")
        expected_basis = (AVAILABILITY_BASIS
                          if self.acceptance_time is not None and not self.public_delay_flag
                          and not self.acceptance_source_conflict
                          else "UNRESOLVED")
        if self.availability_basis != expected_basis:
            raise SecEdgarError("SEC availability basis does not match accepted-time evidence")
        _url(self.metadata_source_url)
        ensure_sha256(self.metadata_sha256, "metadata_sha256")
        if (self.header_source_url is None) != (self.header_sha256 is None):
            raise SecEdgarError("SEC original header reference and hash must be retained together")
        if self.header_source_url is not None:
            if self.header_source_url != self.header_url:
                raise SecEdgarError("SEC header source URL does not match filing identity")
            ensure_sha256(self.header_sha256, "header_sha256")

    @property
    def availability_time(self) -> datetime | None:
        return self.acceptance_time if not (self.public_delay_flag or self.acceptance_source_conflict) else None

    @property
    def source_url(self) -> str:
        return archive_url(self.cik, self.accession_number, self.primary_document)

    @property
    def header_url(self) -> str:
        return archive_url(
            self.cik, self.accession_number, self.accession_number + ".hdr.sgml"
        )


def _cik(value: str) -> str:
    try:
        normalized = normalize_cik(value)
    except ValueError as exc:
        raise SecEdgarError("SEC CIK must be one to ten ASCII digits") from exc
    if normalized is None or int(normalized) == 0:
        raise SecEdgarError("SEC issuer CIK is missing or zero")
    return normalized


def _url(url: str) -> str:
    if not isinstance(url, str):
        raise SecEdgarError("SEC source URL must be text")
    parts = urlsplit(url)
    if (
        parts.scheme != "https"
        or parts.netloc not in ("www.sec.gov", "data.sec.gov")
        or parts.query or parts.fragment
        or any(part in (".", "..") for part in unquote(parts.path).split("/"))
    ):
        raise SecEdgarError("source URL must be a direct official HTTPS SEC URL")
    if parts.netloc == "data.sec.gov":
        if not parts.path.startswith("/submissions/"):
            raise SecEdgarError("only SEC submissions API paths are authorized")
    elif (not parts.path.startswith("/Archives/edgar/data/")
          and parts.path != "/files/company_tickers.json"):
        raise SecEdgarError("only original SEC filing archive paths are authorized")
    return url


def archive_url(cik: str, accession: str, filename: str) -> str:
    normalized = _cik(cik)
    if not isinstance(accession, str) or not _ACCESSION.fullmatch(accession):
        raise SecEdgarError("invalid SEC accession number")
    if not isinstance(filename, str) or not _DOCUMENT.fullmatch(filename) or filename in (".", ".."):
        raise SecEdgarError("SEC document name is unsafe or unsupported")
    return (
        f"https://www.sec.gov/Archives/edgar/data/{int(normalized)}/"
        f"{accession.replace('-', '')}/{filename}"
    )


def _date(value: object, field: str, *, optional: bool = False) -> date | None:
    if optional and value in (None, ""):
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise SecEdgarError(f"invalid SEC {field}")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SecEdgarError(f"invalid SEC {field}") from exc


def _json(payload: bytes) -> dict:
    try:
        value = json.loads(payload)
    except (ValueError, UnicodeError) as exc:
        raise SecEdgarError("SEC submissions response is not valid JSON") from exc
    if not isinstance(value, dict):
        raise SecEdgarError("SEC submissions response must be an object")
    return value


def _incomplete_submission_record(columns, index, *, cik, issuer_name, source_url, digest, error):
    """Preserve one invalid row, never fabricate a primary document or PIT pass."""
    raw = {key: values[index] for key, values in columns.items()
           if isinstance(values, list) and len(values) == len(columns["accessionNumber"])}
    normalized_dates = {}
    for field, column in (("filing_date", "filingDate"), ("report_date", "reportDate")):
        try:
            value = _date(raw[column], column, optional=column == "reportDate")
            normalized_dates[field] = value.isoformat() if value else None
        except SecEdgarError:
            normalized_dates[field] = None
    primary = raw["primaryDocument"]
    return {
        "sec_cik": cik, "issuer_name": issuer_name, "form_type": raw["form"],
        "accession_number": raw["accessionNumber"], "primary_document": primary,
        **normalized_dates, "acceptance_raw_json": raw.get("acceptanceDateTime"),
        "metadata_source_url": source_url, "metadata_source_hash": digest,
        "row_ordinal": index + 1, "raw_metadata": raw,
        "source_url": archive_url(cik, raw["accessionNumber"], primary) if primary else None,
        "source_hash": None, "availability_time": None,
        "pit_status": "UNRESOLVED", "filing_eligibility": "UNRESOLVED",
        "retrieval_status": "NOT_ATTEMPTED", "manual_review_needed": True,
        "error_type": type(error).__name__, "error_message": str(error),
        "reason": "PRIMARY_DOCUMENT_MISSING" if primary in (None, "") else "ORIGINAL_SUBMISSION_RECORD_INVALID",
    }


def parse_submissions(
    payload: bytes, *, expected_cik: str, source_url: str,
    allowed_forms: frozenset[str] = ANNUAL_FORMS,
    on_incomplete_record: Callable[[dict], None] | None = None,
) -> tuple[SecFilingMetadata, ...]:
    """Parse official column arrays without treating current names as history.

    Historical files omit a top-level CIK; their issuer binding comes from the
    exact CIK-prefixed URL linked by the verified main submissions response.
    JSON acceptance strings remain raw claims until header corroboration.
    """
    if (not isinstance(allowed_forms, frozenset) or not allowed_forms
            or not allowed_forms <= SOURCE_FORMS):
        raise SecEdgarError("SEC allowed forms must be a nonempty supported frozenset")
    if on_incomplete_record is not None and not callable(on_incomplete_record):
        raise SecEdgarError("incomplete-record callback must be callable")
    normalized = _cik(expected_cik)
    _url(source_url)
    expected_source = re.compile(
        rf"https://data\.sec\.gov/submissions/CIK{normalized}(?:-submissions-[0-9]+)?\.json\Z"
    )
    if not expected_source.fullmatch(source_url):
        raise SecEdgarError("SEC submissions source URL does not match issuer CIK")
    body = _json(payload)
    if "filings" in body:
        if _cik(str(body.get("cik", ""))) != normalized:
            raise SecEdgarError("SEC submissions issuer CIK mismatch")
        issuer_name = body.get("name")
        if not isinstance(issuer_name, str) or not issuer_name.strip():
            raise SecEdgarError("SEC submissions issuer name is missing")
        try:
            columns = body["filings"]["recent"]
        except (KeyError, TypeError) as exc:
            raise SecEdgarError("SEC submissions filings.recent is missing") from exc
    else:
        issuer_name = "SEC history metadata; current name unavailable"
        columns = body
    if not isinstance(columns, dict):
        raise SecEdgarError("SEC submissions column arrays are missing")
    required = ("accessionNumber", "filingDate", "reportDate", "form", "primaryDocument")
    if any(not isinstance(columns.get(key), list) for key in required):
        raise SecEdgarError("SEC submissions required column array is missing")
    size = len(columns["accessionNumber"])
    if size > 100_000:
        raise SecEdgarError("SEC submissions row bound exceeded")
    if any(len(columns[key]) != size for key in required):
        raise SecEdgarError("SEC submissions column lengths differ")
    accepted = columns.get("acceptanceDateTime", [None] * size)
    if not isinstance(accepted, list) or len(accepted) != size:
        raise SecEdgarError("SEC acceptanceDateTime column length differs")
    digest = hashlib.sha256(payload).hexdigest()
    records: list[SecFilingMetadata] = []
    accessions: set[str] = set()
    for index in range(size):
        accession = columns["accessionNumber"][index]
        if not isinstance(accession, str) or not _ACCESSION.fullmatch(accession):
            raise SecEdgarError("invalid SEC accession number")
        if accession in accessions:
            raise SecEdgarError("duplicate SEC accession number")
        accessions.add(accession)
        form = columns["form"][index]
        if not isinstance(form, str) or not form:
            raise SecEdgarError("SEC form type is missing")
        if form not in allowed_forms:
            continue
        primary = columns["primaryDocument"][index]
        if primary in (None, "") and on_incomplete_record is not None:
            error = SecEdgarError("SEC document name is unsafe or unsupported")
            on_incomplete_record(_incomplete_submission_record(
                columns, index, cik=normalized, issuer_name=issuer_name,
                source_url=source_url, digest=digest, error=error))
            continue
        # Unsafe nonempty names and non-string values remain global hard guards.
        archive_url(normalized, accession, primary if isinstance(primary, str) else "")
        try:
            raw_accepted = accepted[index]
            if raw_accepted not in (None, "") and not isinstance(raw_accepted, str):
                raise SecEdgarError("invalid SEC acceptanceDateTime claim")
            records.append(SecFilingMetadata(
                cik=normalized, issuer_name=issuer_name, form_type=form,
                accession_number=accession, primary_document=primary,
                filing_date=_date(columns["filingDate"][index], "filingDate"),
                report_date=_date(columns["reportDate"][index], "reportDate", optional=True),
                acceptance_time=None, acceptance_raw_json=raw_accepted or None,
                acceptance_raw_header=None, availability_basis="UNRESOLVED",
                metadata_source_url=source_url, metadata_sha256=digest,
                acceptance_claim_status=_acceptance_claim_status(raw_accepted or None, None),
                acceptance_source_conflict=(_acceptance_claim_status(raw_accepted or None, None)
                                            == "UNRESOLVED"),
            ))
        except SecEdgarError as error:
            if on_incomplete_record is None:
                raise
            on_incomplete_record(_incomplete_submission_record(
                columns, index, cik=normalized, issuer_name=issuer_name,
                source_url=source_url, digest=digest, error=error))
    return tuple(records)


_HEADER_TAGS = {
    "ACCESSION NUMBER": "ACCESSION-NUMBER",
    "CONFORMED SUBMISSION TYPE": "TYPE",
    "CENTRAL INDEX KEY": "CIK",
    "FILED AS OF DATE": "FILING-DATE",
    "CONFORMED PERIOD OF REPORT": "PERIOD",
    "COMPANY CONFORMED NAME": "CONFORMED-NAME",
    "DATE AS OF CHANGE": "DATE-OF-FILING-DATE-CHANGE",
}


def _header_field(text: str, name: str, *, optional: bool = False) -> str | None:
    """Read observed SEC readable-header and tagged SGML forms together.

    These are exact source field aliases, not guessed fields. Conflicting
    values in either representation are rejected rather than prioritized.
    """
    matches = re.findall(r"^\s*" + re.escape(name) + r":\s*([^\r\n<]+)", text, re.MULTILINE)
    tag = _HEADER_TAGS[name]
    matches.extend(re.findall(r"^\s*<" + re.escape(tag) + r">[ \t]*([^\r\n<]+)",
                              text, re.MULTILINE))
    values = {value.strip() for value in matches}
    if optional and not values:
        return None
    if len(values) != 1:
        raise SecEdgarError(f"original SEC header has missing or conflicting {name}")
    return values.pop()


def _acceptance_claim_status(raw_json: str | None, accepted: datetime | None) -> str:
    """Compare the literal aware JSON instant to original header UTC, without repairs."""
    if raw_json is None:
        return "NOT_PRESENT"
    try:
        claimed = datetime.fromisoformat(raw_json.replace("Z", "+00:00"))
        ensure_aware(claimed, "SEC JSON acceptance claim")
    except (ValueError, TypeError):
        return "UNRESOLVED"
    if accepted is None:
        return "UNVERIFIED"
    return "MATCH" if claimed == accepted else "CONFLICT"


def _accepted_utc(raw: str) -> datetime:
    if not isinstance(raw, str) or not re.fullmatch(r"[0-9]{14}", raw):
        raise SecEdgarError("original SEC acceptance timestamp is invalid")
    try:
        eastern = ZoneInfo("America/New_York")
        naive = datetime.strptime(raw, "%Y%m%d%H%M%S")
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise SecEdgarError("SEC Eastern acceptance timezone/date is unavailable or invalid") from exc
    accepted = naive.replace(tzinfo=eastern)
    if accepted.utcoffset() != accepted.replace(fold=1).utcoffset():
        raise SecEdgarError("SEC local acceptance timestamp is ambiguous or nonexistent")
    if accepted.astimezone(timezone.utc).astimezone(eastern).replace(tzinfo=None) != naive:
        raise SecEdgarError("SEC local acceptance timestamp is nonexistent")
    return accepted.astimezone(timezone.utc)


def _scoped_filers(text: str, expected_cik: str) -> tuple[str, tuple[SecFilerClaim, ...]]:
    """Select the expected issuer only inside explicit FILER blocks; retain co-filers."""
    blocks = []
    opens = list(re.finditer(r"<FILER>", text))
    if opens:
        tagged = list(re.finditer(r"<FILER>(.*?)</FILER>", text, re.DOTALL))
        if len(tagged) != len(opens) or len(re.findall(r"</FILER>", text)) != len(opens):
            raise SecEdgarError("original SEC header has malformed FILER blocks")
        blocks = [(match.start(), match.end(), match.group(1), "TAGGED_FILER") for match in tagged]
    else:
        starts = list(re.finditer(r"^[ \t]*FILER:[ \t\r]*$", text, re.MULTILINE))
        for index, match in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
            tail = text[match.end():end]
            boundary = re.search(r"</SEC-HEADER>|^[ \t]*(?:SUBJECT COMPANY|REPORTING-OWNER|ISSUER):", tail, re.MULTILINE)
            if boundary:
                end = match.end() + boundary.start()
            blocks.append((match.start(), end, text[match.end():end], "READABLE_FILER"))
    if not blocks:
        cik = _cik(_header_field(text, "CENTRAL INDEX KEY"))
        if cik != expected_cik:
            raise SecEdgarError("original SEC header issuer CIK mismatch")
        return _header_field(text, "COMPANY CONFORMED NAME"), ()
    claims = tuple(SecFilerClaim(_header_field(body, "CENTRAL INDEX KEY"),
        _header_field(body, "COMPANY CONFORMED NAME"), start, end, kind)
        for start, end, body, kind in blocks)
    names = {}
    for claim in claims:
        if claim.cik in names and names[claim.cik] != claim.issuer_name:
            raise SecEdgarError("original SEC header has conflicting duplicate FILER issuer claims")
        names[claim.cik] = claim.issuer_name
    if expected_cik not in names:
        raise SecEdgarError("original SEC header FILER blocks do not contain the expected issuer CIK")
    return names[expected_cik], claims


def parse_sec_header(payload: bytes, metadata: SecFilingMetadata) -> SecFilingMetadata:
    """Corroborate original filer fields; accession prefixes may identify agents."""
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise SecEdgarError("SEC header is not valid UTF-8") from exc
    if _header_field(text, "ACCESSION NUMBER") != metadata.accession_number:
        raise SecEdgarError("original SEC header accession mismatch")
    if _header_field(text, "CONFORMED SUBMISSION TYPE") != metadata.form_type:
        raise SecEdgarError("original SEC header form mismatch")
    issuer_name, filer_claims = _scoped_filers(text, metadata.cik)
    filed = _header_field(text, "FILED AS OF DATE")
    if filed != metadata.filing_date.strftime("%Y%m%d"):
        raise SecEdgarError("original SEC header filing date mismatch")
    report = _header_field(text, "CONFORMED PERIOD OF REPORT",
                           optional=metadata.form_type not in ANNUAL_FORMS)
    try:
        report_date = datetime.strptime(report, "%Y%m%d").date() if report is not None else None
    except ValueError as exc:
        raise SecEdgarError("original SEC header reporting period is invalid") from exc
    if metadata.report_date is not None and report_date != metadata.report_date:
        raise SecEdgarError("original SEC header reporting period mismatch")
    matches = re.findall(r"<ACCEPTANCE-DATETIME>\s*([^\r\n<]+)", text)
    raw_values = {value.strip() for value in matches}
    if len(raw_values) > 1:
        raise SecEdgarError("original SEC header acceptance times conflict")
    raw = raw_values.pop() if raw_values else None
    accepted_time = _accepted_utc(raw) if raw is not None else None
    raw_change_date = _header_field(text, "DATE AS OF CHANGE", optional=True)
    change_date = None
    if raw_change_date is not None:
        try:
            change_date = datetime.strptime(raw_change_date, "%Y%m%d").date()
        except ValueError as exc:
            raise SecEdgarError("original SEC header change date is invalid") from exc
    private_marker = "<PRIVATE-TO-PUBLIC>" in text
    public_delay = private_marker or (change_date is not None and change_date > metadata.filing_date)
    claim_status = _acceptance_claim_status(metadata.acceptance_raw_json, accepted_time)
    claim_conflict = claim_status in {"CONFLICT", "UNRESOLVED"}
    return replace(
        metadata, issuer_name=issuer_name, filer_claims=filer_claims,
        report_date=report_date,
        acceptance_time=accepted_time,
        acceptance_raw_header=raw,
        availability_basis=(AVAILABILITY_BASIS if accepted_time is not None and not public_delay
                            and not claim_conflict
                            else "UNRESOLVED"),
        header_source_url=metadata.header_url, header_sha256=hashlib.sha256(payload).hexdigest(),
        post_acceptance_change_date=change_date, private_to_public=private_marker,
        public_delay_flag=public_delay, acceptance_claim_status=claim_status,
        acceptance_source_conflict=claim_conflict,
    )


def check_sec_pit(metadata: SecFilingMetadata, cutoff: ReviewCutoff) -> AvailabilityResult:
    accepted_bound = check_observation_availability(
        observation_date=metadata.filing_date,
        availability_time=metadata.acceptance_time, cutoff=cutoff.timestamp,
    )
    if accepted_bound.status is Status.FAIL:
        return accepted_bound
    result = check_observation_availability(
        observation_date=metadata.filing_date,
        availability_time=metadata.availability_time, cutoff=cutoff.timestamp,
    )
    if result.status is Status.FAIL:
        return result
    if metadata.acceptance_claim_status == "CONFLICT":
        return AvailabilityResult(
            Status.UNRESOLVED,
            "SEC submissions acceptance claim conflicts with original header acceptance; public availability unresolved",
        )
    if metadata.acceptance_claim_status == "UNRESOLVED":
        return AvailabilityResult(
            Status.UNRESOLVED,
            "SEC submissions acceptance claim is not a valid aware timestamp; public availability unresolved",
        )
    if metadata.private_to_public:
        return AvailabilityResult(
            Status.UNRESOLVED, "SEC private-to-public marker leaves historical public availability unresolved"
        )
    if (metadata.post_acceptance_change_date is not None
            and metadata.post_acceptance_change_date > metadata.filing_date):
        return AvailabilityResult(
            Status.UNRESOLVED, "SEC post-acceptance change leaves current historical content availability unresolved"
        )
    return result
