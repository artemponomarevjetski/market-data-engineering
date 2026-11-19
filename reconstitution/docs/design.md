# Design decisions and review guide

## Purpose and boundary

The public package isolates a PDF evidence adapter and the review contracts needed to explain its downstream use. The PDF adapter, metadata/header parsing, paragraph filtering, deterministic selection, canonical hashing, and eligibility rules were extracted from an existing Python implementation. The runnable synthetic fixture, packaging, and independent demonstrations were added for this public example.

The larger original workflow is not shipped here. This package does not collect online filings, invoke language models, connect to cloud storage, reproduce benchmark portfolios, or execute a production reconstitution process. Those capabilities are outside this example's code and claims.

## Preserve evidence before interpretation

A useful research paragraph needs more than its text. Its source, location, extraction method, and relevant date context should survive subsequent ranking and review.

The PDF adapter retains the hash of the original PDF and a hash of each extracted page. A passage identifier is derived from its source/location metadata. The quoted text is an exact slice of the page transcript, so a reviewer can replay the slice and detect a mismatch. Layout extraction remains pinned to pypdf 6.10.0; changing extractor versions requires rerunning the fixture and checking the resulting transcripts and offsets.

A paragraph can be reproducibly extracted and still be unsuitable evidence. Explicit section ranges restrict admissible roles to business, operating/financial discussion, and financial notes. The next page must contain the declared boundary heading. The adapter rejects excluded filing items within a selected section and filters career, personnel, risk-language, and replacement-character passages. These are conservative heuristics. Complex layouts and legitimate text that resembles an exclusion can require a reviewed section map or a different adapter.

Selection reserves representation across allowed roles and ranks remaining passages deterministically using the supplied terms. Ranking does not change the quotations or decide whether an issuer meets a thematic or financial rule.

## Correspondence is narrower than authentication

The proof combines four retained bindings: a PDF, its receipt, submissions metadata, and a filing header. Each binding stores its exact byte count and SHA-256. The verifier checks receipt consistency, accession uniqueness, issuer identity, report period, cover and body claims, and matching identifiers across the PDF and header.

These checks establish that the supplied records agree. The code does not independently retrieve authoritative sources. An HTTPS URL or a self-declared OFFICIAL_IR origin does not authenticate that origin. Accordingly, source_origin_verified remains false. The demo uses the SYNTHETIC declaration and reports that status explicitly.

The SEC accession identifies the corresponding retained metadata record. It is not proof that a PDF contains exactly the same bytes or text as a separate SEC filing body. The public output retains sec_body_byte_equivalence_verified=false.

## Dates belong to distinct checks

Three dates can answer different questions:

| Date or timestamp | Question |
|---|---|
| Reporting-period end | Which period does the report describe? |
| Evidence availability | When could the evidence have been used? |
| Review cutoff | At what time is the decision being reconstructed? |

The PDF verifier checks its reporting-period cutoff. It reports metadata availability without pretending that extraction itself establishes point-in-time eligibility.

The separate review layer checks timezone-aware availability and the bound review context. An unknown availability time stays unresolved. A future observation or late input fails the availability check; the overall eligibility assessment reports UNRESOLVED because a prerequisite is unusable. That is distinct from INELIGIBLE, which represents a completed mandatory rule failure after the prerequisites are established.

The synthetic demo makes these distinctions observable: an unconfirmed methodology, a confirmed one-rule fixture, a late input, and an input with unknown availability produce separate recorded outcomes.

## Fail with an explainable reason

The public extraction adds explicit validation for malformed proof fields and bounded page ranges before constructing range collections. Local reads are restricted to regular files and a byte limit; input bindings are verified before their contents are used. The extractor rejects encrypted PDFs, excessive page counts, and out-of-range requested pages.

These checks improve predictability for this local demonstration. They do not turn a general PDF parser into a security sandbox. A service processing arbitrary uploaded documents would also need execution time and memory limits, access isolation, and operational monitoring.

The adapter does not make a model call, infer a missing identifier, synthesize a replacement quote, or silently convert a missing review prerequisite into a pass. The error path is part of the intended behavior and is exercised by the tests.

## Public adaptation

The extraction keeps the original narrow algorithms and contracts while removing dependencies on unrelated orchestration modules. Public modules have neutral names and a versioned public proof schema. Demo documents, identifiers, and metadata are synthetic; original client documents, account details, cloud locations, and reviewer records are absent from this package.

The example demonstrates a reproducible engineering component and its explicit limits. Its deterministic fixture result is a regression target, not a measured result on a real portfolio or a claim of investment performance.
