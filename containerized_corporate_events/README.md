# Corporate-Action Snapshots and CSV Comparison

Python examples for extracting corporate-action records from a provider database, calculating hypothetical share and cash outcomes, and comparing dated CSV snapshots. The directory also preserves a historical Docker packaging recipe.

The extractor produces corporate-action reports. Security-master reconciliation and the wider ETL workflow are documented in the [repository README](../README.md).

## Files

| File | Purpose |
|---|---|
| [corporate_events.py](corporate_events.py) | Query SQL Server through ODBC and write a dated corporate-action CSV. |
| [diff_between_timestamped_records.py](diff_between_timestamped_records.py) | Compare the contents of dated snapshots, excluding their final close-price column. |
| [Dockerfile](Dockerfile) | Historical Python/ODBC container recipe that requires adaptation. |
| [sample-invocation.md](sample-invocation.md) | Original command notes, including paths and entry points that do not apply to the current directory. |

## Requirements and database configuration

Use a Python 3 environment. Extraction requires `pyodbc`, an installed SQL Server ODBC driver, and access to the expected provider database. Comparison uses the Python standard library and requires no database connection. This repository has no pinned dependency manifest for these examples.

Install the Python dependency in your chosen environment:

```bash
python3 -m pip install pyodbc
```

Install the ODBC driver separately using Microsoft's instructions for [macOS](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/install-microsoft-odbc-driver-sql-server-macos) or [Linux](https://learn.microsoft.com/en-us/sql/connect/odbc/linux-mac/installing-the-microsoft-odbc-driver-for-sql-server). The provider schema and credentials are not supplied. Referenced objects include `SecMSTRX`, `SecMapX`, `DS2CapEvent`, `DS2xRef`, `RDCSecMapX`, `RDCQuoteInfo`, `RDCRICData`, and `Ds2PrimqtPrc`.

Supply these environment variables before extraction:

| Variable | Value to configure |
|---|---|
| `MSSQL_SERVER` | SQL Server host or instance |
| `MSSQL_DATABASE` | Provider database name |
| `MSSQL_USERNAME` | Database login |
| `MSSQL_PASSWORD` | Database password |

The script reads exported variables; it does not load a `.env` file. Keep credentials outside Git. Also review the connection string's `PORT=xxx` placeholder and driver selection: the code takes the first driver returned by `pyodbc.drivers()`, otherwise falling back to a legacy macOS ODBC 13 library path. Setting the four variables alone does not finish connection setup.

## Extract a snapshot

Commands below run from the repository root. Inspect the arguments first:

```bash
python3 containerized_corporate_events/corporate_events.py --help
python3 containerized_corporate_events/diff_between_timestamped_records.py --help
```

After configuring the connection, create an output directory and specify an explicit source date:

```bash
mkdir -p output/corporate-events/snapshots
python3 containerized_corporate_events/corporate_events.py \
  --working-directory output/corporate-events/snapshots \
  --source-date 2019-01-01
```

| Argument | Behavior |
|---|---|
| `-d`, `--working-directory` | Existing directory for generated SQL and CSV files. If omitted, the script creates and prints a temporary directory. |
| `-s`, `--source-date` | Lower bound on event effective dates. Supply `YYYY-MM-DD`; the current default is a full execution timestamp, and the date-validation helper is not connected to this argument. |

The query applies that lower bound, an upper-date expression based on `GETDATE()`, and `Q.MarketDate = EffectiveDate`. The example `MERG` action filter is commented out. Date expressions and mappings must match the provider schema.

| Output | Contents |
|---|---|
| `query_corporate_events.txt` | Generated query text in the working directory. |
| `corporate_events_data_YYYY_MM_DD.csv` | Results in that directory; the filename uses the execution date. |

Both files are opened for writing. Repeating extraction on the same day overwrites that day's CSV. Preserve earlier snapshots under their original dates for comparison.

### Calculations and result interpretation

The query uses a hypothetical holding of **100 shares**. For nonzero old shares, it computes whole shares as `FLOOR(100 * NumNewShares / NumOldShares)` and retains the fractional remainder. For nonzero old and new shares, cash in lieu is `((Close_ - CashAmt) / (NumNewShares / NumOldShares)) * fractional_shares`; total cash adds `100 * CashAmt`.

With nonzero old shares and zero new shares, total cash is `100 * CashAmt`. Zero old shares instead yield zero whole/fractional shares and cash in lieu, with total cash falling back to `CashAmt` alone. Review numeric types, missing values, currencies, and event conventions before interpreting these historical assumptions.

Cash-result fields and the closing price are formatted strings with a literal `$`; dates are also strings. Python sorts those date strings rather than parsed dates. The CSV heading `ActionTypeCode` contains the selected action description, and the last column's acquiring-company label should be checked against the actual price join by event `InfoCode`.

The query/fetch retry loop has no configured attempt limit or backoff. A persistent database error can therefore keep retrying.

## Compare dated snapshots

Before running the comparison, review its large allocation: it creates **20,750,101 empty lists** indexed by numeric dates, then scans that entire range.

Use a flat directory containing only compatible, nonempty snapshots with a header and the extractor's column order. Keep one file per date, a consistent filename prefix, and zero-padded `_YYYY_MM_DD.csv` suffixes. Use at least two dates. Although file discovery walks subdirectories, opening files uses only their basenames in the selected directory.

```bash
python3 containerized_corporate_events/diff_between_timestamped_records.py \
  --working-directory output/corporate-events/snapshots
```

The implementation removes the final column before comparing whole rows. For each newer snapshot, it reports a row when that row is absent from **at least one older snapshot**. Consequently, it can report a row already present in the immediately preceding snapshot; it does not directly report records that disappeared. It also attempts to skip rows effective on their snapshot date, but its string conversion does not pad single-digit months or days.

The report is `corporate_events_timestamped_diff_YYYY_MM_DD.csv` in the **parent of the input directory**. It contains a 16-column header and data rows, interspersed with shorter timestamp-section rows. Another run on the same day overwrites the report.

## Docker recipe status

The Dockerfile uses `python:3.8-buster`, Debian 10 package configuration, `msodbcsql17`, and `unixodbc-dev`. It copies the build context, attempts to install an absent `requirements.txt`, and defines `CMD []` without an application command. Update the base image, dependency installation, driver setup, and runtime command before attempting deployment.

The invocation notes also reference an absent `test.py` and historical local paths. Use the actual entry points above when adapting the example.

For related computations without Python, see the [SQL guide](../sql/README.md). Its standalone query has different active filters. This documentation reflects source inspection; live database execution and Docker builds require separate validation.
