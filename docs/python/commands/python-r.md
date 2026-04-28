# Calling Python or R

Wrappers for vartools' embedded `-python` / `-R` interpreters, used to run user code on each light curve from within a pipeline.  Note that pyvartools does not yet ship a typed wrapper for `-python` — use `Raw` (see [Miscellaneous](misc.md)) or write a custom `VartoolsCommand` subclass.

---

### `R` — Run R code

**Syntax**

```python
cmd.R(command, fromfile=False, init=None, init_fromfile=False,
      vars=None, invars=None, outvars=None, outputcolumns=None,
      process_all_lcs=False, verbose=False, continueprocess=None)
```

**Description**

Execute arbitrary R code on each light curve. VARTOOLS embeds the user-supplied code in an R function and calls it once per light curve (or once for all light curves with `process_all_lcs=True`). Light-curve variables are passed to R as native R vectors. `vars` specifies variables to pass both into and out of R; `invars`/`outvars` allow separate control. `init` is R code run once before the batch loop begins (typically used for library imports and function definitions).

The `R_HOME` environment variable must be set before calling vartools (find the correct value with `R RHOME`; adding `export R_HOME=$(R RHOME)` to your `.bashrc` is recommended). Under `-parallel`, a separate R sub-process is launched per thread; initialization runs independently for each thread, and globals are not shared between threads.

CLI equivalent: [`-R`](../../cli/python-r.md#-r).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Inline R code (default), or path to an R script file when `fromfile=True`. |
| `fromfile` | `bool` | If `True`, treat `command` as a file path rather than an inline string. |
| `init` | `str` or `None` | R code (or file path when `init_fromfile=True`) executed once before processing. Typical use: library imports and function definitions. |
| `init_fromfile` | `bool` | If `True`, `init` is a file path. |
| `vars` | `str` or `None` | Comma-separated list of variables passed both into and received back from R. |
| `invars` | `str` or `None` | Variables passed into R only (alternative to `vars`). |
| `outvars` | `str` or `None` | Variables received back from R only (alternative to `vars`). |
| `outputcolumns` | `str` or `None` | Subset of out-vars to emit in the output statistics table as `R_<name>_N`. |
| `process_all_lcs` | `bool` | Pass all light curves at once. Vector inputs arrive as lists of vectors; scalar inputs as lists. The output variables must also be lists with one entry per LC. |
| `verbose` | `bool` | Allow R to print to stdout (default: R runs in `--slave` mode). |
| `continueprocess` | `int` or `None` | Reuse the sub-process from the *N*-th prior `-R` (1-indexed). Shares R state; no initialization code may be supplied. |

**Output**

This command produces no output statistics by default; user-defined `outputcolumns` appear as `R_<name>_N` in `result.vars`.

**Examples**

**Example 1.** Compute the standard deviation of the magnitudes for each light curve in `EXAMPLES/lc_list` using R; the result appears as `R_b_0` in the output table.

```python
batch = (vt.Pipeline()
         .R("b <- sd(mag)",
            invars="mag", outvars="b", outputcolumns="b")
         ).run_filelist("EXAMPLES/lc_list",
                        columns={"t": 1, "mag": 2, "err": 3})
print(batch.vars[["Name", "R_b_0"]])
```

**Example 2.** Same as Example 1 but using `process_all_lcs=True` to send the whole batch to R at once. Inside R, `mag` arrives as a list of vectors and the output `b` must also be a list (one entry per LC).

```python
batch = (vt.Pipeline()
         .R("b <- list(); for(i in 1:length(mag)) "
            "{ b[[i]] <- sd(mag[[i]]); }",
            invars="mag", outvars="b", outputcolumns="b",
            process_all_lcs=True)
         ).run_filelist("EXAMPLES/lc_list",
                        columns={"t": 1, "mag": 2, "err": 3})
```

**Example 3.** ARIMA modelling using R's `forecast` package. After saving the original `mag`, we bin and resample the LC onto a uniform grid (ARIMA needs evenly-sampled data), call `auto.arima`, and subtract the residuals to obtain the smoothed model `mag_arima`. The model is then resampled back to the original time grid and the original `mag` is restored. Requires `tseries` and `forecast` to be installed in R.

The pyvartools `resample` wrapper does not yet expose the
`-resample linear file list listcolumn 1 tcolumn 1` form needed for the
back-resampling step in this example, so the cleanest Python equivalent
goes through `subprocess`:

```python
import subprocess
subprocess.run([
    "vartools", "-l", "EXAMPLES/lc_list",
    "-inputlcformat", "t:1,mag:2,err:3",
    "-header",
    "-savelc",
    "-binlc", "average", "binsize", "0.05", "taverage",
    "-resample", "linear", "delt", "fix", "0.05",
    "-R",
    ("mag_ts <- ts(mag, start=1, end=length(t), frequency=1); "
     "arima_model <- auto.arima(mag_ts); "
     "mag_arima <- mag - as.vector(arima_model$residuals);"),
    "init", "library(tseries); library(forecast);",
    "invars", "mag,t", "outvars", "mag_arima",
    "-resample", "linear", "file", "list", "listcolumn", "1", "tcolumn", "1",
    "-restorelc", "1", "vars", "mag",
    "-o", "EXAMPLES/OUTDIR1", "nameformat", "%s.arimamodel",
    "columnformat", "t,mag,mag_arima",
], check=True)
```

The resulting `*.arimamodel` files contain `t`, the original `mag`, and the smoothed `mag_arima`:

![EXAMPLES/2 — ARIMA model overlay](../../assets/examples/R_arimamodel_2_data.png)
![ARIMA model residuals — EXAMPLES/2](../../assets/examples/R_arimamodel_2_resid.png)

**Example 4.** Same as Example 3 but with the ARIMA fit + diagnostic plots wrapped in a function `DoArimaFitPlot` defined in `EXAMPLES/Rexample4.R`. The function writes per-LC `*.arimaforecast.png` and `*.arimaresiduals.png` files via R's `forecast` plotting helpers.

![ARIMA forecast plot for EXAMPLES/2](../../assets/examples/R_arimaforecast_2.png)
![ARIMA residuals plot for EXAMPLES/2](../../assets/examples/R_arimaresiduals_2.png)

---
