"""Offline PDF evidence and typed review contracts, extracted as a small example."""

from .bindings import FileBinding, bind, digest, json_bytes, read_bound
from .filings import SecFilingMetadata, check_sec_pit, parse_sec_header, parse_submissions
from .pdf import (
    PARSER_VERSION, PDF_METHOD, PROOF_SCHEMA_VERSION, PdfProof, PdfSection,
    extract_page_quotes, page_texts, section_ranges, verify_ir_pdf,
)
from .review import (
    AvailabilityResult, CalculationWindow, EligibilityAssessment, EligibilityStatus,
    HumanApproval, MethodologyRule, MethodologyVersion, PointInTimeError, Provenance,
    ReviewCutoff, RuleCheckResult, RuleException, SecurityIdentity, Status,
    assess_eligibility, check_availability, check_observation_availability, require_available,
)

__all__ = [
    "AvailabilityResult", "CalculationWindow", "EligibilityAssessment", "EligibilityStatus",
    "FileBinding", "HumanApproval", "MethodologyRule", "MethodologyVersion", "PARSER_VERSION",
    "PDF_METHOD", "PROOF_SCHEMA_VERSION", "PdfProof", "PdfSection", "PointInTimeError",
    "Provenance", "ReviewCutoff", "RuleCheckResult", "RuleException", "SecFilingMetadata",
    "SecurityIdentity", "Status", "assess_eligibility", "bind", "check_availability",
    "check_observation_availability", "check_sec_pit", "digest", "extract_page_quotes",
    "json_bytes", "page_texts", "parse_sec_header", "parse_submissions", "read_bound",
    "require_available", "section_ranges", "verify_ir_pdf",
]
