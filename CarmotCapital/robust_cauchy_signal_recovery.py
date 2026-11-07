#!/usr/bin/env python3
"""Recover two shared sinusoidal frequencies under independent Cauchy noise.

New educational implementation (2026), based on the technical problem in a
19 August 2020 discussion with George Sokoloff. This is not recovered historical
code or a validated market prediction model. See problem_formulation.md.

Requires NumPy and SciPy. Importing this module performs no computation or I/O.
"""

import argparse
import json

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.signal import find_peaks


def phase_distance_mod_pi(estimated, reference):
    """Smallest absolute angular distance when a loading sign is unknown."""
    difference = np.asarray(estimated) - np.asarray(reference)
    return np.abs((difference + np.pi / 2) % np.pi - np.pi / 2)


def _validate(data, dt, fmin, fmax, min_separation):
    y = np.asarray(data, dtype=float)
    if y.ndim != 2 or y.shape[0] < 4 or y.shape[1] < 32:
        raise ValueError("Expected at least 4 channels and 32 samples, rows=channels.")
    if not np.isfinite(y).all():
        raise ValueError("Data must be finite; missing values need explicit handling.")
    if not np.isfinite(dt) or dt <= 0:
        raise ValueError("dt must be finite and positive.")
    fmin = 0.01 / dt if fmin is None else fmin
    fmax = 0.45 / dt if fmax is None else fmax
    nyquist = 0.5 / dt
    if not (0 < fmin < fmax < nyquist):
        raise ValueError("Require 0 < fmin < fmax < 0.5/dt, in cycles/time.")
    separation = 2 / (y.shape[1] * dt) if min_separation is None else min_separation
    if not np.isfinite(separation) or not 0 < separation < fmax - fmin:
        raise ValueError("Frequency separation must fit inside the search band.")
    return y, separation, fmin, fmax


def _spectral_frequencies(scaled, dt, fmin, fmax, min_separation):
    """Winsorized median periodogram: a robust initialization heuristic."""
    samples = scaled.shape[1]
    times = np.arange(samples) * dt
    windowed = np.clip(scaled, -4.0, 4.0) * np.hanning(samples)
    nfft = 1 << int(np.ceil(np.log2(8 * samples)))
    grid = np.fft.rfftfreq(nfft, d=dt)
    power = np.median(np.abs(np.fft.rfft(windowed, n=nfft)) ** 2, axis=0)
    peaks, _ = find_peaks(power)
    peaks = peaks[(grid[peaks] >= fmin) & (grid[peaks] <= fmax)]
    ordered = peaks[np.argsort(power[peaks])[::-1]]
    if ordered.size < 2:
        raise ValueError("No two interior spectral peaks found in the search band.")

    # Greedy selection assumes both true components are prominent across channels.
    first = ordered[0]
    eligible = ordered[
        (np.abs(grid[ordered] - grid[first]) >= min_separation)
        & (np.abs(np.log(grid[ordered] / grid[first])) < 2)
    ]
    if eligible.size == 0:
        raise ValueError("No separated peak pair satisfies the stated frequency ratio.")
    initial = np.sort(grid[[first, eligible[0]]])
    radius = min(1 / (samples * dt), (initial[1] - initial[0]) / 3)

    def negative_power(frequency):
        projection = windowed @ np.exp(-2j * np.pi * frequency * times)
        return -float(np.median(np.abs(projection) ** 2))

    refined = []
    for frequency in initial:
        result = minimize_scalar(
            negative_power,
            bounds=(max(fmin, frequency - radius), min(fmax, frequency + radius)),
            method="bounded",
            options={"xatol": 1e-9 / dt, "maxiter": 100},
        )
        if not result.success:
            raise RuntimeError("Local spectral frequency refinement failed.")
        refined.append(result.x)
    frequencies = np.sort(refined)
    if frequencies[1] - frequencies[0] < min_separation:
        raise ValueError("Refined components are closer than the required separation.")
    if np.abs(np.log(frequencies[1] / frequencies[0])) >= 2:
        raise ValueError("Refined frequency ratio violates the problem constraint.")
    return frequencies


def _cauchy_regression(scaled, design, max_iter):
    """Fit channel coefficients by Cauchy-loss IRLS, with a fixed robust scale.

    The loss is sum(log(1 + (residual/scale)**2)). It is nonconvex;
    this initialized local fit is not a proof of global recovery.
    """
    beta = np.linalg.lstsq(design, np.clip(scaled, -4.0, 4.0).T, rcond=None)[0].T
    residual = scaled - beta @ design.T
    center = np.median(residual, axis=1, keepdims=True)
    scale = np.maximum(np.median(np.abs(residual - center), axis=1), 1e-8)
    converged = False
    for iteration in range(max_iter):
        residual = scaled - beta @ design.T
        weights = (scale[:, None] / np.hypot(scale[:, None], residual)) ** 2
        normal = np.einsum("mn,ni,nj->mij", weights, design, design, optimize=True)
        rhs = (weights * scaled) @ design
        ridge = 1e-10 * np.sum(weights, axis=1)
        normal += ridge[:, None, None] * np.eye(design.shape[1])
        updated = np.linalg.solve(normal, rhs[..., None])[..., 0]
        relative_change = np.max(np.abs(updated - beta)) / (1 + np.max(np.abs(beta)))
        beta = updated
        if relative_change < 1e-7:
            converged = True
            break
    return beta, scale, iteration + 1, converged


def recover(data, dt=1.0, fmin=None, fmax=None, min_separation=None, max_iter=40):
    """Estimate frequencies and phases from an M-channel by N-sample matrix.

    Assumes equally spaced known times t = arange(N)*dt, two distinct positive
    frequencies in an unaliased band, and unknown real signed mixing coefficients.
    Phases are relative to the first sample and identifiable only modulo pi.
    Frequencies are sorted increasingly. Returned mixing has shape (2, M).
    """
    y, separation, fmin, fmax = _validate(data, dt, fmin, fmax, min_separation)
    if not isinstance(max_iter, (int, np.integer)) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer.")
    location = np.median(y, axis=1)
    channel_scale = np.median(np.abs(y - location[:, None]), axis=1)
    if np.any(channel_scale <= 0):
        raise ValueError("Every channel must have positive median absolute deviation.")
    scaled = (y - location[:, None]) / channel_scale[:, None]
    frequencies = _spectral_frequencies(scaled, dt, fmin, fmax, separation)
    times = np.arange(y.shape[1]) * dt
    angles = 2 * np.pi * times[:, None] * frequencies[None, :]
    design = np.column_stack(
        (np.ones(y.shape[1]), np.cos(angles[:, 0]), np.sin(angles[:, 0]),
         np.cos(angles[:, 1]), np.sin(angles[:, 1]))
    )
    beta, noise_scale, iterations, converged = _cauchy_regression(scaled, design, max_iter)
    phases, coherence, loadings = [], [], []
    for component in range(2):
        cosine = beta[:, 1 + 2 * component]
        sine = beta[:, 2 + 2 * component]
        individual = np.arctan2(-sine, cosine)
        reliability = (np.hypot(cosine, sine) / noise_scale) ** 2
        reliability = np.minimum(reliability, np.quantile(reliability, 0.9))
        total = np.sum(reliability)
        if total <= 0:
            raise RuntimeError("A component has no measurable channel loading.")
        resultant = np.sum(reliability * np.exp(2j * individual)) / total
        phase = (0.5 * np.angle(resultant)) % np.pi
        phases.append(phase)
        coherence.append(np.abs(resultant))
        loadings.append(
            channel_scale * (cosine * np.cos(phase) - sine * np.sin(phase))
        )
    phases = np.asarray(phases)
    mixing = np.asarray(loadings)
    sources = np.cos(2 * np.pi * frequencies[:, None] * times + phases[:, None])
    intercept = location + channel_scale * beta[:, 0]
    clean_estimate = mixing.T @ sources
    fitted = clean_estimate + intercept[:, None]
    return {
        "frequencies": frequencies,
        "angular_frequencies": 2 * np.pi * frequencies,
        "phases_mod_pi": phases,
        "phase_coherence": np.asarray(coherence),
        "mixing": mixing,
        "intercept": intercept,
        "clean_estimate": clean_estimate,
        "median_absolute_residual": float(np.median(np.abs(y - fitted))),
        "irls_iterations": iterations,
        "irls_converged": converged,
    }


def synthetic_data(channels=1000, samples=300, dt=1.0, noise_scale=0.7,
                   seed=20200819, signed_mixing=False):
    """Generate new synthetic observations; no historical or market data."""
    if channels < 4 or samples < 32 or not np.isfinite(dt) or dt <= 0:
        raise ValueError("Need >=4 channels, >=32 samples and finite positive dt.")
    if not np.isfinite(noise_scale) or noise_scale < 0:
        raise ValueError("noise_scale must be finite and nonnegative.")
    rng = np.random.default_rng(seed)
    frequencies = np.array([0.071, 0.173]) / dt
    phases = np.array([0.4, -0.9])
    times = np.arange(samples) * dt
    mixing = rng.uniform(0.25, 1.25, size=(2, channels))
    if signed_mixing:
        mixing *= rng.choice([-1.0, 1.0], size=mixing.shape)
    sources = np.cos(2 * np.pi * frequencies[:, None] * times + phases[:, None])
    clean = mixing.T @ sources
    observed = clean + noise_scale * rng.standard_cauchy(size=clean.shape)
    return observed, {
        "frequencies": frequencies, "phases": phases, "mixing": mixing, "clean": clean,
        "noise_scale": noise_scale, "seed": seed,
    }


def report(result, truth=None):
    """JSON-friendly diagnostics; coherence is not a calibrated confidence level."""
    output = {
        key: result[key].tolist()
        for key in ("frequencies", "angular_frequencies", "phases_mod_pi", "phase_coherence")
    }
    output.update(
        median_absolute_residual=result["median_absolute_residual"],
        irls_iterations=result["irls_iterations"],
        irls_converged=result["irls_converged"],
        frequency_units="cycles per unit of dt",
        phase_units="radians modulo pi, relative to first sample",
    )
    if truth is not None:
        output["synthetic_truth"] = {
            "frequencies": truth["frequencies"].tolist(),
            "phases_mod_pi": (truth["phases"] % np.pi).tolist(),
            "cauchy_scale": truth["noise_scale"],
            "seed": truth["seed"],
        }
        output["absolute_frequency_error"] = np.abs(
            result["frequencies"] - truth["frequencies"]
        ).tolist()
        output["phase_error_mod_pi"] = phase_distance_mod_pi(
            result["phases_mod_pi"], truth["phases"]
        ).tolist()
        output["median_absolute_clean_signal_error"] = float(
            np.median(np.abs(result["clean_estimate"] - truth["clean"]))
        )
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", help="Numeric CSV, no header: channels in rows, samples in columns.")
    parser.add_argument("--dt", type=float, default=1.0, help="Known sample spacing.")
    parser.add_argument("--fmin", type=float, help="Lower band limit in cycles/time; default .01/dt.")
    parser.add_argument("--fmax", type=float, help="Upper band limit in cycles/time; default .45/dt.")
    parser.add_argument("--min-separation", type=float, help="Default 2/(samples*dt).")
    parser.add_argument("--channels", type=int, default=1000, help="Synthetic demo only.")
    parser.add_argument("--samples", type=int, default=300, help="Synthetic demo only.")
    parser.add_argument("--noise-scale", type=float, default=0.7, help="Cauchy scale, not std. dev.")
    parser.add_argument("--seed", type=int, default=20200819)
    parser.add_argument("--signed-mixing", action="store_true", help="Synthetic demo only.")
    args = parser.parse_args(argv)
    try:
        if not np.isfinite(args.dt) or args.dt <= 0:
            raise ValueError("dt must be finite and positive.")
        if args.csv:
            data, truth = np.loadtxt(args.csv, delimiter=",", ndmin=2), None
        else:
            data, truth = synthetic_data(
                args.channels, args.samples, args.dt, args.noise_scale, args.seed, args.signed_mixing
            )
        fmin = 0.01 / args.dt if args.fmin is None else args.fmin
        fmax = 0.45 / args.dt if args.fmax is None else args.fmax
        result = recover(data, args.dt, fmin, fmax, args.min_separation)
    except (OSError, ValueError, RuntimeError, np.linalg.LinAlgError) as error:
        parser.error(str(error))
    print(json.dumps(report(result, truth), indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
