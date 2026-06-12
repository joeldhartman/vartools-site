# Statistics

Commands for computing variability and scatter statistics on light curves.

---

## `-rms`

```
-rms
    ["maskpoints" maskvar]
```

Calculate the RMS of the light curves. The output includes the RMS, the mean magnitude, the expected RMS (derived from the formal photometric uncertainties), and the number of points in the light curve.

Python equivalent: [`rms`](../python/commands/statistics.md#rms-root-mean-square).

**Parameters**

- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included in the calculation; all others are excluded.

**Examples**

**Example 1.** Calculate the mean magnitude, RMS, and expected RMS based on the formal magnitude uncertainties for all light curves in a list file.

```bash
vartools -l EXAMPLES/lc_list -header -rms
```

Output:
```
#Name Mean_Mag_0 RMS_0 Expected_RMS_0 Npoints_0
EXAMPLES/1   ...
EXAMPLES/2   ...
...EXAMPLES/10  ...
```

---

## `-rmsbin`

```
-rmsbin
    Nbin bintime1...bintimeN
    ["maskpoints" maskvar]
```

Calculate the RMS after applying a moving mean filter to the light curves. Similar to [`-chi2bin`](statistics.md#-chi2bin), this measures the correlated (red) noise component by binning on specified timescales. `Nbin` filters are applied, each producing a separate RMS estimate. The note that light curves passed to the next command are **unchanged** by this command.

Python equivalent: [`rmsbin`](../python/commands/statistics.md#rmsbin-binned-rms).

**Parameters**

- `Nbin` — Number of time bins (filters) to apply.
- `bintime1...bintimeN` — Half-widths of each moving mean filter, in **minutes**. The full filter window for filter *i* is `2.0 * bintimei`.
- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included.

**Examples**

**Example 1.** Apply moving-mean filters to the light curves and compute statistical measures for each filter. The filters operate by replacing each point in the light curve with the mean of all points that are within the specified number of minutes of that point. This example uses five time-window filters (5.0, 10.0, 60.0, 1440.0, and 14400.0 minutes). The output table displays computed RMS values alongside expected RMS values assuming white noise for each binning window. As the filtering window increases, RMS values generally decrease.

```bash
vartools -l EXAMPLES/lc_list -header -rmsbin 5 5.0 10.0 60.0 1440.0 14400.0
```

---

## `-chi2`

```
-chi2
    ["maskpoints" maskvar]
```

Calculate chi-squared per degree of freedom (χ²/dof) for the light curves. The output includes χ²/dof and the error-weighted mean magnitude.

Python equivalent: [`chi2`](../python/commands/statistics.md#chi2-chi-squared-statistic).

**Parameters**

- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included.

**Examples**

**Example 1.** Calculate chi-squared per degree of freedom and the weighted mean magnitude for all light curves in a list.

```bash
vartools -header -l EXAMPLES/lc_list -chi2
```

Output:
```
#Name Chi2_0 Weighted_Mean_Mag_0
EXAMPLES/1  34711.71793  10.24430
EXAMPLES/2   1709.50065  10.11178
EXAMPLES/3     27.06322  10.16684
EXAMPLES/4      5.19874  10.35137
EXAMPLES/5      8.26418  10.43932
EXAMPLES/6      3.94650  10.52748
EXAMPLES/7     10.39941  10.56951
EXAMPLES/8      4.19887  10.61132
EXAMPLES/9      2.67020  10.73129
EXAMPLES/10      3.72218  10.87763
```

---

## `-chi2bin`

```
-chi2bin
    Nbin bintime1...bintimeNbin
    ["maskpoints" maskvar]
```

Calculate χ²/dof after applying a moving mean filter to the light curves. As with `-rmsbin`, the light curves passed to the next command are unchanged. `Nbin` filters are used, producing `Nbin` separate estimates of χ²/dof and the error-weighted mean.

Python equivalent: [`chi2bin`](../python/commands/statistics.md#chi2bin-binned-chi-squared).

**Parameters**

- `Nbin` — Number of filters.
- `bintime1...bintimeNbin` — Half-widths of the moving mean filters, in **minutes**. The full window for filter *i* is `2.0 * bintimei`.
- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included.

**Examples**

**Example 1.** Apply moving-mean filters to light curves and calculate chi-squared per degree of freedom along with the weighted mean magnitude for each filter. This example uses 5 filters with durations of 5.0, 10.0, 60.0, 1440.0, and 14400.0 minutes. As formal errors decrease according to white noise expectations, chi-squared values increase with larger filter sizes when red noise is present.

```bash
vartools -l EXAMPLES/lc_list -header -chi2bin 5 5.0 10.0 60.0 1440.0 14400.0
```

---

## `-stats`

```
-stats
    var1,var2,... stats1,stats2,...
    ["maskpoints" maskvar]
```

Compute one or more general statistics on one or more light-curve vectors (e.g., `t`, `mag`, `err`, or any user-defined variable). Every requested statistic is computed for every listed variable.

Python equivalent: [`stats`](../python/commands/statistics.md#stats-generic-statistics).

**Parameters**

- `var1,var2,...` — Comma-separated list of variable names to compute statistics on.
- `stats1,stats2,...` — Comma-separated list of statistics to compute. Every statistic is computed for every variable.
- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are used in the calculations.

**Available statistics strings**

| String | Description |
|--------|-------------|
| `mean` | Arithmetic mean |
| `weightedmean` | Mean weighted by 1/σ² |
| `median` | Median |
| `wmedian` | Median weighted by light curve uncertainties |
| `stddev` | Standard deviation with respect to the mean |
| `meddev` | Standard deviation with respect to the median |
| `medmeddev` | Median of the absolute deviations from the median |
| `MAD` | 1.483 × medmeddev. Equals stddev for a Gaussian distribution in the large-N limit |
| `kurtosis` | Kurtosis |
| `skewness` | Skewness |
| `pct%f` | The %f-th percentile, where %f is a floating point number between 0 and 100 (e.g., `pct25`) |
| `wpct%f` | Percentile including light curve uncertainties as weights |
| `max` | Maximum value (equivalent to `pct100`) |
| `min` | Minimum value (equivalent to `pct0`) |
| `sum` | Sum of all elements in the vector |

**Example**

```bash
vartools -l EXAMPLES/lc_list -stats mag,err mean,stddev,MAD
```

**Examples**

**Example 1.** Calculate various statistical measures for light curve magnitudes and magnitudes after adding Gaussian noise. The `-expr` parameter defines a new variable with noise added, while `-stats` specifies which variables and statistics to compute. Percentile statistics (`pct##`) represent the specified percentile values.

```bash
vartools -i EXAMPLES/3 \
    -oneline \
    -expr 'mag2=mag+0.01*gauss()' \
    -stats mag,mag2 \
        mean,weightedmean,median,stddev,meddev,medmeddev,MAD,kurtosis,skewness,pct10,pct20,pct80,pct90,max,min,sum
```

---

## `-alarm`

**Syntax**
```
-alarm
    ["maskpoints" maskvar]
```

**Description**

Calculate the alarm variability statistic for each light curve. This statistic is designed to detect time-correlated variability — long runs of consecutive positive or negative residuals are penalised more heavily than randomly distributed deviations of the same RMS, making the alarm sensitive to coherent signals that other low-order moments may miss.

Python equivalent: [`alarm`](../python/commands/statistics.md#alarm-alarm-statistic).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"maskpoints" maskvar` | Optional. Only points with `maskvar > 0` contribute. |

**Output columns**: `Alarm_N`.

**References**

Cite [Tamuz, Mazeh, and North 2006](https://ui.adsabs.harvard.edu/abs/2006MNRAS.367.1521T/abstract), MNRAS, 367, 1521.

**Examples**

**Example 1.** Compute the alarm statistic for `EXAMPLES/2`.

```bash
vartools -i EXAMPLES/2 -header -alarm
```

---

## `-Jstet`

```
-Jstet
    timescale <"skipnormalize" | dates> ["maskpoints" maskvar]
```

Calculate Stetson's J statistic, L statistic, and the kurtosis for each light curve. The J statistic measures time-correlated variability by comparing pairs of observations that are close in time.

Python equivalent: [`Jstet`](../python/commands/statistics.md#jstet-stetson-j-statistic).

**Parameters**

- `timescale` — Time in minutes that distinguishes between "near" (correlated) and "far" (uncorrelated) observation pairs.
- The second positional argument selects the normalisation. It is **either**
  - `dates` — file containing JDs for *every possible observation* in the survey, in the first column. `weight_max` is computed once from that schedule, and the reported J is `J_stetson * (sum_w_actual / weight_max)` — a multiplier that downweights LCs missing observations relative to the full schedule. Useful within a single survey; misleading across surveys with different cadences. (This is the vartools historical default and differs from Stetson's original definition.)
  - **or** the literal keyword `"skipnormalize"` — skip the rescaling and report Stetson's original `J` and `L = J * Kurtosis`. Use this when comparing across surveys, or when you want the textbook definition.
- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included.

**Citation:** [Stetson, P.B. 1996](https://ui.adsabs.harvard.edu/abs/1996PASP..108..851S/abstract), PASP, 108, 851.

**Examples**

**Example 1.** Calculate Stetson's J statistic, L statistic, and kurtosis for all light curves in a list, using 0.5 days to distinguish between "near" and "far" observations.

```bash
vartools -l EXAMPLES/lc_list -header \
    -Jstet 0.5 EXAMPLES/dates_tfa
```

Output:
```
#Name Jstet_0 Kurtosis_0 Lstet_0
EXAMPLES/1  98.13279   0.96779  94.97154
EXAMPLES/2  30.19309   0.94719  28.59852
EXAMPLES/3   0.65597   0.92816   0.60885
EXAMPLES/4   0.34402   0.84500   0.29070
EXAMPLES/5   0.58730   0.92120   0.54102
EXAMPLES/6   0.34455   0.93794   0.32317
EXAMPLES/7   0.41754   0.92501   0.38623
EXAMPLES/8   0.46381   0.96124   0.44583
EXAMPLES/9   0.22075   0.80997   0.17880
EXAMPLES/10   0.25784   0.92806   0.23929
```

**Example 2.** Same calculation, but report Stetson's original `J` / `L` (no `sum_w / weight_max` rescaling).

```bash
vartools -l EXAMPLES/lc_list -header \
    -Jstet 0.5 skipnormalize
```

The values are larger than in Example 1 because they aren't downscaled by the `sum_w / weight_max < 1` survey-completeness factor.

---

## `-autocorrelation`

```
-autocorrelation
    start stop step outdir ["maskpoints" maskvar]
```

Calculate the discrete auto-correlation function ([Edelson and Krolik 1988](https://ui.adsabs.harvard.edu/abs/1988ApJ...333..646E/abstract), ApJ, 333, 646) for each light curve. The results are written to files in `outdir` with the suffix `.autocorr` (i.e., `outdir/$basename.autocorr`).

Python equivalent: [`autocorrelation`](../python/commands/statistics.md#autocorrelation-autocorrelation-function).

!!! note "Cross-reference"
    For period-finding using autocorrelation-based methods, see the [Period Finding](period-finding.md) page.

**Parameters**

- `start` — Start time for sampling the autocorrelation, in days.
- `stop` — Stop time for sampling the autocorrelation, in days.
- `step` — Step size for sampling, in days.
- `outdir` — Directory where output `.autocorr` files are written.
- `"maskpoints" maskvar` — Optional. Only points with `maskvar > 0` are included.

**Notes**

Rather than using the variance in the denominator (as in the Edelson and Krolik formula), the formal uncertainty is used. This avoids imaginary numbers when measurement errors are overestimated. To use the variance in the denominator instead, issue `-changeerror` before calling this command.

Due to binning, when the variance is used in the denominator the autocorrelation function may be smaller than 1 unless the time step is less than the minimum time difference between consecutive measurements.

**Citation:** [Edelson, R.A. & Krolik, J.H. 1988](https://ui.adsabs.harvard.edu/abs/1988ApJ...333..646E/abstract), ApJ, 333, 646.

**Examples**

**Example 1.** Compute the discrete auto-correlation function (DACF) of a single light curve spanning time lags from 0 to 10.0 days with a step of 0.05 days. Output is written to `EXAMPLES/OUTDIR1/2.autocorr`.

```bash
vartools -i EXAMPLES/2 -header \
    -autocorrelation 0.0 10. 0.05 EXAMPLES/OUTDIR1
```

Output:
```
#Name
EXAMPLES/2
```

![Discrete autocorrelation function for EXAMPLES/2](../assets/examples/autocorrelation_ex1.png)

---

## `-vonNeumann`

**Syntax**
```
-vonNeumann
    ["weighted"]
    ["maskpoints" maskvar]
```

**Description**

Calculate the von Neumann (1941) ratio `η = δ² / s²` for each light curve, where `δ² = (1/(N−1)) · Σᵢ (yᵢ₊₁ − yᵢ)²` is the mean-square successive difference and `s² = (1/N) · Σᵢ (yᵢ − ȳ)²` is the variance. For uncorrelated Gaussian noise `E[η] = 2` (variance ≈ 4/N); smoothly varying (positively correlated) signals drive η well below 2, and anti-correlated (alternating) signals push η above 2. Widely used as a variability indicator for sparse and unevenly sampled photometric time series.

The statistic is order-dependent — the light curve is time-sorted automatically before the calculation (the parser sets `require_sort = 1`).

Python equivalent: [`vonNeumann`](../python/commands/statistics.md#vonneumann-von-neumann-ratio).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"weighted"` | Optional. Switch to the inverse-variance-weighted form: per-point weights `wᵢ = 1/σᵢ²` enter the variance and pairwise weights `w_pair_i = 1/(σᵢ² + σᵢ₊₁²)` enter the mean-square successive difference. The weighted ratio is computed as `η_w = (2N/(N−1)) · Σᵢ w_pair_i (yᵢ₊₁ − yᵢ)² / Σᵢ wᵢ (yᵢ − ȳ_w)²`; the `2N/(N−1)` prefactor restores `E[η_w] = 2` for white noise regardless of the σ distribution (a raw ratio-of-weighted-averages instead converges to `⟨w⟩/⟨w_pair⟩`, which equals 2 only for homoscedastic errors). For homoscedastic σ the weighted form reduces exactly to the unweighted form. Points with NaN magnitude (or NaN / non-positive uncertainty when weighted) are dropped. |
| `"maskpoints" maskvar` | Optional. Only points with `maskvar > 0` are included. |

The trailing keyword block is parsed in strict order (`weighted` before `maskpoints`); mis-ordering or duplicating keywords produces a command-syntax error.

**Output columns**: `VonNeumann_Ratio_N`.

**References**

Cite [von Neumann, J. 1941](https://www.jstor.org/stable/2235951), Annals of Mathematical Statistics, 12, 367; for astronomical applications see [Sokolovsky, K. V., et al. 2017](https://ui.adsabs.harvard.edu/abs/2017MNRAS.464..274S/abstract), MNRAS, 464, 274.

**Examples**

**Example 1.** Unweighted η for a strongly periodic light curve (η ≪ 2 indicates strong sample-to-sample correlation).

```bash
vartools -i EXAMPLES/2 -oneline -vonNeumann
```

**Example 2.** Inverse-variance-weighted form.

```bash
vartools -i EXAMPLES/2 -oneline -vonNeumann weighted
```

**Example 3.** Weighted η with a mask restricting the calculation to the first 30 days of the LC.

```bash
vartools -i EXAMPLES/2 -oneline \
    -expr 'mask=((t-t[0])<30)' \
    -vonNeumann weighted maskpoints mask
```


## `-percentileratios`

**Syntax**
```
-percentileratios
    ["percentilepairs" p1:q1,p2:q2,...,pN:qN]
    ["maskpoints" maskvar]
```

**Description**

Compute robust scatter statistics from the magnitude distribution. For each pair of percentiles `(p, q)` with `0 < p < q < 100`, two statistics are emitted per light curve:

```
amp_p_q  = pct(q) - pct(p)
asym_p_q = (pct(q) - median) / (median - pct(p))
```

plus one additional statistic that does not depend on the pair list:

```
medmeddev_over_stddev = median(|x - median(x)|) / stddev(x)
```

For any symmetric distribution the `asym` statistics tend to `1.0`; positively-skewed distributions (heavy upper tail) produce `asym > 1` and negatively-skewed distributions produce `asym < 1`. For independent Gaussian noise `medmeddev/stddev` tends to `0.6745` in the large-N limit, with smaller values indicating heavier tails and larger values indicating lighter tails or significant outliers.

Percentile interpolation matches the [`-stats`](#stats) command (the same `percentile()` helper in `statistics.c`), so values are directly comparable to the corresponding `pct(p)` columns from `-stats`. NaN magnitudes are dropped before any statistic is computed; light curves with fewer than two finite magnitudes, and ratios with a zero denominator (e.g. `median == pct(p)`, or `stddev == 0`), produce NaN outputs.

When the `maskpoints` keyword is given, the median, the stddev, the MAD, and all percentile statistics are computed only over points with `maskvar > 0`. The mask filter is applied alongside NaN rejection, before any statistic is computed.

Python equivalent: [`percentileratios`](../python/commands/statistics.md#percentileratios-robust-scatter-ratios).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"percentilepairs" p1:q1,p2:q2,...` | Optional. Comma-separated list of percentile pairs to use in place of the defaults `5:95,1:99`. Each pair must satisfy `0 < p, q < 100` and `p != q`; pairs given with `p > q` are silently canonicalized to `p < q`; duplicate pairs (after canonicalization) are rejected at parse time. Floating-point percentiles are accepted (e.g. `2.5:97.5`). |
| `"maskpoints" maskvar` | Optional. Name of a light-curve vector; only points with `maskvar > 0` are included in the calculation. The trailing keywords are parsed in strict order: `percentilepairs` must come before `maskpoints`. |

**Output columns**

| Column | Meaning |
|--------|---------|
| `PERCENTILERATIOS_amp_PCTp_PCTq_N` | `pct(q) - pct(p)` for pair `(p, q)`. |
| `PERCENTILERATIOS_asym_PCTp_PCTq_N` | `(pct(q) - median) / (median - pct(p))` for pair `(p, q)`. |
| `PERCENTILERATIOS_medmeddev_over_stddev_N` | `median(|x - median(x)|) / stddev(x)`. |

The `p` and `q` values are formatted with two decimal places in the column names (e.g. `PCT5.00`, `PCT97.50`), following the `-stats` convention. When referencing these columns as variables in `-expr`, replace `.` with `_` (e.g. `PERCENTILERATIOS_amp_PCT5_00_PCT95_00_N`); this substitution is handled by vartools' identifier parser.

**Examples**

**Example 1.** Defaults (`5:95` and `1:99` pairs) on EXAMPLES/2.

```bash
vartools -i EXAMPLES/2 -oneline -percentileratios
```

**Example 2.** Custom pairs with a mix of integer and floating-point percentiles. The `95:5` entry is canonicalized to `5:95` before column names are emitted.

```bash
vartools -i EXAMPLES/2 -oneline \
    -percentileratios percentilepairs 10:90,20:80,2.5:97.5,95:5
```

**Example 3.** A synthetic Gaussian LC: `asym_p_q ≈ 1` for any symmetric distribution and `medmeddev_over_stddev ≈ 0.6745` for independent Gaussian noise.

```bash
vartools -i EXAMPLES/2 -oneline \
    -expr 'mag=gauss()' \
    -percentileratios
```


## `-beyondNsigma`

**Syntax**
```
-beyondNsigma
    ["Nvalues" N1,N2,...,Nk]
    ["useMAD"]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, compute the fraction of magnitudes that lie more than `N*sigma` above the median and the fraction that lie more than `N*sigma` below the median, for a user-supplied list of `N` values:

```
frac_above_N = #{ x : x > median + N*sigma } / N_rej
frac_below_N = #{ x : x < median - N*sigma } / N_rej
```

where `N_rej` is the number of finite magnitudes after NaN rejection. Comparisons are strict (`>` and `<`).

By default `sigma` is the sample standard deviation. When the `useMAD` keyword is given, `sigma` is taken to be `1.483 * median(|x - median(x)|)` instead — the Gaussian-consistent calibration of the MAD. The MAD-based scale is robust to heavy tails or outliers: outliers inflate the stddev and widen the `N*sigma` threshold, masking themselves, while the MAD reflects the bulk's scale and the same thresholds correctly flag the outliers.

The `N=1` instance of this statistic corresponds to the `Beyond1Std` feature of [Nun et al. 2015](https://arxiv.org/abs/1506.00010) (the FATS package for variable-star feature engineering), generalized here to an arbitrary list of `N` values and to a choice of stddev or MAD scale.

NaN magnitudes are dropped before any statistic is computed; light curves with fewer than two finite magnitudes produce NaN outputs. When `sigma == 0` (degenerate distribution in which every magnitude equals the median) the fractions are reported as zero, since no point strictly exceeds a zero threshold.

When the `maskpoints` keyword is given, the median, sigma, threshold counts, and the `N_rej` denominator are all computed only over points with `maskvar > 0`. The mask filter is applied alongside NaN rejection, before any statistic is computed.

Python equivalent: [`beyondNsigma`](../python/commands/statistics.md#beyondnsigma-fraction-beyond-n-sigma).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"Nvalues" N1,N2,...,Nk` | Optional. Comma-separated list of `N` values to evaluate, replacing the defaults `1,3,5`. Each value must satisfy `N > 0`; duplicates are rejected at parse time. Floating-point values are accepted (e.g. `Nvalues 1.5,2.5,4.0`). |
| `"useMAD"` | Optional. If given, use `1.483 * MAD` as the scale instead of the sample standard deviation. |
| `"maskpoints" maskvar` | Optional. Name of a light-curve vector; only points with `maskvar > 0` are included in the calculation. |

The trailing keywords are parsed in strict order: `Nvalues`, then `useMAD`, then `maskpoints`.

**Output columns**

| Column | Meaning |
|--------|---------|
| `BEYONDNSIGMA_frac_above_NX.XX_M` | Fraction of magnitudes with `x > median + N*sigma`. |
| `BEYONDNSIGMA_frac_below_NX.XX_M` | Fraction of magnitudes with `x < median - N*sigma`. |

`X.XX` is the `N` value formatted with two decimal places (e.g. `N1.00`, `N2.50`) and `M` is the 0-indexed command position in the pipeline. When referencing these columns as variables in `-expr`, replace `.` with `_` (e.g. `BEYONDNSIGMA_frac_above_N1_00_M`); this substitution is handled by vartools' identifier parser.

**References**

Cite [Nun et al. 2015](https://arxiv.org/abs/1506.00010), arXiv:1506.00010 (the FATS package for variable-star feature engineering).

**Examples**

**Example 1.** Defaults (`N = 1, 3, 5`) on EXAMPLES/2.

```bash
vartools -i EXAMPLES/2 -oneline -beyondNsigma
```

**Example 2.** Custom floating-point N values with the MAD-based scale, more robust to heavy tails or outliers than the stddev-based default.

```bash
vartools -i EXAMPLES/2 -oneline \
    -beyondNsigma Nvalues 0.5,1.0,1.5 useMAD
```

**Example 3.** A synthetic Gaussian LC. For independent Gaussian noise, `frac_above_N1.00 ≈ frac_below_N1.00 ≈ 0.1587` (one-tailed `1 - Phi(1)`) and `frac_above_N3.00 ≈ frac_below_N3.00 ≈ 0.00135`.

```bash
vartools -i EXAMPLES/2 -oneline \
    -expr 'mag=gauss()' \
    -beyondNsigma
```


## `-slopestats`

**Syntax**
```
-slopestats
    ["bintime" B1,B2,...,Bk]
    ["binshift" binshift]
    ["threshold" T1,T2,...,Tj]
    ["maxgap" maxgap]
    ["useMAD"]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, compute per-pair slope statistics over consecutive points after time-sorting (and optionally after binning). For pairs of consecutive points `(t_i, m_i)`, `(t_{i+1}, m_{i+1})` the slope `s_i = (m_{i+1} - m_i) / (t_{i+1} - t_i)` is formed, and five statistics are reported per (LC, binsize) combination:

```
median_abs_dmdt = median(|s_i|)
max_abs_dmdt    = max(|s_i|)
mad_dmdt        = 1.483 * median(|s_i - median(s_i)|)
frac_above_T    = #{ s_i : s_i - <s> >  T*sigma } / N_pairs
frac_below_T    = #{ s_i : s_i - <s> < -T*sigma } / N_pairs
```

`<s>` is the mean of the slopes; deviations are mean-centered regardless of the choice of sigma flavor. Comparisons against `T*sigma` are strict (`>` and `<`). The 1.483 factor on `mad_dmdt` calibrates the median absolute deviation to the Gaussian standard deviation in the large-N limit.

By default `sigma` is the sample standard deviation of the slopes (normalized by `N_pairs - 1`, matching vartools' `stddev()`). When the `useMAD` keyword is given, `sigma` is `1.483 * median(|s_i - median(s_i)|)` instead (= `mad_dmdt`), which is more robust to heavy tails or outliers.

The `bintime` keyword takes a comma-separated list of bin sizes in **minutes** (assuming the light curve time axis is in days; the kernel divides each bintime by 1440 before binning). Each binsize produces its own column set, tagged in the column name as `_BTX.XX`. Within each bin, an unweighted average of `(t, m)` is taken, and consecutive-bin slopes are formed from those averages. Empty bins are skipped; singleton bins are kept. The `binshift` keyword (only valid in combination with `bintime`) shifts the first bin by a fraction of the binwidth: `t0_bin = t[0] - binshift * binsize`. Canonical use is `0 <= binshift < 1`.

The `maxgap` keyword (in the same time units as the LC, i.e. days) drops any consecutive pair whose time separation exceeds `maxgap`, suppressing spurious large slopes that span long observational gaps. When binning is in effect `maxgap` is applied to the binned light curve.

The `max_abs_dmdt` statistic corresponds to the `MaxSlope` feature of [Richards et al. 2011](https://ui.adsabs.harvard.edu/abs/2011ApJ...733...10R/abstract). The `frac_above_T*sigma` and `frac_below_T*sigma` statistics are slope-domain generalizations of the magnitude-domain `Beyond1Std` feature of the same paper, extended to a user-supplied list of `T` values and split into signed above/below counts. The `mad_dmdt` statistic is the slope-domain analog of the magnitude-domain median absolute deviation (here with the Gaussian-calibrated 1.483 factor).

NaN magnitudes are dropped before any binning or pair-formation step. If fewer than one pair survives the filter for a given binsize, the five stats are all reported as NaN for that binsize. When `sigma == 0` (e.g. all slopes equal), the threshold fractions are reported as zero while the median/max/MAD remain well-defined.

When the `maskpoints` keyword is given, the mask filter is applied alongside NaN rejection on the magnitudes, before any binning or pair-formation step.

**Expected values for Gaussian white noise.** For magnitudes `m_i ~ N(0, σ²)` iid with uniform spacing `dt`, the slopes `s_i = (m_{i+1} − m_i)/dt` are Gaussian with stddev `σ_s = sqrt(2)·σ/dt`. (Adjacent slopes have correlation `−1/2` because they share a magnitude, but the median/MAD/max statistics are leading-order insensitive to this correlation.) The large-N expectations are:

| Statistic | Expectation |
|-----------|-------------|
| `median_abs_dmdt` | `0.6745 · σ_s ≈ 0.9540 · σ/dt` |
| `mad_dmdt`        | `σ_s = sqrt(2) · σ/dt ≈ 1.4142 · σ/dt` |
| `max_abs_dmdt`    | `σ_s · sqrt(2·ln N_pairs) ≈ 2·sqrt(ln N_pairs) · σ/dt` (leading order) |
| `frac_above_T = frac_below_T` | `1 − Φ(T)` (e.g. `0.1587` at `T=1`, `0.00135` at `T=3`, `2.87×10⁻⁷` at `T=5`) |

The `mad_dmdt` formula is exact-in-the-limit by construction — the `1.483` factor is calibrated so that `1.483 · medmeddev(Gaussian) → σ`. The `max_abs_dmdt` expression is the leading order of the Gumbel limit law for the maximum of N independent Gaussians (Cramér 1946, *Mathematical Methods of Statistics*, eq. 28.6.13); a more accurate next-order asymptotic is `σ_s · ( sqrt(2·ln N_pairs) − (ln ln N_pairs + ln 4π) / (2·sqrt(2·ln N_pairs)) + γ / sqrt(2·ln N_pairs) )` with `γ ≈ 0.5772` the Euler–Mascheroni constant.

These expectations assume uniform sampling. For non-uniform `dt_i` the slope distribution is heteroskedastic with `stddev s_i = sqrt(2)·σ/dt_i`; `max_abs_dmdt` is then dominated by the smallest `dt_i` rather than the typical spacing, while `median_abs_dmdt` and `mad_dmdt` remain robust and reflect a typical `dt`.

Python equivalent: [`slopestats`](../python/commands/statistics.md#slopestats-per-pair-slope-statistics).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"bintime" B1,B2,...,Bk` | Optional. Comma-separated list of bin sizes in **minutes**. Each value must satisfy `B > 0`; duplicates are rejected at parse time. If omitted, no binning is performed. |
| `"binshift" binshift` | Optional. Fraction of the binwidth by which to shift the first bin. Canonical use is `0 <= binshift < 1`. Only valid in combination with `bintime`. |
| `"threshold" T1,T2,...,Tj` | Optional. Comma-separated list of `T` values for the threshold-fraction statistics. Defaults to `T = 3`. Each value must satisfy `T > 0`; duplicates are rejected at parse time. |
| `"maxgap" maxgap` | Optional. Drop consecutive pairs whose time separation exceeds `maxgap`, in the same units as the LC time axis (days). Must satisfy `maxgap > 0`. |
| `"useMAD"` | Optional. If given, use `1.483 * MAD` of the slopes as `sigma` instead of the sample standard deviation. |
| `"maskpoints" maskvar` | Optional. Name of a light-curve vector; only points with `maskvar > 0` are included in the calculation. |

The trailing keywords are parsed in strict order: `bintime`, `binshift`, `threshold`, `maxgap`, `useMAD`, `maskpoints`.

**Output columns**

| Column | Meaning |
|--------|---------|
| `SLOPESTATS_median_abs_dmdt[_BTX.XX]_M` | Median of `|s_i|`. |
| `SLOPESTATS_max_abs_dmdt[_BTX.XX]_M` | Maximum of `|s_i|`. |
| `SLOPESTATS_mad_dmdt[_BTX.XX]_M` | `1.483 * median(|s_i - median(s_i)|)`. |
| `SLOPESTATS_frac_above_TY.YY[_BTX.XX]_M` | Fraction of slopes with `s_i - <s> > T*sigma`. |
| `SLOPESTATS_frac_below_TY.YY[_BTX.XX]_M` | Fraction of slopes with `s_i - <s> < -T*sigma`. |

`Y.YY` is the threshold value formatted with two decimal places (e.g. `T3.00`, `T1.50`); `X.XX` is the bin size in minutes formatted with two decimal places (e.g. `BT5.00`, `BT60.00`). The `_BTX.XX` segment is omitted entirely when no `bintime` is given. `M` is the 0-indexed command position in the pipeline. When both threshold and bin appear, threshold is named first and bin second; all columns for a given binsize are emitted together (bin is the outer loop in the column registration).

**References**

Cite [Richards et al. 2011](https://ui.adsabs.harvard.edu/abs/2011ApJ...733...10R/abstract), ApJ, 733, 10.

**Examples**

**Example 1.** Defaults (threshold `T = 3`, no binning) on EXAMPLES/2.

```bash
vartools -i EXAMPLES/2 -oneline -slopestats
```

**Example 2.** Binning at 10 and 30 minutes, multiple thresholds, and a maximum-gap filter to suppress slopes that span long observational gaps.

```bash
vartools -i EXAMPLES/2 -oneline \
    -slopestats bintime 10,30 threshold 1,3 maxgap 0.5
```

**Example 3.** Half-bin alignment shift via `binshift` and the robust MAD-based scale via `useMAD`.

```bash
vartools -i EXAMPLES/2 -oneline \
    -slopestats bintime 10 binshift 0.5 useMAD
```

---

## `-CodyM`

**Syntax**
```
-CodyM "trendwindow" <"var" varname | "expr" exprstring | trendwindow>
    ["outlierwindow" <"var" varname | "expr" exprstring | outlierwindow>]
    ["sigclip" <"var" varname | "expr" exprstring | sigclip>]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, compute the flux-asymmetry statistic `M` of [Cody et al. 2014](https://ui.adsabs.harvard.edu/abs/2014AJ....147...82C/abstract) (their Equation 7). `M` measures whether a light curve is asymmetric with respect to reflection about the median magnitude:

```
M = (<d_10%> - d_med) / sigma_d
```

where `d_med` is the median of the long-term-detrended, outlier-filtered light curve, `sigma_d` is its standard deviation, and `<d_10%>` is the mean of the combined faintest-decile and brightest-decile magnitude values. For magnitude-valued light curves `M` moves in the positive direction for dipping signatures (asymmetric toward faint excursions) and in the negative direction for bursting signatures (asymmetric toward bright excursions); a value close to zero indicates a symmetric magnitude distribution. The sign convention is reversed for flux input.

The statistic is computed as follows. (1) Points with NaN magnitudes, and — when `maskpoints` is given — points whose mask variable is `<= 0`, are rejected. (2) A long-term trend is removed by subtracting a boxcar-mean smooth of full width `trendwindow` (in time-axis units). `M` is only sensitive to asymmetry on timescales shorter than roughly half the light-curve duration, so removing longer trends is necessary. (3) Outliers are rejected at the `sigclip`-sigma level (default `5`).

- **Two-stage scheme (paper-faithful):** when `outlierwindow` is given, outliers are identified on a separate residual formed by subtracting a short-timescale boxcar smooth of full width `outlierwindow` from the light curve. Real variability is largely removed in that residual, so only true glitches exceed the threshold; the genuine dips and bursts that `M` quantifies survive into the `M` calculation.
- **Single-stage scheme:** when `outlierwindow` is omitted, outliers are identified directly on the trend-detrended curve. Simpler, but a deep dip or burst can clip itself and bias `M` toward zero.

Setting `sigclip = 0` disables outlier rejection entirely.

(4) On the trend-detrended, outlier-filtered curve of `N'` points, `M` is evaluated using deciles of `round(0.1 * N')` points each. `M` and `d_10%` are reported as NaN when fewer than two points survive, when the curve is flat (`sigma_d = 0`), or when the two deciles would overlap; `d_med`, `sigma_d`, and `Npoints` remain meaningful in the flat / overlapping-decile cases.

`trendwindow`, `outlierwindow`, and `sigclip` each accept a fixed value, or `var` followed by the name of a light-curve-list variable, or `expr` followed by an analytic expression evaluated per light curve. Literal numeric values are validated at parse time (`trendwindow > 0`, `outlierwindow > 0`, `sigclip >= 0`); per-LC values from `var` / `expr` are validated at runtime and yield NaN for the affected light curve on a bad value.

Python equivalent: [`CodyM`](../python/commands/statistics.md#codym-flux-asymmetry-statistic-m).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"trendwindow" Wt` | Required. Boxcar full width for the long-term detrend, in the same units as the light-curve time axis. Must satisfy `Wt > 0`. Accepts `var` / `expr` per-LC sourcing. |
| `"outlierwindow" Wo` | Optional. Short-timescale boxcar full width that enables the two-stage outlier-rejection scheme. Must satisfy `Wo > 0`. Accepts `var` / `expr`. |
| `"sigclip" S` | Optional. Outlier-rejection threshold in sigma. Defaults to `5.0`; `S = 0` disables rejection. Must satisfy `S >= 0`. Accepts `var` / `expr`. |
| `"maskpoints" maskvar` | Optional. Name of a light-curve vector; only points with `maskvar > 0` contribute. |

The trailing keywords are parsed in strict order: `trendwindow`, `outlierwindow`, `sigclip`, `maskpoints`.

**Output columns**

| Column | Meaning |
|--------|---------|
| `CODYM_M_N` | The statistic `M`. NaN when the curve is flat, the deciles overlap, or `N' < 2`. |
| `CODYM_d10_N` | Mean of the combined faintest-decile and brightest-decile values. Tracks `CODYM_M_N`'s NaN cases. |
| `CODYM_dmed_N` | Median of the detrended, outlier-filtered curve. |
| `CODYM_sigma_d_N` | Standard deviation of the detrended, outlier-filtered curve. |
| `CODYM_Npoints_N` | Number of points surviving the NaN/mask filter and the sigma-clip. |

`N` is the 0-indexed command position in the pipeline.

**References**

Cite [Cody, A. M. et al. 2014](https://ui.adsabs.harvard.edu/abs/2014AJ....147...82C/abstract), AJ, 147, 82.

**Examples**

**Example 1.** Dipping signature on a light curve with an injected transit signal. `M` moves in the positive (dipping) direction relative to the baseline `EXAMPLES/3` (try comparing the two to see the shift).

```bash
vartools -i EXAMPLES/3.transit -oneline -CodyM trendwindow 10
```

**Example 2.** Bursting signature on a light curve with an injected microlensing event. `M` moves strongly in the negative (bursting) direction. The microlensing event spans many days, so `trendwindow` must be longer than the event timescale to preserve it — a 100-day boxcar on a ~30-day light curve is essentially a constant subtract.

```bash
vartools -i EXAMPLES/4.microlensinject -oneline \
    -CodyM trendwindow 100
```

**Example 3.** Two-stage outlier-rejection scheme on the transit-injected light curve: outliers are identified on a 0.1-day residual smooth rather than on the trend-detrended curve, so the genuine transit dips survive into the `M` calculation.

```bash
vartools -i EXAMPLES/3.transit -oneline \
    -CodyM trendwindow 10 outlierwindow 0.1 sigclip 5
```

---

## `-CodyQ`

**Syntax**
```
-CodyQ <"aov" | "ls" | "bls" | "pdm" | "ftp" | "injectharm" |
    "fix" period | "fixcolumn" <colname | colnum> |
    "list" ["column" col] | "var" varname | "expr" exprstring>
    "trendwindow" <"var" varname | "expr" exprstring | trendwindow>
    ["phasesmooth" <"var" varname | "expr" exprstring | phasesmooth>]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, compute the quasi-periodicity statistic `Q` of [Cody et al. 2014](https://ui.adsabs.harvard.edu/abs/2014AJ....147...82C/abstract) (their Equation 6). `Q` assesses how close the light curve is to the photometric noise floor before and after a phase-folded periodic model is subtracted:

```
Q = (rms_resid^2 - sigma^2) / (rms_raw^2 - sigma^2)
```

where `rms_raw` is the standard deviation of the long-term-detrended light curve, `rms_resid` is the standard deviation of the same curve after subtraction of a boxcar-smoothed phase model at the supplied period, and `sigma^2` is the mean of the per-point squared errors over the surviving points. `Q` approaches 0 for a strictly periodic light curve (the phase model captures essentially all the variance) and approaches 1 for one with no detectable periodicity (the phase model removes nothing; the denominator can collapse to a non-positive value in this regime, yielding NaN); intermediate values indicate quasi-periodic variability.

**Period source.** Exactly one of these forms must come first after `-CodyQ`:

| Keyword | Meaning |
|---------|---------|
| `aov` / `ls` / `bls` / `pdm` / `ftp` / `injectharm` | Copy the primary peak period of the most recent corresponding command in the pipeline. |
| `fix P` | Use the literal value `P` (days). |
| `fixcolumn <colname \| colnum>` | Read the period from an output column of a prior command. |
| `list ["column" col]` | Read the period from the input-list file (optionally from a specific column). |
| `var varname` | Read the period from a per-light-curve variable. |
| `expr exprstring` | Evaluate an analytic expression for the period per light curve. |

The statistic is computed as follows. (1) Points with NaN magnitudes, points with `sig <= 0`, and — when `maskpoints` is given — points with `maskvar <= 0` are rejected. (2) A long-term trend is removed by subtracting a boxcar-mean smooth of full width `trendwindow` (in time-axis units; Cody used 10 days for CoRoT data). (3) `rms_raw` is computed from the detrended curve. (4) `sigma^2` is the mean of the per-point squared errors over the surviving points. (5) The detrended curve is phase-folded to the supplied period using `t[0]` as the epoch; the circular phase-domain smoother below is invariant under a global phase shift, so the choice of epoch does not affect `Q` and is not exposed. (6) A smoothed phase model is built by boxcar-averaging the detrended values in the phase domain with full width `phasesmooth` as a fraction of the period (default `0.25`, matching the paper); the smoother wraps circularly at phase 0/1. (7) `rms_resid` is the standard deviation of `(detrended - model)`. (8) `Q` is reported per the equation above; the denominator `rms_raw^2 - sigma^2` going to or below zero (the "aperiodic pileup at `Q ~ 1`" regime in the paper's Figure 29) is reported as NaN.

`trendwindow` and `phasesmooth` each accept a fixed value, or `var` followed by the name of a light-curve-list variable, or `expr` followed by an analytic expression evaluated per light curve. The period source itself supports per-LC `var` / `expr` through the same mechanism. Literal numeric values are validated at parse time (`trendwindow > 0`, `phasesmooth ∈ (0, 1]`, `period > 0`); per-LC values from `var` / `expr` / `fixcolumn` are validated at runtime and yield NaN for the affected light curve on a bad value.

Python equivalent: [`CodyQ`](../python/commands/statistics.md#codyq-quasi-periodicity-statistic-q).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| period source | Required. One of `aov`, `ls`, `bls`, `pdm`, `ftp`, `injectharm`, `fix P`, `fixcolumn <colname\|colnum>`, `list ["column" col]`, `var varname`, or `expr exprstring` as described above. |
| `"trendwindow" Wt` | Required. Boxcar full width for the long-term detrend, in the same units as the light-curve time axis. Must satisfy `Wt > 0`. Accepts `var` / `expr`. |
| `"phasesmooth" f` | Optional. Phase-domain boxcar full width as a fraction of the period. Defaults to `0.25`. Must satisfy `0 < f <= 1`. Accepts `var` / `expr`. |
| `"maskpoints" maskvar` | Optional. Name of a light-curve vector; only points with `maskvar > 0` contribute. |

The trailing keywords are parsed in strict order: `trendwindow`, `phasesmooth`, `maskpoints`.

**Output columns**

| Column | Meaning |
|--------|---------|
| `CODYQ_Q_N` | The statistic `Q`. NaN when `rms_raw^2 - sigma^2 <= 0`, or when the inputs are invalid. |
| `CODYQ_Period_N` | The period actually used (the resolved value for `var` / `expr` / back-reference sources). |
| `CODYQ_RMS_raw_N` | Standard deviation of the trend-detrended light curve. |
| `CODYQ_RMS_resid_N` | Standard deviation of the residual after subtracting the smoothed phase model. |
| `CODYQ_Sigma_N` | `sqrt(sigma^2)` = root-mean-square of the per-point errors over the surviving points. |
| `CODYQ_Npoints_N` | Number of points surviving the NaN/mask/sig filter. |

`N` is the 0-indexed command position in the pipeline. The diagnostic columns remain meaningful when `CODYQ_Q_N` is NaN due to a non-positive denominator.

**References**

Cite [Cody, A. M. et al. 2014](https://ui.adsabs.harvard.edu/abs/2014AJ....147...82C/abstract), AJ, 147, 82.

**Examples**

**Example 1.** Literal-fix period.

```bash
vartools -i EXAMPLES/2 -oneline -CodyQ fix 1.234 trendwindow 10
```

**Example 2.** Period sourced from a prior `-aov` command.

```bash
vartools -i EXAMPLES/2 -oneline \
    -aov 0.5 4.0 0.1 5 1 0 \
    -CodyQ aov trendwindow 10
```

---

## `-structurefunction`

**Syntax**
```
-structurefunction "bins" <"log" Nbins | "linear" Nbins | "edges" e1,e2,...,en>
    ["lagrange" <"var" varname | "expr" exprstring | lagmin>
                <"var" varname | "expr" exprstring | lagmax>]
    ["estimator" <"squared" | "mad">]
    ["fitDRW" ["sigma0" <"var" varname | "expr" exprstring | sigma0>]
              ["tau0"   <"var" varname | "expr" exprstring | tau0>]]
    ["reportsfvalsintable" e1,e2,...,en]
    ["save" outdir]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, compute the ensemble structure function (SF) on lag bins constructed from all pairs of observations, and optionally fit a damped-random-walk (DRW) model. Two estimators are supported, selected by `estimator` (default `squared`).

With `estimator squared` the squared-difference form is used with bin-averaged noise subtraction:

```
SF^2(dt) = <(m_j - m_i)^2>_pairs in bin - <sigma_i^2 + sigma_j^2>_pairs in bin
SF(dt)   = sqrt(SF^2)
```

This is the `D^(1)(tau)` of [Simonetti, Cordes & Heeschen 1985](https://ui.adsabs.harvard.edu/abs/1985ApJ...296...46S/abstract) (their Equation A1 with `M = 1`, finite-sample estimator A8), with the noise correction of their Equation A13 generalised from homoscedastic to heteroscedastic measurement uncertainties. Bins where the noise-subtracted variance is non-positive are noise-dominated and reported as NaN.

With `estimator mad` the absolute-deviation form of [Hughes, Aller & Aller 1992](https://ui.adsabs.harvard.edu/abs/1992ApJ...396..469H/abstract) and [Schmidt et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...714.1194S/abstract) (their Equation 2) is used with per-pair noise subtraction:

```
V(dt) = <(sqrt(pi)/2) * |m_j - m_i| - sqrt(sigma_i^2 + sigma_j^2)>_pairs in bin
```

The `sqrt(pi)/2` factor converts the mean absolute deviation of a Gaussian into its standard deviation. The MAD form is more robust to outliers and stays real-valued at the noise floor (the per-pair subtraction gives a biased-low real value as `V` approaches the noise level rather than an undefined negative variance), at the cost of a slightly biased response to `V` approaching the noise floor.

The labels "first-order" and "second-order" are deliberately avoided: they label a polynomial-detrending differencing scheme in the Rutman 1978 / Simonetti 1985 time-series literature and the moment power of the difference in the AGN-variability literature, with opposite assignments to the same statistic.

Per-bin error bars are reported as `sigma_SF = SF / sqrt(2 N_eff)` (squared) or `sigma_SF = SF / sqrt(N_eff / (pi/2 - 1))` (mad), where `N_eff = min(N_pairs, N_obs/2)` caps the effective number of independent pairs. The bound recovers the right `~SF / sqrt(N_obs)` precision floor at long lags rather than continuing to shrink as `1 / sqrt(N_pairs)`.

If `fitDRW` is given, a damped-random-walk model is fit to the well-determined SF bins. The DRW is the continuous-time first-order autoregressive (CAR(1)) / Ornstein–Uhlenbeck process introduced for AGN optical variability by [Kelly, Bechtold & Siemiginowska 2009](https://ui.adsabs.harvard.edu/abs/2009ApJ...698..895K/abstract) (their Equation 1), with autocovariance `C(dt) = sigma_long^2 * exp(-dt / tau)`. The analytic SF follows as

```
SF_DRW(dt) = SF_inf * sqrt(1 - exp(-dt / tau)),    SF_inf = sqrt(2) * sigma_long
```

This `(SF_inf, tau)` parameterisation is the one used by [MacLeod et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...721.1014M/abstract). Note that Kelly et al. themselves fit the CAR(1) likelihood directly via a state-space representation, not the SF. The fit minimises `chi^2 = sum [(SF_obs - SF_model) / sigma_SF]^2` over the bins with a finite SF, using a downhill simplex (Nelder–Mead) on `(log SF_inf, log tau)`. The reported scalar amplitude is the MacLeod 2010 long-term magnitude standard deviation `sigma_long = SF_inf / sqrt(2)`; to convert to Kelly's SDE driving-noise amplitude `sigma_K` (units mag · day^(-1/2)) use `sigma_K = sigma_long * sqrt(2 / tau)`.

If `save outdir` is given, a four-column aux file `<outdir>/<lcname>.sf` (`dt_center  SF  sigma_SF  n_pairs`) is written for each light curve; bins with no pairs or noise-dominated SF appear with `SF = sigma_SF = NaN`. If `reportsfvalsintable e1,e2,...,en` is given, four scalar columns per requested lag are also emitted in the result table.

Python equivalent: [`structurefunction`](../python/commands/statistics.md#structurefunction-ensemble-structure-function).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"bins" "log" Nbins` | Required. Lay out `Nbins` log-spaced lag bins between `lagmin` and `lagmax`. `Nbins >= 2`. |
| `"bins" "linear" Nbins` | Required. Lay out `Nbins` linearly spaced lag bins between `lagmin` and `lagmax`. `Nbins >= 2`. |
| `"bins" "edges" e1,...,en` | Required. Use an explicit list of strictly increasing positive bin edges. Produces `n - 1` bins. `n >= 3`. |
| `"lagrange" lagmin lagmax` | Optional. Fix the lag range for `log` / `linear` binning. Defaults: `lagmin` = smallest consecutive time spacing in the filtered LC; `lagmax` = full baseline. Ignored for `edges`. Each value accepts `var` / `expr`. Literals: `lagmin > 0`, `lagmax > lagmin`. |
| `"estimator" "squared"`/`"mad"` | Optional. SF estimator family. Default `squared`. |
| `"fitDRW"` | Optional. Fit a DRW model and emit five scalar columns. |
| `"sigma0" S` | Optional (only with `fitDRW`). Initial guess for `sigma_long`. Accepts `var` / `expr`. `S > 0`. |
| `"tau0" T` | Optional (only with `fitDRW`). Initial guess for `tau`. Accepts `var` / `expr`. `T > 0`. |
| `"reportsfvalsintable" e1,...,en` | Optional. For each requested lag emit four scalar columns. Edges must be strictly increasing and `> 0`. |
| `"save" outdir` | Optional. Write the full SF curve as `<outdir>/<lcname>.sf`. |
| `"maskpoints" maskvar` | Optional. Only points with `maskvar > 0` contribute. |

The trailing keywords are parsed in strict order: `lagrange`, `estimator`, `fitDRW` (`sigma0`, `tau0`), `reportsfvalsintable`, `save`, `maskpoints`.

**Output columns**

When `fitDRW` is in effect:

| Column | Meaning |
|--------|---------|
| `STRUCTUREFUNCTION_SIGMA_N` | Long-term magnitude standard deviation `sigma_long = SF_inf / sqrt(2)` (MacLeod 2010 convention; mag). NaN on non-convergence. |
| `STRUCTUREFUNCTION_TAU_N` | Damping time-scale `tau` (time-axis units). NaN on non-convergence. |
| `STRUCTUREFUNCTION_CHI2_N` | Best-fit `chi^2`. |
| `STRUCTUREFUNCTION_DOF_N` | Well-determined-bin count minus 2. |
| `STRUCTUREFUNCTION_CONVERGED_N` | `1` if the simplex converged within tolerance and the fitted parameters are finite and positive, else `0`. |

When `reportsfvalsintable e1,...,en` is in effect, four scalar columns per requested edge `e_k` (`k = 0..n-1`):

| Column | Meaning |
|--------|---------|
| `STRUCTUREFUNCTION_DT_k_N` | Actual centre of the SF bin that contains `e_k`. NaN if `e_k` is outside the lag range. |
| `STRUCTUREFUNCTION_SF_k_N` | SF value at that bin. NaN if the bin is noise-dominated or empty. |
| `STRUCTUREFUNCTION_SIGMA_SF_k_N` | Per-bin error bar. NaN if `SF_k` is NaN. |
| `STRUCTUREFUNCTION_NPAIRS_k_N` | Number of pairs in the bin. `0` if `e_k` is out of range. |

`N` is the 0-indexed command position in the pipeline.

**References**

Cite [Simonetti, Cordes & Heeschen 1985](https://ui.adsabs.harvard.edu/abs/1985ApJ...296...46S/abstract), ApJ, 296, 46, if you use `estimator squared`.

Cite [Hughes, Aller & Aller 1992](https://ui.adsabs.harvard.edu/abs/1992ApJ...396..469H/abstract), ApJ, 396, 469 and [Schmidt et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...714.1194S/abstract), ApJ, 714, 1194, if you use `estimator mad`.

Cite [Kelly, Bechtold & Siemiginowska 2009](https://ui.adsabs.harvard.edu/abs/2009ApJ...698..895K/abstract), ApJ, 698, 895 and [MacLeod et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...721.1014M/abstract), ApJ, 721, 1014, if you use `fitDRW`.

**Examples**

**Example 1.** Structure function values at three chosen lags.

```bash
vartools -i EXAMPLES/2 -oneline \
    -structurefunction bins log 20 reportsfvalsintable 0.1,1,10
```

**Example 2.** SF curve + DRW fit. `EXAMPLES/2` is an injected sinusoid, so the DRW is the wrong model and `chi^2 / dof` is large; this is how the fit flags model misspecification.

```bash
vartools -i EXAMPLES/2 -oneline -structurefunction bins log 20 fitDRW
```

**Example 3.** Save the full SF curve as an aux file for offline plotting, with the MAD estimator.

```bash
vartools -i EXAMPLES/2 -oneline \
    -structurefunction bins log 30 estimator mad save .
```

## `-drwfit`

**Syntax**
```
-drwfit ["mean" <"fit" | "fix" <"var" varname | "expr" exprstring | mu> | "subtract">]
    ["sigma0" <"var" varname | "expr" exprstring | sigma0>]
    ["tau0"   <"var" varname | "expr" exprstring | tau0>]
    ["mean0"  <"var" varname | "expr" exprstring | mean0>]
    ["save" outdir]
    ["correctlc" <"smoothed" | "forecast">]
    ["modelvar"  <"smoothed" | "forecast"> modelvarname]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, fit a damped-random-walk (DRW) model directly by maximum likelihood. The DRW is the continuous-time first-order autoregressive (CAR(1)) / Ornstein–Uhlenbeck process, equivalently a Gaussian process with a Matérn-1/2 (exponential) covariance kernel `C(dt) = sigma_long^2 * exp(-|dt| / tau)`. It was introduced for AGN optical variability by [Kelly, Bechtold & Siemiginowska 2009](https://ui.adsabs.harvard.edu/abs/2009ApJ...698..895K/abstract).

The likelihood is evaluated with the Kelly 2009 state-space recursion (their Equations 6–13):

```
x*_i    = x_i - mu
x_hat_0 = 0,    Omega_0 = sigma_long^2
a_i     = exp(-(t_i - t_{i-1}) / tau)
K_i     = Omega_{i-1} / (Omega_{i-1} + sig_meas_{i-1}^2)
x_hat_i = a_i * (x_hat_{i-1} + K_i * (x*_{i-1} - x_hat_{i-1}))
Omega_i = sigma_long^2 * (1 - a_i^2) + a_i^2 * Omega_{i-1} * (1 - K_i)
-2 ln L = sum_i [ ln(2 pi (Omega_i + sig_meas_i^2)) + (x*_i - x_hat_i)^2 / (Omega_i + sig_meas_i^2) ]
```

Each evaluation is `O(N)` with no matrix inversion, so the fit is fast even for long light curves. A downhill simplex (Nelder–Mead) minimises `-2 ln L` over `(log sigma_long, log tau)`, or jointly `(log sigma_long, log tau, mu)` when the mean is fit. This direct-likelihood method recovers `tau` substantially more accurately than fitting a DRW to the structure function ([`-structurefunction`](#-structurefunction) `fitDRW`), especially on short baselines (MacLeod 2010 Section 4.2; Kelly 2009 Section 3.1).

The reported amplitude `DRWFIT_SIGMA_N` is the long-term magnitude standard deviation `sigma_long` in the [MacLeod et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...721.1014M/abstract) convention (mag) — the same quantity `-structurefunction` reports, so the two commands are directly comparable on the same light curve. To convert to Kelly's SDE driving-noise amplitude `sigma_K` (units mag · day^(-1/2)) use `sigma_K = sigma_long * sqrt(2 / tau)`.

The long-term mean is controlled by `mean` (default `fit`): `mean fit` fits `mu` jointly (3-parameter simplex); `mean fix <mu>` holds it at a fixed value or per-LC `var` / `expr` source (2-parameter simplex); `mean subtract` removes the weighted mean before fitting, in which case `DRWFIT_MU_N` is meaningless and reported as NaN. The simplex initial guesses are derived from the light curve unless overridden by `sigma0`, `tau0`, and/or `mean0` (default `tau0` = `0.1 * T_baseline`, the central decile of MacLeod 2010's empirical `tau / T_LC` distribution for S82 quasars).

Two likelihood-ratio quality indicators are emitted (see e.g. MacLeod 2010 Section 3.1): `DRWFIT_DLNL_NOISE_N` compares the best-fit DRW to the pure-measurement-noise limit (`sigma_long -> 0`), and `DRWFIT_DLNL_INF_N` compares it to the `tau -> infinity` limit. Both are `ln L_best` minus the limiting `ln L`; large positive values indicate the DRW is strongly preferred over the respective null. The thresholds for a confident detection are left to the user.

If `correctlc smoothed` (or `forecast`) is given, the in-memory light curve is replaced by the DRW residuals before being passed to subsequent commands: `smoothed` subtracts the Rauch–Tung–Striebel smoothed model (a backward pass over the Kalman filter using both past and future points), whitening the curve toward the noise floor; `forecast` subtracts the one-step-ahead Kalman forecast (past points only), which retains the unexplained short-term variability. If `modelvar smoothed modelvarname` (or `forecast`) is given, the DRW model itself is stored in a new light-curve variable for use by later commands, without modifying the light curve.

If `save outdir` is given, an eight-column aux file `<outdir>/<lcname>.drwfit` (`t  x  sig_meas  x_hat_fwd  Omega_fwd  chi_fwd  x_smoothed  Omega_smoothed`) is written, with one row per original light-curve point and NaN rows preserved for filtered-out points. The columns hold the time, magnitude, and measurement error; the forward Kalman state (predicted value, variance, and standardized residual); and the smoothed state (value and variance).

Python equivalent: [`drwfit`](../python/commands/statistics.md#drwfit-direct-drw-maximum-likelihood-fit).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"mean" "fit"` | Optional (default). Fit `mu` jointly with `sigma_long` and `tau`. |
| `"mean" "fix" mu` | Optional. Hold `mu` at a fixed value. Accepts `var` / `expr` for per-LC sourcing. |
| `"mean" "subtract"` | Optional. Subtract the weighted mean before fitting; `DRWFIT_MU_N` is then NaN. |
| `"sigma0" S` | Optional. Initial guess for `sigma_long`. Accepts `var` / `expr`. `S > 0`. |
| `"tau0" T` | Optional. Initial guess for `tau`. Accepts `var` / `expr`. `T > 0`. |
| `"mean0" M` | Optional. Initial guess for `mu` (when the mean is fit). Accepts `var` / `expr`. |
| `"save" outdir` | Optional. Write the per-point aux file `<outdir>/<lcname>.drwfit`. |
| `"correctlc" "smoothed"`/`"forecast"` | Optional. Replace the in-memory light curve with the smoothed or forecast DRW residuals. |
| `"modelvar" "smoothed"`/`"forecast" modelvarname` | Optional. Store the smoothed or forecast DRW model in a new light-curve variable. |
| `"maskpoints" maskvar` | Optional. Only points with `maskvar > 0` contribute to the fit. |

The trailing keywords are parsed in strict order: `mean`, `sigma0`, `tau0`, `mean0`, `save`, `correctlc`, `modelvar`, `maskpoints`.

**Output columns**

| Column | Meaning |
|--------|---------|
| `DRWFIT_SIGMA_N` | Long-term magnitude standard deviation `sigma_long` (MacLeod 2010 convention; mag). |
| `DRWFIT_TAU_N` | Damping time-scale `tau` (time-axis units). |
| `DRWFIT_MU_N` | Fitted long-term mean `mu`. NaN when `mean subtract`. |
| `DRWFIT_LNL_N` | Best-fit `ln L`. |
| `DRWFIT_DLNL_NOISE_N` | `ln L_best - ln L` at the `sigma_long -> 0` (pure-noise) limit. |
| `DRWFIT_DLNL_INF_N` | `ln L_best - ln L` at the `tau -> infinity` limit. |
| `DRWFIT_CONVERGED_N` | `1` if the simplex converged, else `0`. |

`N` is the 0-indexed command position in the pipeline.

**References**

Cite [Kelly, Bechtold & Siemiginowska 2009](https://ui.adsabs.harvard.edu/abs/2009ApJ...698..895K/abstract), ApJ, 698, 895 and [MacLeod et al. 2010](https://ui.adsabs.harvard.edu/abs/2010ApJ...721.1014M/abstract), ApJ, 721, 1014, if you use this command.

**Examples**

**Example 1.** Direct maximum-likelihood DRW fit. `EXAMPLES/2` carries an injected sinusoid rather than genuine DRW variability, so the recovered parameters describe the best DRW approximation to that signal.

```bash
vartools -i EXAMPLES/2 -oneline -drwfit
```

**Example 2.** Subtract the smoothed DRW model in place, then compute the `chi^2` of the corrected light curve.

```bash
vartools -i EXAMPLES/2 -oneline -drwfit correctlc smoothed -chi2
```

**Example 3.** Write the per-point Kalman/smoother aux file for goodness-of-fit diagnostics, holding the mean fixed.

```bash
vartools -i EXAMPLES/2 -oneline -drwfit mean fix 10.12 save .
```


## `-runlength`

**Syntax**
```
-runlength ["k" <"var" varname | "expr" exprstring | k>]
    ["maskpoints" maskvar]
```

**Description**

For each light curve, characterize runs of consecutive points (in time order) relative to the median magnitude and the median absolute deviation. A *run* is a maximal block of consecutive points that all satisfy one condition. This is a fast, robust descriptor of serial coherence that complements the scatter statistics ([`-rms`](#-rms), [`-chi2`](#-chi2), the MAD reported by [`-stats`](#-stats)) and the asymmetry / quasi-periodicity statistics [`-CodyM`](#-codym) / [`-CodyQ`](#-codyq), none of which capture run structure. Long runs above or below the median flag low-frequency coherent variability or a residual trend; long outlier runs flag sustained excursions (flares, blends, systematics) as opposed to isolated bad points.

Let `m` be the median of the (NaN- and mask-filtered) magnitudes and `D = MAD = 1.483 * median(|x - m|)` their median absolute deviation — the same 1.483-scaled estimator reported by [`-stats`](#-stats), so the band `m ± k*D` corresponds to roughly `±k` Gaussian standard deviations. Four conditions are tracked, each on the points in time order:

```
above   : x > m
below   : x < m
outhigh : x - m >  k*D
outlow  : x - m < -k*D
```

The comparisons are strict, so a point exactly at the median is in band and breaks both the above and below runs. The two outlier conditions are sign-specific: a band excursion that crosses from the high side to the low side ends one run and begins another — there is no combined sign-agnostic outlier run. For each condition the command reports the longest run, the number of runs, and the mean run length (`npoints / nruns`, reported as NaN when there are no runs). The light curve is sorted in time before the scan if it is not already in time order.

The run-length scan is a single `O(N)` pass; computing `m` and `D` additionally requires median selection, so the command as a whole is not a single streaming pass.

Python equivalent: [`runlength`](../python/commands/statistics.md#runlength-run-length-statistics-about-the-median-and-mad).

**Parameters**

| Parameter | Description |
|-----------|-------------|
| `"k" k` | Optional. Outlier band half-width in MAD units. Default `3.0`; must be `>= 0`. Accepts `var` / `expr` for per-LC sourcing. |
| `"maskpoints" maskvar` | Optional. Only points with `maskvar > 0` contribute. |

The trailing keywords are parsed in strict order: `k`, `maskpoints`.

**Output columns**

`N` is the 0-indexed command position in the pipeline.

| Column | Meaning |
|--------|---------|
| `RUNLENGTH_ABOVE_MAXLEN_N` | Longest run of consecutive points with `x > m`. |
| `RUNLENGTH_ABOVE_NRUNS_N` | Number of above-median runs. |
| `RUNLENGTH_ABOVE_MEANLEN_N` | Mean above-median run length (NaN if none). |
| `RUNLENGTH_BELOW_MAXLEN_N` / `_NRUNS_N` / `_MEANLEN_N` | Same three statistics for `x < m`. |
| `RUNLENGTH_OUTHIGH_MAXLEN_N` / `_NRUNS_N` / `_MEANLEN_N` | Same three for the high outlier condition `x - m > k*D`. |
| `RUNLENGTH_OUTLOW_MAXLEN_N` / `_NRUNS_N` / `_MEANLEN_N` | Same three for the low outlier condition `x - m < -k*D`. |
| `RUNLENGTH_MEDIAN_N` | Median `m`. |
| `RUNLENGTH_MAD_N` | The 1.483-scaled `D`. |
| `RUNLENGTH_K_N` | The `k` used. |

When no point survives filtering, the run statistics are reported as `0 / 0 / NaN` and the median and MAD as NaN.

**References**

The count of runs about the median underlies the [Wald–Wolfowitz runs test](https://ui.adsabs.harvard.edu/abs/1940AnMaS..11..147W/abstract) (Wald & Wolfowitz 1940, Ann. Math. Statist., 11, 147); `-runlength` reports the descriptive run statistics themselves rather than that test statistic or an associated p-value. No citation is required to use this command.

**Examples**

**Example 1.** Run-length statistics about the median and MAD. `EXAMPLES/2` carries an injected sinusoid, so it shows long above/below runs (roughly half a period of points each) and, because the `±3*MAD` band is wider than the sinusoid amplitude, no outlier runs.

```bash
vartools -i EXAMPLES/2 -oneline -runlength
```

**Example 2.** Narrow the band to `±0.5*MAD` so the sinusoid peaks and troughs fall outside it, producing non-zero `outhigh` and `outlow` runs that trace the coherent excursions.

```bash
vartools -i EXAMPLES/2 -oneline -runlength k 0.5
```
