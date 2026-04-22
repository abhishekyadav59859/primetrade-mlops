# MLOps Rolling Mean Signal Pipeline

A minimal MLOps-style batch job that computes a rolling mean signal on OHLCV financial data. Demonstrates reproducibility, observability, and deployment readiness.

---

## What it does

1. Loads and validates a YAML config (`seed`, `window`, `version`)
2. Sets `numpy.random.seed` for reproducible results
3. Reads an OHLCV CSV and validates the `close` column
4. Computes a rolling mean on `close` using the configured window
5. Generates a binary signal: `1` if `close > rolling_mean`, else `0`
6. Writes structured `metrics.json` and detailed `run.log`

---

## Local run instructions

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
  "latency_ms": 46,
  "seed": 42,
  "status": "success"
}
```

---

## Docker build/run commands

### Build
```bash
docker build -t mlops-task .
```

### Run
```bash
docker run --rm mlops-task
```

The container will:
- Run the full pipeline against the bundled `data.csv` and `config.yaml`
- Print the final `metrics.json` to stdout
- Exit with code `0` on success, non-zero on failure

---

## Config format (`config.yaml`)

```yaml
seed: 42       # Random seed for reproducibility
window: 5      # Rolling mean window size
version: "v1"  # Pipeline version string
```

---

## Error handling

The pipeline handles these cases gracefully and writes an error `metrics.json`:
- Missing input file
- Invalid CSV format
- Empty CSV
- Missing `close` column
- Invalid config structure or missing fields

Error output format:
```json
{
  "version": "v1",
  "status": "error",
  "error_message": "Description of what went wrong",
  "latency_ms": 12
}
```

---

## Project structure

```
├── run.py            # Main pipeline script
├── config.yaml       # Config (seed, window, version)
├── data.csv          # 10,000-row OHLCV dataset
├── requirements.txt  # Python dependencies
├── Dockerfile        # Docker build definition
├── README.md         # This file
├── metrics.json      # Sample output from successful run
└── run.log           # Sample log from successful run
```
