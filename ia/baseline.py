"""AI problem + baseline (previa).

Problem: short-term temperature forecasting to warn the user BEFORE a threshold is crossed.
  - input : the last readings of a device (temperature, humidity, light)
  - target: temperature `HORIZON` readings ahead (default 15 readings = 5 min at 20 s)
  - split : TEMPORAL (train = first 70% in time, test = last 30%), never shuffled, because shuffling
            leaks the future into training and makes the score look better than it is.
  - metric: MAE in °C
  - baseline: persistence ("the temperature in 5 min will be the one I see now")

The linear model below is only a first comparison to show where the final model starts; for the final
delivery it must beat the baseline on the temporal test set and be served on /predict.

Usage:
  python ia/baseline.py --csv readings.csv      # columns: ts,temperature_c,humidity_pct,light_pct
  python ia/baseline.py --demo                  # synthetic data, only to check the script runs
"""
import argparse

import numpy as np
import pandas as pd

HORIZON = 15
LAGS = 6


def make_demo(n=4000, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(n)
    temp = 26 + 3 * np.sin(t / 4320 * 2 * np.pi) + rng.normal(0, 0.15, n)
    return pd.DataFrame({"ts": pd.date_range("2026-11-10", periods=n, freq="20s"), "temperature_c": temp,
                         "humidity_pct": 60 - (temp - 26) * 2 + rng.normal(0, 0.5, n),
                         "light_pct": 50 + 40 * np.sin(t / 4320 * 2 * np.pi)})


def build(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values("ts").dropna(subset=["temperature_c"]).reset_index(drop=True)  # invalid readings are not values
    for k in range(LAGS):
        d[f"t_lag{k}"] = d["temperature_c"].shift(k)
    d["hum"] = d["humidity_pct"].ffill()
    d["light"] = d["light_pct"].ffill()
    d["target"] = d["temperature_c"].shift(-HORIZON)
    return d.dropna(subset=[f"t_lag{k}" for k in range(LAGS)] + ["target", "hum", "light"]).reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if not (a.csv or a.demo):
        raise SystemExit("use --csv FILE or --demo")
    df = make_demo() if a.demo else pd.read_csv(a.csv, parse_dates=["ts"])
    if a.demo:
        print("DEMO MODE: synthetic data, numbers below mean nothing for the project.\n")

    d = build(df)
    cut = int(len(d) * 0.7)
    train, test = d.iloc[:cut], d.iloc[cut:]
    if len(test) < 30:
        raise SystemExit(f"only {len(test)} test rows: collect more data (previa asks for >= 48 h)")

    base_pred = test["t_lag0"]
    base_mae = float(np.mean(np.abs(test["target"] - base_pred)))

    feats = [f"t_lag{k}" for k in range(LAGS)] + ["hum", "light"]
    X = np.c_[np.ones(len(train)), train[feats].to_numpy()]
    w, *_ = np.linalg.lstsq(X, train["target"].to_numpy(), rcond=None)
    pred = np.c_[np.ones(len(test)), test[feats].to_numpy()] @ w
    lin_mae = float(np.mean(np.abs(test["target"].to_numpy() - pred)))

    print(f"rows: train={len(train)} test={len(test)} | horizon={HORIZON} readings")
    print(f"Baseline (persistence) MAE : {base_mae:.3f} °C")
    print(f"Linear on lags       MAE : {lin_mae:.3f} °C  ({'better' if lin_mae < base_mae else 'NOT better'} than baseline)")


if __name__ == "__main__":
    main()
