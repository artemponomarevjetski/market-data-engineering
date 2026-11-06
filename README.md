# Financial Market Data Engineering with Python, SQL, and Docker

**Security-master reconciliation · Historical-price ETL · Corporate actions · Dated CSV comparisons**

A collection of Python implementations, SQL Server queries, and Docker packaging examples for preparing and inspecting financial market data. The code covers provider-data extraction, security identifiers and ticker histories, price series, corporate-action calculations, comparisons of dated snapshots, and a browser-based market-operations alert monitor.

The implementation centers on **Python CSV processing, T-SQL, and SQL Server access through ODBC**. The repository brings together the original market-data, containerization, and standalone SQL projects in one place.

## Repository map

| Location | What it contains | Browse first |
|---|---|---|
| [Python/](Python/) | Dated ETL and corporate-event implementations, comparison variants, and supporting artifacts | [2020-02-03.py](Python/2020-02-03.py) |
| [python-sql-data-external-data-providers/](python-sql-data-external-data-providers/) | Provider ETL and a CTA Plan alert-monitoring example | [etl_code_python_sql.py](python-sql-data-external-data-providers/etl_code_python_sql.py) |
| [examples/containerized_corporate_events/](examples/containerized_corporate_events/) | Corporate-action extraction, snapshot comparison, and the original Docker recipe | [corporate_events.py](examples/containerized_corporate_events/corporate_events.py) |
| [sql/](sql/) | Corporate-action calculations performed directly in SQL Server | [sql_with_computation.sql](sql/sql_with_computation.sql) |
| [docs/](docs/) | Original README copies and the revisions used for consolidation | [Source provenance](docs/source-provenance.md) |

## What the code covers

### 1. Provider ETL and security-master reconciliation

The [provider ETL](python-sql-data-external-data-providers/etl_code_python_sql.py) and the dated implementations in [Python/](Python/) address the relationship between provider security codes, ticker symbols, and their validity periods.

The ETL includes:

- Building security-master and ticker-history records from provider SQL tables.
- Reconciling identifiers against local reference lists and manual ticker mappings.
- Extracting historical open, high, low, close, and volume data in batches.
- Computing daily-return fields and writing dated CSV outputs.
- Creating local ZIP archives and preparing email notifications in the historical workflow.

Outputs include `master_table.csv`, a merged reference table, `addendum_master_table.csv`, `missing_tickers.csv`, generated SQL files, and daily CSV files organized into year/month directories.

The price-export code includes an **unadjusted close** field; review its adjustment conventions and date filters before using the output for research. Data processing uses the Python `csv` module and Python collections.

### 2. Corporate-action extraction

[corporate_events.py](examples/containerized_corporate_events/corporate_events.py) joins provider security, mapping, capital-event, reference, quote, and price tables. It extracts company and ticker information, action descriptions, event dates, exchange terms, cash consideration, and a selected close price.

The query also calculates outcomes for a hypothetical holding of **100 shares**: resulting whole shares, fractional shares, cash in lieu, and total cash.

| Output | Location and meaning |
|---|---|
| `query_corporate_events.txt` | Generated SQL text in the selected working directory |
| `corporate_events_data_YYYY_MM_DD.csv` | Corporate-action results in that directory, named for the execution date |

The `--source-date` argument controls the lower bound on event effective dates. The CSV filename uses the execution date, so another run on the same day overwrites that day's file.

### 3. Comparison of dated CSV snapshots

[diff_between_timestamped_records.py](examples/containerized_corporate_events/diff_between_timestamped_records.py) reads snapshots whose filenames end in `_YYYY_MM_DD.csv` and compares their row contents across dates. It excludes the final close-price field from the comparison.

Its output is `corporate_events_timestamped_diff_YYYY_MM_DD.csv`, written to the **parent of the input directory**. Place the input snapshots directly in the selected directory. Related historical comparison implementations are retained in [Python/](Python/).

### 4. Computation inside SQL Server

[sql_with_computation.sql](sql/sql_with_computation.sql) demonstrates corporate-action arithmetic directly in T-SQL, independently of Python. It combines provider-table joins with calculations for resulting shares, leftover fractions, cash in lieu, and final cash for a hypothetical 100-share position.

Before execution in a SQL Server client, replace the `xxx, yyy` security-code placeholders and review the date and price filters. The standalone SQL and the Python extraction query retain **different active filters**; their results should be evaluated separately. Several cash fields are formatted as currency strings.

### 5. Docker packaging example

The [Dockerfile](examples/containerized_corporate_events/Dockerfile) records the original approach to packaging Python with SQL Server ODBC dependencies, including `msodbcsql17` and `unixodbc-dev`.

This is a **historical recipe that needs updating before use**. It uses `python:3.8-buster` and Debian 10 installation steps, refers to a `requirements.txt` that is absent from the repository, and defines no default application command. The [sample invocation notes](examples/containerized_corporate_events/sample-invocation.txt) also contain old local paths and references to an absent `test.py` entry point.

### 6. Browser-based operations monitoring

[scraping_web_page_with_heavy_java_script.py](python-sql-data-external-data-providers/scraping_web_page_with_heavy_java_script.py) is a separate example of monitoring the **CTA Plan alerts page**. It uses Selenium with Firefox to obtain browser-rendered content, lxml to inspect it, and email code to send alerts.

The script starts its browser and polling loop at module level. Review the browser APIs, recipients, configuration, and notification behavior before running or importing it.

## Getting started

Clone the consolidated repository:

    git clone https://github.com/artemponomarevjetski/market-data-engineering.git
    cd market-data-engineering

Start by inspecting a component and its arguments. These help commands exit before database access, snapshot processing, or output generation:

    python3 examples/containerized_corporate_events/corporate_events.py --help
    python3 examples/containerized_corporate_events/diff_between_timestamped_records.py --help

| Component | Arguments |
|---|---|
| Provider ETL | `--start-date`, `--working-directory`, `--nblocks`, `--email-notification`, `--top`, `--archive` |
| Corporate-action extractor | `-d` / `--working-directory`; `-s` / `--source-date` |
| Snapshot comparison | `-d` / `--working-directory` |

For the corporate-action extractor, use an explicit source date in `YYYY-MM-DD` form. A supplied working directory must already exist. Each component has its own inputs and execution assumptions.

### Dependencies and configuration

Use a dedicated Python 3 environment and configure the selected component. The repository has no shared dependency manifest or pinned environment.

| Component | Python dependencies | Other requirements |
|---|---|---|
| Provider ETL | `pyodbc`, `boltons`, `tqdm`, `yagmail` | SQL Server ODBC driver, provider schema, local mapping inputs |
| Corporate-action extraction | `pyodbc` | SQL Server ODBC driver and provider schema |
| Snapshot comparison | Python standard library | Compatible dated CSV inputs |
| CTA Plan monitoring | `selenium`, `lxml`, `yagmail` | Firefox, a compatible browser driver, and mail configuration |
| Standalone SQL | No Python dependency | A SQL Server client and the expected provider tables |

The Python database examples read connection settings from exported environment variables:

| Variable | Purpose |
|---|---|
| `MSSQL_SERVER` | Database server |
| `MSSQL_DATABASE` | Provider database |
| `MSSQL_USERNAME` | Database login |
| `MSSQL_PASSWORD` | Database password |

Python does not automatically load a `.env` file. Keep actual connection settings outside Git. Review the legacy `PORT=xxx` placeholder, ODBC-driver selection, and provider-specific table names before connecting; setting the four variables alone does not complete that setup.

### Reference files and completion emails

The dated ETL variants and provider ETL use these environment settings:

| Variable | Default / purpose |
|---|---|
| `MARKET_DATA_REFERENCE_FILENAME` | `master_file_reference.csv`; input CSV located beside the selected ETL script, copied into its working directory and reused there. |
| `MARKET_DATA_COMPARISON_FILENAME` | `master_table_merged.csv`; comparison output written in the working directory. |
| `MARKET_DATA_REPORT_RECIPIENTS` | Comma-separated recipient addresses; required only when the existing email-notification path executes. There is no default recipient. |

The two filenames must be nonempty basenames without directory components or null characters, and must differ even when compared without case. To retain an existing local input or output naming convention, set the corresponding variable privately to that filename before running the script. The reference file must exist beside the chosen script; the ETL checks this before its existing directory-clearing step. These checks do not make an arbitrary working directory safe: continue to use a dedicated disposable directory.

Report recipients are trimmed and empty comma-separated entries are ignored; an empty final list raises an error. Mail sender authentication and the existing notification conditions still need component-specific configuration. Recipient lookup stays inside that notification path. Published notification text and historical log paths use neutral project labels.

### Execution notes

- **Provider ETL:** the historical workflow recursively clears its supplied working directory. Use a dedicated disposable output directory. It also expects local files such as `master_file_reference.csv`, `ManualLookUpOfTickers.csv`, and `test.py` that are not supplied in the tracked repository.
- **Snapshot comparison:** the current implementation allocates 20,750,101 empty lists. Review or adapt that allocation before processing real data.
- **Alert monitor:** the polling loop can repeatedly email the same alert; configure and review notification behavior before use.

These are historical implementations and reference examples. Live database execution, current dependency compatibility, and Docker builds require component-specific validation.

## Historical implementations and supporting material

[Python/](Python/) preserves dated scripts from December 2019 through February 2020, corporate-event and comparison variants, and other working versions. Files named `test_corporate_events.py`, `test.py_bckp`, and `test.py_new` are historical scripts or working copies.

Supporting material includes the exchange-code workbook, QAD query-training archives, a master CSV, a log, and a historical ODBC library. Their original locations are retained alongside the code.

## Consolidation and original documentation

This repository combines:

| Original project | Current location |
|---|---|
| `python-sql-market-data` | `Python/` and `python-sql-data-external-data-providers/` |
| `containerization-via-dockerization` | `examples/containerized_corporate_events/` |
| `sql` | `sql/` |

The [source provenance](docs/source-provenance.md) records the exact original revisions. Copies of all three original READMEs are preserved in [docs/source-readmes/](docs/source-readmes/). This root README describes the inspected combined code; the preserved documents retain their original wording and historical setup instructions.

This public repository begins with an anonymized snapshot and an independent root commit. The original consolidated repository and its historical commits are retained separately. The three projects' original Git histories are not part of this public repository's commit ancestry. The preserved original READMEs document the earlier projects and may refer to their former locations.
