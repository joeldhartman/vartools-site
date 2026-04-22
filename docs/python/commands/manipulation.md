# Light Curve Manipulation

Commands that transform, resample, or reinterpret the light curve in-memory — column arithmetic, time manipulation, unit conversions, and Fourier transforms of evenly-sampled data.

---

## `sortlc` — Sort observations

```python
cmd.sortlc(var=None, reverse=False)
```

Sort observations by time (default) or by any other variable. `reverse=True` sorts in descending order.

---

## `binlc` — Bin in time

```python
cmd.binlc(method="average", binsize=None, nbins=None,
          time_output="tcenter", bincolumns=None,
          bincolumnsonly=False, T0=None, firstbinshift=None,
          maskpoints=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `method` | `str` | `"average"`, `"median"`, or `"weightedaverage"`. |
| `binsize` | `float` | Bin width in time units. Either `binsize` or `nbins` must be given. |
| `nbins` | `int` | Number of bins (alternative to `binsize`). |
| `time_output` | `str` | Output time for each bin: `"tcenter"`, `"taverage"`, `"tmedian"`, or `"tnoshrink"`. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Bin in time with 0.01-day bins (median combination)
result = lc.binlc(method="median", binsize=0.01)
binned_lc = result.lc

# Phase-fold then bin into 100 phase bins.  `cmd.Phase(period="ls")`
# back-references the prior LS and works both in a single Pipeline and
# across chain steps.
pipe = vt.Pipeline([
    cmd.LS(0.1, 10.0, 0.1, npeaks=1),
    cmd.Phase(period="ls"),
    cmd.binlc(method="median", nbins=100),
])
result = pipe.run(lc, capture_lc=True)
phase_binned_lc = result.lc
```

---

## `Phase` — Phase-fold the light curve

```python
cmd.Phase(period="ls", T0=None, phasevar=None, startphase=None)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | `float` or `str` | Period to fold on. Can be a number, or a keyword like `"ls"`, `"aov"`, `"bls"`, or `"fixcolumn NAME"` to inherit the period found by a prior pipeline command. |
| `T0` | `float`, `str`, or `None` | Reference epoch. Accepts a number, or `"bls <phase_offset>"` to derive `T0 = Tc - phase_offset * Period` from the prior BLS result (e.g. `T0="bls 0.5"` puts mid-transit at phase 0.5). |
| `phasevar` | `str` or `None` | Name of the output phase variable. |
| `startphase` | `float` or `None` | Starting phase (default 0). |

!!! tip "Back-references work across chain steps"
    `period` accepts `"ls"`, `"aov"`, `"bls"`, and `"fixcolumn NAME"`; `T0` accepts the `"bls <phase_offset>"` form. All of these resolve correctly inside a single `Pipeline` *and* across chain boundaries (e.g. `lc.LS(...).Phase(period="ls")` or `lc.BLS(...).Phase(period="bls", T0="bls 0.5")`). In batch-chain mode the resolved values become per-LC, so each light curve is folded on its own period / Tc. Missing prior command → `LookupError`.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Phase-fold at a known period
result = lc.Phase(period=1.2354)
phased_lc = result.lc   # time column replaced by orbital phase

# Use period found by BLS, set mid-transit at phase 0.5.
# `period="bls"` and `T0="bls 0.5"` work across the chain boundary —
# pyvartools reads BLS_Period_1 / BLS_Tc_1 from the prior result.
lc_transit = vt.LightCurve.from_file("EXAMPLES/3.transit")
result = (
    lc_transit
        .BLS(0.5, 5.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=20000, npeaks=1)
        .Phase(period="bls", T0="bls 0.5")
        .binlc(method="median", nbins=200)
)
phase_binned_lc = result.lc
```

---

## `resample` — Resample onto a new time grid

```python
cmd.resample(method="linear",
             left=None, right=None,
             nbreaks=None, order=None,
             file_times=None, file_column=None,
             gaps=None,
             tstart=None, tstop=None, delt=None, Npoints=None)
```

Methods: `"nearest"`, `"linear"`, `"spline"`, `"splinemonotonic"`, `"bspline"`. Specify the new grid with `delt` (step size), `Npoints` (number of points), or `file_times` (times from a file).

| Parameter | Type | Description |
|-----------|------|-------------|
| `left` | `float` or `None` | First-derivative boundary condition at the left edge of the spline. Only for `method="spline"` or `"splinemonotonic"`. |
| `right` | `float` or `None` | First-derivative boundary condition at the right edge of the spline. Only for `method="spline"` or `"splinemonotonic"`. |
| `nbreaks` | `int` or `None` | Number of interior break points for B-spline fitting. Only for `method="bspline"`. |
| `order` | `int` or `None` | Polynomial order of the B-spline. Only for `method="bspline"`. |
| `file_times` | `str` or `None` | Path to a file containing times (emits `"file" "fix" path`), or a string starting with `"list"` for list-column mode (e.g. `"list column 2"`). |
| `file_column` | `int` or `None` | Column number in the times file. Only used with the `"fix"` form (path given). |
| `gaps` | `str` or `None` | Gaps option string, e.g. `"fix"`, `"list"`, `"fixcolumn myvar"`, `"expr someexpr"`. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")

# Linear interpolation with default time grid
result = lc.resample(method="linear")

# Monotonic spline onto a fixed time grid with 1000 points
result2 = lc.resample(method="splinemonotonic",
                      tstart=53726, tstop=53756, Npoints=1000)

# B-spline with 20 break points, order 3
result3 = lc.resample(method="bspline", nbreaks=20, order=3, Npoints=500)
```

---

## `expr` — Analytic expression

```python
cmd.expr(expression, vartype=None, outputcolumns=None)
```

Evaluate an analytic expression to create or update a variable. The expression string has the form `varname=formula`, e.g. `"residual=mag-model"`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | `str` | Expression of the form `varname=formula`. |
| `vartype` | `str` or `None` | Type of the LHS variable: `None` (per-observation, default), `"listvar"` (per-star), `"scalar"` (per-thread), or `"const"` (global constant). |
| `outputcolumns` | `str` or `None` | Comma-separated list of column names to output. |

The `vartype` parameter controls what kind of variable is created on the left-hand side:

- **`None`** (default) — per-observation light-curve vector, one value per point.
- **`"listvar"`** — per-star variable that persists across all light curves. LC vectors on the RHS are evaluated at the first observation (index 0). Useful with aggregate functions.
- **`"scalar"`** — per-thread scalar value.
- **`"const"`** — global constant, same value for all LCs.

The expression engine supports aggregate functions like `mean(mag)`, `stddev(mag)`, `pct(mag, 95.0)`, and filtering like `mean(mag, t>53730)`. See the [Analytic Expressions](../../cli/expressions.md) reference for the complete list of operators, functions, and constants.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/1")

# Apply a mathematical transform in-place
result = lc.expr("mag=sqrt(mag+5)")

# Compute per-star mean magnitude using an aggregate function.
# `avg` is a `listvar` variable created inside vartools — it must be visible
# to the next `-expr` step, so these three commands share one Pipeline.
pipe = vt.Pipeline([
    cmd.expr("avg=mean(mag)", vartype="listvar"),
    cmd.expr("dmag=mag-avg"),
    cmd.rms(),
])
result = pipe.run(lc)

# Define a global constant and use it
pipe = vt.Pipeline([
    cmd.expr("zp=25.0", vartype="const"),
    cmd.expr("flux=10^(-0.4*(mag-zp))"),
])

# Convert to flux, normalise by median, then compute statistics
pipe = vt.Pipeline([
    cmd.expr("flux=10^(-0.4*(mag-25.0))"),
    cmd.stats("flux", ["median"]),
    cmd.expr("flux=flux/STATS_flux_MEDIAN_1"),
    cmd.stats(["flux", "mag"], ["median", "stddev"]),
])
result = pipe.run(lc)
print(result.vars["STATS_flux_MEDIAN_1"])   # original median flux
print(result.vars["STATS_flux_MEDIAN_3"])   # ≈ 1.0 after normalisation
```

---

## `FFT` / `IFFT` — Fast Fourier Transform

```python
cmd.FFT(input_real, input_imag, output_real, output_imag)
cmd.IFFT(input_real, input_imag, output_real, output_imag)
```

Compute the FFT or inverse FFT of two variables (real and imaginary parts). Results are stored in the named output variables.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/11")

# High-pass Fourier filter on a uniformly sampled light curve
pipe = vt.Pipeline([
    cmd.FFT("mag", "NULL", "fftreal", "fftimag"),
    cmd.rms(),
    # Zero low-frequency components (below 1/500 of full spectrum)
    cmd.expr("fftreal=(NR>(Npoints_1/500.0))*(NR<(Npoints_1*499.0/500.0))*fftreal"),
    cmd.expr("fftimag=(NR>(Npoints_1/500.0))*(NR<(Npoints_1*499.0/500.0))*fftimag"),
    cmd.IFFT("fftreal", "fftimag", "mag_filter", "NULL"),
])
result = pipe.run(lc, capture_lc=True)
```

---

## `difffluxtomag` / `fluxtomag` — Flux conversions

```python
cmd.difffluxtomag(mag_constant, offset=0.0, magcolumn=None)
cmd.fluxtomag(mag_constant, offset=0.0)
```

Convert differential or absolute flux to magnitude. `mag_constant` and `offset` accept numbers, variable names, or expression strings.

**Examples**

```python
# Synthesize a flux-unit light curve from an existing magnitude LC,
# then convert it back to magnitudes using `fluxtomag`.
import numpy as np

lc_mag = vt.LightCurve.from_file("EXAMPLES/2")
t, mag, err = lc_mag.t, lc_mag.mag, lc_mag.err
flux = 10.0 ** (-0.4 * (mag - 25.0))
lc_flux = vt.LightCurve.from_arrays(t, flux, err * flux * np.log(10) / 2.5)

# `mag_constant` is the zero-point magnitude (here 25.0, matching the
# synthesis above).
result = lc_flux.fluxtomag(25.0, offset=0.0)
print(result.lc.mag[:3])   # back to approximately the original values
```

---

## `changeerror` — Rescale measurement uncertainties

```python
cmd.changeerror(maskpoints=None)
```

`changeerror` replaces the formal per-point uncertainties with the RMS of the
light curve.  Useful before χ² or MCMC fitting when the quoted uncertainties
are known to be mis-calibrated.

**Example**

```python
lc = vt.LightCurve.from_file("EXAMPLES/4")
result = (
    lc.chi2()
      .changeerror()
      .chi2()
)
print(result.vars["Chi2_0"])   # 5.19874 (original)
print(result.vars["Chi2_2"])   # ≈ 1.0 (after rescaling errors to RMS)
```

---

## `converttime` — Time system conversion

```python
cmd.converttime(input_format, output_format, ra=None, dec=None,
                input_subtract=None, output_subtract=None,
                input_sys=None, output_sys=None, ephemfile=None,
                leapsecfile=None)
```

Convert between time systems. `input_format` / `output_format` are `"mjd"`, `"jd"`, `"hjd"`, or `"bjd"`. For HJD/BJD conversions, provide `ra` and `dec` in degrees. `input_sys` / `output_sys` can be `"tdb"` or `"utc"`.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/1")

# Convert JD (minus 2400000) to HJD for a known sky position
result = lc.converttime(
    input_format="jd",
    output_format="hjd",
    ra=88.079166,
    dec=32.5533,
    input_subtract=2400000.0,
)
hjd_lc = result.lc
```

---

## `match` — Match against a catalog

```python
cmd.match(catalog, matchcolumn, addcolumns, missing="nanmissing",
          source="file", inlist_column=None, skipnum=None,
          skipchar=None, delimiter=None, opencommand=None)
```

Match each light curve against rows in a catalog file and add columns from the catalog. `addcolumns` is a comma-separated list like `"ra:2,dec:3"`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `catalog` | `str` | Path to the catalog file. Ignored when `source="inlist"`. |
| `source` | `str` | `"file"` (default) — one catalog for all LCs; `"inlist"` — each LC specifies its own catalog in a list column. |
| `inlist_column` | `str` or `int` or `None` | Column number/name in the input list that holds per-LC catalog paths. Required when `source="inlist"`. |
| `matchcolumn` | `str` | Column specification for matching, e.g. `"t:1"` (variable:column) or `"1"` (column number). |
| `addcolumns` | `str` | Comma-separated `varname:colnum[:dtype]` specs for columns to import. |
| `missing` | `str` | How to handle unmatched rows: `"cullmissing"`, `"nanmissing"`, or `"missingval <value>"`. |

---

## `rescalesig` / `ensemblerescalesig` — Rescale per-point uncertainties

```python
cmd.rescalesig(maskpoints=None)
cmd.ensemblerescalesig(sigclip=5.0, maskpoints=None)
```

Rescale the formal per-point magnitude uncertainties so that the reduced χ² (relative to the weighted mean magnitude) equals 1. `rescalesig` operates on each light curve independently. `ensemblerescalesig` computes a single rescaling factor from the full collection of light curves, which is more robust for batches dominated by well-behaved constant sources and is the more common choice for survey-scale photometry pipelines.

**Parameters**

- `sigclip : float` (ensemblerescalesig only) — σ-clipping threshold for identifying outlier stars during the ensemble factor determination. Default 5.0.
- `maskpoints : str, optional` — Mask-variable name; only points with `mask > 0` contribute.

**Output columns**: `RescaleFactor_N` (`rescalesig`); `SigmaRescaleFactor_N` (`ensemblerescalesig`).

---
