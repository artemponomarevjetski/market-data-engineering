"""Generate deterministic, entirely fictional PDF and filing-metadata fixtures.

No network request is made. The SEC-shaped URLs are parser inputs only; the
identifiers, issuer, document and figures are not records of a real filing.
"""

from contextlib import contextmanager
from copy import deepcopy
import io
import os
from pathlib import Path
import textwrap

import pypdf
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from index_reconstitution import PARSER_VERSION, PROOF_SCHEMA_VERSION, bind, json_bytes


ISSUER = "Synthetic Example Industries"
SYMBOL = "SYNTHDEMO"
CIK = "9999999999"
ACCESSION = "9999999999-25-000001"
EIN = "00-0000000"
FILE_NUMBER = "000-00000"
PERIOD_END = "2024-12-31"
FILING_DATE = "2025-03-03"
ACCEPTANCE_TIME = "2025-03-03T14:00:00+00:00"
SOURCE_URL = "https://synthetic-issuer.example/reports/annual-2024.pdf"
METADATA_URL = "https://data.sec.gov/submissions/CIK9999999999.json"
REPORTING_CUTOFF = "2024-12-31"
REVIEW_CUTOFF = "2025-03-04T20:00:00+00:00"

FILENAMES = {
    "pdf": "synthetic_annual_report.pdf",
    "submissions": "synthetic_submissions.json",
    "header": "synthetic_header.sgml",
    "retrieval_receipt": "synthetic_receipt.json",
}

SECTIONS = [
    {"role": "BUSINESS", "first_page": 2, "last_page": 2,
     "start_heading": "Item 1. Business", "next_heading": "Item 1A. Risk Factors"},
    {"role": "OPERATING_FINANCIAL", "first_page": 4, "last_page": 4,
     "start_heading": "Item 7. Management Discussion and Analysis", "next_heading": "Item 7A. Market"},
    {"role": "FINANCIAL_NOTES", "first_page": 6, "last_page": 6,
     "start_heading": "Notes to Financial Statements", "next_heading": "Item 9. Changes"},
]


def page_paragraphs():
    """Return fresh synthetic page content, including a Unicode-offset example."""
    return {
        1: ["SYNTHETIC FIXTURE - NOT A REAL FILING", "FORM 10-K", ISSUER,
            f"Symbol: {SYMBOL}    EIN: {EIN}    File number: {FILE_NUMBER}",
            "Annual period ended December 31, 2024",
            "This locally generated example exists only to demonstrate reproducible PDF parsing."],
        2: ["Item 1. Business - café fixture",
            "This Annual Report covers the twelve-month period from January 1, 2024 to December 31, 2024.",
            "Synthetic Example Industries manufactures battery storage modules for fictional industrial customers. "
            "This paragraph describes an illustrative operating activity solely to exercise evidence extraction. "
            "It contains no real company research, customer information, or investment conclusion."],
        3: ["Item 1A. Risk Factors", "Boundary page retained for the section-range check."],
        4: ["Item 7. Management Discussion and Analysis",
            "In this synthetic scenario, battery module sales are described as a source of operating revenue. "
            "The amounts and conclusions are deliberately omitted. This paragraph tests a separate operating "
            "and financial evidence section without making a claim about an actual business."],
        5: ["Item 7A. Market", "Boundary page retained for the section-range check."],
        6: ["Notes to Financial Statements",
            "The fictional accounting notes describe battery inventory and illustrative product revenue recognition. "
            "No balance, valuation, market statistic, or real customer information appears in this fixture. "
            "Its sole purpose is to provide repeatable financial-note evidence for parser tests."],
        7: ["Item 9. Changes", "End boundary. This document is synthetic throughout."],
    }


def _literal(text):
    encoded = text.encode("cp1252")
    return encoded.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)")


def make_pdf(pages=None, *, encrypted=False, blank_page_count=None):
    """Produce actual PDF bytes using only the same pinned pypdf dependency.

    Helvetica is a standard PDF font. WinAnsiEncoding supplies a real accented
    character so tests can distinguish transcript character offsets from UTF-8
    byte offsets. No font download, OCR, reportlab or runtime clock is used.
    """
    if pypdf.__version__ != PARSER_VERSION:
        raise ValueError("Install the exact pypdf version declared by the package")
    writer = pypdf.PdfWriter()
    writer.add_metadata({
        "/Title": "Synthetic annual-report evidence fixture",
        "/Author": "Synthetic fixture generator",
        "/Subject": "Fictional offline parser example; not an issuer filing",
        "/CreationDate": "D:20250303000000Z",
        "/ModDate": "D:20250303000000Z",
    })
    if blank_page_count is not None:
        for _ in range(blank_page_count):
            writer.add_blank_page(width=612, height=792)
    else:
        content = page_paragraphs() if pages is None else pages
        for number in sorted(content):
            page = writer.add_blank_page(width=612, height=792)
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
                NameObject("/Encoding"): NameObject("/WinAnsiEncoding"),
            })
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
            })
            commands = [b"BT", b"/F1 11 Tf", b"16 TL", b"54 738 Td"]
            for index, paragraph in enumerate(content[number]):
                if index:
                    commands.append(b"T*")
                for line in textwrap.wrap(paragraph, width=78) or [""]:
                    commands.extend([b"(" + _literal(line) + b") Tj", b"T*"])
            commands.append(b"ET")
            stream = DecodedStreamObject()
            stream.set_data(b"\n".join(commands))
            # This PDF-object primitive is fixed by the declared pypdf pin.
            page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("synthetic-fixture-only", use_128bit=True)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


@contextmanager
def fixture_directory(path):
    """Resolve portable basename bindings inside their fixture directory."""
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def relative_binding(directory, name):
    binding = bind(Path(directory) / name)
    binding["path"] = name
    return binding


def write_fixture(directory):
    """Write once into an existing empty directory; return a portable proof."""
    directory = Path(directory).absolute()
    if directory.is_symlink() or directory.resolve() != directory or not directory.is_dir():
        raise ValueError("Fixture directory must be a real local directory")
    if any(directory.iterdir()):
        raise FileExistsError("Fixture directory must be empty; existing files are preserved")
    metadata = {
        "fixture_only": True, "cik": int(CIK), "name": ISSUER,
        "filings": {"recent": {
            "accessionNumber": [ACCESSION], "filingDate": [FILING_DATE],
            "reportDate": [PERIOD_END], "acceptanceDateTime": [ACCEPTANCE_TIME],
            "form": ["10-K"], "primaryDocument": ["synthetic_annual_report.htm"],
        }, "files": []},
    }
    header = (
        "<SEC-HEADER>\n"
        f"<ACCESSION-NUMBER>{ACCESSION}\n<TYPE>10-K\n<PERIOD>20241231\n"
        "<FILING-DATE>20250303\n<ACCEPTANCE-DATETIME>20250303090000\n"
        f"<FILER>\n<COMPANY-DATA>\n<CONFORMED-NAME>{ISSUER}\n<CIK>{CIK}\n"
        f"<IRS-NUMBER>{EIN.replace('-', '')}\n</COMPANY-DATA>\n"
        f"<FILING-VALUES>\n<FILE-NUMBER>{FILE_NUMBER}\n</FILING-VALUES>\n"
        "</FILER>\n</SEC-HEADER>\n"
    ).encode("utf-8")
    originals = {"pdf": make_pdf(), "submissions": json_bytes(metadata), "header": header}
    bindings = {}
    for role, raw in originals.items():
        with (directory / FILENAMES[role]).open("xb") as handle:
            handle.write(raw)
        bindings[role] = relative_binding(directory, FILENAMES[role])
    receipt = {
        "fixture_only": True, "retrieved_at": "2025-03-03T15:00:00+00:00",
        "sha256": bindings["pdf"]["sha256"], "path": bindings["pdf"]["path"],
        "bytes": bindings["pdf"]["bytes"], "final_url": SOURCE_URL,
    }
    with (directory / FILENAMES["retrieval_receipt"]).open("xb") as handle:
        handle.write(json_bytes(receipt))
    bindings["retrieval_receipt"] = relative_binding(directory, FILENAMES["retrieval_receipt"])
    proof = {
        "schema_version": PROOF_SCHEMA_VERSION, "parser_version": PARSER_VERSION,
        "symbol": SYMBOL, "reporting_period_end": PERIOD_END, "form_type": "10-K",
        "source_url": SOURCE_URL, "source_origin": "SYNTHETIC", "bindings": bindings,
        "cik": CIK, "metadata_url": METADATA_URL, "accession_number": ACCESSION,
        "sections": deepcopy(SECTIONS), "cover_page": 1, "period_proof_page": 2,
        "issuer_name": ISSUER, "ein": EIN, "sec_file_number": FILE_NUMBER,
    }
    with (directory / "proof.json").open("xb") as handle:
        handle.write(json_bytes(proof))
    return proof
