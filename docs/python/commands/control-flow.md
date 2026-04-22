# Control Data Flow

Save / restore light-curve state, emit output columns or files, and take branching decisions inside a pipeline.

---

## `savelc` / `restorelc` — Light-curve state snapshots

```python
cmd.savelc()
cmd.restorelc(savenumber=1, vars=None)
```

`savelc` saves a snapshot of the current light curve state.  `restorelc`
restores a previous snapshot — useful for running multiple analysis branches
on the same underlying data without re-reading the file.

**Example**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Run LS and BLS with different clipping levels; restore between them
pipe = vt.Pipeline([
    cmd.savelc(),
    cmd.clip(5.0),
    cmd.savelc(),
    cmd.LS(0.1, 100.0, 0.1, npeaks=3, clip=5.0, clipiter=1),
    cmd.aov(0.1, 100.0, 0.1, 0.01, npeaks=1, clip=5.0, clipiter=1),
    cmd.restorelc(savenumber=1),   # back to pre-5σ-clip state
    cmd.clip(10.0),
    cmd.BLS(0.1, 20.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=10000, npeaks=1),
    cmd.restorelc(savenumber=2),   # back to 5σ-clipped state
    cmd.changeerror(),
])
batch = pipe.run_batch(lcs, nthreads=4)
print(batch.vars)
```

---

## `o` — Output light curve

```python
cmd.o(filename=None, nameformat=None, columnformat=None, allcols=False,
      fits=False, noclobber=False, copyheader=False,
      namecommand=None, namefromlist=None, delimiter=None,
      logcommandline=False, capture=False, key="o")
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `filename` | `str` or `None` | Output file path (or directory in batch mode). Required unless `capture=True`. |
| `nameformat` | `str` or `None` | Format string for output filenames in batch mode, e.g. `"file_%s_%05d.txt"` (`%s` = LC basename, `%d` = sequence number). |
| `columnformat` | `str` or `None` | Output column spec, e.g. `"t:%17.9f,mag:%9.5f,err:%9.5f"`. |
| `allcols` | `bool` | Write every light-curve-vector variable defined by commands *before* this `cmd.o` in the pipeline, with a type-appropriate default `printf` format and a `# name1 name2 …` header line for ASCII output. Mutually exclusive with `columnformat`. Handy when a prior command has created new vectors (e.g. `cmd.Phase(..., phasevar="ph")`, `cmd.linfit(..., modelvar="m")`) that you want to capture without listing each one. Default `False`. |
| `fits` | `bool` | Write output in FITS binary table format. |
| `noclobber` | `bool` | Do not overwrite an existing output file. |
| `copyheader` | `bool` | Copy the FITS header from the input file to the output file. |
| `namecommand` | `str` or `None` | Shell command used to generate the output filename dynamically. |
| `namefromlist` | `bool`, `str`, or `None` | Derive output filename from the input list. `True` uses the default column; a string specifies a column name/number (emits `namefromlist column <col>`). |
| `delimiter` | `str` or `None` | Column delimiter character for the output file (default: whitespace). |
| `logcommandline` | `bool` | Write the full vartools command line into the output file header. |
| `capture` | `bool` | If `True`, capture the written light curve into `result.files[key]`. For single-LC runs this is a `LightCurve`; for batch runs it is a list of `LightCurve` objects. When `filename=None`, the output goes to a temporary file that is cleaned up automatically. Default `False`. |
| `key` | `str` | Key under which the captured LC(s) appear in `result.files`. Default `"o"`. Use a unique key when the pipeline contains more than one `cmd.o(capture=True)`. |

`cmd.o` can be used in three modes:

- **Write to disk only** (`filename="path"`, `capture=False`): existing behaviour; the LC is saved to disk.
- **Capture only** (`capture=True`, `filename=None`): the LC is written to a temp file, captured into `result.files[key]`, and the temp file is cleaned up automatically.
- **Write and capture** (`capture=True`, `filename="path"`): the LC is both saved to disk and captured into `result.files[key]`.

When `capture=True` and no explicit `columnformat` is given, pyvartools passes the `allcols` flag to `-o` so the captured DataFrame contains every LC-vector variable registered up to that point in the pipeline (matching the library-mode fast path). If `columnformat` is given, the captured DataFrame uses the variable names listed in it.

**Examples**

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Capture the intermediate light curve state (no file left on disk)
pipe = vt.Pipeline([
    cmd.clip(5.0),
    cmd.o(capture=True, key="clipped"),   # captured, no disk file
    cmd.LS(0.1, 10.0, 0.1, npeaks=1),
])
result = pipe.run(lc)
clipped_lc = result.files["clipped"]     # LightCurve after sigma-clipping
print(result.vars["LS_Period_1_2"])     # clip=0, o=1, LS=2

# Write to disk AND capture
result2 = vt.Pipeline([
    cmd.clip(5.0),
    cmd.o(filename="EXAMPLES/OUTDIR1/2.clipped", capture=True, key="clipped"),
]).run(lc)
# File written to disk and also available as result2.files["clipped"]

# Multiple intermediate snapshots
pipe3 = vt.Pipeline([
    cmd.clip(5.0),
    cmd.o(capture=True, key="after_clip"),
    cmd.medianfilter(0.05),
    cmd.o(capture=True, key="after_filter"),
])
result3 = pipe3.run(lc)
after_clip   = result3.files["after_clip"]
after_filter = result3.files["after_filter"]

# Batch: result.files["o"] is a list of LightCurves, one per input LC
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline([
    cmd.LS(0.1, 100.0, 0.1, npeaks=1),
    cmd.expr("phase=t"),
    cmd.changevariable("t", "phase"),
    cmd.Phase(period="ls"),
    cmd.o(capture=True, key="phased"),
]).run_batch(lcs)
phased_lcs = batch.files["phased"]   # list of 10 LightCurve objects

# Write to a named directory with a custom nameformat.  Disk-backed outputs
# (-o directory ... nameformat) require on-disk input filenames, so use
# run_filelist rather than run_batch here.
vt.Pipeline([
    cmd.LS(0.1, 100.0, 0.1, npeaks=1),
    cmd.Phase(period="ls"),
    cmd.o("EXAMPLES/OUTDIR1",
          nameformat="file_%s_%05d_simout.txt",
          columnformat="t:%11.5f,mag:%7.4f,err:%7.4f"),
]).run_filelist([f"EXAMPLES/{i}" for i in range(1, 11)])
```

---

## `print` — Emit user-computed variables to the output table

```python
cmd.print_cols(variables, columnnames=None, fmt=None)
```

Include the values of one or more user-computed variables (e.g. results of `-expr` commands, or carried-forward scalars) as additional columns in the statistics table. Corresponds to `-print` in the CLI.

**Parameters**

- `variables : str or list[str]` — Variable names to print. Pass a comma-separated string or a list.
- `columnnames : str or list[str], optional` — Override the auto-generated column names (default: `Print_<var>_<idx>_<cmd>`).
- `fmt : str or list[str], optional` — Printf-style format specifiers (e.g. `"%.6f"`).

**Examples**

```python
# Print a vartools output column along with a derived expression
pipe = vt.Pipeline([
    cmd.LS(0.5, 20.0, 4.0, npeaks=1),
    cmd.expr("doubled=2*LS_Period_1_0"),
    cmd.print_cols("LS_Period_1_0,doubled",
              columnnames="Period,Doubled",
              fmt="%.6f,%.6f"),
])
batch = pipe.run_batch(lcs)
print(batch.vars[["Period_2", "Doubled_2"]])
```

---

## `addfitskeyword` — Add a FITS keyword

```python
cmd.addfitskeyword(keyword, dtype, value, comment=None,
                   hdu=None, mode=None, combinelc=None)
```

Add a FITS header keyword to the output statistics table. `dtype` is one of `"TDOUBLE"`, `"TINT"`, `"TLONG"`, `"TSTRING"`. `value` can be a Python scalar (auto-wrapped with `"fix"`) or a full vartools token string like `"var myvar"`.

---

## `changevariable` — Reassign standard column roles

```python
cmd.changevariable(column, var)
```

`changevariable` copies a named variable into one of the standard columns:
``"t"``, ``"mag"``, ``"err"``, or ``"id"``.  Useful when reading FITS files
with non-standard column mappings, or for temporarily swapping the time axis
to a derived variable such as phase.

**Example**

```python
pipe = vt.Pipeline([
    cmd.LS(0.1, 100.0, 0.1, npeaks=1),
    cmd.expr("phase=t"),
    cmd.changevariable("t", "phase"),
    cmd.Phase(period="ls"),
    cmd.changevariable("t", "t"),  # revert so output sorts by time
])
```

---

## `ifcmd` / `elifcmd` / `elsecmd` / `ficmd` — Conditional execution

```python
cmd.ifcmd(condition)
cmd.elifcmd(condition)
cmd.elsecmd()
cmd.ficmd()
```

Build a conditional block using the four vartools flow-control commands (`-if`, `-elif`, `-else`, `-fi`). Each wrapper emits a single CLI token; `ifcmd` and `elifcmd` additionally take the condition expression as a single token. A block **must** be closed with `ficmd()`.

The classes are named `ifcmd` / `elifcmd` / `elsecmd` / `ficmd` because `if`, `elif`, `else`, and `fi` overlap with Python reserved words.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Run different statistics depending on variability level.  Each branch
# runs in the same vartools invocation, so output-column suffixes keep
# their positional indices across branches.
pipe = vt.Pipeline([
    cmd.rms(),
    cmd.ifcmd("RMS_0>10*Expected_RMS_0"),
        cmd.stats("mag", "stddev"),
    cmd.elifcmd("Npoints_0>3000"),
        cmd.stats("mag", "kurtosis"),
    cmd.elsecmd(),
        cmd.rms(),
    cmd.ficmd(),
])
batch = pipe.run_batch(lcs)
print(batch.vars.columns.tolist())
```

---
