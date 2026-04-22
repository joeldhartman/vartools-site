# Polynomial detrending

Fit a quadratic polynomial in time to each light curve in a list and subtract
it, comparing the RMS before and after. A quadratic trend was injected into
`EXAMPLES/1`, so that LC shows the strongest improvement.

## Command line

```bash
./vartools -l EXAMPLES/lc_list \
    -rms \
    -expr listvar 'tzero=median(t)' \
    -linfit 'a*(t-tzero)*(t-tzero)+b*(t-tzero)+c' 'a,b,c' correctlc \
    -rms \
    -header
```

```
#Name Mean_Mag_0 RMS_0 Expected_RMS_0 Npoints_0 Linfit_a_2 Linfit_erra_2 \
Linfit_b_2 Linfit_errb_2 Linfit_c_2 Linfit_errc_2 Mean_Mag_3 RMS_3 \
Expected_RMS_3 Npoints_3
EXAMPLES/1  10.24745   0.15944   0.00101  3122 0.00025540627746 1.956e-07 \
0.01438325055783 2.7252e-06 10.19165753386 2.0551e-05  -0.00017   0.00211 \
0.00101  3122
EXAMPLES/2  10.11802   0.03663   0.00102  3313 -5.0541833e-06 1.932e-07 \
0.000265335127 2.9164e-06 10.11151684161 1.9443e-05   0.00616   0.03657 \
0.00102  3313
...
```

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]
batch = vt.Pipeline([
    cmd.rms(),
    cmd.expr("tzero=median(t)", vartype="listvar"),
    cmd.linfit(
        function="a*(t-tzero)*(t-tzero)+b*(t-tzero)+c",
        paramlist="a,b,c",
        correct_lc=True,
    ),
    cmd.rms(),
]).run_batch(lcs)
print(batch.vars[["Name", "RMS_0", "Linfit_a_2", "Linfit_b_2",
                  "Linfit_c_2", "RMS_3"]])
```

```
  Name    RMS_0    Linfit_a_2  Linfit_b_2  Linfit_c_2    RMS_3
0    1  0.15944  2.554063e-04    0.014383   10.191658  0.00211
1    2  0.03663 -5.054183e-06    0.000265   10.111517  0.03657
2    3  0.00490 -1.270601e-07    0.000082   10.166625  0.00485
3    4  0.00209 -5.885294e-06    0.000087   10.351700  0.00205
4    5  0.00288 -3.693628e-06    0.000114   10.439339  0.00285
...
```

## Notes

The polynomial is written as a function of `(t - tzero)` rather than `t`
directly. For typical JDs near 2 453 000, evaluating `t*t` floats around
6e12 and differencing such values against each other loses precision;
`(t - tzero)*(t - tzero)` stays in a numerically well-behaved range. The
`listvar` form of `-expr` computes one `tzero` per light curve, used in the
subsequent `-linfit` on that LC.

`-linfit` is used here instead of the older `-decorr`, which accomplished the
same quadratic fit but with a rigid CLI syntax. `-linfit` accepts an arbitrary
analytic expression plus a comma-separated parameter list, and emits cleanly
named output columns (`Linfit_a_2`, `Linfit_b_2`, `Linfit_c_2`).

For `EXAMPLES/1` the RMS drops from 0.15944 mag to 0.00211 mag (a factor of
~75) — that LC had a quadratic injected into it. The other LCs in the list
were not modified, so their RMS barely changes.
