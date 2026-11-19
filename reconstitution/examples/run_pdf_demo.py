#!/usr/bin/env python3
"""Run actual PDF extraction and separate synthetic eligibility cases, offline."""

import argparse
from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sys

from index_reconstitution import (
    MethodologyRule, MethodologyVersion, PARSER_VERSION, PDF_METHOD, Provenance,
    ReviewCutoff, RuleCheckResult, SecurityIdentity, Status, assess_eligibility,
    check_availability, digest, json_bytes, page_texts, verify_ir_pdf,
)
from synthetic_fixture import (
    ACCESSION, CIK, FILENAMES, ISSUER, REPORTING_CUTOFF, REVIEW_CUTOFF, SYMBOL,
    fixture_directory, write_fixture,
)


_DEFAULT_AVAILABILITY = object()


def assess_synthetic_case(summary, *, confirmed=False, availability=_DEFAULT_AVAILABILITY):
    """Evaluate one deliberately narrow fixture rule using the actual contracts."""
    cutoff = ReviewCutoff(datetime.fromisoformat(REVIEW_CUTOFF), "synthetic-demo-v1")
    security = SecurityIdentity(
        "synthetic-security", "synthetic-issuer", SYMBOL, "SYNTHETIC_EXCHANGE", date(2024, 1, 1),
    )
    rule = MethodologyRule(
        "retained-source-available", "The retained synthetic source must be available by the explicit cutoff.",
        required_evidence=(ACCESSION,),
    )
    methodology = MethodologyVersion(
        cutoff.methodology_version_id, "synthetic demonstration rule; not an index-provider methodology",
        date(2024, 1, 1), (rule,), confirmed=confirmed,
    )
    if availability is _DEFAULT_AVAILABILITY:
        availability = datetime.fromisoformat(summary["acceptance_timestamp"]) if summary["acceptance_timestamp"] else None
    provenance = Provenance(
        source="https://synthetic-issuer.example/reports/annual-2024.pdf",
        source_record_id=ACCESSION, issuer_id=security.issuer_id, security_id=security.security_id,
        observation_date=date.fromisoformat(summary["filing_date"]),
        reporting_period=summary["reporting_period_end"], availability_time=availability,
        review_cutoff=cutoff, methodology_version_id=methodology.version_id,
        content_sha256=summary["source_sha256"],
        transformations=("synthetic_local_pdf_correspondence", "separate_availability_review"),
    )
    check = RuleCheckResult(rule.rule_id, methodology.version_id, Status.PASS, (provenance,))
    assessment = assess_eligibility(security, methodology, cutoff, (check,))
    temporal = check_availability(provenance, cutoff)
    return {
        "status": assessment.status.value,
        "unresolved_reasons": list(assessment.unresolved_reasons),
        "availability_status": temporal.status.value, "availability_reason": temporal.reason,
        "availability_time": availability.isoformat() if availability else None,
        "review_cutoff": cutoff.timestamp.isoformat(),
        "methodology_version": methodology.version_id, "methodology_confirmed": confirmed,
        "scope": "One explicit synthetic rule only; not actual index eligibility or an investment recommendation.",
    }


def run_demo(output_directory):
    """Create a new output directory and return the generated stable result."""
    directory = Path(os.path.abspath(os.path.expanduser(str(output_directory))))
    if any(path.is_symlink() for path in (directory, *directory.parents)):
        raise ValueError("Output directory must not traverse a symlink")
    directory.mkdir(exist_ok=False)
    proof = write_fixture(directory)
    with fixture_directory(directory):
        retained = {}
        summary, evidence, cik = verify_ir_pdf(proof, SYMBOL, REPORTING_CUTOFF, ["battery"], retained)
        raw = Path(FILENAMES["pdf"]).read_bytes()
        pages = page_texts(raw, range(1, 8))
        for record in evidence:
            text = pages[record["pdf_page"]]
            if text[record["source_start"]:record["source_end"]] != record["quote"]:
                raise ValueError("An evidence locator did not replay exactly")
            if digest(text.encode("utf-8")) != record["page_text_sha256"]:
                raise ValueError("An evidence page hash did not replay exactly")
        cutoff = datetime.fromisoformat(REVIEW_CUTOFF)
        result = {
            "schema_version": "index-reconstitution.demo.v1",
            "fixture": {
                "synthetic": True, "offline": True, "issuer": ISSUER, "symbol": SYMBOL,
                "cik": cik, "accession_number": ACCESSION,
                "notice": "All documents and issuer identifiers are fictional fixtures. No source authenticity or real company conclusion is claimed.",
            },
            "parser": {"name": "pypdf", "version": PARSER_VERSION, "method": PDF_METHOD},
            "source_validation": summary,
            "evidence": evidence,
            "quote_replay": {
                "records_checked": len(evidence), "all_offsets_exact": True,
                "offset_unit": "Unicode code points within each extracted page string",
                "transcript_file": "page_texts.json",
            },
            "provenance": dict(sorted(retained.items())),
            "eligibility_reviews": {
                "unconfirmed_methodology": assess_synthetic_case(summary),
                "confirmed_synthetic_rule": assess_synthetic_case(summary, confirmed=True),
                "late_availability": assess_synthetic_case(summary, confirmed=True, availability=cutoff + timedelta(seconds=1)),
                "unknown_availability": assess_synthetic_case(summary, confirmed=True, availability=None),
            },
        }
        with Path("page_texts.json").open("xb") as handle:
            handle.write(json_bytes({str(page): text for page, text in pages.items()}))
        with Path("result.json").open("xb") as handle:
            handle.write(json_bytes(result))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, help="New local directory; existing paths are never overwritten")
    args = parser.parse_args()
    try:
        result = run_demo(args.output_dir)
    except (ValueError, OSError) as error:
        print(f"Demo stopped: {error}", file=sys.stderr)
        return 1
    print("Synthetic offline demo completed using pypdf " + PARSER_VERSION + ".")
    print(f"Replayed {result['quote_replay']['records_checked']} exact PDF text locators.")
    print("Source validation and methodology eligibility are separate in result.json.")
    print("Files written to " + str(Path(args.output_dir).absolute()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
