# Carmot Capital: research discussions with George Sokoloff

This folder records Art Ponomarev's account of research collaboration and technical discussions with George Sokoloff. Art describes work involving Python analysis of strange attractors, heavy-tailed Cauchy distributions, and possible applications of agentic AI to commerce.

George's historical affiliation with **Carmot Capital LLC** is documented in an [SEC issuer filing](https://www.sec.gov/Archives/edgar/data/1685528/000109544918000105/xslFormDX01/primary_doc.xml), which identifies him as its managing member. A [conference organizer's profile](https://www.terrapinn.com/template/live/engage/6929/15112) identifies him as founder and chief investment officer. The correspondence below records Art's exchanges with George; it does not establish a particular fund vehicle as the contracting party.

## Contents

| File | Purpose |
|---|---|
| [problem_formulation.md](problem_formulation.md) | The dated 2020 sinusoid-recovery problem, notation, sampling and identifiability assumptions, method, and reproducibility results. |
| [robust_cauchy_signal_recovery.py](robust_cauchy_signal_recovery.py) | A new implementation for recovering two shared sinusoidal frequencies and phases from many channels with Cauchy noise. |
| [strange_attractor_market_forecasting.py](strange_attractor_market_forecasting.py) | A separate Lorenz-attractor demonstration and chronological forecasting experiment for a supplied market price series. |

Both Python modules were written in **2026** for this repository. Original historical notebooks, source code, and experimental datasets have not been supplied.

## Dated technical correspondence: 19 August 2020

In correspondence supplied by Art, George formulated a problem involving two cosine signals, a full-row-rank mixing matrix with 1,000 output channels, 300 time samples, and additive Cauchy noise. The goal was to recover the two frequencies and phases.

The [technical formulation](problem_formulation.md) preserves the distinction between the original question and the new implementation. It also explains ambiguities in the phase notation, the matrix-coefficient condition, and the sampling rate. The correspondence documents a research question, not a completed historical recovery result.

## Further correspondence context

Other excerpts supplied by Art record:

- **16 May:** coordination of an in-person meeting.
- **24-26 May:** discussion concerning human cognitive biases being incorporated into large language models.
- **22 June:** Art proposed possible further paid technical work, such as a technical sprint, prototype, research tooling, or data/ML infrastructure work.

The year is not shown in those excerpts and is not inferred here. The June message describes a proposal for further work.

## Run the examples

Use Python 3.9 or later. Install the dependencies and run commands from this directory:

```bash
python -m pip install numpy scipy

# Recover the parameters of newly generated 1,000-channel, 300-sample data.
python robust_cauchy_signal_recovery.py

# Explore signed mixing with a different fixed seed.
python robust_cauchy_signal_recovery.py --channels 250 --seed 23 --signed-mixing

# Simulate Lorenz dynamics and print chronological forecast errors.
python strange_attractor_market_forecasting.py

# Save the synthetic Lorenz forecasts to a new CSV.
python strange_attractor_market_forecasting.py --output lorenz_forecasts.csv

# Evaluate a supplied market price series.
python strange_attractor_market_forecasting.py \
  --csv prices.csv \
  --date-column date \
  --close-column close \
  --output market_forecasts.csv
```

The Cauchy example prints JSON and writes no output files. The forecasting example writes a CSV only when `--output` is supplied and refuses to overwrite an existing file. Importing either module runs no demonstration.

### Market CSV requirements

The forecasting input needs `date` and `close` columns, or names specified through the command-line options. Dates must be unique, increasing ISO-8601 dates or times; naive timestamps are interpreted as UTC. Prices must be finite and positive. Use a consistent price-adjustment convention, a consistent sampling interval, and enough observations for the chosen training and embedding settings.

No market data are downloaded. The code contains no brokerage or trading integration.

## Strange attractors and forecasting

The default example integrates the Lorenz equations using fourth-order Runge-Kutta. It constructs a state from delayed observations of the Lorenz system's x coordinate and uses nearby past states to forecast the next increment. This illustrates short-horizon forecasting in a known deterministic nonlinear system.

In market mode, the method instead embeds past log returns and predicts the next log return and corresponding next close. It compares those predictions with a zero-return/random-walk forecast and a causal rolling-mean forecast.

The initial training fraction defaults to 70%, followed by expanding chronological evaluation. At each forecast:

- Training targets must already be known at the forecast origin.
- Feature scaling uses only eligible past training rows.
- A configurable temporal exclusion window prevents selecting immediately adjacent observations as nearest neighbors.
- Later evaluation observations enter training only after their targets become known.
- Model settings remain fixed during the evaluation.

Output includes mean absolute error and root mean squared error, origin and target times, actual and predicted values, training counts, and the latest eligible and selected neighbor origins. These are forecast errors, not trading returns.

### Verification and interpretation

In-memory checks confirmed finite Lorenz trajectories, correct market return-to-price alignment, known training targets, and compliance with the temporal exclusion window. Perturbing future observations left earlier Lorenz and market forecasts unchanged. Invalid dates, duplicate or out-of-order observations, and nonpositive or nonfinite prices were rejected.

The Cauchy example has its own [assumptions, numerical checks, and limitations](problem_formulation.md). The two examples address different mathematical questions.

A successful Lorenz demonstration does not establish that markets follow a low-dimensional chaotic system. Recovery from synthetic Cauchy-contaminated observations does not establish predictable market signals. Market use would require further evaluation across instruments and periods, data-quality checks, and a separate execution and transaction-cost model.

## Scientific background

- Edward N. Lorenz, [Deterministic Nonperiodic Flow](https://journals.ametsoc.org/view/journals/atsc/20/2/1520-0469_1963_020_0130_dnf_2_0_co_2.xml), 1963.
- George Sugihara and Robert M. May, [Nonlinear forecasting as a way of distinguishing chaos from measurement error in time series](https://www.nature.com/articles/344734a0), 1990.

The forecasting code uses inverse-distance nearest-neighbor regression. These papers provide background; the script does not claim to reproduce their complete methods.

[Repository overview](../README.md) | [Financial AI consulting proposal](../hedge_fund_proposal/proposal.md)
