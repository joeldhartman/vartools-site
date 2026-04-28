# Miscellaneous

Commands and helpers that don't fit the other categories.

---

### `findblends` — Search for blended transits

**Syntax**

```python
cmd.findblends(matchrad, period="list", radec=False, nharm=1,
               xycol=None, starlist=None, zeromag=None,
               nofluxconvert=False, save_matches=False)
```

**Description**

Determine whether a detected periodic signal in a light curve is likely due to flux contamination (blending) from a nearby variable star. For each light curve, `findblends` looks at all neighbours within `matchrad` (arcseconds when `radec=True`, pixels otherwise), measures their Fourier amplitude at the supplied period, and reports the brightest variable in flux space. A list-mode run with x/y (or RA/Dec) columns is required.

CLI equivalent: [`-findblends`](../../cli/misc.md#-findblends).

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `matchrad` | `float` | Matching radius. Arcseconds when `radec=True`, pixels otherwise. |
| `period` | `float` or `str` | Transit period source. Valid values: `"list"` (read from input list column), `"fix <period>"` (fixed numeric value), `"fixcolumn <col>"` (column name or number). Default `"list"`. The `"fixcolumn NAME"` form is resolved both inside a single `Pipeline` and across chain steps (e.g. `lc.BLS(...).findblends(..., period="fixcolumn BLS_Period_1_0")`); in the chained form the column *name* (not a numeric index) is required. A missing column raises `LookupError`. |
| `radec` | `bool` | Treat the x/y columns as RA and Dec in degrees; `matchrad` is then in arcseconds. |
| `nharm` | `int` | Number of harmonics for the Fourier amplitude measurement. Default `1`; `0` = pure sinusoid. |
| `xycol` | `tuple` or `None` | `(xcol, ycol)` — column names or numbers for the x/y (or RA/Dec) columns in the input list. |
| `starlist` | `str` or `None` | Path to an external star-list file (`lcname x y` per line) used as the catalogue of blending candidates. Default: match against the input light-curve list. |
| `zeromag` | `float` or `None` | Zero-point magnitude for the magnitude-to-flux conversion (vartools default `25.0`). |
| `nofluxconvert` | `bool` | Skip the magnitude-to-flux conversion (input is already in flux units). |
| `save_matches` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures the matched-star list as `result.files["findblends_matches_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |

**Output**

Suffix `N` is the pipeline command index:

| Column | Description |
|--------|-------------|
| `FindBlends_Period_N` | Period used for the Fourier amplitude measurement. |
| `FindBlends_LCname_N` | Name of the brightest blended variable (in flux). |
| `FindBlends_FluxAmp_N` | Flux amplitude of that variable. |

When `save_matches` is enabled:

| File key | Description |
|----------|-------------|
| `result.files["findblends_matches_N"]` | DataFrame with the per-target matched-star list and their flux amplitudes. |

**Examples**

**Example 1.** The list `EXAMPLES/lc_list_testblend` contains two LCs along with x/y coordinates. Searched with `LS` and then check for blends — any stars within 2 pixels are potential blends, and the period from `LS` is used. The result reports `EXAMPLES/2` as the source of the variability for both LCs since it has the higher flux amplitude.

```python
batch = (vt.Pipeline()
         .LS(0.1, 10.0, 0.1, npeaks=1)
         .findblends(matchrad=2.0, period="fixcolumn LS_Period_1_0")
         ).run_filelist("EXAMPLES/lc_list_testblend")
```

---

### `columnsuffix` — Set output column suffix

**Syntax**

```python
cmd.columnsuffix(suffix)
```

**Description**

Replace the default 0-based command-index suffix on subsequent commands' output column names with a user-supplied string. By default vartools appends the command's pipeline position (e.g. `LS_Period_1_0`, `LS_Period_1_1`) to every output column; `columnsuffix` substitutes `suffix` instead, making column names predictable regardless of the command's position in the pipeline. The suffix applies to all commands that follow until another `columnsuffix` is encountered.

This command does not produce any per-light-curve statistics output of its own.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `suffix` | `str` | Suffix string to append to subsequent commands' output column names in place of the numeric command index. |

**Output**

No statistics or auxiliary file output. The command modifies the column-naming convention used by all later commands in the pipeline.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe = vt.Pipeline().columnsuffix("ls").LS(0.5, 10.0, 1e-3)
result = pipe.run(lc)
period = float(result.vars["LS_Period_1_ls"])
```

If your pipeline contains multiple period-search commands with different suffixes, you can read each result unambiguously:

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe = (vt.Pipeline()
        .columnsuffix("ls")
        .LS(0.5, 10.0, 1e-3)
        .columnsuffix("aov")
        .aov(0.5, 10.0, 1e-3, 4.0))
result = pipe.run(lc)
ls_period  = float(result.vars["LS_Period_1_ls"])
aov_period = float(result.vars["Period_1_aov"])
```

---

### `Raw` — Pass arbitrary CLI arguments

**Syntax**

```python
cmd.Raw(args)
```

**Description**

Escape hatch for commands not yet wrapped in the Python API or for experimental options. The supplied tokens are appended verbatim to the vartools command line. `args` may be either a whitespace-delimited string (split on whitespace) or a list of pre-tokenised strings.

Because pyvartools cannot inspect the command, `Raw` does not contribute named outputs to `result.vars`; any data produced by the underlying command must be parsed manually from `result.stdout` or auxiliary files.

**Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `args` | `str` or `list` of `str` | Raw vartools CLI tokens. A string is split on whitespace; a list is used as-is. |

**Output**

No structured output. Whatever the underlying vartools command writes appears in `result.stdout` and any files it produces.

**Examples**

```python
cmd.Raw("-LS 0.1 10.0 0.1 5 1 0")
cmd.Raw(["-LS", "0.1", "10.0", "0.1", "5", "1", "0"])
```

---
