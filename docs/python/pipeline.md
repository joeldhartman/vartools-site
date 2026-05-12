# Pipeline

`Pipeline` is an alternative to the [Chaining API](chaining.md). Use it when:

- **You're running a survey-scale batch.** `run_batch()` and
  `run_filelist()` process all the light curves in one call, amortising
  setup cost across the whole batch and supporting multi-threaded
  parallel processing via `nthreads=N`.
- **You want to attach per-LC values that aren't simple command
  parameters.** `perlc_vars` lets you supply a different value per
  light curve for things like search period bounds, output filenames,
  or metadata referenced by name in analytic expressions.
- **You want to initialise per-observation variables before the chain
  runs.** `perpoint_vars` lets you create custom per-point variables
  (masks, weights, indices) without modifying your light curves.
- **You want to reuse the same command sequence many times.** A
  `Pipeline` instance can be run repeatedly against different inputs.
- **Your light curves are already on disk and you don't want to round-trip
  through Python.** `run_file()` and `run_filelist()` read the files
  directly.
- **You need to checkpoint a long-running job.** Set `stats_file=PATH`
  to flush statistics to disk as each light curve completes, and
  `resume=True` to pick up where a killed run left off.  See
  [Streaming output and resume](#streaming-output-and-resume).
- **You want to validate the pipeline shape before running it.**
  `Pipeline.validate()` returns the list of output column names the
  pipeline would produce, or raises `PipelineValidationError` if the
  pipeline is malformed — useful for fast turnaround during pipeline
  construction.

A `Pipeline` is built by chaining command builders and run on one or more
light curves. The same `Pipeline` produces identical results regardless
of which execution path pyvartools chooses internally; you don't need to
think about it.

---

## Construction

The canonical form is the **builder API** — every vartools command is a
method on `Pipeline` that appends the command and returns the pipeline
itself, so calls can be chained:

```python
import pyvartools as vt

pipe = vt.Pipeline().clip(5.0).LS(0.5, 10.0, 1e-3).rms()
```

Each method forwards its positional and keyword arguments to the
matching `cmd.X(...)` constructor, so the builder form is equivalent to
the list form below — whichever reads better for the situation at hand.

### Extending an existing pipeline

The builder methods return `self`, so any follow-up call continues the
chain on the same pipeline object:

```python
pipe = vt.Pipeline().clip(5.0)
pipe = pipe.LS(0.5, 10.0, 1e-3).rms()
```

### Alternative: list form and `add()`

You can also pass a pre-built list of `cmd.X(...)` instances to the
constructor, which is convenient when commands are assembled
programmatically:

```python
from pyvartools import commands as cmd

pipe = vt.Pipeline([cmd.clip(5.0), cmd.LS(0.5, 10.0, 1e-3), cmd.rms()])
```

For commands that don't have a direct builder method (e.g.
[`UserCommand`](../extensions/user-commands.md) for a generic extension
library), use `add(command)`, which appends a `VartoolsCommand` instance
and returns the pipeline:

```python
pipe = (vt.Pipeline()
        .clip(5.0)
        .add(vt.UserCommand("USERLIBS/src/mylib.so", "mylib", "fix 1.0"))
        .rms())
```

---

## Run methods

### `run(lc, capture_lc=False, outdir=None, timeout=None, perpoint_vars=None, randseed=None, skipmissing=False, jdtol=None, matchstringid=False) → Result`

Run the pipeline on a single light curve held in memory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `lc` | `LightCurve`, `str` / `os.PathLike`, `pd.DataFrame`, or astropy `TimeSeries` | The light curve to process. A path is loaded via [`LightCurve.from_file()`](lightcurve.md#lightcurvefrom_filepath-formatnone-t_colunset-mag_colunset-err_colunset-hdu1-name); DataFrames and TimeSeries objects are coerced to `LightCurve` automatically. |
| `capture_lc` | `bool` | If `True`, return the (possibly modified) output light curve as `result.lc`. In library mode, the data is read directly from C memory; in subprocess mode, a temporary file is used. Default `False`. |
| `outdir` | `str` or `None` | Directory for command output files (e.g. periodogram files from `save_periodogram=True`). If `None` (default), a temporary directory is created and its contents are captured into `result.files` before it is deleted. |
| `timeout` | `int` or `None` | Maximum number of seconds to wait for the vartools process. Raises `RunError` if the process exceeds the limit. `None` means no limit. |
| `perpoint_vars` | `dict[str, PerPointVar]` or `None` | Per-observation variables to create and initialise from an analytic expression before the pipeline runs (useful for masks, weights, indices). See [Initialised LC variables](#initialised-lc-variables-perpoint_vars). |
| `randseed` | `int` or `None` | Seed for the random-number generator. Pass an `int` to make stochastic commands (e.g. MCMC) reproducible. |
| `skipmissing` | `bool` | If `True`, silently skip light curves that fail to load (e.g. missing files) rather than aborting the run. Default `False`. |
| `jdtol` | `float` or `None` | Tolerance (in days) for matching observations across light curves by time. Used by commands that join external data on time. |
| `matchstringid` | `bool` | If `True`, match light curves to external data by their string `id` attribute rather than by time. Default `False`. |

If the `LightCurve` contains columns beyond the default three (`t`, `mag`, `err`), pyvartools automatically makes the extra columns available to commands by name. See [Additional columns](#additional-columns).

Returns a [`Result`](results.md) object.

---

### `run_file(path, capture_lc=False, outdir=None, timeout=None, perpoint_columns=None, perpoint_vars=None, randseed=None, skipmissing=False, jdtol=None, matchstringid=False) → Result`

Run the pipeline on a light curve file already on disk. vartools reads the file directly — no Python I/O is performed.

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` or `Path` | Path to the light curve file on disk. |
| `capture_lc` | `bool` | Capture the output light curve as `result.lc`. |
| `outdir` | `str` or `None` | Directory for command output files. |
| `timeout` | `int` or `None` | Timeout in seconds. |
| `columns` | `list[str]`, `dict`, or `None` | Column layout of the input light-curve file (which column is `t`, which is `mag`, etc.). See [Additional columns](#additional-columns) below. |
| `perpoint_vars` | `dict[str, PerPointVar]` or `None` | Per-observation variables to create and initialise. See [Initialised LC variables](#initialised-lc-variables-perpoint_vars). |
| `randseed` | `int` or `None` | Seed for the random-number generator. Pass an `int` to make stochastic commands (e.g. MCMC) reproducible. |
| `skipmissing` | `bool` | If `True`, silently skip light curves that fail to load (e.g. missing files) rather than aborting the run. Default `False`. |
| `jdtol` | `float` or `None` | Tolerance (in days) for matching observations across light curves by time. Used by commands that join external data on time. |
| `matchstringid` | `bool` | If `True`, match light curves to external data by their string `id` attribute rather than by time. Default `False`. |

The light curve name reported in `result.vars["Name"]` is taken from the file stem (i.e. the filename without directory or extension).

Returns a [`Result`](results.md) object.

---

### `run_batch(lcs, nthreads=1, capture_lc=False, outdir=None, timeout=None, raise_on_error=True, perpoint_vars=None, perlc_vars=None, randseed=None, skipmissing=False, jdtol=None, matchstringid=False, stats_file=None, stats_file_mode="overwrite", stats_file_buffer_lines=None, resume=False) → BatchResult`

Run the pipeline on a list of light curves in memory. All light curves are written to temporary files and processed in a single vartools invocation using `-l`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `lcs` | list of `LightCurve`, `str` / `os.PathLike`, `DataFrame`, or `TimeSeries` | The light curves to process. Path entries are loaded via [`LightCurve.from_file()`](lightcurve.md#lightcurvefrom_filepath-formatnone-t_colunset-mag_colunset-err_colunset-hdu1-name); mixed types are allowed. For path-only inputs, [`run_filelist()`](#run_filelistpaths-nthreads1-capture_lcfalse-outdirnone-timeoutnone-raise_on_errortrue-perpoint_columnsnone-perpoint_varsnone-perlc_varsnone-combinelcsfalse-lcnumvarlcnum-randseednone-skipmissingfalse-jdtolnone-matchstringidfalse-stats_filenone-stats_file_modeoverwrite-stats_file_buffer_linesnone-resumefalse--batchresult) is more efficient — vartools reads the files directly with no Python I/O. |
| `nthreads` | `int` | Number of parallel threads to use. Default `1`. |
| `capture_lc` | `bool` | If `True`, capture the modified output LC for each light curve and return them as `result.lcs`. |
| `outdir` | `str` or `None` | Directory for command output files. |
| `timeout` | `int` or `None` | Timeout in seconds for the whole batch. |
| `raise_on_error` | `bool` | If `True` (default), a vartools failure raises `RunError`. If `False`, the exception is stored in `result.error` and `result.vars` will be empty. |
| `perpoint_vars` | `dict[str, PerPointVar]` or `None` | Per-observation variables to create and initialise. See [Initialised LC variables](#initialised-lc-variables-perpoint_vars). |
| `perlc_vars` | `dict` or `None` | Per-LC variables — one value per light curve. Values can be supplied directly (a list / tuple / `numpy.ndarray` / `pandas.Series` of length `len(lcs)`, or a `(values, type)` tuple) or as a reference to an existing list-file column (`int` or `PerLCColumn`). Mixing the two forms in the same dict is fine. See [Per-LC variables](#per-lc-variables-perlc_vars) and [Per-LC values from Python](#per-lc-values-from-python). |
| `randseed` | `int` or `None` | Seed for the random-number generator. Pass an `int` to make stochastic commands (e.g. MCMC) reproducible. |
| `skipmissing` | `bool` | If `True`, silently skip light curves that fail to load (e.g. missing files) rather than aborting the run. Default `False`. |
| `jdtol` | `float` or `None` | Tolerance (in days) for matching observations across light curves by time. Used by commands that join external data on time. |
| `matchstringid` | `bool` | If `True`, match light curves to external data by their string `id` attribute rather than by time. Default `False`. |
| `stats_file` | `str` or `None` | If set, also stream the stats table to this file as each light curve completes. The file content matches `result.vars` and can be reloaded by a subsequent `resume=True` call. See [Streaming output and resume](#streaming-output-and-resume). |
| `stats_file_mode` | `"overwrite"` or `"append"` | Default `"overwrite"`. With `"append"` the existing file is preserved and only new rows are added; `resume=True` sets this automatically when an existing file is detected. |
| `stats_file_buffer_lines` | `int` or `None` | Maximum number of light curves whose results are queued in memory before flushing to `stats_file` in parallel runs. Default `None` → auto-scales to a safe value for the given thread count.  Setting it below `nthreads` caps effective parallelism (threads beyond it stall waiting for a free slot).  Has no effect when `nthreads=1`.  See [Flush cadence in parallel runs](#flush-cadence-in-parallel-runs). |
| `resume` | `bool` | If `True` and `stats_file` exists, parse it, skip any light curves whose row is already present, and append rows for the remaining ones. The pipeline's column layout is validated against the file via [`validate()`](#validate); a mismatch raises `PipelineValidationError`. Pipelines containing `-copylc` cannot be resumed. Default `False`. |

Extra columns in the first `LightCurve` are propagated automatically; all light curves in the batch are assumed to share the same column structure. See [Additional columns](#additional-columns).

Returns a [`BatchResult`](results.md) object.

---

### `run_filelist(paths, nthreads=1, capture_lc=False, outdir=None, timeout=None, raise_on_error=True, perpoint_columns=None, perpoint_vars=None, perlc_vars=None, combinelcs=False, lcnumvar="lcnum", randseed=None, skipmissing=False, jdtol=None, matchstringid=False, stats_file=None, stats_file_mode="overwrite", stats_file_buffer_lines=None, resume=False) → BatchResult`

Run the pipeline on a collection of light curve files on disk. No Python I/O is performed — vartools reads the files directly. This is the most efficient method for large surveys.

| Parameter | Type | Description |
|-----------|------|-------------|
| `paths` | `str`, `Path`, or list of `str`/`Path` | Either a path to an existing vartools list file (one LC file path per line), or a Python list of individual LC file paths. If a list is given, a temporary list file is written automatically. |
| `nthreads` | `int` | Number of parallel threads. |
| `capture_lc` | `bool` | Capture output LCs as `result.lcs`. |
| `outdir` | `str` or `None` | Directory for command output files. |
| `timeout` | `int` or `None` | Timeout in seconds. |
| `raise_on_error` | `bool` | If `False`, errors are stored in `result.error` rather than raised. |
| `perpoint_columns` | `list[str]`, `dict`, or `None` | Column layout of the input light-curve files (which column is `t`, which is `mag`, etc.). See [Additional columns](#additional-columns) below. |
| `perpoint_vars` | `dict[str, PerPointVar]` or `None` | Per-observation variables to create and initialise. See [Initialised LC variables](#initialised-lc-variables-perpoint_vars). |
| `perlc_vars` | `dict[str, int \| PerLCColumn]` or `None` | Per-LC variables, read from columns of the on-disk list file (`int` or `PerLCColumn` — schema form only).  To supply values directly from Python, use `run_batch()` instead. |
| `combinelcs` | `bool` | If `True`, append `combinelcs` to the `-l` flag — vartools then treats each line of the list file as a *group* of comma-separated paths combined into one in-memory light curve. The list file (or list of strings passed as `paths`) is responsible for the grouping; pyvartools does not split anything itself. PerLC parameter values are rejected when `combinelcs=True`. |
| `lcnumvar` | `str` or `None` | Only used when `combinelcs=True`. Name of the per-observation integer variable vartools creates to record which file each point came from. Defaults to `"lcnum"`; pass `None` to opt out. |
| `randseed` | `int` or `None` | Seed for the random-number generator. Pass an `int` to make stochastic commands (e.g. MCMC) reproducible. |
| `skipmissing` | `bool` | If `True`, silently skip light curves that fail to load (e.g. missing files) rather than aborting the run. Default `False`. |
| `jdtol` | `float` or `None` | Tolerance (in days) for matching observations across light curves by time. Used by commands that join external data on time. |
| `matchstringid` | `bool` | If `True`, match light curves to external data by their string `id` attribute rather than by time. Default `False`. |
| `stats_file` | `str` or `None` | Stream the stats table to this file as each row is produced. See [Streaming output and resume](#streaming-output-and-resume). |
| `stats_file_mode` | `"overwrite"` or `"append"` | Default `"overwrite"`. |
| `stats_file_buffer_lines` | `int` or `None` | Maximum number of light curves queued before flushing to `stats_file` in parallel runs. Should be `>= nthreads`; see the `run_batch` entry and [Flush cadence in parallel runs](#flush-cadence-in-parallel-runs). |
| `resume` | `bool` | Resume from a partial `stats_file`, skipping already-completed light curves. See [Streaming output and resume](#streaming-output-and-resume). Pipelines containing `-copylc` cannot be resumed. Default `False`. |

Returns a [`BatchResult`](results.md) object.

#### Example — `combinelcs=True` with a pre-built list file

The list file holds one *group* per line — paths within a group are joined by commas, and vartools combines each group into a single in-memory light curve.

```python
# Build a tiny groups.txt on the fly that pairs EXAMPLES/2 with EXAMPLES/3.
import tempfile, os
list_path = os.path.join(tempfile.mkdtemp(), "groups.txt")
with open(list_path, "w") as f:
    f.write("EXAMPLES/2,EXAMPLES/3\n")
    f.write("EXAMPLES/4,EXAMPLES/5\n")

batch = vt.Pipeline().rms().run_filelist(list_path, combinelcs=True)
print(batch.vars)   # one row per line in the list file
```

---

### `run_combinelc(files, nthreads=1, capture_lc=False, outdir=None, timeout=None, raise_on_error=True, perpoint_columns=None, perpoint_vars=None, perlc_vars=None, perlcsegment_vars=None, lcnumvar="lcnum", delimiter=",", randseed=None, skipmissing=False, jdtol=None, matchstringid=False) → Result`

Single-group convenience wrapper around `run_combinelcs()`. Combines *files* into one in-memory light curve, runs the pipeline, and returns a single [`Result`](results.md) (not a `BatchResult`).

```python
# Combine two segments of the same star and run an LS period search on the
# combined LC.  EXAMPLES/2 stands in for "telescope A"; we pass it twice
# just to exercise the combine path.
result = (vt.Pipeline()
          .rms()
          .LS(0.5, 10.0, 1e-3, npeaks=1)
          ).run_combinelc(["EXAMPLES/2", "EXAMPLES/2"])
print(result.vars["LS_Period_1_1"])
```

`perlcsegment_vars` accepts a flat list of length `len(files)` per variable (one value per segment) and `perlc_vars` accepts a single value per variable; both auto-wrap to the nested shape that `run_combinelcs()` expects. See [`run_combinelcs()`](#run_combinelcs) for the full description.

All other keyword arguments forward to `run_combinelcs()`.

---

### `run_combinelcs(groups, nthreads=1, capture_lc=False, outdir=None, timeout=None, raise_on_error=True, perpoint_columns=None, perpoint_vars=None, perlc_vars=None, perlcsegment_vars=None, lcnumvar="lcnum", delimiter=",", randseed=None, skipmissing=False, jdtol=None, matchstringid=False) → BatchResult`

Run the pipeline using vartools `-l … combinelcs` mode. Each entry in *groups* is a list of file paths that vartools combines into a single in-memory light curve before passing it to the command chain. The result contains one row in `batch.vars` per group.

This mode of processing can be used to merge light curve files from multiple telescopes with the `-stitch` user command before running other processes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `groups` | list of lists of `str`/`Path` | Each inner list is one group of files to combine. Files within a group are joined by `delimiter` to form one line in the vartools list file. |
| `nthreads` | `int` | Number of parallel threads. |
| `capture_lc` | `bool` | Capture the combined output LC for each group as `result.lcs`. |
| `outdir` | `str` or `None` | Directory for command output files. |
| `timeout` | `int` or `None` | Timeout in seconds. |
| `raise_on_error` | `bool` | If `False`, errors are stored in `result.error` rather than raised. |
| `columns` | `list[str]`, `dict`, or `None` | Column layout of the input light-curve files (which column is `t`, which is `mag`, etc.). See [Additional columns](#additional-columns). |
| `perpoint_vars` | `dict[str, PerPointVar]` or `None` | Per-observation variables to create and initialise. |
| `perlc_vars` | `dict` or `None` | Per-LC variables, one value per group (length `len(groups)`). Accepts a sequence of values, a `(values, type)` tuple to override the auto-detected type, or schema entries (`int` or `PerLCColumn`) that reference a column in an existing list file. See [Per-LC variables](#per-lc-variables-perlc_vars). |
| `perlcsegment_vars` | `dict` or `None` | Per-segment variables, with a value for each segment within each group. Each entry is a sequence of length `len(groups)` whose *i*-th element is itself a sequence of length `len(groups[i])`. The type is inferred from the values (`int`, `float`, `str`); pass a `(values, type)` tuple to override. Used by commands like `stitch` that need a per-segment label. |
| `lcnumvar` | `str` or `None` | Name of the per-observation integer variable vartools creates to record which file each point came from. Defaults to `"lcnum"`; pass `None` to opt out of emitting the `lcnumvar` qualifier. |
| `delimiter` | `str` | Delimiter used to join paths within a group in the list file. Default `","` (the vartools `combinelcs` default). The same delimiter is used for `perlcsegment_vars` sub-columns. |
| `randseed` | `int` or `None` | Seed for the random-number generator. Pass an `int` to make stochastic commands (e.g. MCMC) reproducible. |
| `skipmissing` | `bool` | If `True`, silently skip light curves that fail to load (e.g. missing files) rather than aborting the run. Default `False`. |
| `jdtol` | `float` or `None` | Tolerance (in days) for matching observations across light curves by time. Used by commands that join external data on time. |
| `matchstringid` | `bool` | If `True`, match light curves to external data by their string `id` attribute rather than by time. Default `False`. |

PerLC array parameters are supported: each PerLC must have one value per group (`len(groups)`). The values are appended as additional columns to the temporary list file and wired up via `-inlistvars`, exactly as in `run_batch()`/`run_filelist()`. A length mismatch raises `ValueError`.

#### Type inference for `perlcsegment_vars` / `perlc_vars`

The vartools type for each variable is inferred from the Python values:

| Python value | Inferred type |
|---|---|
| `int` (or `bool`) | `"int"` |
| `float` | `"double"` |
| `str` | `"string"` |

Pass a `(values, type)` tuple to override — e.g. when you want a string-valued ID column whose values happen to look numeric:

```python
perlc_vars={"id": (["001", "002", "003"], "string")}
```

String values may not contain whitespace; vartools list-file columns are whitespace-separated, so an embedded space would corrupt the row.

Returns a [`BatchResult`](results.md) object.

#### Example — combine two per-telescope files and compute RMS

```python
import pyvartools as vt
from pyvartools import commands as cmd

# Each sublist holds the files that belong to one "source" — imagine
# observations of the same star taken by two different telescopes.
groups = [
    ["EXAMPLES/1", "EXAMPLES/2"],
    ["EXAMPLES/3", "EXAMPLES/4"],
]

batch = vt.Pipeline().rms().run_combinelcs(groups)
print(batch.vars)   # one row per group
```

#### Example — opt out of the per-point file index

By default `run_combinelcs()` passes `lcnumvar lcnum` to vartools, creating an integer variable `lcnum` per observation. Pass `lcnumvar=None` to suppress it:

```python
batch = vt.Pipeline().rms().run_combinelcs(groups, lcnumvar=None)
```

#### Example — multi-telescope stitch + period search

```python
from pyvartools.commands import stitch

batch = (vt.Pipeline()
        .expr("mask=0")
        .stitch("mag", "err", "mask", "lcnum", method="median")
        .LS(0.5, 10.0, 1e-3, npeaks=1)).run_combinelcs(groups, nthreads=2)

print(batch.vars[["Name", "LS_Period_1_2"]])   # LS is the 3rd command (index 2)
```

#### Example — attach per-segment and per-LC metadata

`-stitch shifts_file` requires a per-observation string field label (so each segment can be tagged with the telescope or chip it came from) and a per-LC star name (so shifts can be matched against an external shifts table). Use `perlcsegment_vars` for the per-segment label and `perlc_vars` for the per-LC name:

```python
import pyvartools as vt

result = (vt.Pipeline()
          .expr("mask=1")
          .stitch("mag", "err", "mask", "lcnum",
                  method="poly 5", groupbytime=0.5, fitonly=True,
                  shifts_file=("fieldname", "starname"),
                  out_shifts_file="/tmp/shifts.txt")
          ).run_combinelc(
              ["EXAMPLES/2", "EXAMPLES/2.shifted"],
              perlcsegment_vars={"fieldname": ["2_A", "2_B"]},
              perlc_vars={"starname": "2"},
          )
print(open("/tmp/shifts.txt").read())
# 2 2_A,0,3313;2_B,0.30000000000003313,3313
```

The same pattern works for the plural form when each group needs its own labels:

```python
plural_pipe = (vt.Pipeline()
               .expr("mask=1")
               .stitch("mag", "err", "mask", "lcnum",
                       method="poly 3", fitonly=True))
batch = plural_pipe.run_combinelcs(
    groups=[["EXAMPLES/2", "EXAMPLES/2.shifted"],
            ["EXAMPLES/2", "EXAMPLES/2.shifted"]],
    perlcsegment_vars={"fieldname": [["G1_A", "G1_B"], ["G2_A", "G2_B"]]},
    perlc_vars={"starname": ["TIC1", "TIC2"]},
)
print(len(batch.vars))   # 2 — one row per group
```

The `starname` values supplied via `perlc_vars` are *vartools variables*, not the
``Name`` column of the stats DataFrame.  Pipeline commands that consume them
(such as `-stitch shifts_file`) see the per-LC string; everything else still
keys off the input filename.

---

## `validate()`

```text
validate(nthreads=1, randseed=None, skipmissing=False, jdtol=None,
         matchstringid=False, timeout=30, perlc_vars=None) → list[str]
```

Check that the pipeline is well-formed without processing any data, and return the list of expected output column names. Useful for catching errors during pipeline construction, and for inspecting the exact column layout the run will produce.

```python
pipe = vt.Pipeline().LS(0.1, 10.0, 0.1, npeaks=3).rms()
cols = pipe.validate()
# ['Name', 'LS_Period_1_0', 'Log10_LS_Prob_1_0', ..., 'RMS_1', ...]
```

A malformed pipeline raises `PipelineValidationError` with a message describing what was wrong:

```python
bad_pipe = vt.Pipeline().add(vt.commands.Raw("--no-such-flag"))
try:
    bad_pipe.validate()
except vt.PipelineValidationError as e:
    print(e)   # human-readable error message
```

For pipelines that reference per-LC variables by name (e.g.
`cmd.LS("minp", "maxp", 0.1)`), pass the same `perlc_vars=` dict you'd use
at run time so the parser can resolve those names:

```python
pipe = vt.Pipeline().LS("minp", "maxp", 0.1, npeaks=1)
cols = pipe.validate(perlc_vars={"minp": [0.3, 0.5], "maxp": [3.0, 5.0]})
```

Both values-form (`{name: [vals, ...]}`) and schema-form (`{name: int}`,
`{name: PerLCColumn(...)}`) are accepted — `validate()` only needs the
names to resolve, not the values themselves.

`validate()` is intended for construction-time / debug use rather than tight inner loops.  The [resume path](#streaming-output-and-resume) calls it internally to check that a partial stats file was produced by the same pipeline that's now trying to resume from it.

---

## Streaming output and resume

`run_batch()` and `run_filelist()` accept `stats_file=PATH` to write the
per-light-curve stats table to disk as each light curve completes,
alongside the in-memory `BatchResult`.  The file is a space-delimited
table with a `#`-prefixed header line (one row per light curve, identical
column order to `result.vars`).  Each row is flushed to disk as soon as
vartools finishes that light curve, so a long-running batch leaves a
partial-but-recoverable file behind even if the process is killed.

```text
#Name LS_Period_1_0 Log10_LS_Prob_1_0 ... Print__vtpy_seq__0_1
EXAMPLES/1 0.97817996 -5612.03157 ... 0
EXAMPLES/2 1.23534018 -4222.27256 ... 1
...
```

Easy to load:

```python
import pandas as pd
df = pd.read_csv(...)                      # load survey.stats produced above
df = df.rename(columns={df.columns[0]: df.columns[0].lstrip("#")})
```

`awk`, `gnuplot`, and `pandas` all consume this format directly without
extra preprocessing.

#### Flush cadence in parallel runs

When `nthreads > 1`, vartools queues per-light-curve output in a small
internal ring instead of writing each row directly.  This is what lets
multiple threads keep computing while one of them takes its turn on
the output mutex.  Rows reach the file when a thread finishes a light
curve, finds the ring full, drains it, then pushes its own result on.

`stats_file_buffer_lines` controls how big that ring is.  The
trade-off has a sharp inflection at `stats_file_buffer_lines ==
nthreads`:

* **`stats_file_buffer_lines >= nthreads`** — every thread always has
  somewhere to put its result.  Full parallel throughput; rows reach
  the file in bursts up to the buffer size whenever the ring fills.
* **`stats_file_buffer_lines < nthreads`** — only that many threads
  can have results in flight at once.  Threads beyond it stall
  waiting for a slot to free up.  **Effective parallelism caps at
  `stats_file_buffer_lines`** — wall-clock matches a run with
  `nthreads=stats_file_buffer_lines`.

One common case where this matters: you set
`stats_file_buffer_lines=1` for a true real-time log of a long-running
batch.  That works correctly but serialises the run — you trade
throughput for live visibility.

```python
# I want every LC's row on disk as soon as it's computed, throughput
# is secondary (e.g. monitoring an overnight survey).
pipe.run_batch(..., stats_file="survey.stats", nthreads=1,
               stats_file_buffer_lines=1)

# Default — vartools auto-scales the buffer to ~2x nthreads when you
# leave this unset, so full parallel throughput is preserved without
# you having to tune anything.
pipe.run_batch(..., stats_file="survey.stats", nthreads=8)

# Only set an explicit value if you have a specific reason — for
# example, to bound peak memory when each row is large.
pipe.run_batch(..., stats_file="survey.stats", nthreads=64,
               stats_file_buffer_lines=128)
```

When `nthreads=1` the buffer ring is bypassed entirely and each row is
flushed as it finishes regardless of this setting.

```python
pipe = vt.Pipeline().LS(0.1, 10.0, 0.1, npeaks=1).rms()
result = pipe.run_batch(..., stats_file="survey.stats", nthreads=8)
```

If that run is killed partway through, re-launch with `resume=True`:

```python
result = pipe.run_batch(..., stats_file="survey.stats", resume=True,
                        nthreads=8)
```

Resume will:

1. Validate the partial file's column layout against the current pipeline
   via `validate()`.  A mismatch (different commands, different `npeaks`,
   etc.) raises `PipelineValidationError` with both column lists side by
   side.
2. Read the rows already in the file, identify their input-list positions
   from the per-row sequence number that pyvartools embeds in every
   streamed file, and skip those LCs.
3. Run vartools on only the unprocessed LCs, appending their rows to the
   file and remapping their sequence numbers so the on-disk file stays
   aligned with the original input order.
4. Return a `BatchResult` whose `vars` DataFrame combines the pre-existing
   rows with the freshly-computed ones.

Caveats:

* `capture_lc=True` and `result.files` only cover the **freshly-run**
  light curves — resumed positions get `None` entries.  If you want the
  full set, re-run from scratch (or keep `save_*=True` files on disk so
  you can stitch them back together yourself).
* Pipelines containing `-copylc` are rejected — one input row produces
  multiple output rows in that case, breaking the seq-based identity used
  for resume.  Drop `copylc` or re-run from scratch.
* `-randseed time` means the new rows from the resume run aren't
  bit-identical to what would have been produced in the original run.
  Same caveat as anywhere randomness is used.

---

## Examples

### Single light curve

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe = vt.Pipeline().clip(5.0).LS(0.5, 10.0, 1e-3)

result = pipe.run(lc)
print(result.vars["LS_Period_1_1"])
```

To get the modified light curve back (e.g. after sigma clipping):

```python
result = pipe.run(lc, capture_lc=True)
modified_lc = result.lc  # LightCurve with clipped points removed
```

### From disk

```python
result = pipe.run_file("EXAMPLES/2")
print(result.vars["LS_Period_1_1"])
```

### Batch from memory

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 6)]
batch = pipe.run_batch(lcs, nthreads=4)
print(batch.vars)          # pd.DataFrame, one row per LC
print(batch.vars.columns)  # all output column names
```

### Batch from disk (most efficient for large surveys)

When you already have a list file or a directory of light curves, `run_filelist` avoids all Python-side I/O:

```python
# From an existing vartools list file
batch = pipe.run_filelist("EXAMPLES/lc_list", nthreads=4)

# Or supply an explicit Python list of paths
batch = pipe.run_filelist([f"EXAMPLES/{i}" for i in range(1, 6)], nthreads=4)

# Save the statistics table
batch.vars.to_csv("EXAMPLES/results.csv", index=False)
```

### Error handling in batch

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 6)]
batch = pipe.run_batch(lcs, raise_on_error=False)
if batch.ok:
    print(batch.vars)
else:
    print(f"Pipeline failed: {batch.error}")
```

---

## Additional columns

A light curve file is treated as having three default columns — time, magnitude, and uncertainty — in columns 1, 2, and 3.  Any additional columns can be made available to commands under a named variable (so that, e.g., `cmd.expr("detrended = mag - 0.05*airmass")` can reference an `airmass` column).

pyvartools handles this automatically:

- **`run()` and `run_batch()`** — when the input `LightCurve` carries extra columns (e.g. via `LightCurve.from_arrays(..., aux={"airmass": ...})`), pyvartools propagates them by name so commands can reference them directly.
- **`run_file()` and `run_filelist()`** — the file is read directly from disk, so you tell pyvartools its column layout through the `columns` / `perpoint_columns` parameter.

### Specifying columns for disk-based runs

**List form** — variable names in column order:

```python
# Columns: t=1, mag=2, err=3
result = pipe.run_file(
    "EXAMPLES/2",
    perpoint_columns=["t", "mag", "err"],
)
```

**Dict form with integer column numbers** — explicit mapping:

```python
result = pipe.run_file(
    "EXAMPLES/2",
    perpoint_columns={"t": 1, "mag": 2, "err": 3},
)
```

**Dict form with FITS column names** — for FITS binary tables:

```python
result = pipe.run_file(
    "EXAMPLES/example.fits",
    perpoint_columns={"t": "BJD", "mag": "Mag", "err": "Err"},
)
```

### Automatic discovery in memory-based runs

Extra (or non-standard) columns on a `LightCurve` are propagated automatically — pyvartools makes them available to commands by name without you having to declare anything.

```python
import numpy as np
import pyvartools as vt
from pyvartools import commands as cmd

t       = np.linspace(0, 30, 500)
mag     = 10.0 + 0.1 * np.sin(2 * np.pi * t / 2.3)
err     = np.full(500, 0.01)
airmass = 1.0 + 0.5 * np.abs(np.sin(np.pi * t / 15.0))

# Extra column "airmass" — directly referenceable in cmd.expr, cmd.linfit, etc.
lc = vt.LightCurve.from_arrays(t, mag, err, aux={"airmass": airmass})
result = vt.Pipeline().rms().run(lc)

# Only t and mag — fine; commands that don't need err just won't see it.
lc2 = vt.LightCurve.from_arrays(t=t, mag=mag)
result2 = vt.Pipeline().rms().run(lc2)

# No standard columns at all — only custom vectors named "phase" and "flux".
phase_arr = (t % 2.3) / 2.3
flux_arr  = 1.0 - 0.01 * np.sin(2 * np.pi * phase_arr)
lc3 = vt.LightCurve.from_arrays(aux={"phase": phase_arr, "flux": flux_arr})
```

The same applies to `run_batch()` — all light curves in the batch should share the same column structure, since the layout is inferred from the first light curve and applied to the whole batch.

---

## Initialised LC variables (`perpoint_vars`)

`perpoint_vars` lets you **create a new per-observation variable** on each light curve before the pipeline runs, initialising it from an analytic expression rather than reading it from a file column.  This is useful for creating mask flags, synthetic indices, or any per-point derived quantity that downstream commands can reference.

The expression is evaluated once per observation. The special variable `NR` holds the 0-based observation index.

### `PerPointVar`

```python
from pyvartools import PerPointVar

PerPointVar(type="double", init="0")
```

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | `str` | `"double"` | Variable type: `"double"`, `"float"`, `"int"`, `"long"`, `"short"`, `"string"`, `"char"`, or `"utc"`. |
| `init` | `str` | `"0"` | Initialisation expression. May reference `NR` (0-based obs index) or other per-point variables already defined on the light curve. |

Pass a `dict[str, PerPointVar]` as `perpoint_vars` to any run method. The dictionary key is the variable name used inside vartools commands.

!!! note
    `perpoint_vars` is for **creating new** per-observation variables. If your light curve has a non-standard layout of the actual data columns (e.g. time is not in column 1), use `columns` / `perpoint_columns` on `run_file()` / `run_filelist()` (or pass a `LightCurve` with the correct column names for `run()` / `run_batch()`) to declare the layout — the standard columns continue to work alongside any `perpoint_vars` entries you add.

### Examples

**Create an integer mask variable, initially all zeros (unmasked):**

```python
import pyvartools as vt
from pyvartools import PerPointVar, commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")

result = vt.Pipeline().rms().run(
    lc,
    perpoint_vars={"mymask": PerPointVar(type="int", init="0")},
)
print(result.vars["RMS_0"])
```

**Index each observation (0-based) using `NR`:**

```python
result = vt.Pipeline().rms().run(
    lc,
    perpoint_vars={"obs_idx": PerPointVar(type="double", init="NR")},
)
```

**Use a per-observation flag to inflate errors for early observations (t < 10):**

```python
result = vt.Pipeline().expr("err = err * (1 + 9*early_mask)").rms().run(
    lc,
    perpoint_vars={"early_mask": PerPointVar(type="int", init="t<10")},
)
print(result.vars["RMS_1"])
```

---

## Per-LC variables (`perlc_vars`)

`perlc_vars` defines **per-LC scalar variables** — one value per light curve in the batch.  These variables are accessible to commands like `LS`, `aov`, and `BLS` by name (e.g. `minp="myperiod"` in `cmd.LS`).

### `PerLCColumn`

```python
from pyvartools import PerLCColumn

PerLCColumn(col=2, type="double", init=None, combinelc=False)
```

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `col` | `int` | *(required)* | Column number in the list file (1-based). Use `0` to initialise from an expression instead of reading from a column. |
| `type` | `str` | `"double"` | Variable type: `"double"`, `"float"`, `"int"`, `"long"`, `"short"`, `"string"`, `"char"`, or `"utc"`. |
| `init` | `str` or `None` | `None` | Initialisation expression used when `col=0`. The special variable `NF` holds the 0-based line number. |
| `combinelc` | `bool` | `False` | If `True`, the same value is applied to all light curves that share the same LC name (used when combining multiple observations into a single LC). |

As a shorthand, `int` values are accepted in place of `PerLCColumn` objects when only a column number is needed:

```python
perlc_vars={"myperiod": 2}   # equivalent to PerLCColumn(col=2)
```

### With `run_filelist()`

`run_filelist()` is the primary method for using `perlc_vars`. The list file may contain extra columns beyond the LC file path. vartools reads those columns and maps them to the specified variable names.

**Example list file (`EXAMPLES/lc_list_periods`):**

```
EXAMPLES/1 0.573
EXAMPLES/2 0.412
EXAMPLES/3 1.891
```

**Use the period from column 2 as the minimum search period for LS:**

```python
import pyvartools as vt
from pyvartools import PerLCColumn, commands as cmd

pipe = vt.Pipeline().LS("myperiod", 100.0, 0.1)
batch = pipe.run_filelist(
    "EXAMPLES/lc_list_periods",
    perlc_vars={"myperiod": PerLCColumn(col=2)},
)
print(batch.vars[["Name", "LS_Period_1_0"]])
```

Here `minp="myperiod"` is a bare identifier string, so each LC's `minp` is taken from its row of the `myperiod` column.

**Expression-initialised per-star variable (`col=0`) using the line number `NF`:**

```python
batch = pipe.run_filelist(
    "EXAMPLES/lc_list_periods",
    perlc_vars={
        "myperiod": PerLCColumn(col=2),
        "lc_idx": PerLCColumn(col=0, type="double", init="NF"),
    },
)
```

### With `run_batch()`

`run_batch()` builds a temporary list file from the in-memory light curves, and pyvartools owns its layout, so it can append columns for values supplied from Python.  `perlc_vars` accepts both schema and values entries here:

```python
import pyvartools as vt

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]
periods = [0.573, 0.412, 1.891]   # one minp per LC

pipe = vt.Pipeline().LS("myperiod", 100.0, 0.1)
batch = pipe.run_batch(lcs, perlc_vars={"myperiod": periods})
```

For schema entries with `col=0` (expression-initialised) the column reference is unchanged from `run_filelist()`.  See [Per-LC values from Python](#per-lc-values-from-python) below for the full dispatch rules and a per-LC output-name example.

### Per-LC values from Python

In `run_batch()` (and `LightCurveBatch.run()`), each non-schema entry of `perlc_vars` is rendered into a fresh list-file column.  Recognised value shapes:

| Spec form | Interpretation |
|-----------|----------------|
| `int` *or* `PerLCColumn(...)` | Schema — column reference, identical to `run_filelist()` semantics. |
| `list` / `tuple` / `np.ndarray` / `pd.Series` of length `len(lcs)` | Values — one per LC.  Type is auto-detected from the first non-`None` value (`bool` → `int`). |
| `(values, type)` tuple | Values with explicit type override.  `type` is one of `"double"`, `"float"`, `"int"`, `"long"`, `"short"`, `"string"`, `"char"`, `"utc"`. |

The original gap this closed: per-LC output names through `cmd.o(namefromlist=...)`:

```python
import os, tempfile
import pyvartools as vt

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]
outnames = [f"OutputName_is_this_{i}" for i in range(1, 4)]
outdir = tempfile.mkdtemp(prefix="namefromlist_")

batch = (vt.Pipeline()
         .clip(5.0).expr("tmp=t+2*mag")
         .o(outdir=outdir, allcols=True,
            namefromlist="outname",
            capture=True, key="clipped")
         ).run_batch(lcs, perlc_vars={"outname": outnames})

print(sorted(os.listdir(outdir)))
# ['OutputName_is_this_1', 'OutputName_is_this_2', 'OutputName_is_this_3']
```

Each LC's processed output is written to `<outdir>/<outname>` instead of being keyed by the input LC's name.

`run_filelist()` rejects values-form entries with a clear error pointing here — in list-file mode pyvartools is not the writer of the on-disk list, so it cannot append columns.  Schema entries (`int` / `PerLCColumn`) still work in `run_filelist()`.

### Reserved variable names

The names `t`, `mag`, `err`, and `id` are reserved by vartools and cannot be used as `perlc_vars` variable names.

---

## Per-LC array parameters

Some numeric parameters on period-search commands accept a **per-LC array** — a different value for each light curve in a batch — as a direct alternative to a single fixed scalar. This lets you, for example, run LS on a hundred stars each with individually tailored search bounds, without writing a custom list file.

### Supported types

Any of the following may be passed for a supported parameter:

| Type | Example |
|------|---------|
| `numpy.ndarray` (1-D) | `np.array([0.1, 0.5, 0.2])` |
| `pyvartools.PerLC` | `PerLC([0.1, 0.5, 0.2])` |
| `pandas.Series` | `pd.Series([0.1, 0.5, 0.2])` |

`PerLC` is a thin wrapper that tags an array explicitly as a per-LC sequence, making intent clear in code. It behaves identically to a numpy array at runtime.

```python
from pyvartools import PerLC
```

### Supported (command, parameter) pairs

Per-LC arrays are supported wherever vartools itself accepts the `var varname` syntax. The complete list, confirmed against the installed binary:

| Command | Supported parameters |
|---------|---------------------|
| `LS` | `minp`, `maxp`, `subsample` |
| `aov` | `minp`, `maxp`, `subsample`, `finetune`, `nbin` |
| `aov_harm` | `nharm`, `minp`, `maxp`, `subsample`, `finetune` |
| `BLS` | `minper`, `maxper`, `rmin`, `rmax`, `qmin`, `qmax`, `stellar_density`, `min_exp_dur_frac`, `max_exp_dur_frac`, `nbins`, `subsample`, `nfreq`, `df` |
| `clip` | `sigclip`, `niter` |
| `fluxtomag` / `difffluxtomag` | `mag_constant`, `offset` |
| `medianfilter` | `time` |
| `harmonicfilter` | `clip` |
| `linfit` | `reject` |
| `Phase` | `period`, `T0` |
| `MandelAgolTransit` | `P0`, `T00`, `r0`, `a0`, `inclination`/`bimpact`, `e0`, `omega0`, `mconst0`, `K0`, `gamma0`, `ld_coeffs` |
| `Starspot` | `period`, `a0`, `b0`, `alpha0`, `i0`, `chi0`, `psi00`, `mconst0` |
| `nonlinfit` | `amoeba_tolerance`, `amoeba_maxsteps`, `mcmc_naccept`, `mcmc_nlinkstotal`, `mcmc_fracburnin`, `mcmc_eps` |
| `BLSFixDurTc` | `duration`, `Tc`, `fixdepth`, `qgress`, `minper`, `maxper`, `nfreq` |
| `BLSFixPerDurTc` | `period`, `duration`, `Tc`, `fixdepth`, `qgress` |
| `autocorrelation` | `start`, `stop`, `step` |
| `dftclean` | `nbeam`, `maxfreq`, `gain`, `SNlimit`, `finddirtypeaks_clip` |
| `wwz` | `maxfreq`, `freqsamp`, `tau0`, `tau1`, `dtau`, `c` |
| `binlc` | `binsize`, `nbins`, `firstbinshift`, `T0` |
| `Injectharm` | `period`, `amplitude`, `phase` |
| `Injecttransit` | all injection parameters (`period`, `Rp`, `Mp`, `phase`, `sini`, etc.) |
| `addnoise` | all noise parameters (`sig_white`, `sig_red`, `rho`, `gamma`, `nu`, `bintime`) |
| `microlens` | `f0`, `f1`, `u0`, `t0`, `tmax` |

Any numeric parameter listed above can be passed as a number (fixed), a string variable name (per-star `var`), or an expression string (per-LC `expr`). The PerLC array mechanism (numpy array / pd.Series) also works for all of these.

### How it works

When `run_batch()` detects a per-LC array on any command parameter, the value is automatically registered as a per-LC variable (one entry per LC) and the command's parameter is rewritten to read from it. This is all transparent — you don't need to set up `perlc_vars` yourself.

### Constraints

- **`run_batch()` and `run_filelist()` (list of paths) only.** `run()` and `run_file()` process a single light curve and raise `ValueError` if any per-LC array is present.
- **`run_filelist()` with a pre-built list file (a single path string) is not supported.** pyvartools cannot safely append extra columns to a list file it did not create. Pass a Python list of paths instead and let the pipeline write the list file.
- **`run_filelist(combinelcs=True)` is not supported.** When the user supplies a comma-joined list file directly, pyvartools cannot safely append extra value columns to it; a `ValueError` is raised. Use `run_combinelcs()` instead — it builds the list file itself and accepts PerLC values (one per group).
- The array length must equal the number of light curves. A `ValueError` with a clear message is raised if it does not.

!!! tip "Need per-LC values on unsupported parameters?"
    `Pipeline.run_batch()` only supports per-LC arrays for the parameters listed
    in the table above — those are the parameters that vartools knows how to
    read from a named per-LC variable.  If you need to vary a parameter that is
    **not** in the supported list — for example `harmonicfilter.period`,
    `MandelAgolTransit.P0`, or any parameter on a custom command — use
    [`LightCurveBatch`](chaining.md#batch-chaining-lightcurvebatch) instead.
    `LightCurveBatch` resolves arrays to scalars in Python before each
    individual run, so it works for **any** parameter on **any** command with no
    restrictions.  The trade-off is one vartools invocation per light curve rather
    than one for the entire batch.

### Examples

**Different period search range for each LC:**

```python
import numpy as np
import pyvartools as vt
from pyvartools import commands as cmd

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in [2, 3, 4, 5, 6]]

# Each star gets its own [minp, maxp] bounds
result = (vt.Pipeline()
        .LS(
            minp=np.array([0.1, 0.5, 0.1, 0.2, 0.3]),
            maxp=np.array([5.0, 10.0, 8.0, 6.0, 7.0]),
            subsample=0.001,
            npeaks=1,
        )).run_batch(lcs, nthreads=4)

print(result.vars[["Name", "LS_Period_1_0"]])
```

**Using the `PerLC` wrapper for readability:**

```python
from pyvartools import PerLC, commands as cmd

pipe = (vt.Pipeline()
        .aov(
            minp=PerLC([0.1, 0.5, 0.1, 0.2, 0.3]),
            maxp=10.0,               # scalar: same for all LCs
            subsample=0.001,
            finetune=2,
            npeaks=1,
        ))
result = pipe.run_batch(lcs)
print(result.vars[["Name", "Period_1_0", "AOV_1_0"]])
```

**BLS with per-LC period bounds:**

```python
result = (vt.Pipeline()
        .BLS(
            minper=np.array([0.1, 0.5, 0.1, 0.2, 0.3]),
            maxper=np.array([5.0, 10.0, 8.0, 6.0, 7.0]),
            rmin=0.01,
            rmax=0.5,
            nbins=200,
            nfreq=5000,
            npeaks=1,
        )).run_batch(lcs)
print(result.vars[["Name", "BLS_Period_1_0", "BLS_SDE_1_0"]])
```

**Mixing per-LC and scalar parameters** — scalar values are broadcast to all light curves as usual:

```python
# minp varies per LC; maxp and subsample are fixed for all
pipe = (vt.Pipeline()
        .LS(
            minp=PerLC([0.1, 0.3, 0.05]),
            maxp=20.0,
            subsample=0.001,
        ))
```

**Multiple per-LC parameters** — multiple parameters can vary simultaneously:

```python
# Both minp and maxp differ per LC
pipe = (vt.Pipeline()
        .LS(
            minp=np.array([0.1, 0.5, 0.1]),
            maxp=np.array([5.0, 20.0, 10.0]),
            subsample=np.array([0.001, 0.0005, 0.001]),
        ))
```

---

## Output files

Commands that produce auxiliary output files (periodograms, fitted model curves, coefficient tables, etc.) expose a `save_*` parameter. Each such parameter accepts four modes controlled by a `bool`, a directory path string, or an [`Output`](commands/index.md#auxiliary-output-files) object:

| Value | Mode | Written to disk? | Captured in `result.files`? |
|-------|------|-----------------|------------------------------|
| `False` (default) | suppress | no | no |
| `True` | temp, capture | pipeline-managed temp dir (auto-deleted) | **yes** |
| `"/path/to/dir"` | disk only | that directory | no |
| `Output("/path/to/dir", capture=True)` | disk + capture | that directory | **yes** |

```python
import pyvartools as vt
from pyvartools import Output, commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")

pipe = vt.Pipeline().LS(0.5, 10.0, 1e-3, save_periodogram=True)
result = pipe.run(lc)
pgram = result.files["LS_periodogram_0"]   # pd.DataFrame
pgram.to_csv("EXAMPLES/periodogram.csv", index=False)

# Mode 3: write to EXAMPLES/OUTDIR1/, do NOT capture into Python
pipe3 = vt.Pipeline().LS(0.5, 10.0, 1e-3, save_periodogram="EXAMPLES/OUTDIR1")
result3 = pipe3.run(lc)
# EXAMPLES/OUTDIR1/stdin.ls is on disk; result3.files has no "LS_periodogram_0"

# Mode 2: write to EXAMPLES/OUTDIR1/ AND capture into Python
pipe2 = (vt.Pipeline()
        .LS(0.5, 10.0, 1e-3,
           save_periodogram=Output("EXAMPLES/OUTDIR1", capture=True)))
result2 = pipe2.run(lc)
pgram2 = result2.files["LS_periodogram_0"]   # read from EXAMPLES/OUTDIR1/stdin.ls
```

### Key naming

Captured files appear in `result.files` under keys of the form **`"{CommandName}_{logical}_{idx}"`**, where `idx` is the zero-based position of the command in the pipeline. This ensures that two period-search commands (or any two commands sharing a logical name) never overwrite each other's results.

All commands with `save_*` parameters and their corresponding key patterns (command at pipeline index `N`):

| Command | `save_*` param | Key in `result.files` | Description |
|---------|---------------|-----------------------|-------------|
| `LS` | `save_periodogram` | `"LS_periodogram_N"` | Frequency vs. LS power |
| `aov` | `save_periodogram` | `"aov_periodogram_N"` | Frequency vs. AOV statistic |
| `aov_harm` | `save_periodogram` | `"aov_harm_periodogram_N"` | Frequency vs. harmonic AOV statistic |
| `BLS` | `save_periodogram` | `"BLS_periodogram_N"` | BLS power spectrum |
| `BLS` | `save_model` | `"BLS_model_N"` | Best-fit transit model |
| `BLSFixPer` | `save_model` | `"BLSFixPer_model_N"` | Best-fit model at fixed period |
| `BLSFixDurTc` | `save_periodogram` | `"BLSFixDurTc_periodogram_N"` | BLS power spectrum |
| `BLSFixDurTc` | `save_model` | `"BLSFixDurTc_model_N"` | Best-fit model |
| `BLSFixPerDurTc` | `save_model` | `"BLSFixPerDurTc_model_N"` | Best-fit model at fixed parameters |
| `autocorrelation` | `save_result` | `"autocorrelation_result_N"` | Lag vs. autocorrelation value |
| `dftclean` | `save_dspec` | `"dftclean_dspec_N"` | Dirty spectrum |
| `dftclean` | `save_wfunc` | `"dftclean_wfunc_N"` | Window function |
| `dftclean` | `save_cspec` | `"dftclean_cspec_N"` | CLEAN spectrum |
| `wwz` | `save_transform` | `"wwz_transform_N"` | Full WWZ time-frequency map |
| `wwz` | `save_maxtransform` | `"wwz_maxtransform_N"` | WWZ maximum power vs. time |
| `harmonicfilter` | `save_model` | `"harmonicfilter_model_N"` | Fitted harmonic series |
| `Injectharm` | `save_model` | `"Injectharm_model_N"` | Injected signal model |
| `Injecttransit` | `save_model` | `"Injecttransit_model_N"` | Injected transit model |
| `linfit` | `save_model` | `"linfit_model_N"` | Fitted linear model curve |
| `nonlinfit` | `save_model` | `"nonlinfit_model_N"` | Fitted non-linear model curve |
| `decorr` | `save_model` | `"decorr_model_N"` | Fitted decorrelation model |
| `TFA` | `save_coeffs` | `"TFA_coeffs_N"` | TFA trend coefficients |
| `TFA` | `save_model` | `"TFA_model_N"` | Reconstructed TFA trend |
| `TFA_SR` | `save_coeffs` | `"TFA_SR_coeffs_N"` | TFA-SR trend coefficients |
| `TFA_SR` | `save_model` | `"TFA_SR_model_N"` | Reconstructed TFA-SR trend |
| `SYSREM` | `save_model` | `"SYSREM_model_N"` | SYSREM model |
| `SYSREM` | `save_trends` | `"SYSREM_trends_N"` | SYSREM trend vectors |
| `MandelAgolTransit` | `save_model` | `"MandelAgolTransit_model_N"` | Fitted transit model LC |
| `MandelAgolTransit` | `save_phcurve` | `"MandelAgolTransit_phcurve_N"` | Phase-folded transit model |
| `MandelAgolTransit` | `save_jdcurve` | `"MandelAgolTransit_jdcurve_N"` | Time-domain transit model |
| `SoftenedTransit` | `save_model` | `"SoftenedTransit_model_N"` | Fitted trapezoidal transit model |
| `Starspot` | `save_model` | `"Starspot_model_N"` | Fitted starspot model |
| `microlens` | `save_model` | `"microlens_model_N"` | Fitted microlensing model |
| `findblends` | `save_matches` | `"findblends_matches_N"` | Matched blend candidate list |

### `autocorrelation` — special case

`autocorrelation` always writes its output file (the vartools CLI provides no option to suppress it). `save_result=False` suppresses Python capture but the file is still written to a temp directory and discarded after the run.

### Batch runs

For batch runs, `batch.files[key]` is a **list** of DataFrames — one per light curve (or `None` where the file was not produced):

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 6)]
batch = pipe.run_batch(lcs)
for i, pgram in enumerate(batch.files["LS_periodogram_0"]):
    pgram.to_csv(f"EXAMPLES/pgram_{i}.csv", index=False)
```

### The `Output` class

```python
from pyvartools import Output

Output(path=None, capture=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` or `None` | Directory to write the file to. `None` uses the pipeline-managed temp directory. |
| `capture` | `bool` | Whether to include the file in `result.files`. Default `True`. |

See [Auxiliary output files](commands/index.md#auxiliary-output-files) in the command reference for full examples.

---

## The `Result` and `BatchResult` objects

See the [Results](results.md) reference page for full attribute documentation. A brief summary:

**`Result`** (single LC):

- `result.vars` — `pd.Series` indexed by vartools output variable names
- `result.lc` — `LightCurve` or `None` (only if `capture_lc=True`)
- `result.files` — `dict[str, pd.DataFrame]`

**`BatchResult`** (multiple LCs):

- `batch.vars` — `pd.DataFrame`, one row per light curve
- `batch.lcs` — list of `LightCurve` or `None` (only if `capture_lc=True`)
- `batch.files` — `dict[str, list[pd.DataFrame]]`
- `batch.ok` — `True` if the run completed without error
- `batch.error` — `RunError` or `None`

---

## Performance and reusing a Pipeline

A `Pipeline` is **reusable** — once constructed, you can run it against any number of light curves.  The first run pays a fixed setup cost; subsequent runs reuse the parsed pipeline state and just feed in new light-curve data, so a loop of many runs is much faster than constructing a new pipeline each time:

```python
import pyvartools as vt

pipe = vt.Pipeline().rms()
for i in range(2, 8):
    lc = vt.LightCurve.from_file(f"EXAMPLES/{i}")
    result = pipe.run(lc)
```

For multiple light curves, prefer `run_batch()` or `run_filelist()` — these amortise setup across the whole batch in a single call.

### Per-LC output filenames — `cmd.o(outname=PerLC([...]))`

For batch runs that need each LC's output to land at its own filename (rather than `<outdir>/<lc.name>`), wrap a list of names in `PerLC` and pass it as `outname`:

```python
import os, tempfile
import pyvartools as vt
from pyvartools import commands as cmd

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]
outdir = tempfile.mkdtemp(prefix="perlc_outname_doc_")
names = [f"clipped_{i:03d}.txt" for i in range(1, 4)]

batch = vt.Pipeline([
    cmd.clip(5.0),
    cmd.o(outdir=outdir, outname=vt.PerLC(names), allcols=True),
]).run_batch(lcs)

assert sorted(os.listdir(outdir)) == sorted(names)
```

`outname=PerLC([...])` requires `outdir=` to also be set; the per-LC names land at `<outdir>/<name_i>`.

### Configuring the library backend

pyvartools ships with an optional shared library (`libvartoolspipeline.so`) that lets a `Pipeline` run entirely in-process, skipping per-call subprocess startup. It's installed by `make install` and is used automatically when available.

You don't normally need to think about whether a given run goes through the in-process path or a subprocess — pyvartools picks the right one and the results are the same either way. A few configurations always go through the subprocess path:

| Situation | Reason |
|-----------|--------|
| The shared library isn't installed or can't be found | No in-process backend available |
| `nthreads > 1` on `run_batch()` / `run_filelist()` | Parallel runs use the subprocess path |
| `timeout=` is set | The in-process path doesn't enforce timeouts |
| `resume=True` from a partial `stats_file` | Subprocess path only |

If the shared library is installed in a non-standard location, point pyvartools at it:

=== "Python"

    ```python
    import pyvartools as vt
    try:
        vt.set_library("/path/to/libvartoolspipeline.so")
    except FileNotFoundError:
        pass
    ```

=== "Environment variable"

    ```bash
    export VARTOOLS_LIBRARY=/path/to/libvartoolspipeline.so
    ```

To force the subprocess path globally (e.g. for benchmarking or debugging):

```bash
export VARTOOLS_USE_LIBRARY=0
```

---

## Error handling

`RunError` is raised (or stored) when:

- vartools exits with a non-zero status
- vartools cannot be found on `PATH`
- The `timeout` is exceeded

```python
from pyvartools.results import RunError

try:
    result = pipe.run(lc, timeout=30)
except RunError as e:
    print(f"vartools failed: {e}")
```
