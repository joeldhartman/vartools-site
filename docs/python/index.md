# pyvartools — Python API Overview

**pyvartools** is the Python interface to VARTOOLS. It lets you
load light curves into Python, run any combination of VARTOOLS analysis
commands on them, and work with the results as standard Python and pandas
objects.

---

## How it works

Every VARTOOLS analysis command (period search, detrending, sigma
clipping, transit fitting, …) has a corresponding Python class in
`pyvartools.commands`. These commands act on light curves, which can
be stored in LightCurve objects. The commands produce Result objects
that contain computed statistics, possibly modified light curves, and
any other auxiliary datasets (e.g., periodograms computed by a
period-finding command).

Internally, pyvartools passes the light curves and command sequence to the
VARTOOLS engine in one of two ways:

- **Library mode** — if `libvartoolspipeline.so` is installed (which
  `make install` does automatically), the engine runs **in-process**:
  light curve arrays are passed directly to the C library. Results,
  including modified light curves, are read back from C memory without
  writing to disk.
- **Subprocess mode** — if the shared library is not available, pyvartools
  launches the `vartools` binary as a subprocess, passing the light curve
  via stdin and parsing its stdout. The results are identical; only
  performance differs. This mode is also used automatically for operations
  that require output files on disk (e.g. writing periodogram files), or when
  using the `nthreads` parameter to perform multi-threaded batch processing.

From the user's perspective both modes behave identically; the choice is made
automatically.

---

## Three calling styles

### 1. Top-level functions (simplest)

The quickest way to run a single command is to call it directly on the `vt`
module. The first argument is the light curve — pass a filename, a
`LightCurve` object, a DataFrame, a 2-D numpy array, or a tuple of
`(t, mag, err)` arrays:

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

Call commands directly as methods on a `LightCurve` object. Every command
executes **immediately** and returns a `Result`. Further commands can be 
executed on the `Result` which accumulates any statistics and output produced 
by the new command:

```python
import pyvartools as vt

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Single command — immediate
result = lc.LS(0.5, 10.0, 0.1)
print(result.varobjs.LS.Period_1)

# Chain multiple commands — each step runs immediately and returns a Result;
# the chain is split into one vartools call per step
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
r2 = r1.Killharm(period=r1.varobjs.LS.Period_1, nharm=2)
```

!!! note "Pipeline-stateful commands"
    A handful of commands (`savelc`, `restorelc`, `columnsuffix`, `ifcmd`, `o`)
    only work correctly within a single vartools invocation.  Calling them as
    methods on `LightCurve` or `Result` raises a `NotImplementedError` with a
    message directing you to use `Pipeline` instead.

See the [Method Chaining API](chaining.md) page for the full reference.

### 3. Pipeline objects (for reuse and efficient batch processing)

A `Pipeline` holds an ordered sequence of commands and can be applied to
many different light curves. This is the natural choice when you want to
define an analysis procedure once and run it over a large collection of files:

```python
import pyvartools as vt
from pyvartools import commands as cmd

pipe = vt.Pipeline([
    cmd.clip(sigclip=5.0),
    cmd.LS(0.5, 10.0, 0.1),
])

# Run on a single light curve
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = pipe.run(lc)

# Run on a list of light curves — one vartools call for all of them
batch = pipe.run_batch([vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)])
print(batch.vars[["Name", "LS_Period_1_1"]])

# Read files directly from disk, and use 2 parallel processes
# no Python I/O, fastest for large surveys
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
cmd.Killharm(period="ls", nharm=3, nsubharm=0)
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

pipe = vt.Pipeline([
    columnsuffix("short"),
    LS(minp=0.5, maxp=5.0, subsample=0.1),
    columnsuffix("long"),
    LS(minp=5.0, maxp=50.0, subsample=0.1),
])
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
| `pipe.run_combinelcs(groups)` | list of file-path groups | `BatchResult` |

All run methods accept `capture_lc=True` to include the output light curve in
the result, and the global vartools options `randseed`, `skipmissing`, `jdtol`,
and `matchstringid`.  Batch methods also accept `nthreads=N` to run vartools
with `-parallel N`.
