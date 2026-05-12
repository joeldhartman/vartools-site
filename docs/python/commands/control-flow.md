# Control Data Flow

Save / restore light-curve state, emit output columns or files, and take branching decisions inside a pipeline.

---

### `savelc` / `restorelc` — Light-curve state snapshots

**Syntax**

```python
cmd.savelc()
cmd.restorelc(savenumber=1, vars=None)
```

**Description**

Checkpoint and restore the in-memory light-curve state. `savelc` saves a snapshot of the current light curve state; `restorelc` restores a previous snapshot. Useful for running multiple analysis branches on the same underlying data without re-reading the file from disk, and for undoing a destructive transformation.

Each `savelc` call is numbered in the order it appears (1, 2, 3, …). `restorelc(savenumber=N)` restores the N-th save point. Conditional constructs (`-if` / `-elif` / `-else` / `-fi`) are ignored by `savelc` and `restorelc` — they always execute.

CLI equivalent: [`-savelc` / `-restorelc`](../../cli/control-flow.md#-savelc-restorelc).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `savenumber` | `int` | (`restorelc` only.) Index of the `savelc` snapshot to restore (1-based). |
| `vars` | `str` or `list[str]` or `None` | (`restorelc` only.) Restore only the named variables instead of the full light curve. |

**Output**

`savelc` and `restorelc` produce no output of their own — they only mutate the in-memory light-curve state seen by subsequent commands.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Run LS and BLS with different clipping levels; restore between them
pipe = (vt.Pipeline()
        .savelc()
        .clip(5.0)
        .savelc()
        .LS(0.1, 100.0, 0.1, npeaks=3, clip=5.0, clipiter=1)
        .aov(0.1, 100.0, 0.1, 0.01, npeaks=1, clip=5.0, clipiter=1)
        .restorelc(savenumber=1)
        .clip(10.0)
        .BLS(0.1, 20.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=10000, npeaks=1)
        .restorelc(savenumber=2)
        .changeerror())
batch = pipe.run_batch(lcs, nthreads=4)
print(batch.vars)
```

---

### `o` — Output light curve

**Syntax**

```python
cmd.o(outname=None, outdir=None, nameformat=None, columnformat=None,
      allcols=False, fits=False, noclobber=False, copyheader=False,
      namecommand=None, namefromlist=None, changesuffix=None,
      delimiter=None, logcommandline=False, gzip=False, bzip2=False,
      capture=False, key="o")
```

**Description**

Write the current light curve to a file, capture it back into a `Result` object, or both. Useful for saving intermediate state mid-pipeline (e.g. after sigma-clipping or filtering) and for the final output of a processed batch.

The CLI `-o` keyword takes a single positional argument that is interpreted as a *filename* in single-LC mode (`vartools -i ...`) and as a *directory* in list mode (`vartools -l ...`). pyvartools splits this dual semantics into two explicit kwargs:

- `outname=` is used when the pipeline runs through `Pipeline.run` or `Pipeline.run_file` (single-LC mode);
- `outdir=` is used when it runs through `Pipeline.run_filelist`, `Pipeline.run_batch`, or `Pipeline.run_combinelcs` (list mode).

A pipeline that supplies both can be reused in either mode; if the wrong one is supplied for the run method invoked, a clear `RuntimeError` is raised at run time.

`cmd.o` can be used in three modes:

- **Write to disk only** (`outname=` or `outdir=` set, `capture=False`): the LC is saved to disk.
- **Capture only** (`capture=True`, no `outname`/`outdir`): the LC is captured into `result.files[key]`. In library mode this is purely in-memory (vartools snapshots the LC variables into a buffer keyed by ``key``; no temporary file is ever written). In subprocess fallback mode the LC is written to a mode-appropriate temporary path and read back; pyvartools cleans the temp file up.
- **Write and capture** (`capture=True` plus `outname=` or `outdir=`): both saved to disk and captured.

When `capture=True` and no explicit `columnformat` is given, pyvartools passes the `allcols` flag to `-o` so the captured DataFrame contains every LC-vector variable registered up to that point in the pipeline (matching the library-mode fast path). If `columnformat` is given, the captured DataFrame uses the variable names listed in it.

CLI equivalent: [`-o`](../../cli/control-flow.md#-o).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `outname` | `str` or `None` | Output filename for single-LC runs (`Pipeline.run` / `run_file`). Use `"-"` for stdout. |
| `outdir` | `str` or `None` | Output directory for list/batch runs (`Pipeline.run_filelist` / `run_batch` / `run_combinelcs`). Per-LC filenames are constructed inside it. Combine with `outname=PerLC([...])` to override the per-LC basename from Python — see [Per-LC output filenames](#per-lc-output-filenames). |
| `nameformat` | `str` or `None` | Format string for output filenames in list mode, e.g. `"file_%s_%05d.txt"` (`%s` = LC basename, `%d` = sequence number). Ignored in single-LC mode. |
| `columnformat` | `str` or `None` | Output column spec, e.g. `"t:%17.9f,mag:%9.5f,err:%9.5f"`. |
| `allcols` | `bool` | Write every light-curve-vector variable defined by commands *before* this `cmd.o` in the pipeline, with a type-appropriate default `printf` format and a `# name1 name2 …` header line for ASCII output. Mutually exclusive with `columnformat`. Handy when a prior command has created new vectors (e.g. `cmd.Phase(..., phasevar="ph")`, `cmd.linfit(..., modelvar="m")`) that you want to capture without listing each one. Default `False`. |
| `fits` | `bool` | Write output in FITS binary table format. |
| `noclobber` | `bool` | Do not overwrite an existing output file. |
| `copyheader` | `bool` | Copy the FITS header from the input file to the output file. |
| `namecommand` | `str` or `None` | Shell command used to generate the output filename dynamically (list mode only). |
| `namefromlist` | `bool`, `str`, or `None` | Derive output filename from the input list (list mode only). `True` uses the default column; a string specifies a column name/number (emits `namefromlist column <col>`). To supply per-LC output names from Python rather than from a column already on the list file, pass the names via `perlc_vars` on `run_batch()` or `LightCurveBatch.run()` — see [Per-LC values from Python](../pipeline.md#per-lc-values-from-python). |
| `changesuffix` | `tuple[str, str]` or `None` | After the default basename has been built, strip a trailing `old_suffix` (if present) and append `new_suffix`. Either may be empty. Applied **before** any `fits` / `gzip` / `bzip2` suffix. Mutually exclusive with `nameformat` / `namecommand` / `namefromlist`. E.g. `changesuffix=(".fits", ".txt")` rewrites `foo.fits` → `foo.txt`. List-mode only. |
| `delimiter` | `str` or `None` | Column delimiter character for the output file (default: whitespace). |
| `logcommandline` | `bool` | Write the full vartools command line into the output file header. |
| `gzip` / `bzip2` | `bool` | Compress the output. The corresponding `.gz` / `.bz2` extension is appended if not already present, and the data are piped through the `gzip` or `bzip2` external program (must be on `PATH`). Combined with `fits=True`, `gzip=True` produces a gzip-compressed FITS file via cfitsio's native `.fits.gz` driver; `bzip2=True` cannot be combined with `fits=True`. Compression cannot be combined with stdout (`outname="-"`) when `fits=True`. Compressed inputs (`.gz`, `.Z`, `.bz2` for ASCII; `.fits.gz`, `.fits.fz`, `.fits.Z`, `.fits.bz2` for FITS) are auto-detected and decompressed on read. Mutually exclusive. |
| `capture` | `bool` | If `True`, capture the written light curve into `result.files[key]`. For single-LC runs this is a `LightCurve`; for batch runs it is a list of `LightCurve` objects. When neither `outname` nor `outdir` is supplied, the output goes to a mode-appropriate temporary path that is cleaned up automatically. Default `False`. |
| `key` | `str` | Key under which the captured LC(s) appear in `result.files`. Default `"o"`. Use a unique key when the pipeline contains more than one `cmd.o(capture=True)`. |

**Caveat — FITS input, ASCII output.** In batch mode, when the input list contains FITS light curves and the output is **ASCII** (`fits=False`), the default output filename follows the input basename — so `kplr.fits` is written as ASCII to a file *also* named `kplr.fits`. The `.fits` suffix is then misleading: the file holds plain text. Use `changesuffix` to rewrite it:

```python
.o(outdir="./outdir", changesuffix=(".fits", ".txt"))
```

For arbitrary renaming (multi-part suffixes, inserting tags, etc.) use `namecommand` with `sed`:

```python
.o(outdir="./outdir",
   namecommand=r"sed -n 's|^.*/\([^/]*\)\.fits  *\([^ ]*\) .*$|\2/\1.txt|p'")
```

**Output**

`cmd.o` writes one light-curve file per LC and adds no columns to the per-LC statistics table.

When `capture=True`:

| File key | Description |
|----------|-------------|
| `result.files[key]` | Captured light curve. For single-LC runs, a `LightCurve`; for batch runs, a list of `LightCurve` objects (one per input LC, `None` if the file is missing). The default `key` is `"o"`; set `key="..."` to disambiguate multiple capturing `cmd.o` calls in the same pipeline. |

**Examples**

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Capture the intermediate light curve state (no file left on disk)
pipe = (vt.Pipeline()
        .clip(5.0)
        .o(capture=True, key="clipped")
        .LS(0.1, 10.0, 0.1, npeaks=1))
result = pipe.run(lc)
clipped_lc = result.files["clipped"]     # LightCurve after sigma-clipping
print(result.vars["LS_Period_1_2"])     # clip=0, o=1, LS=2

# Write to disk AND capture
result2 = (vt.Pipeline()
        .clip(5.0)
        .o(outname="EXAMPLES/OUTDIR1/2.clipped", capture=True, key="clipped")).run(lc)
# File written to disk and also available as result2.files["clipped"]

# Multiple intermediate snapshots
pipe3 = (vt.Pipeline()
        .clip(5.0)
        .o(capture=True, key="after_clip")
        .medianfilter(0.05)
        .o(capture=True, key="after_filter"))
result3 = pipe3.run(lc)
after_clip   = result3.files["after_clip"]
after_filter = result3.files["after_filter"]

# Batch: result.files["o"] is a list of LightCurves, one per input LC
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = (vt.Pipeline()
        .LS(0.1, 100.0, 0.1, npeaks=1)
        .expr("phase=t")
        .changevariable("t", "phase")
        .Phase(period="ls")
        .o(capture=True, key="phased")).run_batch(lcs)
phased_lcs = batch.files["phased"]   # list of 10 LightCurve objects

# Write to a named directory with a custom nameformat.  Both run_filelist
# (paths) and run_batch (in-memory LightCurves) work — the per-LC output
# basenames come from the input filename for run_filelist, or from each
# LC's .name attribute for run_batch.
(vt.Pipeline()
        .LS(0.1, 100.0, 0.1, npeaks=1)
        .Phase(period="ls")
        .o(outdir="EXAMPLES/OUTDIR1",
          nameformat="file_%s_%05d_simout.txt",
          columnformat="t:%11.5f,mag:%7.4f,err:%7.4f")).run_filelist([f"EXAMPLES/{i}" for i in range(1, 11)])
```

!!! note "Performance: library mode"
    Most `cmd.o` configurations run in pyvartools' in-process library
    mode when `libvartoolspipeline` is installed, skipping the per-call
    subprocess fork:

    - **`outname=PATH`** (single-LC) and **`outdir=DIR`** (batch): library
      mode writes the file directly from inside the C call; the output
      file is byte-identical to subprocess mode.
    - **`capture=True` with no path**: library mode handles this entirely
      in memory.  No temporary file is written, no temp directory is
      allocated.  Multiple `cmd.o(capture=True)` snapshots at distinct
      points in one pipeline are produced in a single library call.
      Per-call cost is typically ~2 ms vs ~50 ms for subprocess.

    `capture=True` combined with `outname=`/`outdir=` (write and capture
    both) also runs in library mode via the C-side `capture_id` keyword:
    the file is written and the post-write LC arrays are pulled into
    `result.files[key]` in one library call.

    Pipelines mixing `cmd.o(...)` with auxiliary `save_*=True` outputs
    (e.g. `save_periodogram`) also run in library mode — the C-side
    writers fopen/fwrite into a per-Pipeline tmpdir during the in-
    process call, and pyvartools reads the files back with the
    existing parsers.  Performance is between full library mode and
    subprocess (still does the disk I/O for the side-output files);
    point `TMPDIR` at `/dev/shm` to make those writes RAM-only.

#### Per-LC output filenames

Batch runs (`run_batch`, `LightCurveBatch.run()`, `run_filelist` with
in-memory LCs) default to `<outdir>/<lc.name>` for each LC's output
file.  To pick the per-LC basenames from Python instead — without
needing a list file or `perlc_vars` plumbing — wrap a list of strings
in `PerLC` and pass it as `outname`:

```python
import os, tempfile
import pyvartools as vt
from pyvartools import commands as cmd

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]
outdir = tempfile.mkdtemp(prefix="cmd_o_perlc_outname_")
names = [f"star_{i:03d}.lc" for i in range(1, 4)]

batch = vt.Pipeline([
    cmd.clip(5.0),
    cmd.o(outdir=outdir, outname=vt.PerLC(names), allcols=True),
]).run_batch(lcs)

assert sorted(os.listdir(outdir)) == sorted(names)
```

The PerLC list must have one entry per light curve in the batch.
Both `outdir=` and the PerLC `outname=` are required together;
`outname=PerLC([...])` without `outdir=` raises a clear `ValueError`
at run-batch entry.  The same pipeline works in subprocess mode
(`VARTOOLS_USE_LIBRARY=0`) and produces byte-identical output files.

Multiple `cmd.o(outname=PerLC(...))` instances in a single pipeline
each map to their own outdir with their own per-LC names — pyvartools
allocates a distinct synthetic inlist variable per `cmd.o`.  Combining
with `capture=True` also works: the file is written under
`<outdir>/<name_i>` *and* the LC is captured into `result.files[key]`.

The auto-rewrite (which translates `outname=PerLC([...])` into a
synthetic `namefromlist` + per-call inlist update) leaves the user's
`cmd.o` instance unchanged after the run via `try/finally`, so a
Pipeline reused across multiple calls behaves identically each time.

---

### `print_cols` — Emit user-computed variables to the output table

**Syntax**

```python
cmd.print_cols(variables, columnnames=None, fmt=None)
```

**Description**

Include the values of one or more user-computed variables (e.g. results of `-expr` commands, list-input columns, or carried-forward scalars) as additional columns in the per-LC statistics table. This is the primary way to surface user-defined scalars in the final results table. Light-curve vectors are reduced to their first element.

The Python wrapper class is named `print_cols` because `print` is a Python built-in; the underlying CLI command is `-print`.

CLI equivalent: [`-print`](../../cli/control-flow.md#-print).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `variables` | `str` or `list[str]` | Variable names to print. Pass a comma-separated string or a list of strings. |
| `columnnames` | `str` or `list[str]` or `None` | Override the auto-generated column names. Default names are `Print_<var>_<idx>_<cmd>`. |
| `fmt` | `str` or `list[str]` or `None` | Printf-style format specifiers for each column (e.g. `"%.6f"`). |

**Output**

Per command index `N`:

| Column | Description |
|--------|-------------|
| `Print_<var>_<j>_N` | Value of the `j`-th requested variable (0-based). Replaced by the entry in `columnnames` when supplied. The trailing `_N` suffix is omitted when `-columnsuffix` is in effect for the pipeline. |

**Examples**

Print five variables to the output statistics table — the LC name, x/y coordinates from the input list, the `RMS_0` output column, and the first value of `mag` (since `mag` is a per-LC vector, `print_cols` emits its first element).

```python
batch = (vt.Pipeline()
         .rms()
         .print_cols("name,x,y,RMS_0,mag",
                     fmt="%20s,%.2f,%.2f,%.3f,%.3f")
         ).run_filelist("EXAMPLES/lc_list_tfa_sr_bin",
                        perlc_vars={
                            "name": vt.PerLCColumn(col=1, type="string"),
                            "x": vt.PerLCColumn(col=2),
                            "y": vt.PerLCColumn(col=3),
                        })
```

---

### `addfitskeyword` — Add a FITS keyword

**Syntax**

```python
cmd.addfitskeyword(keyword, dtype, value, comment=None,
                   hdu=None, mode=None, combinelc=None)
```

**Description**

Add a FITS header keyword to any subsequently output FITS-format light curve. Use this together with `cmd.o(..., fits=True)` to attach metadata derived from list-file columns, expressions, or fixed constants.

`value` may be a Python scalar (auto-wrapped with the `"fix"` keyword) or a full vartools token string such as `"var myvar"`. `dtype` is one of `"TDOUBLE"`, `"TINT"`, `"TLONG"`, or `"TSTRING"`.

CLI equivalent: [`-addfitskeyword`](../../cli/control-flow.md#-addfitskeyword).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `keyword` | `str` | FITS keyword name (max 8 characters). When `combinelc` is set, may contain `%d`, replaced by each unique LC-number value. |
| `dtype` | `str` | Data type: `"TDOUBLE"`, `"TINT"`, `"TLONG"`, or `"TSTRING"`. |
| `value` | scalar or `str` | Keyword value. Bare scalars (`int`/`float`) are auto-prefixed with `"fix"`; pass a string like `"var myvar"` or `"fix 3.14"` to control the form explicitly. |
| `comment` | `str` or `None` | Optional FITS comment string. |
| `hdu` | `str` or `None` | `"primary"` (default) to place the keyword in the primary header, or `"extension"` for the binary-table extension header. |
| `mode` | `str` or `None` | `"append"` to add a duplicate keyword if one already exists, or `"update"` (default) to overwrite. |
| `combinelc` | `str` or `None` | Variable name holding the LC number for combined-LC mode; emits one keyword per unique value. |

**Output**

`addfitskeyword` produces no output of its own — it only attaches metadata to the next FITS file written by `cmd.o(..., fits=True)`.

**Examples**

Convert ASCII `EXAMPLES/1` to a FITS LC at `EXAMPLES/1.tmpout.fits`, attaching a string keyword `TMPKEY` taken from the input-list variable `x` (which evaluates to `"HELLO"` for this list line).

```python
# A two-column list file ("EXAMPLES/lc_list_addfitskey" contains
# "EXAMPLES/1 HELLO") supplies the per-LC value of x via perlc_vars.
batch = (vt.Pipeline()
         .addfitskeyword("TMPKEY", "TSTRING", value="var x",
                         comment="a comment")
         .o(outdir="EXAMPLES/", nameformat="%s.tmpout.fits", fits=True)
         ).run_filelist("EXAMPLES/lc_list_addfitskey",
                        perlc_vars={"x": vt.PerLCColumn(col=2, type="string")})
```

---

### `changevariable` — Reassign standard column roles

**Syntax**

```python
cmd.changevariable(column, var)
```

**Description**

Reassign the internal role of one of the four standard columns — time (`"t"`), magnitude (`"mag"`), uncertainty (`"err"`), or image identifier (`"id"`) — to a different named light-curve variable. Subsequent commands then use the new assignment. The original variable still exists; to restore it, issue `cmd.changevariable("mag", "mag")`.

Useful when reading FITS files with non-standard column mappings, or for temporarily swapping the time axis to a derived variable such as phase before running a phase-folded operation.

CLI equivalent: [`-changevariable`](../../cli/control-flow.md#-changevariable).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `column` | `str` | Which built-in role to reassign. One of `"t"`, `"mag"`, `"err"`, or `"id"`. |
| `var` | `str` | Name of the existing light-curve column to promote to that role. |

**Output**

`changevariable` produces no output of its own — it only changes which named variable subsequent commands treat as the time/magnitude/error/id column.

**Examples**

```python
pipe = (vt.Pipeline()
        .LS(0.1, 100.0, 0.1, npeaks=1)
        .expr("phase=t")
        .changevariable("t", "phase")
        .Phase(period="ls")
        .changevariable("t", "t"))
```

---

### `ifcmd` / `elifcmd` / `elsecmd` / `ficmd` — Conditional execution

**Syntax**

```python
cmd.ifcmd(condition)
cmd.elifcmd(condition)
cmd.elsecmd()
cmd.ficmd()
```

**Description**

Build a conditional block using the four vartools flow-control commands (`-if`, `-elif`, `-else`, `-fi`). Each wrapper emits a single CLI token; `ifcmd` and `elifcmd` additionally take the condition expression as a single token. A block **must** be closed with `ficmd()`. Nested blocks are supported.

If `condition` evaluates to `0` (cast to integer), commands inside that branch are skipped; any non-zero integer value causes the branch to execute. Conditions may reference any per-LC scalar produced by an earlier command in the pipeline (e.g. `RMS_0`, `Log10_LS_Prob_1_0`).

The classes are named `ifcmd` / `elifcmd` / `elsecmd` / `ficmd` because `if`, `elif`, `else`, and `fi` overlap with Python reserved words. The corresponding CLI tokens are `-if`, `-elif`, `-else`, `-fi`.

CLI equivalent: [`-if` / `-elif` / `-else` / `-fi`](../../cli/control-flow.md#-if-elif-else-fi).

!!! caution
    Conditional constructs are **ignored** by commands that process all light curves simultaneously (e.g. `-SYSREM`, `-findblends`) and by `savelc` / `restorelc` — those always execute.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `condition` | `str` | (`ifcmd` and `elifcmd` only.) Analytic expression evaluated to decide whether to execute the branch. May reference any variable computed by a preceding command, light-curve vectors, or scalar constants. The branch is taken when the expression evaluates to a non-zero integer. |

**Output**

The conditional wrappers produce no output of their own; the columns and files written by the pipeline are determined by the commands inside each branch.

**Examples**

Run an LS period search and apply a harmonic filter only to light curves with strong periodicity.

```python
batch = (vt.Pipeline()
         .LS(0.5, 20.0, 4.0, npeaks=1)
         .ifcmd("Log10_LS_Prob_1_0 < -10.0")
         .harmonicfilter("ls", nharm=2, nsubharm=0,
                         save_model="EXAMPLES/OUTDIR1")
         .ficmd()
         ).run_filelist("EXAMPLES/lc_list")
```

Apply different statistics depending on the values returned by `rms`. Each branch runs in the same vartools invocation, so output-column suffixes keep their positional indices across branches.

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
pipe = (vt.Pipeline()
        .rms()
        .ifcmd("RMS_0>10*Expected_RMS_0")
        .stats("mag", "stddev")
        .elifcmd("Npoints_0>3000")
        .stats("mag", "kurtosis")
        .elsecmd()
        .rms()
        .ficmd())
batch = pipe.run_batch(lcs)
```

---
