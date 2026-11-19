# Python SEC Filing Parsing

**Form 10-K and Form 20-F metadata/header parsing · Form 10-K PDF evidence extraction**

Python tools for parsing locally retained SEC submissions JSON and original filing headers for **Forms 10-K and 20-F**, with a runnable **Form 10-K PDF evidence workflow** for index-reconstitution research. The package preserves filing identity, reporting periods, acceptance-time corroboration, source hashes, and exact quotation locations in extracted page text.

The PDF workflow verifies retained file hashes and filing correspondence, extracts page-level quotations, and keeps evidence availability and methodology eligibility as separate decisions.

This is a focused public adaptation of engineering work by **Artem (Art) Ponomarev**, with a new synthetic example and isolated tests. The included example uses fictitious company identifiers and generated documents. It demonstrates an evidence-processing component; it does not reconstruct an actual fund or produce investment recommendations.

## Supported SEC documents

| Capability | Form 10-K | Form 20-F |
|---|---|---|
| Parse retained SEC submissions JSON | Supported | Supported |
| Parse and corroborate an original SEC filing header | Supported | Supported |
| Check acceptance-time consistency and historical availability | Supported | Supported |
| Verify PDF cover, filing identity, reporting period, section boundaries, and exact evidence locations | Supported by the focused PDF adapter | Not implemented; the verifier rejects this form |
| Complete synthetic PDF demo and checked-in example result | Included | Not included |

The metadata and header parsers are in [filings.py](src/index_reconstitution/filings.py). The form-specific PDF verifier is in [pdf.py](src/index_reconstitution/pdf.py). Generic PDF text extraction alone does not validate a Form 20-F document's structure or correspondence.

Inputs are retained local documents. This package does not download EDGAR filings or parse SEC HTML/Inline XBRL filing bodies. For the official form names and context, see the SEC's [Form 10-K guide](https://www.sec.gov/search-filings/edgar-search-assistance/using-edgar-research-investments) and [Form 20-F](https://www.sec.gov/about/forms/form20-f.pdf).

## Review the example

- Read the [generated example result](examples/expected_result.json) directly on GitHub.
- Follow the [end-to-end demo](examples/run_pdf_demo.py).
- Inspect the [PDF verifier](src/index_reconstitution/pdf.py) and the [eligibility contracts](src/index_reconstitution/review.py).
- Read the [design decisions and limits](docs/design.md), then explore the [tests](tests/).

## Quick start

Requires **Python 3.11 or later**. The extractor is pinned to **pypdf 6.10.0** because page layout and character offsets depend on the extractor version. Windows installations also install the declared time-zone data dependency.

From this directory in a downloaded or checked-out copy of the repository:

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -e .
    python examples/run_pdf_demo.py --output-dir demo-output
    python -m unittest discover -s tests -v

On Windows, activate the environment with the appropriate script under .venv/Scripts. Running locally is optional; the source and example result are browsable on GitHub.

After dependency installation, the demo uses local files and requires no API key, model service, database, or network request. Choose a new output directory for each run: the demo refuses to overwrite an existing directory.

## What the demo does

It generates a seven-page PDF, corresponding synthetic submissions metadata and a filing header, a receipt, and a proof manifest. It then runs the actual pinned PDF extractor and verifier.

| Stage | What is checked | Result |
|---|---|---|
| Retained inputs | File path, byte count, SHA-256, and receipt consistency | A reproducible set of local inputs |
| Filing correspondence | Issuer identifiers, form, accession, reporting period, and cover/body claims | A PDF-to-metadata correspondence result |
| Section selection | Explicit page ranges, start/end headings, allowed section roles, and excluded items | Permitted business and financial sections |
| Evidence extraction | Exact paragraph text, page hashes, source hash, and character offsets | Quotations that can be replayed against the extracted page |
| Review | Evidence availability, methodology version, mandatory rule checks, and review prerequisites | ELIGIBLE, INELIGIBLE, or UNRESOLVED |

The output directory contains:

| File | Purpose |
|---|---|
| synthetic_annual_report.pdf | Generated, text-based PDF used by the real extractor |
| synthetic_submissions.json and synthetic_header.sgml | Fictitious filing metadata and header |
| synthetic_receipt.json and proof.json | Retained-input bindings and declared correspondence |
| page_texts.json | Extracted page text for replaying quotation offsets |
| result.json | Source-validation summary, evidence, replay checks, provenance, and separate review outcomes |

The portable [example result](examples/expected_result.json) contains no machine-specific absolute paths. The locally generated proof and receipt refer to files in the chosen output directory.

The checked-in run contains three evidence records, one for each permitted section role. For the business quotation on page 2, `page_texts["2"][127:414]` reproduces the recorded quote exactly. The fixture includes an accented character before this passage so the tests can distinguish character offsets from UTF-8 byte offsets.

The package was installed in a fresh Python 3.12 environment with pypdf 6.10.0. All 20 tests passed, and the actual demo result matched the checked-in result. The suite exercises real PDF parsing, input tampering, encrypted and blank PDFs, date conflicts, unresolved reviews, reproducibility, and output preservation.

### Separate review outcomes

The same synthetic evidence is evaluated under four explicit scenarios:

| Scenario | Expected outcome | Reason |
|---|---|---|
| Unconfirmed methodology | UNRESOLVED | A document alone cannot establish confirmed review rules |
| Confirmed synthetic rule | ELIGIBLE | The deliberately limited fixture satisfies its declared mandatory rule |
| Late evidence availability | UNRESOLVED | Evidence was not available by the specified review cutoff |
| Unknown evidence availability | UNRESOLVED | Publication timing cannot be assumed |

ELIGIBLE in the second scenario refers only to that synthetic rule set. It does not establish index membership, selection, weights, returns, or compliance with a real provider's methodology.

## Evidence contract

Each quotation records a source PDF hash, page number, page-text hash, extractor version, section role, and start/end character positions. The central replay invariant is:

    page_text[quote["source_start"]:quote["source_end"]] == quote["quote"]

Offsets refer to Python string positions in the pinned extractor's page transcript. They are not PDF byte offsets, screen coordinates, or offsets in an SEC HTML document.

Two output fields state the boundary explicitly:

    "sec_body_byte_equivalence_verified": false
    "source_origin_verified": false

Local hashes and receipts establish consistency with retained inputs. They do not independently authenticate an issuer's website or prove that a PDF is byte-identical to a separately hosted filing.

The PDF result also reports:

    "point_in_time_eligibility": "NOT_EVALUATED"

Reporting-period bounds are checked by the PDF verifier. Historical availability and methodology checks happen separately in the review layer, which the demo exercises explicitly.

## Code map

| Module | Responsibility |
|---|---|
| [pdf.py](src/index_reconstitution/pdf.py) | Pinned extraction, bounded section validation, evidence records, and proof verification |
| [bindings.py](src/index_reconstitution/bindings.py) | Local file bindings, hashes, and deterministic JSON |
| [filings.py](src/index_reconstitution/filings.py) | Parsing retained SEC submissions metadata and original filing headers, including Forms 10-K and 20-F |
| [review.py](src/index_reconstitution/review.py) | Typed identity, provenance, methodology, availability, and eligibility contracts |
| [_passages.py](src/index_reconstitution/_passages.py) | Personnel-heading and career-paragraph exclusions |
| [_selection.py](src/index_reconstitution/_selection.py) | Deterministic reviewer ranking with representation across permitted section roles |
| [_validation.py](src/index_reconstitution/_validation.py) | Shared validation and canonical serialization |

For a minimal extraction call:

    from index_reconstitution import page_texts

    with open("annual_report.pdf", "rb") as source:
        pages = page_texts(source.read(), {1, 2})

Use the complete demo for proof construction, correspondence checks, quote replay, and eligibility review.

## Scope and limitations

- Supports Form 10-K and Form 20-F submissions metadata/header parsing. The reviewed PDF correspondence path and explicit section maps are Form 10-K only; a Form 20-F PDF adapter is not included.
- Does not automatically discover filings, infer a section map, or parse SEC HTML/Inline XBRL filing bodies.
- Uses a text layer, with no OCR, table reconstruction, or invented text.
- Applies deterministic paragraph filters and term-based reviewer ranking. These are inspectable heuristics, not a learned thematic classifier.
- Rejects encrypted PDFs, invalid page selections, inconsistent bindings, and inadmissible section boundaries. File and page limits are input bounds, not an execution sandbox for hostile documents.
- Preserves missing or contradictory evidence as a failure or unresolved condition. It does not repair identity or fill missing facts with a model.

See [design.md](docs/design.md) for adaptation details, trust boundaries, and engineering tradeoffs. The extractor's own [text-extraction documentation](https://pypdf.readthedocs.io/en/6.10.0/user/extract-text.html) explains why PDF layout and text recovery require care.
