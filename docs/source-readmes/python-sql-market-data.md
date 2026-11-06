# fintech_code_python_sql_market_data

Collection of Python wrappers for financial data cleaning, data wrangling, and analyzing financial markets with Python and SQL.

## Overview
This repository provides reusable code and datasets for financial market analysis, ETL pipelines, and backtesting.  
It combines the strengths of **Python** (data science, automation) and **SQL** (structured queries, integration with data providers).

Key features:
- **Python**: pandas-based processing, containerized execution, servers, cloud pipelines  
- **SQL**: MS Workbench, Data Studio integration  
- **ETL pipelines**: pulling, transforming, and storing structured financial data  
- **Web scraping**: SEC filings and external data providers  
- **Backtesting**: pricing data and historical strategies  
- **M&A modeling**: timestamped repositories of merger & acquisition data  
- **Wrappers**: convenience layers around CSV, SQL, and API data sources  

## Components

### 1. Python Market Data Code
Located in the `Python/` directory.

Includes scripts and datasets for:
- Processing raw market data  
- Corporate event handling  
- Running and validating financial models  
- Managing large-scale CSVs and logs for training and testing  

### 2. External Data Providers
Located in `python-sql-data-external-data-providers/`.

Contains:
- **SQL + Python integration**: query results → pandas DataFrames  
- **Web scraping**: scripts for capturing Schedule D updates (SEC website)  
- **ETL code**: extraction and transformation of provider datasets  

### 3. Core Market Data Project
At the repository root.

Provides:
- Overall project structure and documentation  
- Database mounting and containerization notes  
- Cloud execution strategies for scalable market data analysis  
- Integration of multiple pipelines for end-to-end workflows  

```bash
## Future Work
- Extend scraping to more regulatory and market data sources  
- Add Dockerfiles and cloud deployment scripts  
- Automate continuous ingestion and cleaning  
- Jupyter notebooks with example analyses and walkthroughs  

## Getting Started

Clone the repository:
```bash
git clone git@github.com:artemponomarevjetski/python-sql-market-data.git
cd python-sql-market-data
````

Install dependencies (Python 3.9+ recommended):

```bash
pip install -r requirements.txt
```

Run example scripts:

python Python/2019-12-08.py
```