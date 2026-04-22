# Miscellaneous

Commands and helpers that don't fit the other categories.

---

## `findblends` — Search for blended transits

```python
cmd.findblends(matchrad, period="list", radec=False, nharm=1,
               xycol=None, starlist=None, zeromag=None,
               nofluxconvert=False, save_matches=False)
```

Searches for nearby stars that could be the source of a blended transit signal. `matchrad` is the search radius in arcseconds. `save_matches` accepts `bool`, `str`, or `Output` — see [Auxiliary output files](index.md#auxiliary-output-files); the matched-star list is captured as `result.files["findblends_matches_N"]`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | `float` or `str` | Transit period source. Valid values: `"list"` (from input list column), `"fix <period>"` (fixed value), `"fixcolumn <col>"` (column name/number). Default `"list"`. The `"fixcolumn NAME"` form is resolved both inside a single `Pipeline` and across chain steps (e.g. `lc.BLS(...).findblends(..., period="fixcolumn BLS_Period_1_0")`); in the chained form the column *name* (not a numeric index) is required. Missing column → `LookupError`. |
| `radec` | `bool` | Use RA/Dec coordinates instead of pixel coordinates for matching. |
| `xycol` | `tuple` or `None` | `(xcol, ycol)` — column names or numbers for pixel-coordinate columns. |
| `starlist` | `str` or `None` | Path to an additional star list file used for blending candidates. |
| `zeromag` | `float` or `None` | Zero-point magnitude used for flux conversion. |
| `nofluxconvert` | `bool` | Skip the flux-to-magnitude conversion step. |

---

## `columnsuffix` — Set output column suffix

```python
cmd.columnsuffix(suffix)
```

By default, vartools appends a 0-based command-index suffix to output variable names (e.g. `LS_Period_1_0`, `LS_Period_1_1`). `columnsuffix` replaces the numeric suffix with a user-supplied string for all subsequent commands, making column names predictable regardless of pipeline position.

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe = vt.Pipeline([
    cmd.columnsuffix("ls"),
    cmd.LS(0.5, 10.0, 1e-3),
])
result = pipe.run(lc)
period = float(result.vars["LS_Period_1_ls"])
```

If your pipeline contains multiple period-search commands with different suffixes, you can read each result unambiguously:

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe = vt.Pipeline([
    cmd.columnsuffix("ls"),
    cmd.LS(0.5, 10.0, 1e-3),
    cmd.columnsuffix("aov"),
    cmd.aov(0.5, 10.0, 1e-3, 4.0),
])
result = pipe.run(lc)
ls_period  = float(result.vars["LS_Period_1_ls"])
aov_period = float(result.vars["Period_1_aov"])
```

---

## `Raw` — Pass arbitrary CLI arguments

```python
cmd.Raw(args)
```

An escape hatch for commands not yet wrapped in Python, or for experimental options. Pass either a string (split on whitespace) or a list of tokens:

```python
cmd.Raw("-LS 0.1 10.0 0.1 5 1 0")
cmd.Raw(["-LS", "0.1", "10.0", "0.1", "5", "1", "0"])
```

---
