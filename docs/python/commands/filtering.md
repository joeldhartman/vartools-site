# Filtering & Detrending

Commands that reject outliers, smooth the light curve, or remove ensemble-level systematics.

---

## `clip` — Sigma clipping

```python
cmd.clip(sigclip, iterative=True, niter=None, median=False,
         markclip=None, noinitmark=False, maskpoints=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `sigclip` | `float` or `str` | Clipping threshold in units of standard deviation. Accepts a number, variable name, or expression string. |
| `iterative` | `bool` | Repeat clipping until no points are removed (default `True`). |
| `niter` | `int`, `str`, or `None` | Clip at most this many times (overrides `iterative`). Accepts a number, variable name, or expression. |
| `median` | `bool` | Clip relative to the median instead of the mean. |
| `markclip` | `str` or `None` | Variable name to record clipping mask (1 = kept, 0 = clipped). |

CLI equivalent: `-clip <sigclip|var|expr> <iter|var|expr> [niter <N|var|expr>] [median] ...`

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/5")

# Compute RMS, apply 3-sigma clipping, compute RMS of clipped LC
result = (
    lc.rms()
      .clip(3.0)
      .rms()
)
print(result.vars["Nclip_1"])    # 51 points removed
print(result.vars["RMS_2"])      # RMS after clipping
```

---

## `medianfilter` — Median filtering

```python
cmd.medianfilter(time, method="median", replace=False)
```

Apply a sliding-window median (or mean) filter with window width `time`. `replace=True` writes the smoothed values back into the magnitude column.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/1")

# High-pass and low-pass median filter: save LC, process both ways
pipe = (vt.Pipeline()
        .chi2()
        .savelc()
        .medianfilter(0.05)
        .chi2()
        .restorelc(savenumber=1)
        .medianfilter(0.05, replace=True)
        .chi2())
result = pipe.run(lc)
print(result.vars["Chi2_0"])   # original
print(result.vars["Chi2_3"])   # after high-pass filter
print(result.vars["Chi2_6"])   # after low-pass filter
```

---

## `restricttimes` / `restoretimes` — Time windowing

```python
cmd.restricttimes(mode="JDrange", minJD=None, maxJD=None,
                  JDfilename=None, expression=None, exclude=False,
                  markrestrict=None, noinitmark=False)
cmd.restoretimes(prior_command=1)
```

`restricttimes` discards observations outside a time window or list. `restoretimes` undoes a prior restriction.

Modes: `"JDrange"` (min/max), `"JDlist"` (file of times), `"expr"` (boolean expression).

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3")

# Restrict to a JD window, compute stats, then restore
pipe = (vt.Pipeline()
        .stats("t", ["min", "max"])
        .restricttimes(mode="JDrange", minJD=53740, maxJD=53750)
        .stats("t", ["min", "max"])
        .restoretimes(prior_command=1)
        .stats("t", ["min", "max"]))
result = pipe.run(lc)
print(result.vars["STATS_t_MIN_0"])   # original time range
print(result.vars["STATS_t_MIN_2"])   # restricted range
print(result.vars["STATS_t_MIN_4"])   # restored (original again)

# Restrict using a boolean expression on magnitude
pipe2 = (vt.Pipeline()
        .restricttimes(mode="expr",
                      expression="(mag>10.16311)&&(mag<10.17027)"))
result2 = pipe2.run(lc, capture_lc=True)
```

---

## `TFA` — Trend Filtering Algorithm

```python
cmd.TFA(trendlist, dates_file, pixelsep, correct_lc=True,
        save_coeffs=False, save_model=False, xycol=None,
        clip=None, usemedian=False, useMAD=False,
        readformat=None, trend_coeff_priors=None,
        weight_by_template_stddev=False, fitmask=None,
        outfitmask=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `trendlist` | `str` | Path to a file listing the trend (template) light curves, one per line. |
| `dates_file` | `str` | Path to the dates file (one epoch per line, matching the observation cadence). |
| `pixelsep` | `float` | Maximum pixel separation for selecting trend stars. Stars further than this threshold are excluded. |
| `correct_lc` | `bool` | Subtract the TFA model from the light curve. Default `True`. |
| `save_coeffs` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["TFA_coeffs_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `xycol` | `(int, int)` or `None` | Column numbers `(xcol, ycol)` for pixel coordinates in the trend list. |
| `clip` | `float` or `None` | Sigma-clipping threshold during TFA fitting. |

---

## `TFA_SR` — TFA with signal reconstruction

```python
cmd.TFA_SR(trendlist, dates_file, pixelsep, dotfafirst=1,
           tfathresh=0.001, maxiter=10, signal_mode="bin",
           signal_params=None, signal_period=None,
           correct_lc=True, decorr_params=None, ...)
```

Simultaneous TFA detrending and signal reconstruction. `signal_mode` controls the signal model: `"bin"` (phase-binned), `"signal"` (from file), or `"harm"` (harmonic series with `signal_params=(nharm, nsubharm)`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `signal_period` | `float`, `str`, or `None` | Period sub-option for `"bin"` or `"harm"` signal modes. Float emits `"period" val`; string keyword `"ls"`, `"aov"`, or `"bls"` inherits the best period from the most recent matching prior command. The keyword resolves equally in a single `Pipeline` and across chain steps. Missing prior command → `LookupError`. |
| `decorr_params` | `str` or `None` | Raw token string for simultaneous EPD decorrelation, e.g. `"0 2 col1 1 col2 2"` (iterative_flag Nlcterms lccolumn1 lcorder1 ...). |

---

## `SYSREM` — Systematic noise removal

```python
cmd.SYSREM(ninput_color, ninput_airmass, initial_airmass_file,
           sigma_clip1=5.0, sigma_clip2=5.0, saturation=1e9,
           correct_lc=True, save_model=False, save_trends=False,
           useweights=1, col=None)
```

Tamuz et al. (2005) SYSREM algorithm. Removes systematic effects correlated with colour and airmass across an ensemble of light curves. Both `save_model` and `save_trends` accept `bool`, `str`, or `Output` — see [Auxiliary output files](index.md#auxiliary-output-files). The model is captured as `result.files["SYSREM_model_N"]` and the trend vectors as `result.files["SYSREM_trends_N"]`.

---
