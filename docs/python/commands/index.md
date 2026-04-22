# Command Wrappers

pyvartools exposes every vartools command as a typed Python class under
`pyvartools.commands`.  Each command is categorised the same way as in
the [CLI reference](../../cli/index.md), so a command found on one side
is easily found on the other.

Browse the per-category pages in the sidebar, or use the
[alphabetical Command Index](../../commands.md) to jump straight to a
specific command.

Three common import idioms:

```python
import pyvartools as vt

# 1. Top-level one-liner — accepts path / DataFrame / LightCurve / array
result = vt.LS("EXAMPLES/2", 1.0, 2.0, 0.01)

# 2. Chaining API
lc = vt.LightCurve.from_file("EXAMPLES/2")
result = lc.LS(1.0, 2.0, 0.01).rms()

# 3. Pipeline — the canonical form, underlies both above
from pyvartools import commands as cmd
pipe = vt.Pipeline([cmd.clip(5.0), cmd.LS(0.1, 10.0, 0.1)])
result = pipe.run_file("EXAMPLES/2")
```

---

## Auxiliary output files

Many commands can write auxiliary files (periodograms, model curves, coefficient tables, etc.) to disk. Every such parameter is named `save_*` and accepts four modes, controlled by passing a `bool`, a path string, or an `Output` object.

### The four modes

| Value | Mode | Written to disk? | Captured in Python? |
|-------|------|-----------------|---------------------|
| `False` (default) | 4 — suppress | no | no |
| `True` | 1 — temp, capture | temp dir (auto-deleted) | **yes** — `result.files["key"]` |
| `"/path/to/dir"` | 3 — disk only | that directory | no |
| `Output("/path/to/dir", capture=True)` | 2 — disk + capture | that directory | **yes** — `result.files["key"]` |

### `Output` class

```python
from pyvartools import Output

Output(path=None, capture=True)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `path` | `str` or `None` | Directory to write the file to. `None` means use a pipeline-managed temp directory. |
| `capture` | `bool` | Whether to read the file into Python and include it in `result.files`. Default `True`. |

### Examples

```python
import pyvartools as vt
from pyvartools import commands as cmd, Output

lc = vt.LightCurve.from_file("EXAMPLES/2")

# Mode 1 (default True): temp dir, captured into result.files
result = vt.Pipeline([
    cmd.LS(0.1, 10.0, 1e-3, save_periodogram=True),
]).run(lc)
pgram = result.files["LS_periodogram_0"]   # pd.DataFrame

# Mode 3: written to EXAMPLES/OUTDIR1, NOT in result.files
result = vt.Pipeline([
    cmd.LS(0.1, 10.0, 1e-3, save_periodogram="EXAMPLES/OUTDIR1"),
]).run(lc)
# EXAMPLES/OUTDIR1/stdin.ls written; result.files has no "LS_periodogram_0"

# Mode 2: written to EXAMPLES/OUTDIR1 AND captured
result = vt.Pipeline([
    cmd.LS(0.1, 10.0, 1e-3,
           save_periodogram=Output("EXAMPLES/OUTDIR1", capture=True)),
]).run(lc)
pgram = result.files["LS_periodogram_0"]   # captured from EXAMPLES/OUTDIR1/stdin.ls

# Mode 4 (default False): nothing written, nothing captured
result = vt.Pipeline([
    cmd.LS(0.1, 10.0, 1e-3, save_periodogram=False),
]).run(lc)
# result.files has no "LS_periodogram_0"
```

### Output file keys

Captured files appear in `result.files` under a key of the form `"{CommandName}_{logical_name}_{idx}"`, where `idx` is the 0-based index of the command in the pipeline. For example, the first `LS` command's periodogram is `"LS_periodogram_0"`, and the second is `"LS_periodogram_1"`.

In a batch run (`run_batch` / `run_filelist`) each key maps to a list of DataFrames — one per light curve.

### Note on `autocorrelation`

`autocorrelation` is a special case: the vartools CLI always writes the output file regardless of the `save_result` setting. Passing `save_result=False` suppresses Python capture but the file is still written to a temp directory (and discarded after the run).

---


## Base class

All wrappers inherit from `VartoolsCommand`:

```python
from pyvartools._command import VartoolsCommand
```

Custom commands can be written by subclassing `VartoolsCommand` and implementing `_to_cli_args() → list[str]`. Override `_output_file_specs()` to declare output files that should be captured by the Pipeline.

```python
class MyCommand(VartoolsCommand):
    _vt_name = "mycommand"

    def __init__(self, param: float):
        self.param = param

    def _to_cli_args(self):
        return ["-mycommand", str(self.param)]
```
