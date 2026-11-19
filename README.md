# Automated Feed Formulation & Cost Tracker (API Ingestion & Incremental Loads)



## The Scenario:
Feed accounts for up to 70% of livestock production costs. Commodity prices (corn, soybean meal, wheat) fluctuate daily 
on global markets.

## The Engineering Goal:
Build a pipeline that automatically fetches live commodity prices from a public API, calculates daily ration costs,
and stores historical price trends in SQL


## What It Does:
**API Extraction**: Using Python's `urllib.request` library to pull JSON data from external web sources.


**Data Transformation:** Parsing nested JSON structures into clean Pandas DataFrame.

**Incremental Loading:** Writing SQL logic to append _only_ new daily prices without duplicating yesterday's records.
