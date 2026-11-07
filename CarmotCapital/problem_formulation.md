# Recovering mixed sinusoidal signals under Cauchy noise

## Historical problem

On 19 August 2020, George Sokoloff described a signal-recovery problem to Artem
Ponomarev: infer the frequencies and phases of two sinusoidal factors from
1,000 observed channels, each containing 300 time samples, after linear mixing
and the addition of Cauchy noise. This technical summary is based on
correspondence supplied by Artem.

The accompanying
[`robust_cauchy_signal_recovery.py`](robust_cauchy_signal_recovery.py) is a **new
educational implementation prepared in 2026**. The original correspondence
documents the research question; no original dataset, historical implementation,
or completed historical performance result is supplied here.

## Mathematical model and notation

For known sample times $t_n$, define

$$
S_{k,n}=\cos(b_k t_n+c_k),\qquad
Y=D^\mathsf{T}S+E,
$$

where:

| Symbol | Shape or meaning |
|---|---|
| $S$ | $2\times300$: two underlying sinusoidal signals |
| $D$ | $2\times1000$: unknown mixing coefficients, with row rank two |
| $Y$ | $1000\times300$: observed data, channels in rows |
| $E$ | Additive Cauchy noise; the new example uses independent draws |
| $b_k$ | Positive angular frequency, in radians per unit time |
| $c_k$ | Phase, in radians, relative to the specified time origin |

The stated frequency constraint is
$\lvert\log(b_1/b_2)\rvert<2$. The code uses cyclic frequencies
$f_k=b_k/(2\pi)$, so the same ratio constraint applies to $f_1,f_2$.

### Ambiguities in the original wording

- The two written cosine expressions both use `c1`, although the requested
  outputs include `c1` and `c2`. The implementation assumes two separate phases.
- The mixing matrix is called `D`, but a coefficient condition uses an undefined
  `B`: `median(B) / max(abs(B)) > 0.1`. Its intended meaning requires
  clarification. The default synthetic example uses bounded positive
  coefficients between 0.25 and 1.25. The optional signed-mixing example explores
  a more general sign ambiguity and does not assert compliance with that
  unresolved condition.
- The sampling rate is described as approximately the smaller frequency, without
  defining angular versus cyclic units. That statement does not establish
  alias-free sampling.

These are explicit working assumptions, not corrections attributed to George.

## What can be identified?

**Sampling times and an unaliased search band are necessary.** The example
assumes uniform known spacing `dt`, sets the first sample's time to zero, and
restricts frequencies to $0<f<1/(2\,dt)$. NumPy's
[`rfftfreq`](https://numpy.org/doc/stable/reference/generated/numpy.fft.rfftfreq.html)
uses cycles per unit of sample spacing. Selecting a band in software cannot
establish that real observations were sampled without aliasing; that knowledge
must come from the acquisition process or other prior information.

**Labels and mixing signs are ambiguous.** Swapping the two factors gives the
same observation matrix. Also, negating a row of $D$ while adding $\pi$ to its
phase leaves $Y$ unchanged. The code therefore sorts frequencies and reports
phases modulo $\pi$, rather than claiming an identifiable phase over a full
$2\pi$ interval. A known sign convention could remove the latter ambiguity.

**Rank alone does not ensure reliable recovery.** Coincident frequencies do not
identify two separate factors. Closely spaced frequencies, weak loadings,
unfavorable mixing, and short observation windows can make estimation unstable.
The example's default separation of `2/(samples*dt)` is a conservative algorithm
setting, not a universal mathematical resolution boundary.

## Demonstration method

1. Center and scale each channel using its median and median absolute deviation.
2. Clip standardized observations, apply a Hann window, and aggregate spectral
   power across channels by its median.
3. Select two prominent separated peaks satisfying the frequency-ratio
   constraint, then refine each frequency locally.
4. Fit cosine and sine coefficients per channel with iteratively reweighted
   least squares using Cauchy loss.
5. Aggregate doubled phase angles across channels, which respects the unknown
   loading signs, and reconstruct the shared signals.

For a residual $r$ and fixed robust scale $s$, the regression loss is

$$
\rho(r)=\log\!\left(1+(r/s)^2\right).
$$

[SciPy documents this Cauchy-loss form and its optimization difficulties](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html).
The code implements its reweighted linear fits directly and uses
[`minimize_scalar`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize_scalar.html)
for local spectral refinement.

This is a practical heuristic. Winsorization can distort a spectrum, greedy peak
selection can choose the wrong pair, and local optimization does not guarantee
the global optimum. A returned pair is not evidence by itself that the data
contain exactly two sinusoids.

The Cauchy distribution has no finite mean or variance; its scale parameter is
not a standard deviation
([NIST distribution reference](https://www.itl.nist.gov/div898/handbook/eda/section3/eda3663.htm)).
The demonstration consequently reports median absolute errors and does not
justify recovery through ordinary sample covariance. Its phase-coherence
diagnostic is not a calibrated confidence probability.

## Run the example

Install the two dependencies and run from this directory:

```bash
python -m pip install numpy scipy
python robust_cauchy_signal_recovery.py
```

The default generates **1,000 channels × 300 samples**, with seed `20200819`,
frequencies `[0.071, 0.173]` cycles/sample, phases `[0.4, -0.9]` radians, and
independent Cauchy noise of scale `0.7`.

A smaller signed-mixing example:

```bash
python robust_cauchy_signal_recovery.py --channels 250 --seed 23 --signed-mixing
```

For an existing numeric matrix, supply a header-free CSV with channels in rows,
samples in columns, the known sample spacing, and a justified frequency band:

```bash
python robust_cauchy_signal_recovery.py \
  --csv observations.csv --dt 1 --fmin 0.01 --fmax 0.45
```

The program prints JSON and writes no output files. Importing the module does
not run the example.

## Reproducibility check

In-memory validation with NumPy 2.3.5 and SciPy 1.17.0 produced these default
synthetic results:

| Quantity | Component 1 | Component 2 |
|---|---:|---:|
| True frequency, cycles/sample | 0.07100000 | 0.17300000 |
| Estimated frequency | 0.07092092 | 0.17298032 |
| Absolute frequency error | 0.00007908 | 0.00001968 |
| True phase modulo $\pi$, radians | 0.40000000 | 2.24159265 |
| Estimated phase modulo $\pi$ | 0.48107903 | 2.26285369 |
| Phase error modulo $\pi$, radians | 0.08107903 | 0.02126103 |

The median absolute reconstruction error against the known noiseless synthetic
signal was approximately `0.05427`. The signed-mixing example with 250 channels
and seed `23` gave approximately `0.06835`. A smaller 80-channel, 160-sample
stress case with seed `13` produced larger phase errors, approximately
`0.415` and `0.464` radians, illustrating the dependence on sample size and the
realized noise.

Validation also covered a noise-free case, phase/sign equivalence, sample-spacing
scaling, silent import, valid CLI JSON, and rejection of invalid inputs. These
are reproducibility checks on constructed data, not a general recovery guarantee.

## Relationship to market research

Recovering synthetic latent signals under heavy-tailed noise is a useful
research exercise. It does not establish that financial prices contain stable
sinusoids, deterministic strange attractors, or exploitable forecasts. This
example contains no trading strategy, historical market backtest, client records,
or claim of investment performance.

The separate [strange-attractor example](strange_attractor_market_forecasting.py)
in this folder explores another research direction; it should not be presented
as the same mathematical problem.

[Collaboration overview](README.md) | [Repository overview](../README.md)
