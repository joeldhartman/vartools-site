# Period Finding

Periodogram-based algorithms for discovering or refining periodicities: Lomb-Scargle, Analysis of Variance, Box-Least-Squares, DFT CLEAN, and the Weighted Wavelet Z-transform.

---

## `LS` — Generalized Lomb-Scargle

```python
cmd.LS(minp, maxp, subsample, npeaks=5, save_periodogram=False,
       noGLS=False, whiten=False, clip=None, clipiter=None,
       bootstrap=None, maskpoints=None, fixperiod_snr=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `minp`, `maxp` | `float`, `str`, numpy array, `PerLC`, or `pd.Series` | Period search range (same units as the time column, typically days). See [Variable and expression parameters](#variable-and-expression-parameters) below; for batch per-LC values see [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |
| `subsample` | `float`, `str`, numpy array, `PerLC`, or `pd.Series` | Frequency step as a fraction of 1/T (time span). Smaller values = finer resolution. Typical: `1e-3`. Accepts variable names, expressions, and per-LC arrays. |
| `npeaks` | `int` | Number of peaks to report. Default `5`. |
| `save_periodogram` | `bool`, `str`, or `Output` | Controls auxiliary file output. `True` captures as `result.files["LS_periodogram_N"]`; a path string writes to that directory without capturing; `Output(path, capture=True)` does both. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `noGLS` | `bool` | Use the classical (non-generalised) Lomb-Scargle statistic instead of the generalised (Zechmeister & Kurster) version. |
| `whiten` | `bool` | Iteratively subtract the best-fit sinusoid and re-search. |
| `clip` | `float` | Sigma-clipping threshold applied during whitening iterations. |
| `bootstrap` | `int` | Number of bootstrap resamples for false-alarm probability estimation. |
| `maskpoints` | `str` or `None` | Name of a mask variable; points where the variable is non-zero are excluded from the periodogram. |
| `fixperiod_snr` | `float`, `int`, `str`, or `None` | Evaluate the periodogram at a known period and report its significance. See [fixperiod_snr — fixed-period significance](#fixperiod_snr-fixed-period-significance) below. |

Output statistics include `LS_Period_1_N`, `LS_Amplitude_1_N`, `Log10_LS_Prob_1_N` (log₁₀ of the false-alarm probability) for each of the `npeaks` peaks (N = 0-based command index, or the `columnsuffix` string).

CLI equivalent: `-LS minp maxp subsample npeaks [operiodogram dir] [noGLS] [whiten] ...`

## fixperiod_snr — fixed-period significance

When `fixperiod_snr` is set, vartools evaluates the periodogram at a single known period and appends four extra output columns (N = 0-based pipeline index of the LS command):

| Column | Description |
|--------|-------------|
| `LS_PeriodFix_N` | The fixed period used (omitted when `fixperiod_snr` is a plain number, since it is already known). |
| `Log10_LS_Prob_PeriodFix_N` | Log₁₀ false-alarm probability at that period. |
| `LS_Periodogram_Value_PeriodFix_N` | LS power at that period. |
| `LS_SNR_PeriodFix_N` | SNR = (power − mean) / σ. |

The accepted forms and the CLI tokens they emit:

| Python value | Emitted CLI tokens | When to use |
|---|---|---|
| `1.234` (number) | `fixperiodSNR fix 1.234` | Period known at pipeline-construction time. |
| `"ls"` | `fixperiodSNR ls` | Use the best period found by the most recent prior `-LS` run. |
| `"aov"` | `fixperiodSNR aov` | Use the best period found by the most recent prior `-aov` run. |
| `"injectharm"` | `fixperiodSNR injectharm` | Use the injected-signal period from a prior injection run. |
| `"fixcolumn LS_Period_1_0"` | `fixperiodSNR fixcolumn LS_Period_1_0` | Read the period from a named per-star column. |
| `"list"` | `fixperiodSNR list` | Read the period from the current list-file column. |
| `"list column 2"` | `fixperiodSNR list column 2` | Read the period from column 2 of the list file. |

!!! tip "Back-references work across chain steps"
    `fixperiod_snr` accepts `"ls"`, `"aov"`, `"injectharm"`, and `"fixcolumn NAME"` in both single-Pipeline usage and across chain boundaries (e.g. `lc.LS(...).LS(fixperiod_snr="ls")`). When the keyword appears, pyvartools substitutes the concrete numeric value pulled from the prior `Result` before invoking vartools. The `"aov"` keyword picks the most recent prior `-aov` *or* `-aov_harm`, whichever ran later. `"fixcolumn NAME"` requires a column name (not a numeric column index) when used across a chain boundary. A missing prior command raises `LookupError`.

## Variable and expression parameters

Most numeric parameters throughout pyvartools now accept variable names and expressions in addition to fixed numeric values. This includes parameters on commands such as `clip`, `fluxtomag`, `difffluxtomag`, `medianfilter`, `Killharm`, `linfit`, `Injectharm`, `Injecttransit`, `MandelAgolTransit`, `Starspot`, `nonlinfit`, `BLSFixDurTc`, `BLSFixPerDurTc`, `autocorrelation`, `dftclean`, `wwz`, `binlc`, `addnoise`, `microlens`, and `Phase`.

As an example, `minp`, `maxp`, and `subsample` on `LS` each accept four forms:

| Value | Emitted CLI tokens | When to use |
|-------|--------------------|-------------|
| A number (`float` or `int`) | `0.5` | Fixed value known at pipeline-construction time. |
| A bare identifier string, e.g. `"minperiod"` | `var minperiod` | Value is read from a named per-star vartools variable — typically one loaded from a list file via `run_filelist`. |
| Any other string, e.g. `"tspan/200"` | `expr tspan/200` | Evaluated as a math expression using vartools' built-in expression engine, per light curve. |
| A numpy array, `PerLC`, or `pd.Series` | *(handled automatically)* | A different value for each light curve in a batch run. See [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |

The identifier rule is: if the string matches `[A-Za-z_]\w*` it is treated as a variable name; otherwise it is treated as an expression.

!!! note "Defining variables for the `expr` form"
    The `expr` keyword evaluates an expression against vartools' internal variable registry at the time each light curve is processed. Variables such as `tspan` are *not* built-in; they must be defined by prior commands in the same pipeline. Use `cmd.stats` to compute per-star statistics and `cmd.expr` to derive new variables from them:

    ```python
    cmd.stats("t", "min,max")                         # → STATS_t_MIN_0, STATS_t_MAX_0
    cmd.expr("tspan=STATS_t_MAX_0-STATS_t_MIN_0")     # → tspan
    ```

    The `var` form similarly requires the named variable to exist in the per-star variable registry. This is most naturally supplied via `run_filelist` with a list file that includes per-star columns for `minp` and `maxp`.

**Examples**

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Fixed values — search periods 0.1–10 days, report top 5 peaks with whitening
result = (vt.Pipeline()
        .LS(0.1, 10.0, 0.1, npeaks=5, whiten=True, clip=5.0, clipiter=1,
           save_periodogram=True)).run(lc)
print(result.vars["LS_Period_1_0"])       # 1.23440877
print(result.vars["Log10_LS_Prob_1_0"])   # -4000.59209
pgram = result.files["LS_periodogram_0"]   # pd.DataFrame: frequency vs power

# Expression form — set period range relative to the time baseline of each LC.
# First compute min/max time with cmd.stats, then define tspan with cmd.expr,
# then pass expressions to LS.  LS is at pipeline index 2, so keys end in "_2".
result = (vt.Pipeline()
        .stats("t", "min,max")
        .expr("tspan=STATS_t_MAX_0-STATS_t_MIN_0")
        .LS("tspan/200", "tspan/2", 1e-3, npeaks=1)).run(lc)
print(result.vars["LS_Period_1_2"])       # 1.23534018

# Variable form — minp and maxp are per-star variables read from a list file.
# Each row in the list file supplies different search bounds for each LC.
# batch = pipe.run_filelist("lc_list.txt")   # list file has minp and maxp columns

# Batch: run on many light curves in parallel
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline().LS(0.1, 10.0, 0.1, npeaks=1).run_batch(lcs, nthreads=4)
print(batch.vars[["Name", "LS_Period_1_0", "Log10_LS_Prob_1_0"]])

# fixperiod_snr — evaluate LS at a known period
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Fixed number form: evaluate at period = 1.234
r = vt.Pipeline().LS(0.1, 10.0, 0.1, fixperiod_snr=1.234).run(lc)
print(r.vars["LS_SNR_PeriodFix_0"])            # SNR at period 1.234

# "ls" form: evaluate at the best peak from a prior LS search
r = (vt.Pipeline()
        .LS(0.1, 10.0, 0.1, npeaks=1)
        .LS(0.1, 10.0, 0.1, fixperiod_snr="ls")).run(lc)
print(r.vars["LS_SNR_PeriodFix_1"])            # SNR at period found by first LS

# "aov" form: evaluate LS at the best period from a prior AOV search
r = (vt.Pipeline()
        .aov(0.1, 10.0, 0.1, 0.01, npeaks=1)
        .LS(0.1, 10.0, 0.1, fixperiod_snr="aov")).run(lc)
print(r.vars["LS_SNR_PeriodFix_1"])

# "fixcolumn" form: read the period from a named per-star column
r = (vt.Pipeline()
        .LS(0.1, 10.0, 0.1, npeaks=1)
        .LS(0.1, 10.0, 0.1, fixperiod_snr="fixcolumn LS_Period_1_0")).run(lc)
print(r.vars["LS_PeriodFix_1"])
print(r.vars["Log10_LS_Prob_PeriodFix_1"])
```

---

## `aov` — Analysis of Variance

```python
cmd.aov(minp, maxp, subsample, finetune, npeaks=5, nbin=None,
        save_periodogram=False, whiten=False, clip=None,
        clipiter=None, uselog=False, maskpoints=None, fixperiod_snr=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `minp`, `maxp`, `subsample` | `float` or `str` | Period range and frequency step (same as LS). Accept variable names and expressions — see [Variable and expression parameters](#variable-and-expression-parameters).  Also accept per-LC arrays — see [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |
| `finetune` | `float` or `str` | Oversampling factor applied near peak frequencies for fine-tuning. Accepts var/expr forms and per-LC arrays. |
| `npeaks` | `int` | Number of peaks to report. |
| `nbin` | `int`, `str`, or `None` | Number of phase bins. If `None`, vartools selects automatically. Accepts var/expr forms and per-LC arrays. |
| `save_periodogram` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["aov_periodogram_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `uselog` | `bool` | Use the log of the AOV statistic. |
| `fixperiod_snr` | `float`, `int`, `str`, or `None` | Evaluate the AOV periodogram at a known period and report its significance. Same forms as `LS.fixperiod_snr`. When set, appends `PeriodFix_N`, `AOV_PeriodFix_N`, `AOV_SNR_PeriodFix_N`, `AOV_NEG_LN_FAP_PeriodFix_N`. |

`fixperiod_snr` accepts the same `"ls"` / `"aov"` / `"injectharm"` / `"fixcolumn NAME"` back-reference keywords as `LS.fixperiod_snr`, and they resolve correctly both inside a single `Pipeline` and across chain steps.

Use AoV instead of LS when the signal is strictly periodic but non-sinusoidal (e.g. eclipsing binaries, pulsating stars). AoV is less sensitive to the shape of the variation.

CLI equivalent: `-aov [Nbin N] minp maxp subsample finetune npeaks ...`

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

result = lc.aov(0.1, 10.0, 0.1, 0.01, npeaks=5, nbin=20,
                whiten=True, clip=5.0, clipiter=1, save_periodogram=True)
print(result.vars["Period_1_0"])   # 1.23583047 — top-peak period
pgram = result.files["aov_periodogram_0"]   # pd.DataFrame: frequency vs AOV statistic

# fixperiod_snr — evaluate AOV at a known period.
# `fixperiod_snr="aov"` back-references the prior -aov call, so both steps
# must share one vartools invocation — use Pipeline here.
result = (vt.Pipeline()
        .aov(0.1, 10.0, 0.1, 0.01, npeaks=1)
        .aov(0.1, 10.0, 0.1, 0.01, fixperiod_snr="aov")).run(lc)
print(result.vars["AOV_SNR_PeriodFix_1"])
```

---

## `aov_harm` — Multi-harmonic AoV

```python
cmd.aov_harm(nharm, minp, maxp, subsample, finetune, npeaks=5,
             save_periodogram=False, whiten=False, clip=None,
             clipiter=None, maskpoints=None, fixperiod_snr=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `nharm` | `int` or `str` | Number of harmonics to include in the model.  Also accepts variable names (`"nharmvar"`) and expressions (`"npeaks*2"`) — see [Variable and expression parameters](#variable-and-expression-parameters).  Also accepts per-LC arrays — see [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |
| `minp`, `maxp`, `subsample`, `finetune` | `float` or `str` | Same as `aov`. Accept variable names, expressions, and per-LC arrays — see [Variable and expression parameters](#variable-and-expression-parameters) and [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |
| `fixperiod_snr` | `float`, `int`, `str`, or `None` | Evaluate the AOV_HARM periodogram at a known period and report its significance. Same forms and output columns as `aov.fixperiod_snr`. Accepts the `"ls"` / `"aov"` / `"injectharm"` / `"fixcolumn NAME"` back-references in single-Pipeline and chain usage. |
| All others | — | Same as `aov`. |

Multi-harmonic AoV projects the phase-folded light curve onto a truncated Fourier series. It is better than plain AoV for highly non-sinusoidal signals such as RR Lyrae, Cepheids, and W UMa systems.

CLI equivalent: `-aov_harm nharm minp maxp subsample finetune npeaks ...`

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

result = lc.aov_harm(1, 0.1, 10.0, 0.1, 0.01, npeaks=2,
                     whiten=True, clip=5.0, clipiter=1, save_periodogram=True)
print(result.vars["Period_1_0"])   # 1.23533969 — top-peak period
pgram = result.files["aov_harm_periodogram_0"]

# fixperiod_snr — evaluate AOV_HARM at a known period (numeric, or back-refs
# to a prior -aov or -Injectharm call inside the same Pipeline).
result = lc.aov_harm(2, 0.1, 10.0, 0.1, 0.01, fixperiod_snr=1.23440877)
print(result.vars["AOV_HARM_SNR_PeriodFix_0"])
```

---

## `BLS` — Box-Least-Squares transit search

```python
cmd.BLS(minper, maxper, rmin=0.01, rmax=0.1, nbins=200,
        timezone=0, npeaks=1, subsample=1.0, nfreq=None,
        qmin=None, qmax=None,
        density_mode=False, stellar_density=None,
        min_exp_dur_frac=0.5, max_exp_dur_frac=1.5,
        df=None, extraparams=False, nobinnedrms=False,
        freq_grid=None, adjust_qmin=False, reduce_nbins=False,
        reportharmonics=False,
        save_periodogram=False, save_model=False,
        save_phcurve=False, save_jdcurve=False,
        ophcurve_phmin=0, ophcurve_phmax=1, ophcurve_phstep=0.005,
        ojdcurve_jdstep=0.02,
        correct_lc=False, fittrap=False, maskpoints=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `minper`, `maxper` | `float` or `str` | Period search range.  Also accept variable names and expressions — see [Variable and expression parameters](#variable-and-expression-parameters).  Also accept per-LC arrays — see [Per-LC array parameters](../pipeline.md#per-lc-array-parameters). |
| `rmin`, `rmax` | `float` or `str` | Minimum and maximum fractional transit duration (`r` mode, as a fraction of the orbital period).  Ignored when `qmin`/`qmax` are set.  Accept var/expr forms and per-LC arrays. |
| `qmin`, `qmax` | `float`, `str`, or `None` | Minimum and maximum fractional transit duration in `q` mode (`q` = ingress-to-egress fraction, not full duration).  When set, emits `"q" qmin qmax` instead of `"r" rmin rmax`.  Accept var/expr forms and per-LC arrays. |
| `nbins` | `int` or `str` | Number of phase bins.  Accepts var/expr forms and per-LC arrays. |
| `timezone` | `float` | Time-zone offset (0 for HJD/BJD). |
| `npeaks` | `int` | Number of transit candidates to report. |
| `subsample` | `float` or `str` | Frequency oversampling factor.  Accepts var/expr forms and per-LC arrays. |
| `nfreq` | `int`, `str`, or `None` | Fixed number of test frequencies (overrides `subsample`).  Accepts var/expr forms and per-LC arrays. |
| `density_mode` | `bool` | Use stellar density to set transit duration bounds instead of `rmin`/`rmax`. |
| `stellar_density` | `float`, `str`, or `None` | Stellar density (g/cm³) for density mode.  Accepts var/expr forms and per-LC arrays. |
| `min_exp_dur_frac`, `max_exp_dur_frac` | `float` or `str` | Expected-duration fractions for density mode (default `0.5` and `1.5`).  Accept var/expr forms and per-LC arrays. |
| `df` | `float`, `str`, or `None` | Fixed frequency step (alternative to `subsample`).  Accepts var/expr forms and per-LC arrays. |
| `extraparams` | `bool` | Compute extra BLS statistics (epoch, depth, etc.). |
| `nobinnedrms` | `bool` | Do not compute binned RMS statistics. |
| `freq_grid` | `str` or `None` | Frequency grid mode: `"stepP"` (uniform in period) or `"steplogP"` (log-uniform). |
| `adjust_qmin` | `bool` | Automatically adjust `qmin` based on the minimum cadence. |
| `reduce_nbins` | `bool` | Reduce `nbins` when `adjust_qmin` requires it (only active when `adjust_qmin=True`). |
| `reportharmonics` | `bool` | Report harmonic periods (½, ⅓, … of best period) as additional candidates. |
| `save_periodogram` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["BLS_periodogram_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `save_model` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["BLS_model_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `save_phcurve` | `bool`, `str`, or `Output` | Phase-folded model curve. `True` captures as `result.files["BLS_phcurve_N"]`. |
| `save_jdcurve` | `bool`, `str`, or `Output` | JD-sampled model curve. `True` captures as `result.files["BLS_jdcurve_N"]`. |
| `correct_lc` | `bool` | Subtract the best-fit box from the light curve. |
| `fittrap` | `bool` | Fit a trapezoidal rather than a box-shaped transit. |

Key output statistics: `BLS_Period_1_N`, `BLS_SDE_1_N` (signal detection efficiency), `BLS_SN_1_N` (signal-to-noise), `BLS_Depth_1_N`, `BLS_Qtran_1_N` (fractional duration), `BLS_Tc_1_N` (transit epoch).

CLI equivalent: `-BLS r rmin rmax minper maxper [nf N | optimal s] nbins timezone npeaks ...`

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3.transit")

# Fixed fractional duration (r mode) — simplest default.
result = lc.BLS(0.1, 20.0, rmin=0.01, rmax=0.1,
                nbins=200, nfreq=10000, npeaks=1, fittrap=True,
                save_periodogram=True, save_model=True)
print(result.vars["BLS_Period_1_0"])    # 2.12334706
print(result.vars["BLS_SN_1_0"])        # signal-to-noise
print(result.vars["BLS_SDE_1_0"])       # signal detection efficiency
pgram = result.files["BLS_periodogram_0"]   # pd.DataFrame: frequency vs BLS power

# Q mode (specify min/max fractional transit duration directly)
result2 = lc.BLS(0.1, 20.0, qmin=0.01, qmax=0.1,
                 nbins=200, nfreq=10000, npeaks=3)

# Density mode (recommended when stellar density is known).
# stellar_density in g/cm^3; min/max_exp_dur_frac scale the expected duration.
# Use a wide enough frac range — narrow ranges can exclude all trial periods.
result3 = lc.BLS(0.1, 20.0,
                 density_mode=True, stellar_density=1.4,
                 min_exp_dur_frac=0.1, max_exp_dur_frac=3.0,
                 nbins=200, nfreq=10000, npeaks=1)

# Log-uniform frequency grid with auto qmin adjustment (density mode).
result4 = lc.BLS(0.5, 10.0,
                 density_mode=True, stellar_density=1.4,
                 min_exp_dur_frac=0.1, max_exp_dur_frac=3.0,
                 nbins=200, nfreq=5000,
                 freq_grid="steplogP", adjust_qmin=True, reduce_nbins=True)
```

---

## `BLSFixPer` — BLS with fixed period

```python
cmd.BLSFixPer(period, rmin=0.01, rmax=0.1, nbins=200, timezone=0,
              qmin=None, qmax=None,
              save_model=False, correct_lc=False, fittrap=False,
              maskpoints=None)
```

Searches for the best transit epoch and duration at a known (fixed) period. Useful when a period has already been identified from a prior BLS or LS run.

| Parameter | Type | Description |
|-----------|------|-------------|
| `qmin`, `qmax` | `float` or `None` | Use `q` mode for duration bounds (ingress-to-egress fraction). When set, emits `"q" qmin qmax` instead of `"r" rmin rmax`. |
| All others | — | Same as `BLS`. |

!!! tip "Back-references for `period`"
    `period` accepts `"ls"`, `"aov"`, and `"fixcolumn NAME"` in addition to numeric values. The keyword resolves to the best period from the most recent matching prior command and works equally inside a single `Pipeline` or across chain steps (e.g. `lc.LS(...).BLSFixPer(period="ls")`). With no matching prior command in the chain, a `LookupError` is raised.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3.transit")

# Compute RMS, fit transit at fixed period, then check RMS on residuals
result = (
    lc.rms()
      .BLSFixPer("fix 2.12345", rmin=0.01, rmax=0.1, nbins=200, fittrap=True)
      .rms()
)
print(result.vars["BLSFixPer_Period_1"])    # 2.12345
print(result.vars["BLSFixPer_Depth_1"])     # transit depth
print(result.vars["BLSFixPer_Qtran_1"])     # fractional duration
```

---

## `BLSFixDurTc` — BLS with fixed duration and epoch, searching for period

```python
cmd.BLSFixDurTc(duration, Tc,
                minper=0.1, maxper=100.0, nfreq=10000,
                timezone=0, npeaks=1,
                fixdepth=None, qgress=None,
                save_periodogram=False, save_model=False,
                correct_lc=False, fittrap=False,
                save_phcurve=False, ophcurve_phmin=0.0,
                ophcurve_phmax=1.0, ophcurve_phstep=0.005,
                save_jdcurve=False, ojdcurve_jdstep=0.02,
                maskpoints=None)
```

Runs a BLS period search with the transit duration and epoch (Tc) held fixed.
The period that maximises the BLS statistic is found and reported.

`duration` and `Tc` each accept:

- A float → `fix <value>` (same value for all light curves)
- `"fixcolumn <colname>"` → read from a named per-star column
- `"list"` or `"list column <N>"` → read from an input-list column

| Parameter | Description |
|---|---|
| `duration` | Transit duration (days). |
| `Tc` | Epoch of transit center (JD/BJD). |
| `minper`, `maxper` | Period search range (days). |
| `nfreq` | Number of trial frequencies. |
| `timezone` | Add to JD to get local date (0 for UTC/BJD). |
| `npeaks` | Number of peaks to report. |
| `fixdepth` | Fix transit depth to this value (or column/list spec); `None` to optimise. |
| `qgress` | Fractional ingress/egress duration (requires `fixdepth`). |
| `save_periodogram` | Write BLS power spectrum to output dir. |
| `save_model` | Write best-fit transit model to output dir. |
| `correct_lc` | Subtract transit model from light curve. |
| `fittrap` | Fit a trapezoidal transit instead of a box. |

Output columns (suffix `N` is the pipeline command index):

| Column | Description |
|---|---|
| `BLSFixDurTc_Duration_N` | Fixed transit duration used. |
| `BLSFixDurTc_Tc_N` | Fixed epoch used. |
| `BLSFixDurTc_Period_1_N` | Best-fit period (first peak). |
| `BLSFixDurTc_SN_1_N` | Signal-to-noise of best peak. |
| `BLSFixDurTc_Depth_1_N` | Best-fit transit depth. |
| `BLSFixDurTc_Qtran_1_N` | Fractional transit duration. |
| `BLSFixDurTc_deltaChi2_1_N` | Δχ² of the best transit. |

```python
import pyvartools as vt

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Search for the period with duration and Tc fixed
result = lc.BLSFixDurTc(duration=0.05, Tc=2450000.1,
                        minper=0.5, maxper=10.0, nfreq=5000,
                        timezone=0, npeaks=1)
print(result.vars["BLSFixDurTc_Period_1_0"])     # best-fit period
print(result.vars["BLSFixDurTc_SN_1_0"])         # signal-to-noise
print(result.vars["BLSFixDurTc_Depth_1_0"])      # transit depth
```

---

## `BLSFixPerDurTc` — BLS with fixed period, duration, and epoch

```python
cmd.BLSFixPerDurTc(period, duration, Tc,
                   timezone=0,
                   fixdepth=None, qgress=None,
                   save_model=False, correct_lc=False, fittrap=False,
                   save_phcurve=False, ophcurve_phmin=0.0,
                   ophcurve_phmax=1.0, ophcurve_phstep=0.005,
                   save_jdcurve=False, ojdcurve_jdstep=0.02,
                   maskpoints=None)
```

Computes BLS transit statistics for a fully specified signal — no period
search is performed. The period, duration, and Tc are all fixed; the depth
is optimised by default (or also fixed if `fixdepth` is given).

`period`, `duration`, and `Tc` each accept a float, `"fixcolumn <colname>"`,
or `"list"` / `"list column <N>"` (same forms as `BLSFixDurTc`).

| Parameter | Description |
|---|---|
| `period` | Transit period (days). |
| `duration` | Transit duration (days). |
| `Tc` | Epoch of transit center (JD/BJD). |
| `timezone` | Add to JD to get local date (0 for UTC/BJD). |
| `fixdepth` | Fix transit depth (or column/list spec); `None` to optimise. |
| `qgress` | Fractional ingress/egress duration (requires `fixdepth`). |
| `save_model` | Write best-fit transit model to output dir. |
| `correct_lc` | Subtract transit model from light curve. |
| `fittrap` | Fit a trapezoidal transit instead of a box. |

Output columns (suffix `N` is the pipeline command index):

| Column | Description |
|---|---|
| `BLSFixPerDurTc_Period_N` | Period used. |
| `BLSFixPerDurTc_Duration_N` | Duration used. |
| `BLSFixPerDurTc_Tc_N` | Epoch used. |
| `BLSFixPerDurTc_Depth_N` | Best-fit (or fixed) transit depth. |
| `BLSFixPerDurTc_Qtran_N` | Fractional transit duration. |
| `BLSFixPerDurTc_deltaChi2_N` | Δχ² of the transit signal. |
| `BLSFixPerDurTc_SignaltoPinknoise_N` | Signal-to-pink-noise. |
| `BLSFixPerDurTc_fraconenight_N` | Fraction of Δχ² from one night. |
| `BLSFixPerDurTc_MeanMag_N` | Out-of-transit mean magnitude. |

```python
import pyvartools as vt

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Evaluate BLS statistics at a fully fixed transit signal
result = lc.BLSFixPerDurTc(period=2.12345, duration=0.05, Tc=2450000.1,
                           timezone=0, correct_lc=False)
print(result.vars["BLSFixPerDurTc_Depth_0"])      # transit depth
print(result.vars["BLSFixPerDurTc_deltaChi2_0"])  # Δχ² of signal
print(result.vars["BLSFixPerDurTc_SignaltoPinknoise_0"])   # signal-to-pink-noise
```

---

## `dftclean` — CLEAN periodogram

```python
cmd.dftclean(nbeam, maxfreq=None, save_dspec=False, save_wfunc=False,
             save_cspec=False, gain=0.1, SNlimit=3.0, npeaks=None,
             finddirtypeaks=None, finddirtypeaks_clip=None,
             finddirtypeaks_clipiter=None,
             outcbeam=False, useampspec=False, verboseout=False,
             maskpoints=None)
```

Computes the CLEAN deconvolution periodogram (Roberts et al. 1987). Output files: `"dftclean_dspec_N"` (dirty spectrum), `"dftclean_wfunc_N"` (window function), `"dftclean_cspec_N"` (CLEAN spectrum), `"dftclean_cbeam_N"` (CLEAN beam, when `outcbeam` is set).

| Parameter | Type | Description |
|-----------|------|-------------|
| `finddirtypeaks` | `int` or `None` | Number of peaks to find in the dirty spectrum before CLEANing. |
| `finddirtypeaks_clip` | `float` or `None` | Sigma-clipping threshold for dirty-peak finding. |
| `finddirtypeaks_clipiter` | `int` or `None` | Number of sigma-clipping iterations. |
| `outcbeam` | `bool`, `str`, or `Output` | Write the CLEAN beam to a file. Captured as `result.files["dftclean_cbeam_N"]`. |
| `useampspec` | `bool` | Use the amplitude spectrum instead of power spectrum for CLEANing. |
| `verboseout` | `bool` | Write verbose diagnostics to the output file. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Compute DFT CLEAN periodogram and find the top peak
result = lc.dftclean(4, maxfreq=10.0, npeaks=1, save_dspec=True)
print(result.vars["DFTCLEAN_CSPEC_PEAK_FREQ_0_0"])  # top CLEAN-spectrum peak frequency (cycles/day)
dspec = result.files["dftclean_dspec_0"]   # pd.DataFrame: dirty spectrum (frequency vs power)
```

---

## `wwz` — Weighted Wavelet Z-transform

```python
cmd.wwz(maxfreq="auto", freqsamp=None, tau0="auto", tau1="auto",
        dtau="auto", c=0.0125, save_transform=False,
        save_maxtransform=False,
        transform_format=None, transform_name=None,
        maxtransform_name=None, maskpoints=None)
```

Time-frequency analysis for non-stationary signals. Output files: `"wwz_transform_N"` (full time-frequency map), `"wwz_maxtransform_N"` (maximum power vs. time).

| Parameter | Type | Description |
|-----------|------|-------------|
| `transform_format` | `str` or `None` | Output format for the full transform: `"fits"` or `"pm3d"`. Only applies when `save_transform` is set. |
| `transform_name` | `str` or `None` | Naming format string for the full-transform output file (e.g. `"%s.wwz"`). |
| `maxtransform_name` | `str` or `None` | Naming format string for the max-transform output file. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/8")

# tau0 / tau1 set the time range scanned by the wavelet; derive them
# from the observed time baseline of the light curve.
result = lc.wwz(maxfreq=2.0, freqsamp=0.25,
                tau0=float(lc.t.min()), tau1=float(lc.t.max()),
                dtau=0.1, save_transform=True, save_maxtransform=True)
maxt = result.files["wwz_maxtransform_0"]   # pd.DataFrame: time vs peak frequency/power
```

---

## `GetLSAmpThresh` — LS amplitude threshold

```python
cmd.GetLSAmpThresh(period="ls", minp=0.1, thresh=10.0,
                   mode="harm", nharm=1, nsubharm=0,
                   listfile=None, noGLS=False)
```

Estimates the signal amplitude required to achieve a given detection threshold. Used in injection-recovery studies.

| Parameter | Type | Description |
|-----------|------|-------------|
| `mode` | `str` | Signal model: `"harm"` (Fourier series, default) or `"file"` (read template from `listfile`). |
| `nharm` | `int` | Number of harmonics (only when `mode="harm"`). |
| `nsubharm` | `int` | Number of sub-harmonics (only when `mode="harm"`). |
| `listfile` | `str` or `None` | Path to template signal file (required when `mode="file"`). |
| `noGLS` | `bool` | Use classical Lomb-Scargle instead of the generalized (GLS) form. |

!!! tip "Back-reference for `period`"
    `period` accepts the `"ls"` keyword to inherit the best period from the most recent prior `-LS`. Unlike most back-references, this is resolved by the vartools CLI itself — the CLI only understands `"ls"` / `"list"` and cannot take a bare number in this slot. Within a single `Pipeline` the keyword passes through verbatim. Across a chain boundary, pyvartools detects the mismatch and raises `NotImplementedError` when no prior `-LS` is present in the chain — in that case, use a single `Pipeline` invocation that includes the LS step.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Run LS, fit harmonic (fitonly), then compute minimum detectable amplitude
pipe = (vt.Pipeline()
        .LS(0.1, 10.0, 0.1, npeaks=1)
        .Killharm("ls", nharm=0, nsubharm=0, fitonly=True)
        .GetLSAmpThresh("ls", minp=0.1, thresh=-100.0, nharm=0, nsubharm=0))
result = pipe.run(lc)
print(result.vars["LS_Period_1_0"])           # 1.23440877
print(result.vars["LS_MinimumAmplitude_2"])   # 0.00248 mag
```

---
