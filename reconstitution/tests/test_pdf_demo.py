"""Exercise actual pinned PDF extraction with entirely synthetic local fixtures."""

from copy import deepcopy
from datetime import date, datetime, timedelta
import hashlib
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import pypdf

from index_reconstitution import (
    MethodologyRule, MethodologyVersion, PARSER_VERSION, PDF_METHOD, RuleException,
    extract_page_quotes, json_bytes, page_texts, section_ranges, verify_ir_pdf,
)
from index_reconstitution.bindings import MAX_SOURCE_BYTES

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "examples"))
from run_pdf_demo import assess_synthetic_case, run_demo
from synthetic_fixture import (
    ACCEPTANCE_TIME, ACCESSION, CIK, FILENAMES, REPORTING_CUTOFF, REVIEW_CUTOFF,
    SECTIONS, SOURCE_URL, SYMBOL, fixture_directory, make_pdf, page_paragraphs,
    relative_binding, write_fixture,
)


class PdfEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.proof = write_fixture(self.root)

    def verify(self, proof=None, cutoff=REPORTING_CUTOFF):
        retained = {}
        with fixture_directory(self.root), mock.patch.object(socket, "socket", side_effect=AssertionError("Network use is forbidden in this fixture")):
            result = verify_ir_pdf(self.proof if proof is None else proof, SYMBOL, cutoff, ["battery"], retained)
        return (*result, retained)

    def rebind(self, proof, role, raw):
        path = self.root / FILENAMES[role]
        path.write_bytes(raw)
        proof["bindings"][role] = relative_binding(self.root, path.name)

    def replace_pdf(self, raw, proof=None):
        proof = deepcopy(self.proof) if proof is None else proof
        self.rebind(proof, "pdf", raw)
        receipt = json.loads((self.root / FILENAMES["retrieval_receipt"]).read_bytes())
        receipt.update(sha256=proof["bindings"]["pdf"]["sha256"], bytes=len(raw))
        self.rebind(proof, "retrieval_receipt", json_bytes(receipt))
        return proof

    def test_actual_pdf_replays_roles_unicode_offsets_and_hashes(self):
        raw = (self.root / FILENAMES["pdf"]).read_bytes()
        self.assertTrue(raw.startswith(b"%PDF-"))
        self.assertEqual(pypdf.__version__, "6.10.0")
        self.assertEqual(len(pypdf.PdfReader(io.BytesIO(raw), strict=True).pages), 7)
        summary, evidence, cik, retained = self.verify()
        self.assertEqual(cik, CIK)
        self.assertEqual(len(retained), 4)
        self.assertEqual(summary["source_origin"], "SYNTHETIC")
        self.assertFalse(summary["source_origin_verified"])
        self.assertEqual(summary["page_text_extraction"], "PINNED_PYPDF")
        self.assertEqual(summary["point_in_time_eligibility"], "NOT_EVALUATED")
        self.assertFalse(summary["sec_body_byte_equivalence_verified"])
        self.assertEqual(summary["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(summary["acceptance_timestamp"], ACCEPTANCE_TIME)
        self.assertEqual({record["section_role"] for record in evidence},
                         {"BUSINESS", "OPERATING_FINANCIAL", "FINANCIAL_NOTES"})
        pages = page_texts(raw, range(1, 8))
        for record in evidence:
            text = pages[record["pdf_page"]]
            self.assertEqual(text[record["source_start"]:record["source_end"]], record["quote"])
            self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), record["page_text_sha256"])
            self.assertEqual(record["source_sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(record["location_basis"], PDF_METHOD + ":pypdf:" + PARSER_VERSION)
            self.assertEqual(record["verification_status"], "PASS")
            self.assertFalse(record["sec_body_byte_equivalence_verified"])
        business = next(record for record in evidence if record["section_role"] == "BUSINESS")
        self.assertIn("café", pages[2])
        self.assertNotEqual(len(pages[2][:business["source_start"]].encode("utf-8")), business["source_start"])

    def test_direct_locator_extraction_does_not_claim_upstream_verification(self):
        raw = (self.root / FILENAMES["pdf"]).read_bytes()
        identity = {"source_sha256": hashlib.sha256(raw).hexdigest(),
                    "source_url": SOURCE_URL, "accession_number": ACCESSION}
        evidence = extract_page_quotes(page_texts(raw, range(1, 8)), SECTIONS, identity, ["battery"])
        self.assertEqual(len(evidence), 3)
        self.assertTrue(all(record["verification_status"] == "TRANSCRIPT_LOCATOR_CHECKED" for record in evidence))

    def test_tampered_bound_inputs_fail_without_registering_sources(self):
        for role in FILENAMES:
            with self.subTest(role=role):
                path = self.root / FILENAMES[role]
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                retained = {}
                try:
                    with fixture_directory(self.root), self.assertRaises(ValueError):
                        verify_ir_pdf(self.proof, SYMBOL, REPORTING_CUTOFF, ["battery"], retained)
                    self.assertEqual(retained, {})
                finally:
                    path.write_bytes(original)

    def test_rebound_receipt_must_match_original_pdf_identity(self):
        original = (self.root / FILENAMES["retrieval_receipt"]).read_bytes()
        receipt = json.loads(original)
        for field, replacement in (("sha256", "0" * 64), ("path", "different.pdf"),
                                   ("final_url", "https://different.example/report.pdf"),
                                   ("bytes", receipt["bytes"] + 1)):
            with self.subTest(field=field):
                proof = deepcopy(self.proof)
                changed = dict(receipt, **{field: replacement})
                self.rebind(proof, "retrieval_receipt", json_bytes(changed))
                with self.assertRaises(ValueError):
                    self.verify(proof)
        (self.root / FILENAMES["retrieval_receipt"]).write_bytes(original)

    def test_scope_identity_period_and_parser_mismatches_reject(self):
        mutations = {
            "symbol": "OTHER_SYNTHETIC", "issuer_name": "Another Fictional Issuer",
            "ein": "00-0000001", "sec_file_number": "000-00001", "cik": "9999999998",
            "reporting_period_end": "2025-12-31", "form_type": "20-F",
            "parser_version": "different", "schema_version": "different",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                proof = deepcopy(self.proof)
                proof[field] = value
                with self.assertRaises(ValueError):
                    self.verify(proof)
        with self.assertRaises(ValueError):
            self.verify(cutoff="2024-12-30")
        proof = deepcopy(self.proof)
        del proof["issuer_name"]
        with self.assertRaises(ValueError):
            self.verify(proof)

    def test_rebound_header_identity_and_period_mismatches_reject(self):
        original = (self.root / FILENAMES["header"]).read_bytes()
        for old, new in ((CIK.encode(), b"9999999998"), (b"<PERIOD>20241231", b"<PERIOD>20231231"),
                         (b"<FILING-DATE>20250303", b"<FILING-DATE>20250304")):
            with self.subTest(change=old.decode()):
                proof = deepcopy(self.proof)
                self.rebind(proof, "header", original.replace(old, new))
                with self.assertRaises(ValueError):
                    self.verify(proof)
        (self.root / FILENAMES["header"]).write_bytes(original)

    def test_report_period_pass_does_not_make_future_filing_eligible(self):
        proof = deepcopy(self.proof)
        metadata = json.loads((self.root / FILENAMES["submissions"]).read_bytes())
        metadata["filings"]["recent"]["filingDate"] = ["2025-03-06"]
        metadata["filings"]["recent"]["acceptanceDateTime"] = ["2025-03-06T14:00:00+00:00"]
        header = (self.root / FILENAMES["header"]).read_bytes().replace(b"20250303", b"20250306")
        self.rebind(proof, "submissions", json_bytes(metadata))
        self.rebind(proof, "header", header)
        summary, evidence, _, _ = self.verify(proof)
        self.assertEqual(len(evidence), 3)
        self.assertEqual(summary["point_in_time_eligibility"], "NOT_EVALUATED")
        review = assess_synthetic_case(summary, confirmed=True)
        self.assertEqual(review["status"], "UNRESOLVED")
        self.assertEqual(review["availability_status"], "FAIL")
        self.assertTrue(any("observation date is after review cutoff" in reason for reason in review["unresolved_reasons"]))

    def test_missing_acceptance_is_unresolved_in_separate_review(self):
        proof = deepcopy(self.proof)
        metadata = json.loads((self.root / FILENAMES["submissions"]).read_bytes())
        metadata["filings"]["recent"]["acceptanceDateTime"] = [None]
        header = (self.root / FILENAMES["header"]).read_bytes().replace(b"<ACCEPTANCE-DATETIME>20250303090000\n", b"")
        self.rebind(proof, "submissions", json_bytes(metadata))
        self.rebind(proof, "header", header)
        summary, _, _, _ = self.verify(proof)
        self.assertIsNone(summary["acceptance_timestamp"])
        review = assess_synthetic_case(summary, confirmed=True)
        self.assertEqual(review["status"], "UNRESOLVED")
        self.assertEqual(review["availability_status"], "UNRESOLVED")
        self.assertTrue(any("availability time is unknown" in reason for reason in review["unresolved_reasons"]))

    def test_conflicting_acceptance_claim_is_not_treated_as_available(self):
        proof = deepcopy(self.proof)
        metadata = json.loads((self.root / FILENAMES["submissions"]).read_bytes())
        metadata["filings"]["recent"]["acceptanceDateTime"] = ["2025-03-03T20:00:00+00:00"]
        self.rebind(proof, "submissions", json_bytes(metadata))
        summary, _, _, _ = self.verify(proof)
        self.assertIsNone(summary["acceptance_timestamp"])
        self.assertEqual(assess_synthetic_case(summary, confirmed=True)["status"], "UNRESOLVED")

    def test_malformed_and_oversized_pdf_inputs_reject(self):
        for raw in (b"not a PDF", b"%PDF-1.7\nbroken\n%%EOF\n", b"%PDF-" + b"x" * MAX_SOURCE_BYTES):
            with self.subTest(length=len(raw)), self.assertRaises(ValueError):
                page_texts(raw, [1])

    def test_actual_encrypted_pdf_rejects(self):
        raw = make_pdf(encrypted=True)
        self.assertTrue(pypdf.PdfReader(io.BytesIO(raw), strict=True).is_encrypted)
        with self.assertRaises(ValueError):
            page_texts(raw, [1])

    def test_page_requests_and_actual_page_count_are_bounded(self):
        raw = (self.root / FILENAMES["pdf"]).read_bytes()
        for number in (0, -1, True, 1.5, "1", None, 8, 10**9):
            with self.subTest(number=number), self.assertRaises(ValueError):
                page_texts(raw, [number])
        with self.assertRaises(ValueError):
            page_texts(raw, range(10**12))
        self.assertEqual(list(page_texts(raw, [4, 2, 2])), [2, 4])
        with self.assertRaises(ValueError):
            page_texts(make_pdf(blank_page_count=501), [1])

    def test_blank_actual_pdf_produces_no_invented_text_or_ocr(self):
        raw = make_pdf(blank_page_count=7)
        self.assertEqual(page_texts(raw, [1, 2]), {1: "", 2: ""})
        proof = self.replace_pdf(raw)
        with self.assertRaises(ValueError):
            self.verify(proof)

    def test_invalid_section_boundaries_are_rejected_before_expansion(self):
        pages = page_texts((self.root / FILENAMES["pdf"]).read_bytes(), range(1, 8))
        mutations = (
            ("role", "RISK_FACTORS"), ("first_page", True), ("first_page", 0),
            ("first_page", -1), ("last_page", 10**12), ("last_page", 500),
            ("start_heading", ""), ("next_heading", " "),
            ("start_heading", "Absent heading"), ("next_heading", "Absent boundary"),
        )
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                sections = deepcopy(SECTIONS)
                sections[0][field] = value
                with self.assertRaises(ValueError):
                    section_ranges(pages, sections)
        sections = deepcopy(SECTIONS)
        sections[1]["first_page"] = 2
        with self.assertRaises(ValueError):
            section_ranges(pages, sections)
        pages[2] += "\nItem 1A. Risk Factors"
        with self.assertRaises(ValueError):
            section_ranges(pages, SECTIONS)

    def test_actual_pdf_personnel_and_forward_looking_paragraphs_are_not_evidence(self):
        content = page_paragraphs()
        content[2].extend(["Executive Officers",
            "A fictional executive oversees battery products and appears only in this synthetic personnel paragraph. "
            "This wording must never be admitted as operating-business evidence after the personnel heading."])
        content[4].append("Forward-looking statements about battery products involve risks and uncertainties. "
                          "This synthetic paragraph intentionally tests exclusion of such statements rather than operating evidence.")
        proof = self.replace_pdf(make_pdf(content))
        _, evidence, _, _ = self.verify(proof)
        self.assertEqual(len(evidence), 3)
        self.assertTrue(all("fictional executive" not in record["quote"] and "Forward-looking" not in record["quote"] for record in evidence))

    def test_replacement_characters_in_transcripts_are_not_admitted(self):
        raw = (self.root / FILENAMES["pdf"]).read_bytes()
        pages = page_texts(raw, range(1, 8))
        pages[4] += "\n\nUnreadable \ufffd battery passage. " * 7
        identity = {"source_sha256": hashlib.sha256(raw).hexdigest(), "source_url": SOURCE_URL, "accession_number": ACCESSION}
        records = extract_page_quotes(pages, SECTIONS, identity, ["battery"])
        self.assertTrue(all("\ufffd" not in record["quote"] for record in records))


class DemoAndReviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def test_demo_is_reproducible_offline_and_matches_checked_in_result(self):
        with mock.patch.object(socket, "socket", side_effect=AssertionError("Unexpected network access")):
            first = run_demo(self.root / "first")
            second = run_demo(self.root / "second")
        self.assertEqual(first, second)
        self.assertEqual((self.root / "first" / FILENAMES["pdf"]).read_bytes(), (self.root / "second" / FILENAMES["pdf"]).read_bytes())
        expected = json.loads((PACKAGE_ROOT / "examples" / "expected_result.json").read_bytes())
        self.assertEqual(first, expected)
        self.assertEqual(first["quote_replay"]["records_checked"], 3)
        self.assertTrue(first["quote_replay"]["all_offsets_exact"])
        serialized = json_bytes(first).decode("utf-8")
        self.assertNotIn(str(self.root), serialized)
        self.assertTrue(all(Path(binding["path"]).name == binding["path"] for binding in first["provenance"].values()))
        self.assertEqual(first["eligibility_reviews"]["unconfirmed_methodology"]["status"], "UNRESOLVED")
        self.assertEqual(first["eligibility_reviews"]["confirmed_synthetic_rule"]["status"], "ELIGIBLE")
        self.assertEqual(first["eligibility_reviews"]["late_availability"]["status"], "UNRESOLVED")
        self.assertEqual(first["eligibility_reviews"]["unknown_availability"]["status"], "UNRESOLVED")

    def test_cli_creates_new_output_and_refuses_overwrite(self):
        output = self.root / "cli-output"
        command = [sys.executable, str(PACKAGE_ROOT / "examples" / "run_pdf_demo.py"), "--output-dir", str(output)]
        first = subprocess.run(command, capture_output=True, timeout=30)
        self.assertEqual(first.returncode, 0, first.stderr.decode())
        before = {path.name: path.read_bytes() for path in output.iterdir()}
        second = subprocess.run(command, capture_output=True, timeout=30)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)

    def test_review_cutoff_is_separate_and_inclusive(self):
        result = run_demo(self.root / "review")
        summary = result["source_validation"]
        cutoff = datetime.fromisoformat(REVIEW_CUTOFF)
        self.assertEqual(assess_synthetic_case(summary, confirmed=True, availability=cutoff)["status"], "ELIGIBLE")
        late = assess_synthetic_case(summary, confirmed=True, availability=cutoff + timedelta(seconds=1))
        self.assertEqual(late["status"], "UNRESOLVED")
        self.assertEqual(late["availability_status"], "FAIL")
        self.assertTrue(any("input became available after review cutoff" in reason for reason in late["unresolved_reasons"]))

    def test_confirmation_and_exception_approval_require_typed_values(self):
        rule = MethodologyRule("fixture-rule", "Synthetic rule")
        with self.assertRaises(ValueError):
            MethodologyVersion("fixture-v1", "synthetic", date(2024, 1, 1), (rule,), confirmed="false")
        with self.assertRaises(ValueError):
            RuleException("Synthetic exception", approval="fake approval")


if __name__ == "__main__":
    unittest.main()
