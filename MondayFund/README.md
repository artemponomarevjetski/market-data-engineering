# MondayFund: 2010 consulting with Christina Winch

**Reconstructed 7 Nov 2026**

This folder presents a modern reconstruction of a research discussion in the context of Art Ponomarev's 2010 consulting for Christina Winch. The assumed historical setting is **mid-2010**, with **30 June 2010** used as an illustrative research cutoff. These are reconstruction assumptions, not recovered meeting dates or a claim that this exact protocol was used at the time.

## Presentation

[Schwab ETF Trend Research: MACD Signals and Risk Review](Schwab_ETF_MACD_Consulting_2010_Reconstruction.pdf)

The PDF contains 14 slides in a traditional 4:3 landscape presentation format. It was created in 2026. The title and every page footer identify the reconstruction date.

## Consulting context and evidence

- **Art's recollection:** he supported Christina Winch's Monday investment strategy and ETF risk/timing research in 2010, had access to private records, and worked alongside a colleague who programmed in C.
- **Contemporaneous correspondence:** in a 10 July 2011 LinkedIn message to Mark Scheffler supplied by Art, he referred to consulting for Christina during the preceding year. This supports the 2010 timing; exact engagement dates remain unrecorded.
- **Public context:** a [2011 SEC filing][5] describes the Monday Portfolio as a stock-momentum strategy and distinguishes it from Moderate and Growth ETF portfolios. The filing supplies strategy context; role details follow Art's account.
- **Reconstruction:** the original 2010 slide deck is unavailable. The ETF/MACD material here presents proposed methods and synthetic examples, separate from the proprietary Monday strategy, with no historical backtest results or private client data.

## Historically available research universe

The following first secondary-market trading dates come from the [Schwab Strategic Trust semiannual report dated 28 February 2010][1]. The report uses this definition for inception.

| Ticker | Schwab ETF | First trading date |
|---|---|---|
| SCHB | U.S. Broad Market | 3 Nov 2009 |
| SCHX | U.S. Large-Cap | 3 Nov 2009 |
| SCHA | U.S. Small-Cap | 3 Nov 2009 |
| SCHF | International Equity | 3 Nov 2009 |
| SCHG | U.S. Large-Cap Growth | 11 Dec 2009 |
| SCHV | U.S. Large-Cap Value | 11 Dec 2009 |
| SCHC | International Small-Cap Equity | 14 Jan 2010 |
| SCHE | Emerging Markets Equity | 14 Jan 2010 |

By the illustrative cutoff, these funds had only about five to eight months of live history, before indicator warm-up. Earlier index histories would require separate, explicitly labeled proxy studies. The eight funds overlap in exposure; they are a research universe rather than eight independent portfolio building blocks.

## Proposed research specification

The following is the reconstruction's explicit baseline, not a recovered historical trading rule.

1. **Data and initialization.** Use daily observations, retain chronological order, and document corporate-action adjustments. Initialize recursive EMAs from the first observation. Require an illustrative 60-session warm-up before eligible signals and assess a 90-session warm-up separately as a sensitivity check.
2. **Indicator.** For span `n`, use `alpha = 2 / (n + 1)` and `EMA(n,t) = alpha * Close(t) + (1 - alpha) * EMA(n,t-1)`. Set `MACD = EMA(12) - EMA(26)`, `Signal = EMA(9) of MACD`, and `H = MACD - Signal`. See [Fidelity's definition][2] and the [Schwab momentum reference][3].
3. **Position state.** Start in cash. While in cash, enter when `H(t) > 0` and `H(t-1) <= 0`. While long, exit when `H(t) < 0` and `H(t-1) >= 0`. Otherwise retain the position, including equality; an already-held target state causes no new trade. Use the last warm-up observation as the prior bar. A positive first eligible value alone is not an entry. There is no shorting or leverage.
4. **Execution clock.** Calculate after close `t` and execute at the next available session's open `t+1`. The previous holdings earn the overnight gap before execution. A shifted close-to-close return series is not sufficient to represent this execution assumption.
5. **Capital and cash.** Evaluate each ETF as a separate long/cash sleeve. Any combined model must specify initial allocations in advance. Inactive allocations remain cash; without cross-sleeve rebalancing, weights drift. Do not silently redistribute cash to active ETFs. Specify cash returns and charge every modeled trade's commissions, spread, and slippage.
6. **Accounting.** Use consistent adjusted prices, or raw execution prices with explicit split/dividend bookkeeping. Do not mix incompatible price units, count dividends twice, or deduct fund expenses again when already reflected in the price series.

## Illustrations and divergence

The three PDF charts use deterministic synthetic prices and actual numerical MACD calculations. They contain no historical ETF prices, trade records, or investment performance. The figures use **160 hidden warm-up observations**, which is a chart-construction convention distinct from the proposed live-data eligibility rule.

The charts illustrate a signal-line crossover, a higher price high paired with a lower MACD high, and a lower price low paired with a higher MACD low. Indicator extrema can precede price extrema. Their pairing is retrospective: any systematic pivot rule must define confirmation and delay recognition until the later pivot is observable. Divergence does not guarantee a reversal. The [2025 Schwab divergence article][4] is a reconstruction reference, not a source available in 2010.

## Evaluation and proposed work products

Compare each sleeve with the same ETF held over the same eligible dates, with consistent dividend, cash, and cost treatment. A combined comparison must use the same initial allocations. Report net return, drawdown, exposure/time invested, turnover, trade count, and cost sensitivity. Lower drawdown caused by less market exposure is not sufficient evidence of timing skill. Freeze assumptions before evaluation and report sensitivity checks rather than selecting only a favorable variant.

Proposed outputs are an assumptions sheet, reproducible calculations, an execution ledger, benchmark comparisons, and a limitations review. **Historical ETF metrics remain uncomputed.**

## Sources

1. [Schwab Strategic Trust, semiannual report dated 28 February 2010][1]. Period evidence for fund identities and trading inception dates.
2. [Fidelity, MACD indicator guide][2]. Standard calculation and interpretation, retrieved for this reconstruction.
3. [Charles Schwab, 3 Strength Indicators for Assessing Stock Momentum, 6 June 2025][3]. Modern definition reference.
4. [Charles Schwab, Using Chart Divergences to Make Trading Decisions, 9 September 2025][4]. Modern definition reference.
5. [Ginkgo Multi-Strategy Fund registration filing, 1 April 2011][5]. Public strategy naming and context; consulting-role details follow Art's account.

[Christina Winch's LinkedIn profile](https://www.linkedin.com/in/christina-winch-6b776067/)

[Return to the repository overview](../README.md) | [Fintech consulting proposal](../fintech_consulting_proposal/proposal.md)

[1]: https://www.sec.gov/Archives/edgar/data/1454889/000095012310045321/f55658nvcsrs.htm
[2]: https://www.fidelity.com/learning-center/trading-investing/technical-analysis/technical-indicator-guide/macd
[3]: https://www.schwab.com/learn/story/3-strength-indicators-assessing-stock-momentum
[4]: https://www.schwab.com/learn/story/using-chart-divergences-to-make-trading-decisions
[5]: https://www.sec.gov/Archives/edgar/data/1314414/000091047211000504/coverpage.htm
