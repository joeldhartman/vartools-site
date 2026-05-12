# pyvartools — Python API Overview

**pyvartools** is the Python interface to VARTOOLS. It provides Python classes for the VARTOOLS analysis commands and reads, processes, and returns light curves through standard Python and pandas data structures.

---

## How it works

Every VARTOOLS analysis command (period search, detrending, sigma clipping, transit fitting, ...) has a corresponding Python class in `pyvartools.commands`. The classes act on light curves represented by `LightCurve` objects, and produce `Result` objects containing the computed statistics, the modified light curve (when capture is requested), and any auxiliary datasets associated with the command (e.g., a periodogram produced by a period-finding command).

Internally, pyvartools has two execution paths and selects between them automatically:

- Library mode — the default fast path. The VARTOOLS engine runs in-process via a shared library (`libvartoolspipeline.so`, installed by `make install`).
- Subprocess mode — used when library mode is not available, or for combinations of options the in-process path does not yet cover (e.g. `nthreads > 1`, `timeout=...`, resuming from a partial `stats_file`). The `vartools` binary runs as a separate process.

Both paths produce identical outputs. See [Performance and reusing a Pipeline](pipeline.md#performance-and-reusing-a-pipeline) for the details.

---

## Three calling styles

### 1. Top-level functions

The most direct form for running a single command is to call it as a function on the `vt` module. The first argument is the light curve — a filename, a `LightCurve` object, a DataFrame, a 2-D numpy array, or a tuple of `(t, mag, err)` arrays:

```python
import numpy as np
import pyvartools as vt

# From a filename
result = vt.LS("EXAMPLES/2", 0.5, 10.0, 0.1)

# From a LightCurve object
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = vt.LS(lc, 0.5, 10.0, 0.1)

# From a pandas DataFrame
df = lc.to_dataframe()
result = vt.LS(df, 0.5, 10.0, 0.1)

# From a 2-D numpy array (columns: t, mag, err)
arr2d = np.column_stack([lc.t, lc.mag, lc.err])
result = vt.LS(arr2d, 0.5, 10.0, 0.1)

# From a tuple of 1-D arrays
t, mag, err = lc.t, lc.mag, lc.err
result = vt.LS((t, mag, err), 0.5, 10.0, 0.1)

print(result.varobjs.LS.Period_1)
```

Run-time options (`capture_lc`, `timeout`, `randseed`, …) can be passed as
keyword arguments alongside the command parameters.

### 2. Chaining commands by calling on `LightCurve` or `Result` objects.

Call commands directly as methods on a `LightCurve` object. Each command
executes immediately and returns a `Result`. Further commands can be 
executed on the `Result` which accumulates any statistics and output produced 
by the new command:

```python
import pyvartools as vt

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Single command — immediate
result = lc.LS(0.5, 10.0, 0.1)
print(result.varobjs.LS.Period_1)

# Chain multiple commands — each step runs immediately and returns a Result
result = lc.clip(sigclip=5.0).LS(0.5, 10.0, 0.1).rms()
print(result.varobjs.LS.Period_1)   # top LS period
print(result.varobjs.rms.RMS)       # RMS of the clipped, period-corrected LC
```

Because each step returns a `Result` you can continue the chain from any
intermediate result, passing run-time options (e.g. `capture_lc`, `randseed`)
as keyword arguments:

```python
# Run LS, then remove the best-fit harmonic at the detected period
r1 = lc.LS(0.5, 10.0, 0.1)
r2 = r1.harmonicfilter(period=r1.varobjs.LS.Period_1, nharm=2)
```

!!! note "Pipeline-stateful commands"
    A handful of commands (`savelc`, `restorelc`, `columnsuffix`, `ifcmd`, `o`)
    only make sense inside a single `Pipeline` invocation.  Calling them as
    methods on `LightCurve` or `Result` raises `NotImplementedError`.

See the [Method Chaining API](chaining.md) page for the full reference.

### 3. Pipeline objects

A `Pipeline` is an ordered sequence of commands that can be applied to one or more light curves. It is the appropriate form for defining an analysis procedure once and running it over many input files, and for the other situations covered in the [Pipeline](pipeline.md) page:

```python
import pyvartools as vt
from pyvartools import commands as cmd

pipe = vt.Pipeline().clip(sigclip=5.0).LS(0.5, 10.0, 0.1)

# Run on a file path — pyvartools loads the LC for you
result = pipe.run("EXAMPLES/2")

# Run on an in-memory LightCurve (or a DataFrame, or an astropy TimeSeries)
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = pipe.run(lc)

# Run on a list of paths (or LightCurves) — all processed in one batch call
batch = pipe.run_batch([f"EXAMPLES/{i}" for i in range(1, 11)])
print(batch.vars[["Name", "LS_Period_1_1"]])

# Read files directly from disk with 2 parallel processes —
# no Python I/O, appropriate for large surveys
batch = pipe.run_filelist("EXAMPLES/lc_list", nthreads=2)
print(batch.vars[["Name", "LS_Period_1_1"]])
```

A `Pipeline` is reusable and stateless: the same instance can be run on as
many light curves as needed. 

---

## Light curves

`LightCurve` is the central input data container. It wraps a pandas
DataFrame and understands the standard three-column layout (time `t`,
magnitude `mag`, magnitude uncertainty `err`), but none of these
columns are required — any column layout is accepted.

```python
# From a file on disk (ASCII or FITS)
lc = vt.LightCurve.from_file("EXAMPLES/2")

# From numpy arrays
import numpy as np
t = np.linspace(0, 30, 300)
mag = 10.0 + 0.1*np.sin(2*np.pi*t/2.3)
err = np.full(300, 0.01)
lc = vt.LightCurve.from_arrays(t, mag, err, name="my_star")
```

Extra columns (airmass, pixel coordinates, etc.) are passed through to
vartools automatically.

See [LightCurve](lightcurve.md) for the full API.

---

## Results

Every run method returns a `Result` (single LC) or `BatchResult` (multiple
LCs). Output statistics are available in three equivalent forms:

```python
result = lc.LS(0.5, 10.0, 1e-3)

result.vars["LS_Period_1_0"]   # pandas Series key — e.g. 1.23534
result.varobjs.LS.Period_1       # structured per-command namespace
result.LS_Period_1_0          # attribute shorthand
```

When `capture_lc=True` is passed, the output light curve is available as
`result.lc`. Auxiliary output files (periodograms, model files, etc.) are
available in `result.files`.

`BatchResult` adds a `.vars` DataFrame (one row per LC) and per-LC `Result`
access via `batch[i]` or iteration.

See [Results](results.md) for the full reference.

---

## Commands

Every VARTOOLS command has a Python class in `pyvartools.commands`. Parameters
map directly to the command's arguments:

```python
from pyvartools import commands as cmd

cmd.LS(minp=0.5, maxp=10.0, subsample=0.1)
cmd.BLS(minper=0.5, maxper=10.0, qmin=0.01, qmax=0.1, nfreq=20000, nbins=200)
cmd.harmonicfilter(period="ls", nharm=3, nsubharm=0)
cmd.clip(sigclip=5.0)
cmd.rms()
```

User-developed extension commands (compiled shared libraries) are also
supported via `UserCommand`, `load_userlib()`, and `discover_userlibs()`.
See [Commands](commands/index.md) for the full list and parameter reference.

---

## Output column naming

Output statistics are named following the VARTOOLS convention:

```
LS_Period_1_0    → LS command, top peak (1), command index 0
LS_Period_1_1    → LS command, top peak (1), command index 1 (second command in chain)
BLS_SDE_1_0      → BLS command, top peak, command index 0
```

The numeric suffix is the 0-based position of the command in the pipeline,
making names unique when the same command type appears more than once.

When constructing commands in a `Pipeline` object, you can produce human-readable suffixes by inserting `columnsuffix()` before the command:

```python
from pyvartools.commands import columnsuffix, LS

pipe = (vt.Pipeline()
        .columnsuffix("short")
        .LS(minp=0.5, maxp=5.0, subsample=0.1)
        .columnsuffix("long")
        .LS(minp=5.0, maxp=50.0, subsample=0.1))
result = pipe.run(lc)
print(result.vars["LS_Period_1_short"])
print(result.vars["LS_Period_1_long"])
```

---

## Run method reference

| Method | Input | Returns |
|--------|-------|---------|
| `vt.CMD(lc_input, ...)` | filename / LC / DataFrame / array | `Result` (immediate) |
| `lc.CMD(...)` | — | `Result` (immediate) |
| `result.CMD(...)` | — | `Result` on `result.lc` (prior vars preserved) |
| `LightCurveBatch(lcs).CMD(...).run()` | — | `BatchResult` |
| `LightCurveBatch(lcs).run_CMD(...)` | — | `BatchResult` (immediate) |
| `pipe.run(lc)` | `LightCurve` | `Result` |
| `pipe.run_file(path)` | file path | `Result` |
| `pipe.run_batch(lcs)` | list of `LightCurve` | `BatchResult` |
| `pipe.run_filelist(paths)` | list of paths or path to list-file | `BatchResult` |
| `pipe.run_filelist(paths, combinelcs=True)` | list-file lines of comma-joined paths | `BatchResult` |
| `pipe.run_combinelc(files)` | list of files combined into one LC | `Result` |
| `pipe.run_combinelcs(groups)` | list of file-path groups | `BatchResult` |

All run methods accept `capture_lc=True` to include the output light curve in
the result, and the global vartools options `randseed`, `skipmissing`, `jdtol`,
and `matchstringid`.  Batch methods also accept `nthreads=N` to run vartools
with `-parallel N`.
