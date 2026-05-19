# Statistics

Scalar summary statistics computed over a light curve: moments, autocorrelation, variability indicators, and uncertainty rescaling.

---

### `rms` — Root mean square

**Syntax**

```python
cmd.rms(maskpoints=None)
```

**Description**

Compute the RMS of the light curve. The output includes the unweighted RMS, the mean magnitude, the expected RMS derived from the formal photometric uncertainties, and the number of points used. The light curve passed to subsequent commands is unchanged.

CLI equivalent: [`-rms`](../../cli/statistics.md#-rms).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included in the calculation. |

**Output**

Suffix `N` is the 0-indexed pipeline command position:

| Column | Description |
|--------|-------------|
| `Mean_Mag_N` | Arithmetic mean magnitude. |
| `RMS_N` | Unweighted RMS. |
| `Expected_RMS_N` | RMS predicted from the formal photometric uncertainties (assuming they are accurate). |
| `Npoints_N` | Number of points used. |

**Examples**

```python
# Single light curve
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = vt.Pipeline().rms().run(lc)
print(result.vars["Mean_Mag_0"])
print(result.vars["RMS_0"])

# Batch: compute RMS for all 10 example light curves
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().rms().run_batch(lcs)
print(batch.vars[["Name", "Mean_Mag_0", "RMS_0", "Expected_RMS_0"]])
```

---

### `rmsbin` — Binned RMS

**Syntax**

```python
cmd.rmsbin(nbin, bintimes, maskpoints=None)
```

**Description**

Apply a moving-mean filter to the light curve at one or more timescales and report the RMS of each filtered series. Used to characterise correlated (red) noise: as the filter window grows, white noise averages down as `1/sqrt(N)` while red noise persists. The light curve passed to subsequent commands is unchanged.

`bintimes` are interpreted as half-widths in **minutes** (matching the CLI). The full filter window for each entry is `2 · bintime`.

CLI equivalent: [`-rmsbin`](../../cli/statistics.md#-rmsbin).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `nbin` | `int` | Number of timescale bins (filters) to apply. |
| `bintimes` | list of `float` | Filter half-widths in minutes; one entry per filter. Must have length `nbin`. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included. |

**Output**

For each binning timescale `T_i` (in minutes) and command index `N`, vartools emits an `RMSBin_<T_i>_N` column (and an associated `Expected_RMS_Bin_<T_i>_N` column). The timescale tag in the column name is built from the input minutes value with a one-decimal-place form (e.g. `5.0` minutes becomes `RMSBin_5.0_0`); two distinct input values that round to the same tag will produce duplicate column names, so choose well-separated values.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Compute binned RMS at a range of timescales, in minutes.
# (vartools truncates bin times when forming column names,
# so pick values that are well separated.)
bintimes_min = [5.0, 10.0, 60.0, 1440.0, 14400.0]
batch = vt.Pipeline().rmsbin(5, bintimes_min).run_batch(lcs)
print(batch.vars)
```

---

### `chi2` — Chi-squared statistic

**Syntax**

```python
cmd.chi2(maskpoints=None)
```

**Description**

Compute χ²/dof for the light curve relative to the error-weighted mean magnitude. A value much greater than 1 indicates the formal photometric uncertainties under-predict the observed scatter, signalling either real variability or under-estimated errors. The light curve passed to subsequent commands is unchanged.

CLI equivalent: [`-chi2`](../../cli/statistics.md#-chi2).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included. |

**Output**

Suffix `N` is the 0-indexed pipeline command position:

| Column | Description |
|--------|-------------|
| `Chi2_N` | χ²/dof of the light curve relative to its error-weighted mean. |
| `Weighted_Mean_Mag_N` | Error-weighted mean magnitude. |

**Examples**

```python
# Batch: chi-squared for all example light curves
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().chi2().run_batch(lcs)
print(batch.vars[["Name", "Chi2_0", "Weighted_Mean_Mag_0"]])
```

---

### `chi2bin` — Binned chi-squared

**Syntax**

```python
cmd.chi2bin(nbin, bintimes, maskpoints=None)
```

**Description**

Same idea as `rmsbin` but reports χ²/dof rather than RMS at each binning timescale. With pure white noise, the binned uncertainties shrink as `1/sqrt(N)` and the binned χ² stays near 1; rising χ² with bin size signals red noise.

`bintimes` are half-widths in **minutes**. The light curve passed to subsequent commands is unchanged.

CLI equivalent: [`-chi2bin`](../../cli/statistics.md#-chi2bin).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `nbin` | `int` | Number of filters. |
| `bintimes` | list of `float` | Filter half-widths in minutes; one entry per filter. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included. |

**Output**

For each binning timescale `T_i` (in minutes) and command index `N`, vartools emits a `Chi2Bin_<T_i>_N` column and a `Weight_Mean_Mag_Bin_<T_i>_N` column. The timescale tag is formatted the same way as for [`rmsbin`](#rmsbin-binned-rms) (e.g. `60.0` minutes becomes `Chi2Bin_60.0_0`); choose well-separated bin times to avoid duplicate column names.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
bintimes_min = [5.0, 10.0, 60.0, 1440.0, 14400.0]
batch = vt.Pipeline().chi2bin(5, bintimes_min).run_batch(lcs)
print(batch.vars)
```

---

### `stats` — Generic statistics

**Syntax**

```python
cmd.stats(variables, statistics, maskpoints=None)
```

**Description**

Compute one or more general statistics on one or more light-curve vectors (e.g. `t`, `mag`, `err`, or any user-defined variable). Every requested statistic is computed for every listed variable, producing a `STATS_<var>_<STAT>_N` column for each combination. Useful for downstream variable references (e.g. computing `tspan = STATS_t_MAX_0 - STATS_t_MIN_0`).

`variables` and `statistics` may each be either a comma-separated string or a Python list of strings. Available statistics include `mean`, `weightedmean`, `median`, `wmedian`, `stddev`, `meddev`, `medmeddev`, `MAD`, `kurtosis`, `skewness`, `pct<f>` / `wpct<f>` (any percentile from 0 to 100), `max`, `min`, and `sum`.

CLI equivalent: [`-stats`](../../cli/statistics.md#-stats).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `variables` | `str` or list of `str` | Variable name(s) to compute statistics on. List form is joined with commas before being passed to the CLI. |
| `statistics` | `str` or list of `str` | Statistic name(s); see the table below. List form is joined with commas. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` contribute. |

**Available statistics**

| String | Description |
|--------|-------------|
| `mean` | Arithmetic mean. |
| `weightedmean` | Mean weighted by `1/σ²`. |
| `median` | Median. |
| `wmedian` | Median weighted by light-curve uncertainties. |
| `stddev` | Standard deviation about the mean. |
| `meddev` | Standard deviation about the median. |
| `medmeddev` | Median absolute deviation from the median. |
| `MAD` | `1.483 × medmeddev` (matches stddev for a Gaussian distribution at large `N`). |
| `kurtosis`, `skewness` | Higher moments. |
| `pct<f>` | The `<f>`-th percentile (`0 < f < 100`), e.g. `pct25`. |
| `wpct<f>` | Weighted percentile using the light-curve uncertainties. |
| `max`, `min` | Maximum (`pct100`) and minimum (`pct0`). |
| `sum` | Sum of the elements. |

**Output**

Per variable `V`, statistic `S`, and command index `N`:

| Column | Description |
|--------|-------------|
| `STATS_V_S_N` | Value of statistic `S` computed on variable `V`. The statistic name is upper-cased in the column (e.g. `STATS_mag_MEAN_0`, `STATS_t_MAX_0`). |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3")

# Compute percentile and distribution statistics after adding Gaussian noise
pipe = (vt.Pipeline()
        .expr("mag2=mag+0.01*gauss()")
        .stats(
            ["mag", "mag2"],
            ["mean", "weightedmean", "median", "stddev", "MAD",
             "kurtosis", "skewness", "pct10", "pct90", "max", "min"],
        ))
result = pipe.run(lc)
print(result.vars["STATS_mag_MEAN_1"])
print(result.vars["STATS_mag_MEDIAN_1"])
print(result.vars["STATS_mag2_STDDEV_1"])
```

---

### `autocorrelation` — Autocorrelation function

**Syntax**

```python
cmd.autocorrelation(start, stop, step, save_result=True, maskpoints=None)
```

**Description**

Compute the discrete autocorrelation function (DACF) of the magnitude series following [Edelson and Krolik (1988)](https://ui.adsabs.harvard.edu/abs/1988ApJ...333..646E/abstract). The DACF is sampled at lags from `start` to `stop` in steps of `step` (all in days). Unlike the original Edelson and Krolik formulation, the formal measurement uncertainties are used in the denominator rather than the variance, which avoids imaginary values when errors are over-estimated; precede with `-changeerror` (in the same Pipeline) to recover the variance-based form.

The autocorrelation output file is **always** written to disk; `save_result=False` only suppresses Python capture. The file in that case is written to a temporary directory and discarded after the run.

CLI equivalent: [`-autocorrelation`](../../cli/statistics.md#-autocorrelation).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `start`, `stop`, `step` | `float`, `str`, numpy array, `PerLC`, or `pd.Series` | Lag range and step size (days). |
| `save_result` | `bool`, `str`, or `Output` | Auxiliary file output. `True` (default) captures as `result.files["autocorrelation_result_N"]`; a path string writes to that directory without capturing; `Output(path, capture=True)` does both. See [Auxiliary output files](index.md#auxiliary-output-files) and the note below. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included. |

!!! note "File is always written"
    The autocorrelation output file is always written to disk — `autocorrelation` has no option to suppress the write. Setting `save_result=False` only suppresses Python capture; the file is still written to a temp directory and discarded after the run completes.

**Output**

The command emits no per-LC scalar columns; the autocorrelation function is delivered through the auxiliary output file:

| File key | Description |
|----------|-------------|
| `result.files["autocorrelation_result_N"]` | DataFrame: time-lag (days) vs. autocorrelation. In a batch run this becomes a list of DataFrames, one per light curve. |

**References**

[Edelson, R.A. & Krolik, J.H. 1988](https://ui.adsabs.harvard.edu/abs/1988ApJ...333..646E/abstract), ApJ, 333, 646.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Default (save_result=True): ACF captured into result.files
result = vt.Pipeline().autocorrelation(0.0, 10.0, 0.05).run(lc)
acf = result.files["autocorrelation_result_0"]   # pd.DataFrame: time-lag vs autocorrelation

# save_result=False: file written to temp dir but not captured
result = vt.Pipeline().autocorrelation(0.0, 10.0, 0.05, save_result=False).run(lc)
# result.files has no "autocorrelation_result_0"

# Write to a specific directory and capture (Mode 2)
from pyvartools import Output
result = (vt.Pipeline()
        .autocorrelation(0.0, 10.0, 0.05,
                        save_result=Output("EXAMPLES/OUTDIR1", capture=True))).run(lc)
acf = result.files["autocorrelation_result_0"]   # from EXAMPLES/OUTDIR1/

# Batch — result.files["autocorrelation_result_0"] is a list of DataFrames
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]
batch = vt.Pipeline().autocorrelation(0.0, 10.0, 0.05).run_batch(lcs)
acfs = batch.files["autocorrelation_result_0"]   # list of DataFrames, one per LC
```

![Discrete autocorrelation function for EXAMPLES/2](../../assets/examples/autocorrelation_ex1.png)

---

### `Jstet` — Stetson J-statistic

**Syntax**

```python
cmd.Jstet(timescale, dates=None, skipnormalize=False, maskpoints=None)
```

Exactly one of `dates=` or `skipnormalize=True` must be given.

**Description**

Compute Stetson's J variability index, the L statistic, and the kurtosis of the residuals. J measures time-correlated variability by pairing observations that fall within `timescale` of each other (in the same time units as the light curve's time column); pairs with consistent sign of the residual contribute positively, opposite-sign pairs negatively. The second argument selects how the reported J / L are normalised:

- `dates="path/to/dates_file"` (legacy / survey-wide mode) — the file lists JDs of *every possible observation* in the survey; vartools computes `weight_max` once from that schedule and the reported J equals `J_stetson * (sum_w / weight_max)`. This multiplier downweights LCs missing observations relative to the full schedule. Useful for cross-LC comparison within a single survey; misleading when LCs come from different surveys / cadences.
- `skipnormalize=True` — skip the `(sum_w / weight_max)` rescaling entirely and report Stetson's original J and L. Use this when comparing across surveys, or when you want the textbook definition.

CLI equivalent: [`-Jstet`](../../cli/statistics.md#-jstet).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `timescale` | `float` | Time in the LC's time units that distinguishes "near" (correlated) from "far" (uncorrelated) observation pairs. |
| `dates` | `str` or `None` | Path to a survey-wide dates file (see Description). Mutually exclusive with `skipnormalize`. |
| `skipnormalize` | `bool` | If `True`, skip the survey-completeness rescaling and report Stetson's original J / L. Mutually exclusive with `dates`. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` are included. |

**Output**

Suffix `N` is the 0-indexed pipeline command position:

| Column | Description |
|--------|-------------|
| `Jstet_N` | Stetson's J variability index (rescaled when `dates` is used; original Stetson J when `skipnormalize=True`). |
| `Kurtosis_N` | Kurtosis of the residuals from the mean. |
| `Lstet_N` | Stetson's L statistic = `J × Kurtosis` (rescaled or original, matching J). |

**References**

[Stetson, P.B. 1996](https://ui.adsabs.harvard.edu/abs/1996PASP..108..851S/abstract), PASP, 108, 851.

**Examples**

```python
# Survey-wide mode -- uses a dates file to compute the cross-LC weight_max.
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().Jstet(0.5, dates="EXAMPLES/dates_tfa").run_batch(lcs)
print(batch.vars[["Name", "Jstet_0", "Kurtosis_0", "Lstet_0"]])

# Textbook mode -- Stetson's original J / L, no dates file needed.
batch2 = vt.Pipeline().Jstet(0.5, skipnormalize=True).run_batch(lcs)
print(batch2.vars[["Name", "Jstet_0", "Kurtosis_0", "Lstet_0"]])
```

---

### `alarm` — Alarm statistic

**Syntax**

```python
cmd.alarm(maskpoints=None)
```

**Description**

Compute the alarm variability statistic of [Tamuz, Mazeh and North (2006)](https://ui.adsabs.harvard.edu/abs/2006MNRAS.367.1521T/abstract). The alarm is a detection statistic for coherent signals: long runs of consecutive positive or negative residuals from the mean are penalised more heavily than randomly distributed deviations of the same RMS, making it sensitive to time-correlated structure that low-order moments may miss.

CLI equivalent: [`-alarm`](../../cli/statistics.md#-alarm).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` contribute. |

**Output**

Suffix `N` is the 0-indexed pipeline command position:

| Column | Description |
|--------|-------------|
| `Alarm_N` | The alarm statistic. |

**References**

[Tamuz, O., Mazeh, T. and North, P. 2006](https://ui.adsabs.harvard.edu/abs/2006MNRAS.367.1521T/abstract), MNRAS, 367, 1521.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = lc.alarm()
print(result.vars["Alarm_0"])
```

---

### `vonNeumann` — von Neumann ratio

**Syntax**

```python
cmd.vonNeumann(weighted=False, maskpoints=None)
```

**Description**

Compute the von Neumann (1941) ratio `η = δ² / s²`, where `δ² = (1/(N−1)) · Σᵢ (yᵢ₊₁ − yᵢ)²` is the mean-square successive difference and `s² = (1/N) · Σᵢ (yᵢ − ȳ)²` is the variance. For uncorrelated Gaussian noise `E[η] = 2` (variance ≈ 4/N); smoothly varying (positively correlated) signals drive η well below 2; anti-correlated (alternating) signals push η above 2. Useful as a variability indicator for sparse and unevenly sampled photometric time series.

The light curve is time-sorted automatically before the calculation.

CLI equivalent: [`-vonNeumann`](../../cli/statistics.md#-vonneumann).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `weighted` | `bool` | If `True`, use inverse-variance weighting: per-point weights `wᵢ = 1/σᵢ²` enter the variance and pairwise weights `w_pair_i = 1/(σᵢ² + σᵢ₊₁²)` enter the mean-square successive difference. The weighted ratio is `η_w = (2N/(N−1)) · Σ w_pair_i (yᵢ₊₁ − yᵢ)² / Σ wᵢ (yᵢ − ȳ_w)²`; the `2N/(N−1)` prefactor restores `E[η_w] = 2` for white noise regardless of the σ distribution. For homoscedastic σ the weighted form reduces exactly to the unweighted form. Points with NaN / non-positive uncertainty are dropped. |
| `maskpoints` | `str` or `None` | Name of a mask variable; only points with `maskvar > 0` contribute. |

**Output**

Suffix `N` is the 0-indexed pipeline command position:

| Column | Description |
|--------|-------------|
| `VonNeumann_Ratio_N` | The von Neumann ratio η. |

**References**

[von Neumann, J. 1941](https://www.jstor.org/stable/2235951), Annals of Mathematical Statistics, 12, 367. For astronomical applications see [Sokolovsky, K. V., et al. 2017](https://ui.adsabs.harvard.edu/abs/2017MNRAS.464..274S/abstract), MNRAS, 464, 274.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
# Unweighted: eta near 0.026 (much less than 2) reflects strong correlation.
result = lc.vonNeumann()
print(round(result.vars["VonNeumann_Ratio_0"], 5))

# Weighted variant.
result = lc.vonNeumann(weighted=True)
print(round(result.vars["VonNeumann_Ratio_0"], 5))
```

---

### `percentileratios` — Robust scatter ratios

**Syntax**

```python
cmd.percentileratios(percentilepairs=None, maskpoints=None)
```

**Description**

Compute robust scatter statistics from the magnitude distribution. For each pair of percentiles `(p, q)` with `0 < p < q < 100`, the command emits two statistics per light curve:

```
amp_p_q  = pct(q) - pct(p)
asym_p_q = (pct(q) - median) / (median - pct(p))
```

plus one additional statistic that does not depend on the pair list:

```
medmeddev_over_stddev = median(|x - median(x)|) / stddev(x)
```

For any symmetric distribution `asym → 1.0`; positively-skewed distributions (heavy upper tail) produce `asym > 1` and negatively-skewed distributions produce `asym < 1`. For independent Gaussian noise `medmeddev/stddev → 0.6745` in the large-N limit.

Percentile interpolation matches the [`stats`](#stats-generic-statistics) command, so values are directly comparable to the corresponding `pct(p)` columns from `stats`. NaN magnitudes are dropped before any statistic is computed; light curves with fewer than two finite magnitudes, and ratios with a zero denominator, produce NaN outputs.

CLI equivalent: [`-percentileratios`](../../cli/statistics.md#-percentileratios).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `percentilepairs` | sequence of `(p, q)` pairs, or `None` | Percentile pairs to use. Defaults to `[(5, 95), (1, 99)]` when `None`. Each pair must satisfy `0 < p, q < 100` and `p != q`; pairs with `p > q` are silently canonicalized to `p < q`; duplicate pairs (after canonicalization) are rejected. Floating-point percentiles are accepted (e.g. `(2.5, 97.5)`). |
| `maskpoints` | `str` or `None` | Name of a light-curve vector; only points with `maskvar > 0` are included. The median, stddev, MAD, and all percentile statistics are computed only over the masked-in subset. |

**Output**

Suffix `N` is the 0-indexed pipeline command position. The `p` and `q` values are formatted with two decimal places in the column names (e.g. `PCT5.00`, `PCT97.50`):

| Column | Description |
|--------|-------------|
| `PERCENTILERATIOS_amp_PCTp_PCTq_N` | `pct(q) - pct(p)` for pair `(p, q)`. |
| `PERCENTILERATIOS_asym_PCTp_PCTq_N` | `(pct(q) - median) / (median - pct(p))` for pair `(p, q)`. |
| `PERCENTILERATIOS_medmeddev_over_stddev_N` | `median(|x - median(x)|) / stddev(x)`. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Defaults (5:95 and 1:99 pairs).
result = lc.percentileratios()
print(round(result.vars["PERCENTILERATIOS_asym_PCT5.00_PCT95.00_0"], 4))

# Custom pairs incl. floating-point percentile; 95:5 auto-swaps to 5:95.
result = lc.percentileratios(percentilepairs=[(10, 90), (2.5, 97.5), (95, 5)])
print(round(result.vars["PERCENTILERATIOS_amp_PCT10.00_PCT90.00_0"], 4))
print(round(result.vars["PERCENTILERATIOS_amp_PCT2.50_PCT97.50_0"], 4))
print(round(result.vars["PERCENTILERATIOS_amp_PCT5.00_PCT95.00_0"], 4))
```

---

### `beyondNsigma` — Fraction beyond N sigma

**Syntax**

```python
cmd.beyondNsigma(Nvalues=None, useMAD=False, maskpoints=None)
```

**Description**

For each light curve and each `N` in `Nvalues`, emit two fractions:

```
frac_above_N = #{ x : x > median + N*sigma } / N_rej
frac_below_N = #{ x : x < median - N*sigma } / N_rej
```

where `N_rej` is the number of finite magnitudes after NaN rejection. Comparisons are strict (`>` and `<`).

By default `sigma` is the sample standard deviation. When `useMAD=True`, `sigma` is taken to be `1.483 * median(|x - median(x)|)` instead — the Gaussian-consistent calibration of the MAD. The MAD-based scale is robust to heavy tails or outliers: outliers inflate the stddev and widen the threshold, masking themselves; using MAD recovers a tighter threshold that correctly flags the outliers.

The `N=1` instance corresponds to the `Beyond1Std` feature of [Nun et al. 2015](https://arxiv.org/abs/1506.00010) (the FATS package), generalized here to an arbitrary list of `N` values and to a choice of stddev or MAD scale.

NaN magnitudes are dropped; LCs with fewer than two finite magnitudes produce NaN outputs. When `sigma == 0`, the fractions are reported as zero.

CLI equivalent: [`-beyondNsigma`](../../cli/statistics.md#-beyondnsigma).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `Nvalues` | sequence of `float`, or `None` | `N` values to evaluate. Defaults to `[1.0, 3.0, 5.0]` when `None`. Each value must be strictly positive; duplicates are rejected at construction time. Floating-point values are accepted. |
| `useMAD` | `bool` | If `True`, use `1.483 * MAD` instead of stddev. Default `False`. |
| `maskpoints` | `str` or `None` | Name of a light-curve vector; only points with `maskvar > 0` are included. The median, sigma, threshold counts, and the `N_rej` denominator are all computed over the masked-in subset. |

**Output**

Suffix `N` is the 0-indexed pipeline command position; `X.XX` is the N value with two decimal places (e.g. `N1.00`, `N2.50`):

| Column | Description |
|--------|-------------|
| `BEYONDNSIGMA_frac_above_NX.XX_N` | Fraction of magnitudes with `x > median + N*sigma`. |
| `BEYONDNSIGMA_frac_below_NX.XX_N` | Fraction of magnitudes with `x < median - N*sigma`. |

**Examples**

```python
import numpy as np

# Defaults (N = 1, 3, 5) on a real light curve.
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = lc.beyondNsigma()
print(round(result.vars["BEYONDNSIGMA_frac_above_N1.00_0"], 4))
print(round(result.vars["BEYONDNSIGMA_frac_below_N1.00_0"], 4))

# Custom float N values with the MAD-based robust scale.
result = lc.beyondNsigma(Nvalues=[0.5, 1.0, 1.5], useMAD=True)
print(round(result.vars["BEYONDNSIGMA_frac_above_N0.50_0"], 4))
print(round(result.vars["BEYONDNSIGMA_frac_above_N1.00_0"], 4))

# Synthetic Gaussian noise -> frac_above_N1 should be near 0.1587.
rng = np.random.default_rng(0)
n = 5000
gauss = vt.LightCurve.from_arrays(
    np.linspace(0, 30, n),
    rng.normal(0.0, 1.0, n),
    np.full(n, 1.0),
    name="gauss",
)
result = gauss.beyondNsigma()
above_1 = result.vars["BEYONDNSIGMA_frac_above_N1.00_0"]
print(f"frac_above_N1 = {above_1:.4f}  (Gaussian expectation: 0.1587)")
```

---
