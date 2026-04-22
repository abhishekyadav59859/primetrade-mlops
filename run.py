"""
MLOps-style batch job: rolling mean signal pipeline.
Usage:
    python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def setup_logging(log_file: str) -> logging.Logger:
    logger = logging.getLogger("mlops_pipeline")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    )
    
    fh = logging.FileHandler(log_file)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stderr)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def write_metrics(output_path: str, metrics: dict) -> None:
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)


def load_config(config_path: str, logger: logging.Logger) -> dict:
    logger.info(f"Loading config from: {config_path}")
    if not Path(config_path).exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError("Config file is empty or invalid YAML")

    required_fields = ["seed", "window", "version"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        raise ValueError(f"Config missing required fields: {missing}")

    if not isinstance(config["seed"], int):
        raise ValueError(f"seed must be an integer, got: {type(config['seed'])}")
    if not isinstance(config["window"], int) or config["window"] < 1:
        raise ValueError(f"window must be a positive integer, got: {config['window']}")

    logger.info(
        f"Config validated — seed={config['seed']}, "
        f"window={config['window']}, version={config['version']}"
    )
    return config


def load_dataset(input_path: str, logger: logging.Logger) -> pd.DataFrame:
    logger.info(f"Loading dataset from: {input_path}")

    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        raise ValueError(f"Invalid CSV format: {e}")

    if df.empty:
        raise ValueError("Input CSV is empty")

    if "close" not in df.columns:
        raise ValueError(
            f"Required column 'close' not found. "
            f"Available columns: {list(df.columns)}"
        )

    if df["close"].isnull().all():
        raise ValueError("Column 'close' contains only null values")

    logger.info(f"Dataset loaded — {len(df)} rows, columns: {list(df.columns)}")
    return df


def compute_rolling_mean(df: pd.DataFrame, window: int, logger: logging.Logger) -> pd.DataFrame:
    logger.info(f"Computing rolling mean on 'close' with window={window}")
    df = df.copy()
    df["rolling_mean"] = df["close"].rolling(window=window).mean()
    nan_count = df["rolling_mean"].isnull().sum()
    logger.info(
        f"Rolling mean computed — {nan_count} NaN rows "
        f"(first {window - 1} rows excluded from signal computation)"
    )
    return df


def generate_signal(df: pd.DataFrame, logger: logging.Logger) -> pd.DataFrame:
    logger.info("Generating binary signal: signal=1 if close > rolling_mean, else 0")
    df = df.copy()
    
    valid_mask = df["rolling_mean"].notna()
    df["signal"] = np.nan
    df.loc[valid_mask, "signal"] = (
        df.loc[valid_mask, "close"] > df.loc[valid_mask, "rolling_mean"]
    ).astype(int)
    valid_signals = df.loc[valid_mask, "signal"]
    signal_rate = float(valid_signals.mean())
    logger.info(
        f"Signal generation complete — "
        f"{valid_mask.sum()} valid rows, "
        f"signal_rate={signal_rate:.4f}"
    )
    return df, signal_rate


def parse_args():
    parser = argparse.ArgumentParser(description="MLOps rolling mean signal pipeline")
    parser.add_argument("--input",    required=True, help="Path to input CSV file")
    parser.add_argument("--config",   required=True, help="Path to YAML config file")
    parser.add_argument("--output",   required=True, help="Path to output metrics JSON")
    parser.add_argument("--log-file", required=True, help="Path to log file")
    return parser.parse_args()


def main():
    args = parse_args()
    start_time = time.time()

    logger = setup_logging(args.log_file)
    logger.info("=" * 60)
    logger.info("MLOps Pipeline — Job started")
    logger.info(f"Input:    {args.input}")
    logger.info(f"Config:   {args.config}")
    logger.info(f"Output:   {args.output}")
    logger.info(f"Log file: {args.log_file}")
    logger.info("=" * 60)

    try:
        
        config = load_config(args.config, logger)
        seed    = config["seed"]
        window  = config["window"]
        version = config["version"]

        np.random.seed(seed)
        logger.info(f"Random seed set: numpy.random.seed({seed})")

        df = load_dataset(args.input, logger)
        rows_processed = len(df)

        df = compute_rolling_mean(df, window, logger)

        df, signal_rate = generate_signal(df, logger)

        latency_ms = int((time.time() - start_time) * 1000)

        metrics = {
            "version":        version,
            "rows_processed": rows_processed,
            "metric":         "signal_rate",
            "value":          round(signal_rate, 4),
            "latency_ms":     latency_ms,
            "seed":           seed,
            "status":         "success"
        }

        write_metrics(args.output, metrics)
        logger.info(f"Metrics written to: {args.output}")
        logger.info(f"Metrics summary: {json.dumps(metrics)}")
        logger.info("Job completed successfully")
        logger.info("=" * 60)

        print(json.dumps(metrics, indent=2))
        sys.exit(0)

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_metrics = {
            "version":       config["version"] if "config" in dir() and isinstance(config, dict) else "v1",
            "status":        "error",
            "error_message": str(e),
            "latency_ms":    latency_ms
        }
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        logger.info("=" * 60)

        try:
            write_metrics(args.output, error_metrics)
            logger.info(f"Error metrics written to: {args.output}")
        except Exception as write_err:
            logger.error(f"Could not write error metrics: {write_err}")

        print(json.dumps(error_metrics, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
