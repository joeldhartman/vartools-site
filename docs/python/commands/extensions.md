# Extension Commands

pyvartools ships typed wrappers for the USERLIB extensions bundled with vartools and a generic integration layer for hand-written extensions.

---

## User Extension Commands

vartools supports user-developed commands compiled as shared libraries (`.so` / `.la`). Eight such extensions are bundled with the source tree under `USERLIBS/src/` — `-fastchi2`, `-ftuneven`, `-hatpiflag`, `-jktebop`, `-macula`, `-magadd`, `-splinedetrend`, and `-stitch` (see [Extension Commands](../../cli/extensions.md) for the CLI reference). pyvartools ships typed Python wrappers for all eight, so they can be used exactly like a built-in command; it also exposes a generic integration layer for user-written extensions.

## How extensions are loaded

At the CLI level, an extension is loaded with `-L path/to/lib.so` placed immediately before the command flag:

```bash
vartools -l lc_list -L USERLIBS/src/stitch.so -stitch mag err mask lcnum median -tab
```

If the library is installed into the vartools userlibs data directory (e.g. via `make install` in `USERLIBS/src/`), vartools loads it automatically and the `-L` flag is not needed. pyvartools mirrors both behaviours.


### Bundled typed wrappers

Every bundled extension has a dedicated class in `pyvartools.commands` with typed parameters. Each constructor takes an optional `lib_path=` argument; omit it when the extension is installed and auto-loaded, or pass the path to the `.so` / `.la` file explicitly:

```python
import pyvartools as vt
from pyvartools.commands import fastchi2, stitch

# Auto-loaded extension: just use the command directly
r = vt.fastchi2("EXAMPLES/2", Nharm=2, freqmax=24.0, freqmin=0.1)

# Explicit lib_path for an uninstalled extension (development tree)
pipe = (vt.Pipeline()
        .fastchi2(Nharm=2, freqmax=24.0, freqmin=0.1,
             lib_path="USERLIBS/src/.libs/fastchi2.so"))
```

All typed-wrapper pipelines automatically run in **subprocess mode** (library/in-process mode does not support dynamically loaded extensions).

### `magadd` — add a constant to magnitudes

```python
from pyvartools.commands import magadd
pipe = vt.Pipeline().magadd(5.0)                      # fix 5.0
pipe = vt.Pipeline().magadd("fixcolumn MeanMag_0")    # from prior stats column
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `float` or `str` | Bare number → `fix value`; string → split as `"fix v"`, `"list [column N]"`, `"fixcolumn NAME"`, or `"expr EXPR"`. |
| `lib_path` | `str`, optional | Path to `magadd.so` / `magadd.la`. |

**Examples**

```python
# Add 0.5 mag to every observation of EXAMPLES/2; the two rms calls show the
# mean magnitude shifts by 0.5 while the RMS is unchanged.
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = (vt.Pipeline()
          .rms()
          .magadd(0.5, lib_path="USERLIBS/src/.libs/magadd.so")
          .rms()).run(lc)
print(result.vars["RMS_0"], result.vars["RMS_2"])
```

### `hatpiflag` — HATPI binary flag combiner

```python
from pyvartools.commands import hatpiflag
pipe = (vt.Pipeline()
        .hatpiflag("fiphot_flag", "rejbadframe_mask",
              "tfa_outlier_mask", "pointing_outlier_flag", "quality_flag"))
```

Combines four per-observation inputs (fiphot string flag, reject-bad-frame mask, TFA-outlier mask, pointing-outlier flag) into a single bit-packed flag written to a new output variable.

**Examples**

```python
# Read a 7-column LC (t/mag/err + four HATPI flag columns) and combine the
# four flag vectors into a single quality_flag.  The string-typed fiphot
# flag column is declared with vt.LCColumn(col=4, type="string") in the
# `columns=` mapping.
batch = (vt.Pipeline()
         .hatpiflag("fiphot_flag", "rejbadframe", "tfa_mask",
                    "pointing_outlier", "quality_flag",
                    lib_path="USERLIBS/src/.libs/hatpiflag.so")
         .stats("quality_flag", "mean,sum,max")
         ).run_filelist(["EXAMPLES/2.hatpiflag"],
                        columns={
                            "t": 1, "mag": 2, "err": 3,
                            "fiphot_flag": vt.LCColumn(col=4, type="string"),
                            "rejbadframe": 5,
                            "tfa_mask": 6,
                            "pointing_outlier": 7,
                        })
```

### `fastchi2` — Palmer (2009) fast chi² periodogram

```python
from pyvartools.commands import fastchi2
pipe = (vt.Pipeline()
        .fastchi2(Nharm=2, freqmax=24.0, freqmin=0.1,
             oversample=4, Npeak=3, save_per=True))
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `Nharm` | value-spec | Number of harmonics in the model. |
| `freqmax` | value-spec | Maximum search frequency (cycles/day). |
| `freqmin` | value-spec, optional | Minimum search frequency (default 0). |
| `detrendorder` | value-spec, optional | Polynomial order for pre-detrending. |
| `t0`, `timespan`, `oversample`, `chimargin` | value-spec, optional | Pre-search knobs; see the CLI help for semantics. |
| `Npeak` | int, optional | Number of peaks to report. |
| `norefitpeak` | bool | Skip the fine peak search. |
| `save_per`, `save_model` | `Output`-spec | Periodogram / model-LC output. |
| `omodelvariable` | str, optional | Name of a variable to store the model curve. |

“value-spec” = a number (emitted as `fix N`), or a string `"fix V"` / `"list [column N]"` / `"fixcolumn NAME"` / `"expr EXPR"`.

**Examples**

```python
# Run Palmer's Fast chi^2 periodogram on EXAMPLES/2; search 0.1–10 cyc/day
# with one harmonic and capture the periodogram.
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = lc.fastchi2(Nharm=1, freqmax=10.0, freqmin=0.1,
                     save_per="EXAMPLES/OUTDIR1",
                     lib_path="USERLIBS/src/.libs/fastchi2.so")
```

### `splinedetrend` — basis-spline / poly / harmonic detrending

```python
from pyvartools.commands import splinedetrend
pipe = (vt.Pipeline()
        .splinedetrend(["t:spline:0.1:3", "x:poly:2", "y:poly:2"],
                  sigmaclip=4.0, save_model=True))
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `detrendvecs` | str or list | Single comma-joined string or a list of `VAR:<spline:knotspacing:order \| poly:order \| harm:nharm>[:groupbygap:gapsize]` specs. |
| `sigmaclip` | value-spec, optional | Sigma-clip threshold. |
| `save_model` / `save_coeffs` | `Output`-spec | Model / coefficient output. |
| `omodelvariable` | str, optional | Comma-separated `outvar[:inputvar]` list. |

**Examples**

The canonical example (a TESS sector-1 LC for GAIA DR2 6479535620075955328) reads several auxiliary columns (`x`, `y`, `temp`) from a FITS file. Because that requires a non-default `-inputlcformat` flag while loading the LC inside vartools, the cleanest Python equivalent invokes vartools directly via `subprocess`.

```python
import subprocess
subprocess.run([
    "vartools",
    "-i", "EXAMPLES/6479535620075955328_llc.fits",
    "-inputlcformat", "t:TMID_BJD,mag:IRM1,err:IRE1,x:XIC,y:YIC,temp:CCDTEMP",
    "-L", "USERLIBS/src/.libs/splinedetrend.so",
    "-expr", "magorig=mag",
    "-splinedetrend",
    "t:spline:1.0:3:groupbygap:0.5,x:poly:1,y:poly:1,temp:poly:1",
    "sigmaclip", "fix", "3.0",
    "omodel", "EXAMPLES/OUTDIR1/",
    "omodelcoeffs", "EXAMPLES/OUTDIR1/",
    "omodelvariable", "tmod:t,xmod:x,ymod:y,tempmod:temp",
    "-o", "EXAMPLES/OUTDIR1/6479535620075955328.splinedetrend.lc.txt",
    "columnformat", "t,magorig,mag,err,x,y,temp,tmod,xmod,ymod,tempmod",
    "-rms", "-oneline",
], check=True)
```

### `ftuneven` — complex Fourier transform of unevenly-sampled data

```python
from pyvartools.commands import ftuneven

# Write the FT into four light-curve variables
pipe = (vt.Pipeline()
        .ftuneven(output_vectors=("freq", "ft_real", "ft_imag", "periodogram"),
             freqrange=(0.01, 10.0, 0.001)))

# Write the FT to a per-LC file using an automatic frequency grid
pipe = vt.Pipeline().ftuneven(output_file=True, freqauto=True)
```

Exactly one output mode (`output_vectors`, `output_file`, or both via the `outputvectorsandfile` path) and one frequency source (`freqauto`, `freqrange`, `freqvariable`, or `freqfile`) must be specified. `freqrange` is a `(min, max, step)` tuple of value-specs.

**Examples**

```python
# Compute Scargle's complex Fourier transform of EXAMPLES/2 over a uniform
# frequency grid (radians per unit time), writing the FT to a per-LC file.
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = lc.ftuneven(output_file="EXAMPLES/OUTDIR1",
                     freqrange=(0.05, 5.0, 0.001),
                     lib_path="USERLIBS/src/.libs/ftuneven.so")
```

### `stitch` — stitch multi-segment light curves at offsets

```python
from pyvartools.commands import stitch
pipe = (vt.Pipeline()
        .stitch("mag", "err", "mask", "lcnum", method="median",
           groupbytime=30.0, save_fitted_parameters=True))

# Multiple magnitude/uncertainty/mask variables
pipe = (vt.Pipeline()
        .stitch(["mag_ap1", "mag_ap2"], ["err_ap1", "err_ap2"],
           ["mask_ap1", "mask_ap2"], "lcnum", method="poly 3"))
```

`method` is one of `"median"`, `"mean"`, `"weightedmean"`, `"poly ORDER"`, or `"harmseries PERIODVAR NHARM"`. See the constructor docstring for the full list of optional keywords (`refnum_var`, `fitonly`, `add_stitchparams_fitsheader`, `shifts_file`, etc.).

**Examples**

`-stitch` is most useful with the `-l ... combinelcs` input mode, which combines multiple files into a single in-memory LC. The cleanest way to drive that from pyvartools is `Pipeline.run_combinelc()` for a single combined LC or `run_combinelcs()` for many groups; both default to emitting `lcnumvar lcnum`, which `-stitch` consumes.

```python
import pyvartools as vt
from pyvartools.commands import stitch

# Combine EXAMPLES/2 and EXAMPLES/2.shifted (= EXAMPLES/2 with +0.3 mag) into a
# single LC and remove the inter-segment offset by median.  The two -rms calls
# show the offset before and after stitching.
result = (vt.Pipeline()
          .expr("mask=mag*0+1")
          .rms()
          .stitch("mag", "err", "mask", "lcnum", method="median",
                  lib_path="USERLIBS/src/.libs/stitch.so")
          .rms()
          ).run_combinelc(["EXAMPLES/2", "EXAMPLES/2.shifted"])
print(result.vars[["RMS_1", "RMS_3"]])   # before / after stitching
```

### `jktebop` — detached eclipsing-binary model

```python
from pyvartools.commands import jktebop
pipe = (vt.Pipeline()
        .jktebop("fit",
            Period=2.5,     vary_Period=True,
            T0=0.0,         vary_T0=True,
            r1_r2=0.3, r2_r1=0.5, M2_M1=1.0, J2_J1=1.0,
            i=89.0,         vary_i=True,
            esinomega=0.0, ecosomega=0.0,
            LD1_law="quad", LD1_coeffs=(0.3, 0.3),
            LD2_law="lockLD1",
            correctlc=True, save_model=True))
```

Every mandatory parameter (`Period`, `T0`, `r1_r2`, `r2_r1`, `M2_M1`, `J2_J1`, `i` **or** `bimpact`, `esinomega`, `ecosomega`) is a value-spec; pass the corresponding `vary_*=True` to free that parameter in the fit. Optional parameters: `gravdark1/2`, `reflection1/2`, `L3`, `tidallag`. `save_curve`, `curve_xaxis="jd"|"phase"` and `curve_step` emit a dense model curve.

**Examples**

```python
# Inject a JKTEBOP detached EB signal (P=2.5d, R2/R1=0.5, J2/J1=0.3, i=89 deg,
# circular orbit, quadratic LD) into EXAMPLES/3 and recover the primary eclipse
# with -BLS.
lc = vt.LightCurve.from_file("EXAMPLES/3")
result = (vt.Pipeline()
          .jktebop("inject",
                   Period=2.5, T0=53727.0,
                   r1_r2=0.15, r2_r1=0.5,
                   M2_M1=0.6, J2_J1=0.3,
                   i=89.0,
                   esinomega=0.0, ecosomega=0.0,
                   LD1_law="quad", LD1_coeffs=(0.3, 0.3),
                   LD2_law="lockLD1",
                   save_model="EXAMPLES/OUTDIR1/",
                   lib_path="USERLIBS/src/.libs/jktebop.so")
          .BLS(1.0, 5.0, rmin=0.01, rmax=0.1,
               nbins=200, nfreq=5000, npeaks=1)).run(lc)
```

### `macula` — Kipping (2012) spot model

```python
from pyvartools.commands import macula
pipe = (vt.Pipeline()
        .macula("fit lm",
           Prot=10.0, vary_Prot=True,
           istar=1.4, kappa2=0.0, kappa4=0.0,
           c1=0.2, c2=0.1, c3=0.0, c4=0.0,
           d1=0.2, d2=0.1, d3=0.0, d4=0.0,
           blend=1.0,
           spots=[{
               "Lambda0": 0.0, "Phi0": 1.23, "alphamax": 0.2,
               "fspot": 0.1, "tmax": 0.0, "life": 1000.0,
               "ingress": 0.1, "egress": 0.1,
           }],
           save_model=True))
```

`mode` is `"inject"` or `"fit amoeba"` / `"fit lm"`. Each of the 13 global parameters (`Prot`, `istar`, `kappa2`, `kappa4`, `c1–c4`, `d1–d4`, `blend`) is a keyword-argument value-spec with a matching `vary_<name>` flag. `spots` is a list of dicts, one per active spot, each providing value-specs for the eight per-spot parameters (`Lambda0`, `Phi0`, `alphamax`, `fspot`, `tmax`, `life`, `ingress`, `egress`). Individual spot parameters can be marked free by passing a `(value, True)` tuple (or a `"vary_<name>": True` entry in the dict).

**Examples**

```python
# Inject a single spotted-star light curve into EXAMPLES/3 (Macula's
# "inject" mode), using the LC time sampling and replacing the magnitudes
# with Gaussian noise.  tmax is set to the start time computed by `stats`.
lc = vt.LightCurve.from_file("EXAMPLES/3")
pipe = (vt.Pipeline()
        .stats("t", "min")
        .expr("mag=10.0+err*gauss()")
        .macula(
            "inject",
            Prot=1.234567, istar=1.4567,
            kappa2=0.0, kappa4=0.0,
            c1=0.2, c2=0.1, c3=0.0, c4=0.0,
            d1=0.2, d2=0.1, d3=0.0, d4=0.0,
            blend=1.0,
            spots=[{
                "Lambda0": 0.0, "Phi0": 1.2345,
                "alphamax": 0.2, "fspot": 0.1,
                "tmax": "fixcolumn STATS_t_MIN_0",
                "life": 1000.0,
                "ingress": 0.1, "egress": 0.1,
            }],
            lib_path="USERLIBS/src/.libs/macula.so")
        .o("EXAMPLES/OUTDIR1/3.maculainject"))
result = pipe.run(lc)
```

The injected light curve from Example 1 with the fitted-model curve overplotted (Example 2):

![Macula injected vs fitted model](../../assets/examples/macula_ex1.png)


### Generic integration layer

For user-written extensions that do not ship with vartools — or for quick one-off use of a bundled extension — pyvartools provides four lower-level entry points: `UserCommand`, `load_userlib`, `discover_userlibs`, and the base-class subclass pattern.

## Usage pattern 1 — quick one-off (`UserCommand`)

`UserCommand` is the lowest-level entry point. Pass the library path, the command name, and the raw argument tokens:

```python
import pyvartools as vt
from pyvartools import commands as cmd

# -stitch needs a per-observation mask variable and a per-observation
# lcnum (assigned by run_combinelcs with `lcnumvar=...`).
groups = [["EXAMPLES/1", "EXAMPLES/2"], ["EXAMPLES/3", "EXAMPLES/4"]]

pipe = (vt.Pipeline()
        .expr("mask=0")
        .add(vt.UserCommand(
        "USERLIBS/src/.libs/stitch.so",   # path to .so
        "stitch",                          # command name
        "mag err mask lcnum median",       # raw args (str or list)
    )))
result = pipe.run_combinelcs(groups, lcnumvar="lcnum")
```

When the library is installed and auto-loaded, omit the path:

```python
pipe = (vt.Pipeline()
        .expr("mask=0")
        .add(vt.UserCommand(None, "stitch", "mag err mask lcnum median")))
result = pipe.run_combinelcs(groups, lcnumvar="lcnum")
```

`UserCommand` constructor parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `lib_path` | `str`, `Path`, or `None` | Path to the `.so` / `.la` file. `None` or `""` means the library is auto-loaded from the vartools userlibs directory. |
| `name` | `str`, optional | Command name (e.g. `"stitch"`). Inferred from the filename stem when `lib_path` is given. |
| `args` | `str` or `list[str]` | Raw CLI tokens passed after the command flag. A plain string is split on whitespace. Default: empty. |

Call `.help()` or `.examples()` on any instance to print the vartools help text for the command (requires the binary and library to be loadable):

```python
vt.UserCommand("USERLIBS/src/stitch.so", "stitch").help()
```

## Usage pattern 2 — named class (`load_userlib`)

`load_userlib()` creates a reusable `UserCommand` subclass with the library path and command name pre-bound. The returned class is functionally equivalent to a hand-written command wrapper and can be further subclassed.

```python
Stitch = vt.load_userlib("USERLIBS/src/.libs/stitch.so")

# Pipeline builder methods are generated at import time for the built-in
# command classes, so user classes created at runtime (like this one) are
# added with `.add(instance)`:
pipe = (vt.Pipeline()
        .expr("mask=0")
        .add(Stitch("mag err mask lcnum median")))
result = pipe.run_combinelcs(groups, lcnumvar="lcnum")
```

`load_userlib()` parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `lib_path` | `str` or `Path` | Path to the `.so` / `.la` file. Resolved to an absolute path. |
| `name` | `str`, optional | Command name. Defaults to the filename stem. |
| `cls_name` | `str`, optional | Python class name for the returned type. Defaults to the title-cased command name (e.g. `"Stitch"`). |

The class docstring is populated by running `vartools -L lib -help -name` at creation time, so `help(Stitch)` or `Stitch.help()` shows live vartools documentation.

## Usage pattern 3 — auto-discovery (`discover_userlibs`)

`discover_userlibs()` scans known directories and returns a `{name: cls}` dict of all installed extensions. The default search order is:

1. Paths in `$VARTOOLS_USERLIBS` (colon-separated).
2. `$prefix/share/vartools/userlibs/` derived from the binary location.
3. Any paths passed explicitly via `search_paths`.

```python
# Auto-discover extensions installed system-wide (no matches on this host):
cmds = vt.discover_userlibs()
print(cmds)                            # {} — nothing installed globally

# Provide an explicit search path for an uninstalled / development tree:
cmds = vt.discover_userlibs(search_paths=["USERLIBS/src/.libs"])
print(sorted(cmds))                    # ['fastchi2', 'jktebop', ..., 'stitch']

pipe = (vt.Pipeline()
        .expr("mask=0")
        .add(cmds["stitch"]("mag err mask lcnum median")))
result = pipe.run_combinelcs(groups, lcnumvar="lcnum")
```

## Usage pattern 4 — full Python wrapper (subclass)

For a production-quality wrapper with named, typed arguments, subclass `UserCommand` directly:

```python
class Stitch(vt.UserCommand):
    """Fit and remove zero-point offsets between light curve segments."""

    def __init__(
        self,
        variables: str,
        errors: str,
        masks: str,
        lcnum_var: str,
        method: str = "median",
        lib_path: str = "/usr/local/share/vartools/userlibs/stitch.so",
    ):
        super().__init__(
            lib_path, "stitch",
            f"{variables} {errors} {masks} {lcnum_var} {method}",
        )

# User-defined classes aren't attached as Pipeline builder methods, so
# add them with `.add(...)`:
pipe = (vt.Pipeline()
        .add(Stitch("mag", "err", "mask", "lcnum", method="weightedmean")))
```

Alternatively, build the base class from the factory for a one-line definition:

```python
class Stitch(vt.load_userlib("USERLIBS/src/stitch.so", name="stitch")):
    def __init__(self, variables, errors, masks, lcnum, method="median"):
        super().__init__(f"{variables} {errors} {masks} {lcnum} {method}")
```

## Output statistics

Output statistics produced by user commands appear in `result.vars` automatically — vartools writes them to its standard output just like built-in commands, and pyvartools parses them in the same way. No special configuration is needed.

## Pipeline execution mode

Pipelines that contain `UserCommand` instances always run in **subprocess mode**, even when `libvartoolspipeline.so` is available. The in-process library does not support dynamically loaded extension libraries. This is handled transparently; no change to how you call the pipeline is required.

---

