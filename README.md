# Machine Learning Signal Pipeline — Primetrade.ai

A minimal Machine Learning batch pipeline that computes a rolling mean trading signal 
on real Bitcoin OHLCV data. Demonstrates reproducibility, observability, and deployment readiness.

---

## About

This project is built as part of the Primetrade.ai Machine Learning Internship assessment.
It processes real Bitcoin market data (10,000 rows) and generates binary trading signals
using a rolling mean strategy.

---

## What it does

1. Loads and validates a YAML config (seed, window, version)
2. Sets numpy.random.seed for fully reproducible results
3. Reads real Bitcoin OHLCV CSV data and validates the close column
4. Computes a rolling mean on close price using configured window
5. Generates a binary trading signal: 1 if close > rolling_mean, else 0
6. Writes structured metrics.json and detailed run.log

---

## Dataset

Real Bitcoin OHLCV data with 10,000 rows:
- Columns: timestamp, open, high, low, close, volume_btc, volume_usd
- Source: Primetrade.ai assessment data

---

## Local Setup

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run
```bash
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
```

### Example output (metrics.json)
```json
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4991,
  "latency_ms": 97,
  "seed": 42,
  "status": "success"
}
```

---

## Docker

### Build
```bash
docker build -t mlops-task .
```

### Run
```bash
docker run --rm mlops-task
```

The container will:
- Run the full pipeline against the bundled data.csv and config.yaml
- Print the final metrics.json to stdout
- Exit with code 0 on success, non-zero on failure

---

## Config (config.yaml)

```yaml
seed: 42       # Random seed for reproducibility
window: 5      # Rolling mean window size
version: "v1"  # Pipeline version string
```

---

## Error Handling

Handles all errors gracefully and always writes metrics.json:
- Missing input file
- Invalid CSV format
- Missing close column
- Invalid config

Error output:
```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of what went wrong",
  "latency_ms": 12
}
```

---

## Project Structure

```
├── run.py            # Main ML pipeline script
├── config.yaml       # Config (seed, window, version)
├── data.csv          # Real Bitcoin OHLCV dataset (10,000 rows)
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker deployment
├── README.md         # This file
├── metrics.json      # Sample success output
└── run.log           # Sample pipeline log
```