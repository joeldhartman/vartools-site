# Statistics

Scalar summary statistics computed over a light curve: moments, autocorrelation, variability indicators, and uncertainty rescaling.

---

## `rms` — Root mean square

```python
cmd.rms(maskpoints=None)
```

Computes the RMS and weighted RMS of the light curve. Output statistics: `Mean_Mag_N`, `RMS_N`, `Weighted_RMS_N`.

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

## `rmsbin` — Binned RMS

```python
cmd.rmsbin(nbin, bintimes, maskpoints=None)
```

Computes the binned RMS at a set of specified timescales. `bintimes` is a list of timescales (e.g. `[0.02, 0.05, 0.1]` days).

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Compute binned RMS at a range of timescales, in days.
# (vartools internally truncates bin times for column-naming,
# so pick values that are well separated.)
bintimes_days = [0.01, 0.05, 0.1, 1.0, 10.0]
batch = vt.Pipeline().rmsbin(5, bintimes_days).run_batch(lcs)
print(batch.vars)
```

---

## `chi2` — Chi-squared statistic

```python
cmd.chi2(maskpoints=None)
```

Computes the chi-squared statistic of the light curve. Output: `Chi2_N`, `Chi2_per_dof_N`.

**Examples**

```python
# Batch: chi-squared for all example light curves
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().chi2().run_batch(lcs)
print(batch.vars[["Name", "Chi2_0", "Weighted_Mean_Mag_0"]])
```

---

## `chi2bin` — Binned chi-squared

```python
cmd.chi2bin(nbin, bintimes, maskpoints=None)
```

Same as `rmsbin` but computes chi-squared instead of RMS at each timescale.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
bintimes_days = [0.01, 0.05, 0.1, 1.0, 10.0]
batch = vt.Pipeline().chi2bin(5, bintimes_days).run_batch(lcs)
print(batch.vars)
```

---

## `stats` — Generic statistics

```python
cmd.stats(variables, statistics, maskpoints=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `variables` | `str` or list of `str` | Variable name(s) to compute statistics for. |
| `statistics` | `str` or list of `str` | Statistics to compute: `"mean"`, `"median"`, `"stddev"`, `"min"`, `"max"`, etc. |

```python
cmd.stats("mag", "mean,median,stddev")
cmd.stats(["mag", "err"], ["mean", "stddev"])
```

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

## `autocorrelation` — Autocorrelation function

```python
cmd.autocorrelation(start, stop, step, save_result=True, maskpoints=None)
```

Computes the discrete autocorrelation function of the magnitude series.

| Parameter | Type | Description |
|-----------|------|-------------|
| `start`, `stop`, `step` | `float` | Lag range and step size. |
| `save_result` | `bool`, `str`, or `Output` | Controls Python capture of the output file. Default `True` (captured as `result.files["autocorrelation_result_N"]`). See [Auxiliary output files](index.md#auxiliary-output-files) and the note below. |
| `maskpoints` | `str` or `None` | Name of a mask variable. |

!!! note "File is always written"
    The vartools CLI always writes the autocorrelation file to disk — there is no CLI option to suppress it. Setting `save_result=False` only suppresses Python capture; the file is still written to a temp directory and discarded after the run completes.

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

---

## `Jstet` — Stetson J-statistic

```python
cmd.Jstet(timescale, dates, maskpoints=None)
```

Computes the J variability index (Stetson 1996). Requires a dates file listing observation epochs.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().Jstet(0.5, "EXAMPLES/dates_tfa").run_batch(lcs)
print(batch.vars[["Name", "Jstet_0", "Kurtosis_0", "Lstet_0"]])
```

---

## `alarm` — Alarm statistic

```python
cmd.alarm(maskpoints=None)
```

Computes the alarm statistic of Kovacs, Bakos & Noyes (2005) — a detection statistic for coherent signals that penalizes long run-lengths of positive or negative deviations from the mean more heavily than random scatter.

**Parameters**

- `maskpoints : str, optional` — Name of a mask variable; only points with `mask > 0` contribute to the statistic.

**Output columns**: `Alarm_N`.

---
