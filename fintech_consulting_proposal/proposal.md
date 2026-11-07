# Fintech Consulting Proposal

**Agentic AI Classifier Based on SEC Filings**  
**Art Ponomarev, PhD**  
**Proposed pilot - 7 November 2026**

## Executive proposal

I propose to build an agentic AI system that turns SEC filings into consistent, evidence-linked classifications of public companies. The system would identify a company's disclosed business activities and thematic exposures, explain why each label applies, and give an analyst the exact filing passages needed to review the result.

The intended users are investment-research, fintech, and financial-data teams that need searchable company universes, comparable business profiles, and updates when disclosures change. The practical output is a maintained classification dataset and an analyst review workflow.

The initial scope proposed here is U.S. domestic operating companies, using 10-K, 10-Q, and relevant 8-K filings and amendments. The issuer universe, taxonomy, historical coverage, and acceptance thresholds would be agreed at kickoff. This document describes a proposed implementation and evaluation plan; it does not report an already deployed product or measured investment performance.

## 1. What the classifier would classify

The unit of analysis is **a company, a classification label, and an as-of date**. A company can receive several labels, organized under a versioned hierarchy of industries, business activities, and themes.

For each label, the taxonomy would define its meaning, inclusion and exclusion rules, examples, and required evidence. An initial taxonomy might cover activities such as payment processing, enterprise software, or semiconductor manufacturing, with separate themes such as AI infrastructure. These are illustrative categories for scoping.

The classifier would distinguish:

- **Commercial participation:** the company develops, manufactures, or sells the relevant product or service.
- **Operational use:** the company uses a technology in its own operations.
- **Business relationships:** the disclosure concerns a customer, supplier, partner, or subsidiary, with that relationship recorded.
- **Plans and uncertainty:** the company describes an aspiration, investment plan, hypothetical risk, or discontinued activity.

A keyword in a risk factor would not by itself establish an active business line. Missing disclosure would produce an evidence gap rather than a claim that an activity is absent. Revenue exposure would be recorded only when the filing provides a defensible quantity and reporting context; otherwise it would remain unquantified.

Existing SEC SIC metadata could serve as an industry reference and comparison feature. It would remain distinct from the proposed thematic taxonomy. [5]

## 2. SEC evidence and data preparation

The evidence base would use annual 10-K filings for business context, quarterly 10-Q filings for updates, and selected 8-K filings for relevant developments. Original filings and amendments would remain separate, traceable versions. The SEC describes these form roles and identifies amendments with the /A suffix. [1]

The ingestion service would discover filings through EDGAR submissions metadata and retrieve the underlying narrative documents. SEC data APIs provide filing history and extracted XBRL facts; those facts do not replace the narrative text needed to assess products, business models, or thematic participation. [2]

Preparation would include:

- Resolve issuer identity using CIK and verified company metadata; treat tickers as dated attributes.
- Preserve source documents, URLs, accession numbers, form types, content hashes, and retrieval records.
- Parse headings, text, and tables; retain section and passage locations so evidence can be checked against the original.
- Retrieve relevant business descriptions, management discussion, financial disclosures, risk factors, and referenced documents.
- Flag missing sections, parsing failures, incorporated material, and insufficient document coverage.
- Process new filings and amendments incrementally, retaining earlier classifications and their evidence.

The service would use an identifying User-Agent, caching, retries with backoff, and conservative aggregate throttling under SEC fair-access guidance. The SEC currently publishes a maximum rate of 10 requests per second; the implementation would use a configurable lower operating limit and recheck the current policy before deployment. [3]

### Dates and historical availability

Report-period end, filing date, acceptance time, and retrieval time would be stored separately. The SEC states that its acceptance timestamp is not a timestamp of first public availability on sec.gov. [4]

A historical evaluation would therefore document its availability rule and uncertainty. Prospective processing would log the first successful retrieval. Later amendments would never be silently inserted into an earlier as-of result.

## 3. Agentic workflow

A bounded coordinator would choose the next permitted evidence-gathering or review step based on what is missing. Deterministic code would handle identifiers, parsing, schemas, and persistence; model calls would handle interpretation and proposed labels.

| Component | Responsibility |
|---|---|
| Filing discovery | Select eligible filings for the company and as-of date, and report coverage gaps. |
| Evidence retrieval | Locate relevant passages and tables; seek additional sections when the initial evidence is incomplete. |
| Classification | Apply the approved taxonomy and propose labels, participation types, explanations, and evidence references. |
| Verification | Check that quoted passages exist and support the proposed company, activity, relationship, and period; identify contradictions. |
| Adjudication | Request another bounded retrieval step, mark insufficient evidence, or route an ambiguous case to an analyst. |
| Publication | Validate the output schema and release results under the agreed review policy, with source and execution versions attached. |

Each run would have limits on tool calls, retries, time, and cost. Filing text would be treated as source data, never as instructions to the agents. Tools would be restricted to approved retrieval and processing operations.

A second model's agreement would not be treated as proof. The verifier would combine deterministic citation checks with evidence review, and unresolved cases would remain visible to a human reviewer.

### Reviewable classification output

Each result would include the issuer CIK and name; as-of date; taxonomy label and version; participation type; decision status; explanation; supporting and conflicting passages; filing URL, accession number, and document locator; source hash; model and prompt versions; and review history.

The main decision states would be **supported**, **needs review**, and **insufficient evidence**. A score would be labeled a calibrated probability only after calibration against reviewed examples; otherwise it would be presented as a model score or review-priority indicator.

Deliverables would include structured JSON/CSV output and a simple review interface that places the proposed label beside its source evidence. Analysts could accept, correct, or reject a result with a recorded reason. Disagreement would become input for taxonomy refinement and evaluation.

## 4. Evaluation and acceptance

The pilot would establish a reviewed reference set before evaluating the final system. Analysts would label representative companies and passages using written instructions, with adjudication of disagreements. Difficult cases would include generic marketing language, negation, planned products, subsidiary relationships, stale descriptions, and conflicting filings.

Comparisons would include a simple keyword or retrieval baseline and a single-pass model workflow. The agentic design would need to demonstrate useful gains in evidence quality, coverage, or review efficiency relative to its additional cost and complexity.

Evaluation would use issuer-separated and later-period test sets, keeping related filings and amendments together where needed to avoid leakage. Model and prompt versions, corpus snapshots, and taxonomy versions would be frozen for each reported run. Historical source restrictions alone cannot establish what a pretrained model learned before the experiment; that limitation would be stated.

Taxonomy, prompts, retrieval settings, and release thresholds would be tuned only on a development set. A separate, locked final holdout would be evaluated after those choices are frozen. Results would state how abstentions are scored and report both performance across the full evaluated set and precision and coverage for automatically released labels.

| Evaluation area | What would be measured |
|---|---|
| Classification quality | Per-label precision and recall, macro/micro F1, and consistency within the taxonomy hierarchy. |
| Evidence quality | Citation validity, passage support for the stated claim, correct entity and period, and unsupported-label rate. |
| Coverage and review | Classification coverage, abstention, analyst disagreement, correction rate, and review time. |
| Operational behavior | Cost and latency per company, retrieval/parser failures, repeat-run stability, and behavior after a new filing. |

Acceptance thresholds would be agreed before the final evaluation, including the required precision for automatically released labels and the permitted review workload. The handover would include failures and unresolved coverage gaps as well as aggregate results.

The classifier is a research-data product. Any use in security selection, portfolio construction, or trading would require a separate investment evaluation.

## 5. Pilot delivery and working arrangements

The following is an illustrative six-week sequence, subject to taxonomy complexity, issuer coverage, document quality, and analyst availability.

| Phase | Work and reviewable outputs |
|---|---|
| Week 1: define | Agree on the user workflow, issuer universe, taxonomy, evidence rules, review process, and evaluation plan. |
| Weeks 2-3: implement | Deliver the filing inventory, versioned ingestion/parser pipeline, classification workflow, output schema, and first review interface. |
| Weeks 4-5: evaluate | Complete reviewed examples, compare baselines and refine the workflow on development cases, then run the locked final evaluation and measure cost and review effort. |
| Week 6: hand over | Demonstrate the agreed workflow and deliver code, tests, configurations, evaluation report, operating instructions, and a prioritized next-stage backlog. |

I would provide the Python/SQL engineering, retrieval and agent orchestration, structured-output validation, evaluation tooling, and technical documentation. The client's contribution would be domain definitions, an accountable reviewer, representative research questions, and decisions on hosting and model providers.

Fees, capacity, final milestones, and acceptance criteria would be agreed in a written scope. The implementation would fit the client's approved environment and keep taxonomy, data preparation, and model choices separately versioned so they can evolve.

### Start with one classification question

Choose a company universe and one classification question that is currently expensive to answer consistently. The first milestone is an agreed definition of a correct, evidence-supported label and a small reviewed set on which to test it.

**Contact:** [art.ponomarev.ai@gmail.com](mailto:art.ponomarev.ai@gmail.com) - 650-863-2555 - [LinkedIn](https://www.linkedin.com/in/art-ponomarev-ai/)

## SEC source references

These references describe the public data sources and their constraints. The classifier architecture, taxonomy, workflow, and pilot plan above are proposed project design decisions.

1. [SEC: Using EDGAR to Research Investments](https://www.sec.gov/search-filings/edgar-search-assistance/using-edgar-research-investments) - form types and amendments.
2. [SEC: EDGAR Application Programming Interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) - submissions metadata, XBRL facts, and bulk data.
3. [SEC: Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) - identifiers, archive access, and fair-access guidance.
4. [SEC: Webmaster Frequently Asked Questions](https://www.sec.gov/about/webmaster-frequently-asked-questions) - timestamps, availability, and metadata limitations.
5. [SEC: Standard Industrial Classification Code List](https://www.sec.gov/search-filings/standard-industrial-classification-sic-code-list) - SIC industry reference.

[Repository overview](../README.md)
