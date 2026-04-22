# Calling Python or R

Wrappers for vartools' embedded `-python` / `-R` interpreters, used to run user code on each light curve from within a pipeline.  Note that pyvartools does not yet ship a typed wrapper for `-python` — use `Raw` (see [Miscellaneous](misc.md)) or write a custom `VartoolsCommand` subclass.

---

## `R` — Run R code

```python
cmd.R(command, fromfile=False, init=None, init_fromfile=False,
      vars=None, invars=None, outvars=None, outputcolumns=None,
      process_all_lcs=False, verbose=False, continueprocess=None)
```

Execute inline R code or an R script on each light curve. `vars` specifies variables to pass both into and out of R; `invars`/`outvars` allow separate control. `init` is R code run once before the batch loop begins.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 4)]

# Compute standard deviation via R for each light curve
batch = vt.Pipeline([
    cmd.R("b <- sd(mag)", invars="mag", outvars="b",
          outputcolumns="b"),
]).run_batch(lcs)
print(batch.vars[["Name", "R_b_0"]])

# `process_all_lcs=True` sends every LC's `mag` array into R as a list
# in a single invocation; R code then loops over the list.  Useful for
# global analyses that need all LCs at once (e.g. ensemble models).
```

---
