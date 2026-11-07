# SQL training examples and supporting data

This directory contains the unpacked QAD training material: **39 SQL files and eight supporting data files**. The examples explore provider security identifiers, historical mappings, price series, corporate actions, and security-master reconciliation.

## Browse the queries

| Files | Purpose |
|---|---|
| [1_New_SecurityMaster.sql](1_New_SecurityMaster.sql) and [2_New_Mapping.sql](2_New_Mapping.sql) | Security-master identifiers and mappings to provider datasets. |
| [3_CusipSedol_Changes.sql](3_CusipSedol_Changes.sql) and [4_DS2_CusipSedol_Changes.sql](4_DS2_CusipSedol_Changes.sql) | Historical CUSIP and SEDOL identifier changes. |
| [5_DS2_Pricing.sql](5_DS2_Pricing.sql) | Price series, adjustment conventions, and currency conversion. |
| [6_DS2_Dividends.sql](6_DS2_Dividends.sql) and [7_DS2_CapitalEvents.sql](7_DS2_CapitalEvents.sql) | Dividends and capital events. |
| [8_ISR_Issues_for_an_Issuer.sql](8_ISR_Issues_for_an_Issuer.sql) | Relationships between issuers and their securities. |
| [9_Combining_Data_Sources.sql](9_Combining_Data_Sources.sql) | Combining provider datasets. |
| [10_Update_Tables.sql](10_Update_Tables.sql) | Reading update-log and change tables. |
| [EmulationMasterTable.sql](EmulationMasterTable.sql), plus numbered variants 1 through 24 | Successive security-master and ticker-reconciliation experiments. |
| [Extra_DS2_and_WS_sample_queries_using_Views.sql](Extra_DS2_and_WS_sample_queries_using_Views.sql) | Datastream and Worldscope provider views for prices, market capitalization, fundamentals, and foreign exchange. |
| [SQLQuery_v1.sql](SQLQuery_v1.sql), [SQLQuery_v2.sql](SQLQuery_v2.sql), and [SQLQuery_v3.sql](SQLQuery_v3.sql) | Smaller mapping, RIC, expression, and date-format experiments. |

The numbered master-table variants are independent working versions. They are retained for comparison and are not migrations that should be executed in order.

## Supporting data

| Files | Description |
|---|---|
| [master_file.csv](master_file.csv) | Security-master data; identical to the existing [python/master_file.csv](../../python/master_file.csv). |
| [master_file_sorted_by_ticker.csv](master_file_sorted_by_ticker.csv) | Complete master table from the former Numbers document: 65,534 records and six columns. |
| [master_file_sorted_by_ticker_links.csv](master_file_sorted_by_ticker_links.csv) | All 107 embedded hyperlinks from the Numbers document, with the original link text and URL targets. |
| [QA_Direct.csv](QA_Direct.csv) | Provider-query export. |
| [ric_history.csv](ric_history.csv) | RIC validity history for ten security IDs, with tickers, quote IDs, sequence numbers, and start/end dates and times: 247 records and 10 columns. Formerly `RICdata.csv`. |
| [citigroup_datastream_name_history.csv](citigroup_datastream_name_history.csv) | Citigroup example linking security and vendor identifiers to historical Datastream quote names (`TRAVELERS GP.` and `CITIGROUP`) and validity dates: two records and 10 columns. Formerly `RICdata_from_xlsx.csv`. |
| [datastream_quote_name_history.csv](datastream_quote_name_history.csv) | Datastream quote-name history for 22 `InfoCode` values: 79 records and four columns (`InfoCode`, `StartDate`, `EndDate`, `DSQtName`). Formerly `Results.csv`. |
| [security_master_ric_datastream_join.csv](security_master_ric_datastream_join.csv) | Joined detail across security-master records, provider mappings, RDC quotes/RIC history, and Datastream quote/name history: 852 records and 74 columns. Formerly `Results_from_xlsx.csv`. |

The Citigroup name-history and security-master join CSVs preserve the populated data from the two removed Excel workbooks; their date cells are represented as `yyyy-mm-dd` text. The RIC-history and Datastream quote-name-history CSVs contain separate original datasets. All four datasets retain their original headers, record order, repeated rows and column names, blanks, leading-zero identifiers, significant whitespace, and large integer values.

The Numbers document was removed after all 393,210 table cells matched `master_file_sorted_by_ticker.csv` and its hyperlinks were preserved separately. In the links CSV, `csv_row` is one based and includes the main CSV header; `column_number` is also one based. The 107 links use 34 distinct original URL targets.

When opening these CSVs in spreadsheet software, import identifier and ticker columns as text to preserve leading zeros and literal codes.

## Database requirements

Most examples expect an existing SQL Server provider database with the corresponding tables and views, including security-master/mapping objects and Datastream, Worldscope, and related provider datasets. Database access, credentials, and the full provider schema are not supplied here.

Open and review each example before running it in a suitably configured SQL client. The scripts contain historical filters and exploratory fragments; for example, `SQLQuery_v2.sql` includes `SELECT VERSION()`, which needs adjustment for SQL Server. `10_Update_Tables.sql` reads change-log tables; its title does not imply that it updates rows.

The SQL files use UTF-8 for browsing. `5_DS2_Pricing.sql` was converted from UTF-16 little-endian while preserving its decoded query text; the other files retain their original encoding and line endings.

## Publication notes

These files replace the former training ZIP so that the examples can be reviewed individually. Historical author fields in nine SQL maintenance comments use neutral contributor labels. The supporting data now consists of eight CSV files. Financial issuer names, ticker symbols, provider identifiers, data values, and vendor attribution remain because they are part of the examples.

The examples were inspected without connecting to a live database. Unpacking and metadata cleanup do not establish that every historical query runs unchanged against a current provider schema.
