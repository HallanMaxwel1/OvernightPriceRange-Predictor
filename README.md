# Overnight News Range Predictor

## Overview

The **Overnight News Range Predictor** identifies publicly traded securities with **overnight news events** and estimates their **expected next-day price range** using historical volatility.

It filters news headlines published **outside regular U.S. market hours** and pairs them with rolling statistical measures (based on prior price data) to assess potential price movement **without lookahead bias**.

---

## What It Does

* Detects securities with **overnight news**
* Computes **20-day rolling volatility metrics**
* Predicts a **price range** using historical standard deviation
* Returns a **consolidated dataset** of headlines + price statistics

---

## Key Assumptions

* **Market hours:** 9:30 AM – 4:30 PM ET
  Overnight window: **4:31 PM (prior trading day) → 9:30 AM (target day)**
* **Volatility window:** 20 trading days (parameterizable)
* **Prediction method:** 1 standard deviation
* **Calendar:** U.S. trading calendar assumed (holidays not yet handled)
* **Stationarity:** Past volatility is indicative of future movement

---

## Price Range Formula

Using the prior day’s close and 20-day rolling statistics:

```
Upper Bound = 20-day avg close + (std% × previous close)
Lower Bound = 20-day avg close - (std% × previous close)
```

> Note: This is an assumed model and may break during earnings, regime shifts, or major news events.

---

## Scenarios Handled

* **Monday mornings:** Captures Friday after-hours → Monday pre-market (weekend gap)
* **Tuesday–Friday:** Captures previous day’s after-hours news
* **Multiple headlines per symbol:** All are returned (duplicates possible)

---

## Input Data

**News Headlines (TSV)**

* `temp_offerings_2021_anon.tsv`
* `temp_offerings_2022_anon.tsv`
* `temp_offerings_2023_anon.tsv`
* `temp_offerings_2024_anon.tsv`

**Price Data (TSV)**

* `temp_prices_2021_2024_anon.tsv`
  `(date, symbol, open, high, low, close, volume)`
  ` This file is excluded due to size limits.

---

## Output Metrics

For each qualifying symbol:

* 20-day closing **standard deviation**
* **Previous day’s close**
* 20-day **average closing price**
* Volatility **percentage**
* Upper & lower predicted bounds
* Final **expected price range**

---

## Workflow

1. User inputs a **target date** (MM/DD/YYYY)
2. System identifies tickers with **overnight news**
3. Rolling statistics are computed **using only prior data**
4. A consolidated dataset is returned:

   * Timestamps
   * Symbols
   * Headlines
   * All calculated statistics

> Runtime: ~1 minute for full output

---

## Data Integrity & Lookahead Protection

* No use of future prices
* 20-day window **excludes target date**
* Point-in-time filtering for news & prices
* Temporal filtering occurs **before** symbol matching

---

## Known Limitations

* Market holidays not handled
* Assumes normal return distribution
* No sentiment or headline importance weighting
* Corporate actions not adjusted
* Illiquid or newly listed securities may be excluded

---

## Potential Improvements

* Market holiday calendar support
* Sentiment analysis for headlines
* Multi-sigma ranges (2σ, 3σ)
* Volume-weighted statistics
* Liquidity filters
* Intraday & extended-hours pricing
* Real-time data integration
* Backtesting framework
* Performance optimizations

---
