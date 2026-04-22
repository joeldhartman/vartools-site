# Method Chaining API

pyvartools exposes every VARTOOLS command as a method directly on
`LightCurve`, `Result`, `LightCurveBatch`, and `BatchResult`, eliminating the
need to construct an explicit `Pipeline` for most workflows.

Every command method executes **immediately** and returns a result object —
there is no separate "deferred chain" step or `.run()` call needed on
`LightCurve` or `Result`.

| Object | `CMD(...)` returns | Notes |
|--------|--------------------|-------|
| `LightCurve` | `Result` | Immediate |
| `Result` | `Result` on `result.lc` | Immediate; prior vars preserved |
| `LightCurveBatch` | `LightCurveBatch` (deferred) | Call `.run()` to execute |
| `BatchResult` | `LightCurveBatch` (deferred) | Requires `capture_lc=True` |

---

## Single-LC methods — `lc.CMD(...)`

### Running a single command

```python
import pyvartools as vt

lc = vt.LightCurve.from_file("EXAMPLES/2")

result = lc.LS(0.5, 10.0, 0.1)
print(result.varobjs.LS.Period_1)   # top LS period
```

Run-time options (`capture_lc`, `timeout`, `randseed`, `skipmissing`, `jdtol`,
`matchstringid`) can be passed as keyword arguments alongside command parameters:

```python
result = lc.LS(0.5, 10.0, 0.1, capture_lc=True, randseed=42)
print(result.lc)   # output LightCurve
```

### Chaining multiple commands

Because each call returns a `Result`, you can chain commands using Python's
normal method-call syntax. Each step is a separate vartools invocation:

```python
result = lc.clip(sigclip=5.0).LS(0.5, 10.0, 0.1).rms()

print(result.varobjs.LS.Period_1)   # from LS
print(result.varobjs.rms.RMS)       # from rms
```

The output variables from all commands in the chain are available together in
the final `result.vars` and `result.varobjs` — the same as if you had run them
all in a single `Pipeline`.

You can also branch the chain from any intermediate point:

```python
r_clip = lc.clip(sigclip=5.0)        # Result after clipping

r_ls  = r_clip.LS(0.5, 10.0, 0.1)  # branch: LS on the clipped LC
r_bls = r_clip.BLS(qmin=0.01, qmax=0.1, minper=0.5, maxper=10.0,
                   nfreq=10000, nbins=200)  # branch: BLS on same clipped LC
```

### For maximum efficiency: use Pipeline

Each `.CMD()` call on `LightCurve` or `Result` carries some overhead
in communicating with the vartools library, or in launching a separate
vartools subprocess.  When running many commands, a single `Pipeline`
invocation may be faster:

```python
from pyvartools import commands as cmd

pipe = vt.Pipeline().clip(sigclip=5.0).LS(0.5, 10.0, 0.1).rms()
result = pipe.run(lc)
```

---

## Continuing from a Result — `result.CMD(...)`

All command methods are also available on `Result`. They run the command on
`result.lc` and return a new `Result` that includes the output variables from
**all prior commands** as well as the new one:

```python
r1 = lc.LS(0.5, 10.0, 0.1)
r2 = r1.Killharm(period=r1.varobjs.LS.Period_1, nharm=2)
r3 = r2.rms()

# r3.vars contains LS, Killharm, and rms output — all together
print(r3.varobjs.LS.Period_1)
print(r3.varobjs.rms.RMS)
```

`result.lc` must be non-`None` (i.e. `capture_lc=True` was used, which is
the default for all chain-step calls). An `AttributeError` is raised otherwise.

### Cross-chain references

OUTCOLUMN values produced by a prior chain segment are automatically
injected into subsequent segments as named variables. This means that
analytic expressions in a continuation can reference any output column
from earlier in the chain by its full name (including the `_N` suffix):

```python
r1 = lc.LS(0.5, 10.0, 0.1)
r2 = r1.expr("doubled=2*LS_Period_1_0", vartype="scalar")

r2.vars["LS_Period_1_0"]        # 1.2344 — OUTCOLUMN from the LS segment
r2.lc.scalars["doubled"]        # 2.4688 — SCALAR created by the expr segment
```

Similarly, user-defined scalars (created with `-expr scalar` /
`-expr listvar`) round-trip across segment boundaries and can be
referenced downstream:

```python
r1 = lc.LS(0.5, 10.0, 0.1).expr("halfper=LS_Period_1_0/2", vartype="scalar")
r2 = r1.expr("quarterper=halfper/2", vartype="scalar")

r2.lc.scalars["halfper"]        # LS_Period_1_0 / 2
r2.lc.scalars["quarterper"]     # LS_Period_1_0 / 4
```

**How it works (brief).** pyvartools assembles a CLI for each continuation
that (a) prepends `-expr const '<name>=<value>'` tokens for every scalar
carried forward from the prior segment, (b) emits an explicit
`-columnsuffix <N>` before each user command so the new segment's output
suffixes continue the numbering from where the prior one left off
(avoiding collision with the injected scalar names), and (c) appends
`-printallscalars` so any new scalar state round-trips back to
`result.lc.scalars`.

For batch chains (continuations from a `BatchResult`), the per-LC scalar
values are injected via `-inlistvars` list-file columns instead of
`-expr const`, so each LC sees its own value rather than a shared
constant. This is done automatically by `LightCurveBatch.run()`.

See [`LightCurve.scalars`](lightcurve.md#scalars),
[`BatchResult.lcscalars`](results.md#lcscalars-pddataframe),
and the CLI docs for
[`-startcommandnumber`](../cli/options.md#-startcommandnumber-n) and
[`-printallscalars`](../cli/options.md#-printallscalars).

---

## Pipeline-stateful commands

A handful of VARTOOLS commands — `savelc`, `restorelc`, `columnsuffix`,
`ifcmd`, and `o` — work only within a single vartools invocation. Calling
them as methods on `LightCurve` or `Result` raises `NotImplementedError`:

```python
try:
    lc.columnsuffix("short")
except NotImplementedError as exc:
    print(exc)   # "-columnsuffix is a pipeline-stateful command …"
```

Use `Pipeline` when you need these commands:

```python
from pyvartools import commands as cmd

pipe = (vt.Pipeline()
        .columnsuffix("short")
        .LS(0.5, 5.0, 0.01)
        .columnsuffix("long")
        .LS(5.0, 50.0, 0.1))
result = pipe.run(lc)
print(result.vars["LS_Period_1_short"])
print(result.vars["LS_Period_1_long"])
```

---

## Batch chaining — `LightCurveBatch`

`LightCurveBatch` applies a command chain to a collection of light curves,
running one vartools invocation per LC and collecting results into a
`BatchResult`.

!!! note "Performance for large surveys"
    `LightCurveBatch` runs one vartools invocation per light curve, which is
    convenient but carries per-call overhead. For large collections (hundreds of
    light curves or more), `Pipeline.run_batch()` or `Pipeline.run_filelist()`
    submit all light curves in a single vartools call and are typically a few
    times to ~20× faster, depending on light curve size and command mix. Use
    `LightCurveBatch` for interactive work and moderate-sized batches;
    switch to `Pipeline` for survey-scale processing.

### Creating a batch and running a chain

`LightCurveBatch` uses a **deferred** command-chain model: each `.CMD()` call
appends to the chain without executing it. Call `.run()` to execute the full
chain on all LCs at once:

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 6)]

batch_result = (
    vt.LightCurveBatch(lcs)
      .LS(0.5, 10.0, 1e-3)
      .rms()
      .run()
)

print(batch_result.vars[["Name", "LS_Period_1_0"]])  # DataFrame summary
print(batch_result[0].varobjs.LS.Period_1)             # per-LC access
```

`LightCurveBatch` also accepts `*args` varargs form:

```python
lc1 = vt.LightCurve.from_file("EXAMPLES/1")
lc2 = vt.LightCurve.from_file("EXAMPLES/2")
lc3 = vt.LightCurve.from_file("EXAMPLES/3")
batch = vt.LightCurveBatch(lc1, lc2, lc3)
```

### Immediate batch methods — `batch.run_CMD(...)`

```python
batch_result = vt.LightCurveBatch(lcs).run_LS(0.5, 10.0, 1e-3)
```

### Global options

Use `.with_options()` to set pipeline-level options that apply to every LC
in the batch:

```python
batch_result = (
    vt.LightCurveBatch(lcs)
      .with_options(capture_lc=False, randseed=42)
      .LS(0.5, 10.0, 1e-3)
      .run()
)
```

Options passed directly to `.run()` override those set via `.with_options()`.

### Per-LC array parameters

Any command parameter can be given a **different value for each light curve**
by passing a 1-D numpy array or a pandas Series instead of a scalar.
`LightCurveBatch` processes one LC at a time, so it resolves each array to the
appropriate scalar before running, with no restriction on which parameters are
supported:

```python
import numpy as np
import pyvartools as vt

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 6)]

# Different period search bounds for each star
result = (
    vt.LightCurveBatch(lcs)
      .LS(
          minp=np.array([0.5, 0.5, 1.0, 0.5, 0.5]),
          maxp=10.0,          # scalar: same for all LCs
          subsample=0.1,
      )
      .run()
)
```

When chaining commands from a `BatchResult` — a column from
the prior result can be used as input to the next command:

```python
# Run LS on each LC, then remove the best-fit harmonic at the detected period
br1 = vt.LightCurveBatch(lcs).run_LS(0.5, 10.0, 0.1)

# br1.vars["LS_Period_1_0"] is a Series — one period per LC
br2 = br1.Killharm(period=br1.vars["LS_Period_1_0"], nharm=2).run()
```

**Series index alignment.** When a `pandas.Series` has a string (non-integer)
index — for example after calling `.set_index("Name")` — values are matched to
light curves by name rather than by position:

```python
# Name-indexed Series: each LC gets the value for its own name
periods = br1.vars.set_index("Name")["LS_Period_1_0"]
br2 = br1.Killharm(period=periods, nharm=2).run()
```

**Plain Python lists are not auto-detected** as per-LC arrays, to avoid
ambiguity with fixed multi-valued parameters like `ld_coeffs=[0.236, 0.391]`.
Wrap them explicitly with `PerLC([...])` when you do need a per-LC list:

```python
from pyvartools import PerLC
result = vt.LightCurveBatch(lcs).LS(minp=PerLC([0.5, 0.5, 1.0, 0.5, 0.5]),
                                     maxp=10.0, subsample=0.1).run()
```

!!! note "Comparison with `Pipeline.run_batch()`"
    `Pipeline.run_batch()` also accepts per-LC arrays, via vartools'
    internal `-inlistvars` mechanism.  Every per-star parameter whose CLI
    value-spec accepts one of the `var` / `expr` / `list column`
    keywords is supported — in practice this covers period-search
    parameters on `LS`, `BLS`, `aov`, `aov_harm`, `BLSFixPer`, as well as
    `Phase.period`, `Killharm.period`, `Injectharm.period`,
    `MandelAgolTransit.P0` / `T00`, and common scalar parameters such as
    `clip.sigclip` and `restricttimes.minJD` / `maxJD`.  For those
    parameters the two backends produce identical results; `Pipeline`
    wins on throughput because it runs one vartools invocation for the
    whole batch instead of one per LC.

    `LightCurveBatch` resolves arrays to scalars in Python before each
    individual run, which additionally covers any rare parameter whose
    CLI grammar has no `var` / `expr` / `list column` escape hatch.  The
    trade-off is one vartools invocation per light curve (see the
    performance note above) — use it for interactive work and smaller
    batches, switch to `Pipeline` for survey-scale runs.

---

### Per-LC error handling

If a single LC fails, the error is captured in `batch_result[i].error` and
execution continues for the remaining LCs:

```python
for i, r in enumerate(batch_result):
    if r.ok:
        print(f"LC {i}: P = {r.varobjs.LS.Period_1:.5f} d")
    else:
        print(f"LC {i}: FAILED — {r.error}")
```

### Slicing a BatchResult

Integer index returns a `Result`; a slice returns a sub-`BatchResult`:

```python
first   = batch_result[0]       # Result
sub     = batch_result[1:4]     # BatchResult with LCs 1, 2, 3
best    = batch_result[::2]     # every other LC
```

---

## Continuing from a BatchResult

Command methods on `BatchResult` start a new deferred `LightCurveBatch` built
from the captured output light curves:

```python
# Run LS, then continue with Killharm on the output LCs
br1 = vt.LightCurveBatch(lcs).run_LS(0.5, 10.0, 1e-3)
br2 = br1.Killharm(period=br1.vars["LS_Period_1_0"], nharm=2).run()
```

`batch_result.lcs` must have been captured (`capture_lc=True`, which is
the default for `LightCurveBatch`). An `AttributeError` is raised if
`capture_lc=False` was used.

Immediate methods are also available:

```python
br2 = br1.run_rms()
```

---

## Summary table

| Object | `CMD(...)` | `run_CMD(...)` |
|--------|-----------|----------------|
| `LightCurve` | `Result` (immediate) | — not available — |
| `Result` | `Result` on `result.lc`; prior vars preserved | — not available — |
| `LightCurveBatch` | Appends command, returns new `LightCurveBatch` (deferred) | `BatchResult` (immediate) |
| `BatchResult` | Returns `LightCurveBatch` from `batch.lcs` (deferred) | `BatchResult` (immediate) |
