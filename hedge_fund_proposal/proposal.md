# Financial AI & Quantitative Engineering Consulting

**Art Ponomarev, PhD**  
**For hedge funds, investment firms, and fintech teams**  
**Fully remote - San Francisco Bay Area, USA**  
**Proposal for discussion - 7 November 2026**

## From investment research to reliable systems

I help investment and financial technology teams improve the data, evaluation, and engineering behind their research workflows. My work connects Python and SQL pipelines, quantitative analysis, model validation, and practical AI applications.

An engagement starts with a specific business problem: reconciling inconsistent vendor data, making a research result reproducible, evaluating a model before deployment, or reducing manual work in a document-heavy process. The objective is a useful engineering result that your team can inspect, measure, and maintain.

My background combines hedge-fund data science at FORA Capital, quantitative consulting for Christina Winch, investment-focused ML leadership with Ben Feder at Thesis Machine Learning, and production engineering and scientific computing at Microsoft, TetraMem, and NASA.

## Problems I can help solve

- **Research data requires too much manual reconciliation.** Security identifiers, effective dates, corporate actions, and provider mappings need consistent treatment before analysis can be trusted.
- **A promising result is difficult to reproduce or evaluate.** Data preparation, experiment settings, validation periods, and execution assumptions need to be made explicit.
- **An AI demonstration needs a credible path into daily work.** The team needs representative evaluations, source traceability, controlled tool access, and a clear review process.

The work can support an existing research or engineering team, resolve a bounded technical backlog, or establish the foundations for a larger implementation.

## Consulting services

### 1. Investment data and research infrastructure

Build or improve the path from licensed source data to a documented research dataset.

Work can include security-master reconciliation, vendor-identifier mapping, ticker histories, corporate-action handling, dated snapshot comparisons, and repeatable Python/SQL extraction. Where research depends on what was knowable at a particular time, the engagement examines effective dates, publication dates, revisions, and the availability of historical data.

**Typical deliverables**

- A source-to-output map showing inputs, transformations, dependencies, and ownership.
- Documented identifier, date, duplicate, missing-value, and adjustment rules.
- A reproducible pipeline or focused improvements to an existing workflow.
- Reconciliation reports and data-quality checks with an explicit exception process.
- Configuration, operating instructions, and handover notes.

**Outcome to assess:** whether the team can produce an agreed dataset consistently, explain discrepancies, and trace important fields back to their source.

### 2. Model validation and quantitative research evaluation

Examine whether an experiment's design supports the conclusions being drawn from it.

Work can cover time-aware validation, feature availability, leakage risks, benchmark selection, reproducibility, stability across periods, and sensitivity to assumptions. For trading-signal research, the review can examine the relationship between signal timing, execution timing, corporate-action treatment, costs, exposure, and reported results.

**Typical deliverables**

- An evaluation plan with a primary question, comparison baseline, and acceptance criteria.
- Reproducible experiments, notebooks, or evaluation pipelines.
- A review of data and modeling assumptions, with prioritized findings.
- Benchmark and sensitivity comparisons.
- A concise decision report describing what the evidence supports and what should be investigated next.

**Outcome to assess:** whether the team has a defensible basis to continue, revise, or stop a research direction, with enough documentation for another engineer or researcher to reproduce the assessment.

### 3. AI assistants and controlled agent workflows

Develop useful AI support for research, document review, and recurring reporting.

A pilot might focus on retrieving evidence from a defined document collection, answering questions with source references, preparing a structured research summary, or coordinating a bounded sequence of approved tools. The design starts with a representative workflow and a clear definition of a useful result.

**Typical deliverables**

- A workflow specification identifying users, inputs, outputs, and review steps.
- A working prototype integrated with selected documents or systems.
- An evaluation set and scoring rubric based on representative tasks.
- Source references, execution records, and review behavior when evidence is insufficient.
- Measurements of task quality, completion, latency, and operating cost.
- Deployment and monitoring recommendations appropriate to the pilot's maturity.

**Outcome to assess:** whether the workflow produces useful, traceable results under realistic conditions and fits the team's existing responsibilities and approval process.

## Engagement options

The following are illustrative planning ranges. Final scope and timing depend on access, data readiness, integration requirements, and the team's availability.

| Engagement | Suitable starting point | Indicative scope and outputs |
|---|---|---|
| **Focused assessment** | A recurring problem or an uncertain research result needs diagnosis. | Approximately **1-2 weeks**: review one workflow, establish a baseline, identify the main issues, and produce a prioritized implementation plan. |
| **Scoped pilot** | The team has a defined use case and wants a working result. | Approximately **3-6 weeks**: build or improve one workflow, evaluate it against agreed criteria, and deliver code, documentation, and a handover. |
| **Fractional technical support** | A team needs continuing help across research and engineering. | An agreed recurring allocation for implementation, technical review, evaluation, and delivery planning, with a maintained backlog and regular demonstrations. |

Each engagement should identify an accountable client contact, a bounded set of deliverables, and the decision the work is intended to support.

## Delivery milestones

1. **Define the question.** Agree on the users, current workflow, business problem, available evidence, and boundaries of the engagement.
2. **Establish the baseline.** Inspect representative inputs and outputs, document assumptions, and select the measures that matter.
3. **Implement and review.** Deliver work in small, reviewable increments, with regular demonstrations and a visible record of decisions and unresolved issues.
4. **Evaluate.** Run the agreed checks and comparisons, investigate failures, and document the practical limits of the result.
5. **Hand over.** Deliver the code and findings with instructions for reproducing, operating, and extending the work.

Acceptance criteria are agreed at kickoff and recorded before the final evaluation. Depending on the scope, they may include:

| Area | Examples of acceptance criteria |
|---|---|
| Data workflow | Agreed schema and field coverage; documented reconciliation tolerances; repeatable output from a fixed input snapshot; visible handling of expected exceptions. |
| Model evaluation | Reproducible runs; defined validation periods; documented benchmarks and assumptions; findings tied to supporting evidence. |
| AI workflow | Agreed scoring on representative tasks; accurate source references; appropriate review behavior; acceptable latency and cost for the intended use. |
| Handover | Another team member can follow the operating instructions, reproduce the agreed checks, and identify the owner of each remaining dependency. |

## Relevant experience

**FORA Capital - Senior Data Scientist / Team Lead.** Integrated Refinitiv and Revere data, Python/SQL tools, and cloud-synchronized databases for backtesting and corporate-event arbitrage. Containerized workflows and collaborated with data scientists, DevOps, and brokers.

**Winch Advisory Services - Quantitative consulting, Appleton, Wisconsin, 2010.** Supported Christina Winch's Monday investment strategy and U.S. ETF risk/timing research. The linked [consulting study](../MondayFund/README.md) presents the historical context and a clearly labeled reconstruction prepared in 2026.

**Thesis Machine Learning - Head of Machine Learning, full-time, 2026.** Worked with Ben Feder on investment-focused ML, with responsibilities centered on model validation, technical leadership, and production readiness. Subsequent work included technical white-paper review and discussions about follow-on consulting.

**Microsoft - TetraMem - NASA.** Experience in ML lifecycle automation, evaluation, monitoring, release controls, Monte Carlo simulation, and scientific risk modeling. PhD in Applied Physics from Columbia University.

## Public engineering examples

These repository materials provide concrete examples of the kinds of data and engineering problems I have worked with:

- **[Provider ETL and security-master reconciliation](../python-sql-data-external-data-providers/etl_code_python_sql.py):** Python/SQL extraction, identifier mappings, ticker histories, and research-data preparation.
- **[Corporate-action extraction and snapshot comparison](../containerized_corporate_events/README.md):** event-data processing, dated outputs, and comparisons across snapshots.
- **[SQL training and supporting datasets](../sql/qad_training/README.md):** provider-table queries, financial identifiers, and security-master experiments.
- **[Schwab ETF and MACD research reconstruction](../MondayFund/README.md):** explicit research assumptions, synthetic illustrations, and evaluation methodology.

The repository documents historical implementations and their operating assumptions. A client engagement begins by evaluating the requirements of the client's own environment.

## Working arrangements and client inputs

Engagements are fully remote, with agreed working sessions, progress updates, and review points. I work within the client's established repositories and engineering practices where appropriate.

Useful starting inputs include a description of the workflow, representative data or documents, sample outputs, known problems, and access to the people responsible for the system. Licensed datasets, account access, and necessary internal approvals are arranged by the client. A pilot can begin with an approved sample when broader access would take longer.

The technical approach is selected to fit the existing environment. Core tools include Python, SQL, pandas/NumPy, PyTorch, TensorFlow, MLflow, Azure/AWS, Docker/Kubernetes, CI/CD, and retrieval and agent evaluation.

Fees, capacity, milestones, and acceptance criteria are agreed in a written scope before work begins. The engagement should also establish ownership of deliverables, confidentiality requirements, and the process for handling scope changes.

## Start with one workflow

Bring one research, data, or AI workflow that needs improvement. A scoping discussion can establish the current bottleneck, the available inputs, and the smallest useful first engagement.

**Contact:** [art.ponomarev.ai@gmail.com](mailto:art.ponomarev.ai@gmail.com) - 650-863-2555 - [LinkedIn](https://www.linkedin.com/in/art-ponomarev-ai/)

[Repository overview](../README.md)
