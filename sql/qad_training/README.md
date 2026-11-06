# SQL training examples and supporting data

This directory contains the unpacked QAD training material: **39 SQL files and nine supporting data files**. The examples explore provider security identifiers, historical mappings, price series, corporate actions, and security-master reconciliation.

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
| [SQLQuery_1.sql](SQLQuery_1.sql), [SQLQuery_2.sql](SQLQuery_2.sql), and [SQLQuery_3.sql](SQLQuery_3.sql) | Smaller mapping, RIC, expression, and date-format experiments. |

The numbered master-table variants are independent working versions. They are retained for comparison and are not migrations that should be executed in order.

## Supporting data

| Files | Description |
|---|---|
| [master_file.csv](master_file.csv) | Security-master data; identical to the existing [Python/master_file.csv](../../Python/master_file.csv). |
| [master_file.csv.bz2](master_file.csv.bz2) | A bzip2-compressed copy of the same master CSV. |
| [master_file_sorted_by_ticker.numbers](master_file_sorted_by_ticker.numbers) | A retained Apple Numbers master-table document. |
| [QA_Direct.csv](QA_Direct.csv) | Provider-query export. |
| [RICdata.csv](RICdata.csv) and [RICdata.xlsx](RICdata.xlsx) | RIC-related supporting files in their original formats. |
| [Results.csv](Results.csv) and [Results.xlsx](Results.xlsx) | Retained query-result files. |
| [Untitled.csv](Untitled.csv) | A small exploratory data fragment. |

The compressed CSV is retained to preserve the original material. Both it and the expanded CSV are provided explicitly; their contents are duplicates.

## Database requirements

Most examples expect an existing SQL Server provider database with the corresponding tables and views, including security-master/mapping objects and Datastream, Worldscope, and related provider datasets. Database access, credentials, and the full provider schema are not supplied here.

Open and review each example before running it in a suitably configured SQL client. The scripts contain historical filters and exploratory fragments; for example, `SQLQuery_2.sql` includes `SELECT VERSION()`, which needs adjustment for SQL Server. `10_Update_Tables.sql` reads change-log tables; its title does not imply that it updates rows.

The SQL files use UTF-8 for browsing. `5_DS2_Pricing.sql` was converted from UTF-16 little-endian while preserving its decoded query text; the other files retain their original encoding and line endings.

## Publication notes

These files replace the former training ZIP so that the examples can be reviewed individually. Historical author fields in nine SQL maintenance comments use neutral contributor labels. The five CSV files, two Excel workbooks, Apple Numbers document, and compressed CSV are retained byte-for-byte after inspection. Financial issuer names, ticker symbols, provider identifiers, data values, and vendor attribution remain because they are part of the examples.

The examples were inspected without connecting to a live database. Unpacking and metadata cleanup do not establish that every historical query runs unchanged against a current provider schema.
