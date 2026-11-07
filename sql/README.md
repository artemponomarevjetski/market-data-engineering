# SQL for Financial Market Data

SQL examples for exploring financial data directly in the database: security identifiers, provider mappings, historical prices, dividends, corporate actions, and security-master reconciliation. The collection demonstrates joins, date filters, adjustment factors, and calculations that can be performed without a Python wrapper.

This directory contains **40 SQL files**: one standalone corporate-action calculation example and 39 training queries and experiments. The examples primarily target **Microsoft SQL Server and T-SQL**, using provider-specific tables and views.

## Start here

| Entry point | What it contains |
|---|---|
| [sql_with_computation.sql](sql_with_computation.sql) | A corporate-action query that calculates hypothetical resulting shares, fractional shares, cash in lieu, and total cash. |
| [qad_training/](qad_training/) | The unpacked training collection: 39 SQL files with supporting reference data and query exports. |
| [Training guide and file index](qad_training/README.md) | Descriptions of the individual queries, reconciliation variants, and supporting exports. |

For the Python workflows and the rest of the project, see the [repository README](../README.md).

## Corporate-action calculations

[sql_with_computation.sql](sql_with_computation.sql) combines security-master records, quote identifiers, capital-event details, and closing prices. It starts with a hypothetical holding:

```sql
DECLARE @N_HYPOTH_SHARES INT = 100;
```

The query returns the ticker, company name, action description, event dates, old/new share quantities, offering-company name, cash amount, and additional security-master fields through `A.*`.

Its calculated outputs are:

| Column | Meaning in this example |
|---|---|
| `NumHypothShares` | The hypothetical starting holding, initially 100 shares. |
| `NumSharesFinal` | Whole resulting shares, using `FLOOR(N * NumNewShares / NumOldShares)` when old shares are nonzero. |
| `LeftOverShares` | The fractional remainder after calculating whole shares. |
| `CashInLieu` | The example's valuation of that fractional remainder using the share ratio, cash component, and joined closing price. |
| `CashFinal` | The cash component for the hypothetical holding plus cash in lieu in the nonzero-ratio case. |
| `Close` | The joined closing price, formatted for display. |

For nonzero old and new share quantities, the implemented arithmetic is:

```text
N = hypothetical starting shares
raw_shares = N * NumNewShares / NumOldShares
whole_shares = floor(raw_shares)
fractional_shares = raw_shares - whole_shares
cash_in_lieu = ((Close_ - CashAmt) / (NumNewShares / NumOldShares)) * fractional_shares
total_cash = N * CashAmt + cash_in_lieu
```

These formulas describe this script's assumptions. The zero-share branches behave differently: zero new shares with nonzero old shares produce zero cash in lieu and `N * CashAmt` total cash; zero old shares produce zero whole/fractional shares and cash in lieu, with `CashFinal` falling back to `CashAmt` alone. Review those cases, missing values, and numeric precision for the event types being analyzed.

## Database requirements and execution

Use a SQL Server-compatible SQL client connected to an existing provider database with access to the required objects. The standalone query references:

| Objects | Role in the query |
|---|---|
| `SecMSTRX`, `SecMapX` | Security-master records and provider mappings; the query filters for `TYPE_ = 1` and `VENTYPE = 33`. |
| `DS2CapEvent`, `DS2xRef` | Capital events and action descriptions. |
| `RDCSecMapX`, `RDCQuoteInfo`, `RDCRICData` | Security, quote, ticker, and RIC relationships. |
| `Ds2PrimqtPrc` | Closing-price records. |

Database credentials and the complete provider schema are not supplied. The [supporting CSVs](qad_training/README.md#supporting-data) are historical exports; they do not recreate the database. Standalone SQL uses the connection configured in your SQL client. The `MSSQL_*` environment variables documented elsewhere configure the Python examples.

To adapt the corporate-action example:

1. Open [sql_with_computation.sql](sql_with_computation.sql) and confirm that its tables, fields, and mapping conventions match your database.
2. Set `@N_HYPOTH_SHARES` and replace `xxx, yyy` in `a.seccode in (xxx, yyy)` with the security codes you intend to inspect.
3. Set the desired event-date and action-type filters. The supplied date and `MERG` filters are commented out.
4. Choose an explicit closing-price date rule. The existing price join uses `InfoCode` alone, and `Q.MarketDate = EffectiveDate` is commented out. Without a date restriction, several historical prices can join to one event; `SELECT DISTINCT` does not choose the appropriate price.
5. Run the adapted query in your client and inspect the result before exporting it.

### Interpreting the result

`CashInLieu`, `CashFinal`, and `Close` are converted to text and given a literal `$` suffix. This formatting does not validate or convert currencies. Keep numeric values separately if you need further calculations.

Dates are also formatted as text. The existing `ORDER BY EffectiveDate` uses the formatted alias, so it does not guarantee chronological order. Use the underlying date value for chronological sorting when adapting the query, accounting for the `SELECT DISTINCT` projection.

## Explore the training collection

The [complete training index](qad_training/README.md) covers all 39 SQL files and the supporting datasets. Useful starting points include:

| Topic | Examples |
|---|---|
| Security identifiers and provider mappings | [Security master](qad_training/1_New_SecurityMaster.sql), [mapping](qad_training/2_New_Mapping.sql), and [issuer-to-security relationships](qad_training/8_ISR_Issues_for_an_Issuer.sql). |
| Historical identifier changes | [CUSIP/SEDOL changes](qad_training/3_CusipSedol_Changes.sql) and [Datastream identifier history](qad_training/4_DS2_CusipSedol_Changes.sql). |
| Prices, adjustments, and currency conversion | [Pricing examples](qad_training/5_DS2_Pricing.sql). |
| Dividends and corporate actions | [Dividends](qad_training/6_DS2_Dividends.sql) and [capital events](qad_training/7_DS2_CapitalEvents.sql). |
| Combining datasets and inspecting changes | [Cross-provider joins](qad_training/9_Combining_Data_Sources.sql) and [update/change-log queries](qad_training/10_Update_Tables.sql). |
| Security-master reconciliation | [EmulationMasterTable.sql](qad_training/EmulationMasterTable.sql) and its numbered variants 1 through 24. |
| Provider views and fundamentals | [Datastream and Worldscope view examples](qad_training/Extra_DS2_and_WS_sample_queries_using_Views.sql). |

The numbered reconciliation variants are independent working versions, rather than a sequence of database migrations. `10_Update_Tables.sql` reads update logs and change tables. The smaller `SQLQuery_*.sql` files contain exploratory fragments; for example, `SQLQuery_v2.sql` includes `SELECT VERSION()`, which requires adjustment for SQL Server.

## Relationship to the Python examples

The [corporate-event extractor](../containerized_corporate_events/corporate_events.py) uses related calculations inside a Python workflow that connects through ODBC and writes dated CSV output. Its active date filters and price-date predicate differ from the standalone SQL file, so the two implementations can return different results.

These are historical reference implementations. The documentation reflects inspection of the committed source files; live database execution and compatibility with a particular provider schema require separate validation.
