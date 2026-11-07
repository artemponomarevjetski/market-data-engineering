#!/usr/bin/env python3
"""New 2026 educational demonstration: Lorenz dynamics and causal forecasting.

This is newly written research code, not recovered historical collaboration code.
A Lorenz attractor illustrates nonlinear deterministic dynamics; its existence
does not establish that market prices follow a low-dimensional chaotic system.

Install: python -m pip install numpy
Demo:    python strange_attractor_market_forecasting.py
Market:  python strange_attractor_market_forecasting.py --csv prices.csv \
             --date-column date --close-column close --output forecasts.csv

CSV dates must be strictly increasing ISO-8601 dates/times; naive times are
interpreted as UTC. Closes must be finite and positive. Use a consistently
adjusted price series and a consistent sampling interval; intervals are treated
as observations, not equal calendar durations. No data are downloaded.

The expanding walk-forward model forecasts the next increment of Lorenz x, or
the next log return in market mode. A state is a backward delay embedding.
At origin t, a training origin s must satisfy s + 1 <= t and t - s > theiler.
Feature scaling is refit using ONLY those eligible training rows. Parameters
are fixed before evaluation; later test observations enter training only after
their labels become known. This is sequential evaluation, not a frozen model.

Reference: Lorenz (1963), Deterministic Nonperiodic Flow:
https://journals.ametsoc.org/view/journals/atsc/20/2/1520-0469_1963_020_0130_dnf_2_0_co_2.xml
Nonlinear forecasting background: Sugihara and May (1990):
https://www.nature.com/articles/344734a0
The estimator here is inverse-distance k-nearest-neighbor regression, not a
claim to reproduce either paper's complete method. No trading or alpha claims.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
import math
import sys

try:
    import numpy as np
except ImportError as exc:
    raise ImportError("Install the required dependency: python -m pip install numpy") from exc


def parse_prices(handle, date_column="date", close_column="close"):
    """Read chronological prices; reject malformed rows instead of sorting."""
    reader = csv.DictReader(handle)
    fields = reader.fieldnames or []
    if len(fields) != len(set(fields)):
        raise ValueError("CSV headers must be unique.")
    if date_column not in fields or close_column not in fields:
        raise ValueError(f"CSV requires columns {date_column!r} and {close_column!r}.")
    stamps, prices = [], []
    previous = None
    for row_number, row in enumerate(reader, start=2):
        try:
            raw = row[date_column].strip()
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            stamp = stamp.replace(tzinfo=timezone.utc) if stamp.tzinfo is None else stamp
            stamp = stamp.astimezone(timezone.utc)
            price = float(row[close_column])
        except (TypeError, ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid date or close on CSV row {row_number}.") from exc
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"Incorrect column count on CSV row {row_number}.")
        if previous is not None and stamp <= previous:
            raise ValueError(f"Dates must be unique and increasing: CSV row {row_number}.")
        if not math.isfinite(price) or price <= 0:
            raise ValueError(f"Close must be finite and positive: CSV row {row_number}.")
        stamps.append(stamp.isoformat())
        prices.append(price)
        previous = stamp
    if len(prices) < 4:
        raise ValueError("CSV requires at least four prices; forecasting needs more.")
    return stamps, np.asarray(prices, dtype=float)


def lorenz(steps=3000, dt=0.01, burn_in=1000):
    """Standard Lorenz63, RK4, initial state (1, 1, 1); discard burn-in."""
    if steps < 4 or burn_in < 0 or not math.isfinite(dt) or not 0 < dt <= 0.05:
        raise ValueError("Require steps >= 4, burn-in >= 0, and 0 < dt <= 0.05.")

    def rhs(state):
        x, y, z = state
        return np.array([10 * (y - x), x * (28 - z) - y, x * y - (8 / 3) * z])

    state = np.ones(3, dtype=float)
    trajectory = np.empty((steps, 3), dtype=float)
    with np.errstate(over="raise", invalid="raise"):
        for i in range(steps + burn_in):
            k1 = rhs(state)
            k2 = rhs(state + dt * k1 / 2)
            k3 = rhs(state + dt * k2 / 2)
            k4 = rhs(state + dt * k3)
            state = state + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            if not np.isfinite(state).all():
                raise ValueError("Lorenz integration diverged; reduce dt.")
            if i >= burn_in:
                trajectory[i - burn_in] = state
    return trajectory


def walk_forward(signal, response, *, dimension=3, delay=4, neighbors=8,
                 theiler=20, train_fraction=0.7, min_train=100, mean_window=50):
    """response[s] becomes known at origin s+1. Return audited forecasts."""
    signal = np.asarray(signal, dtype=float)
    response = np.asarray(response, dtype=float)
    if signal.ndim != 1 or response.shape != (len(signal) - 1,):
        raise ValueError("Require a 1-D signal and len(signal)-1 aligned targets.")
    if not np.isfinite(signal).all() or not np.isfinite(response).all():
        raise ValueError("Signals and targets must be finite.")
    counts = (dimension, delay, neighbors, min_train, mean_window)
    if any(not isinstance(v, (int, np.integer)) or v < 1 for v in counts):
        raise ValueError("Dimension, delay, neighbors, min-train and window must be positive integers.")
    if not isinstance(theiler, (int, np.integer)) or theiler < 0:
        raise ValueError("Theiler window must be a nonnegative integer.")
    if not 0 < train_fraction < 1:
        raise ValueError("Train fraction must be strictly between zero and one.")

    span = (dimension - 1) * delay
    first_test = int(train_fraction * (len(signal) - 1))
    if first_test - theiler - span < max(min_train, neighbors):
        raise ValueError("Too few eligible training rows; supply more data or change parameters.")
    origins = np.arange(first_test, len(signal) - 1)
    if not len(origins):
        raise ValueError("No evaluation observations remain.")
    all_origins = np.arange(span, len(signal) - 1)
    embedded = signal[all_origins[:, None] - delay * np.arange(dimension)]
    predicted, rolling, training_counts, latest_neighbors = [], [], [], []

    for t in origins:
        # Exclusive upper bound: s < t-theiler, hence s+1 <= t.
        stop = int(t - theiler - span)
        train_x = embedded[:stop]
        train_y = response[span:t - theiler]
        center, scale = train_x.mean(axis=0), train_x.std(axis=0)
        scale = np.where(scale > 1e-12, scale, 1.0)
        normalized_train = (train_x - center) / scale
        normalized_query = (embedded[t - span] - center) / scale
        distances = np.linalg.norm(normalized_train - normalized_query, axis=1)
        nearest = np.argsort(distances, kind="stable")[:neighbors]
        close_distances = distances[nearest]
        exact = close_distances <= 1e-12
        if exact.any():
            estimate = float(train_y[nearest[exact]].mean())
        else:
            weights = close_distances.min() / close_distances
            estimate = float(np.dot(weights, train_y[nearest]) / weights.sum())
        predicted.append(estimate)
        rolling.append(float(response[max(0, t - mean_window):t].mean()))
        training_counts.append(stop)
        latest_neighbors.append(int(span + nearest.max()))

    result = {
        "origins": origins,
        "actual": response[origins],
        "knn": np.asarray(predicted),
        "zero": np.zeros(len(origins)),
        "rolling_mean": np.asarray(rolling),
        "training_examples": np.asarray(training_counts),
        "latest_training_origin": origins - theiler - 1,
        "latest_neighbor_origin": np.asarray(latest_neighbors),
        "first_test_origin": first_test,
    }
    if any(not np.isfinite(result[key]).all() for key in ("knn", "rolling_mean")):
        raise ValueError("Nonfinite forecast; check input scale and parameters.")
    return result


def score(result):
    """One-step target errors; no transaction-cost, position or P&L model."""
    scores = {}
    for name in ("knn", "zero", "rolling_mean"):
        error = result[name] - result["actual"]
        scores[name] = {
            "mae": float(np.mean(np.abs(error))),
            "rmse": float(np.sqrt(np.mean(error * error))),
        }
    return scores


def forecast_rows(result, times, values, market=False):
    """Stable CSV schema. Target units are identified in every record."""
    offset = 1 if market else 0
    for i, t in enumerate(result["origins"]):
        origin = int(t + offset)
        current = float(values[origin])
        forecasts = {key: float(result[key][i]) for key in ("knn", "zero", "rolling_mean")}
        if market:
            try:
                next_values = {key: math.exp(math.log(current) + value)
                               for key, value in forecasts.items()}
            except OverflowError as exc:
                raise ValueError("Next-price forecast overflow; inspect price scale.") from exc
            next_values["zero"] = current  # Exact random-walk baseline, without roundoff.
            if any(not math.isfinite(v) or v <= 0 for v in next_values.values()):
                raise ValueError("Next-price forecast is not finite and positive.")
        else:
            next_values = {key: current + value for key, value in forecasts.items()}
        yield {
            "origin_time": times[origin],
            "target_time": times[origin + 1],
            "origin_signal_index": int(t),
            "target_kind": "log_return" if market else "lorenz_x_increment",
            "actual_target": float(result["actual"][i]),
            "knn_target": forecasts["knn"],
            "zero_target": forecasts["zero"],
            "rolling_mean_target": forecasts["rolling_mean"],
            "origin_value": current,
            "actual_next_value": float(values[origin + 1]),
            "knn_next_value": next_values["knn"],
            "zero_next_value": next_values["zero"],
            "rolling_mean_next_value": next_values["rolling_mean"],
            "training_examples": int(result["training_examples"][i]),
            "latest_training_origin_signal_index": int(result["latest_training_origin"][i]),
            "latest_neighbor_origin_signal_index": int(result["latest_neighbor_origin"][i]),
        }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", help="Market CSV; omit to simulate Lorenz63.")
    parser.add_argument("--date-column", default="date")
    parser.add_argument("--close-column", default="close")
    parser.add_argument("--output", help="Write forecast CSV; existing files are not overwritten.")
    parser.add_argument("--steps", type=int, default=3000, help="Retained Lorenz observations.")
    parser.add_argument("--burn-in", type=int, default=1000)
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--dimension", type=int, default=3)
    parser.add_argument("--delay", type=int, default=4)
    parser.add_argument("--neighbors", type=int, default=8)
    parser.add_argument("--theiler", type=int, default=20)
    parser.add_argument("--train-fraction", type=float, default=0.7)
    parser.add_argument("--min-train", type=int, default=100)
    parser.add_argument("--mean-window", type=int, default=50)
    args = parser.parse_args(argv)
    try:
        if args.csv:
            with open(args.csv, encoding="utf-8-sig", newline="") as handle:
                times, values = parse_prices(handle, args.date_column, args.close_column)
            signal = np.diff(np.log(values))
            response = signal[1:]
        else:
            values = lorenz(args.steps, args.dt, args.burn_in)[:, 0]
            times = [f"{(i + args.burn_in + 1) * args.dt:.10g}" for i in range(len(values))]
            signal, response = values, np.diff(values)
        settings = {name: getattr(args, name) for name in (
            "dimension", "delay", "neighbors", "theiler", "train_fraction",
            "min_train", "mean_window")}
        result = walk_forward(signal, response, **settings)
        # Materialize and validate all outputs before opening an output file.
        rows = list(forecast_rows(result, times, values, market=bool(args.csv)))
        report = {
            "demonstration_created": "2026",
            "mode": "market" if args.csv else "lorenz",
            "target_kind": rows[0]["target_kind"],
            "evaluation": "expanding chronological one-step forecasts",
            "parameters": settings,
            "input_observations": len(values),
            "first_evaluation_origin": rows[0]["origin_time"],
            "last_evaluation_target": rows[-1]["target_time"],
            "evaluated_forecasts": len(rows),
            "metrics": score(result),
            "interpretation": "Forecast errors only; no evidence of financial alpha or market chaos.",
        }
        rendered = json.dumps(report, indent=2, allow_nan=False)
        if args.output:
            with open(args.output, "x", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
        print(rendered)
    except (OSError, ValueError, FloatingPointError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
