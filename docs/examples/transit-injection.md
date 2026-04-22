# Transit injection

Generate a Mandel-Agol transit model for a light curve with all parameters
fixed. The model is written to `OUTDIR1/3.mandelagoltransit.model`; adding
that signal to the original LC produces a realistic noisy transit LC suitable
for recovery tests (see the
[transit search & fit](transit-search-and-fit.md) example).

## Command line

```bash
./vartools -i EXAMPLES/3 \
    -MandelAgolTransit 2.12345 53725.174 0.1 10.0 i 90.0 0. 0. 0 \
        quad 0.236 0.391 \
        0 0 0 0 0 0 0 0 0 0 0 1 EXAMPLES/OUTDIR1 \
    -header

gawk '{print $1, $2 + $3, $4}' \
    EXAMPLES/OUTDIR1/3.mandelagoltransit.model > EXAMPLES/3.transit
```

```
#Name MandelAgolTransit_Period_0 MandelAgolTransit_T0_0 MandelAgolTransit_r_0 \
MandelAgolTransit_a_0 MandelAgolTransit_bimpact_0 MandelAgolTransit_inc_0 \
MandelAgolTransit_e_0 MandelAgolTransit_omega_0 MandelAgolTransit_mconst_0 \
MandelAgolTransit_ldcoeff1_0 MandelAgolTransit_ldcoeff2_0 \
MandelAgolTransit_chi2_0
EXAMPLES/3  2.12345000 53725.17400000   0.10000  10.00000   0.00000  90.00000 \
  0.00000   0.00000   0.00000   0.23600   0.39100 129730808.07162
```

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/3")

result = (vt.Pipeline()
        .MandelAgolTransit(
            P0=2.12345, T00=53725.174, r0=0.1, a0=10.0, inclination=90.0,
            e0=0.0, omega0=0.0, mconst0=0.0,
            ld_type="quad", ld_coeffs=[0.236, 0.391],
            fitephem=0, fitr=0, fita=0, fitinclterm=0, fite=0, fitomega=0,
            fitmconst=0, fitldcoeffs=[0, 0],
            correct_lc=False,
            save_model=True,
        )).run(lc)

print(result.vars)
```

```
Name                                          3
MandelAgolTransit_Period_0              2.12345
MandelAgolTransit_T0_0                53725.174
MandelAgolTransit_r_0                       0.1
MandelAgolTransit_a_0                      10.0
MandelAgolTransit_bimpact_0                 0.0
MandelAgolTransit_inc_0                    90.0
MandelAgolTransit_e_0                       0.0
MandelAgolTransit_omega_0                   0.0
MandelAgolTransit_mconst_0                  0.0
MandelAgolTransit_ldcoeff1_0              0.236
MandelAgolTransit_ldcoeff2_0              0.391
MandelAgolTransit_chi2_0        129730808.07162
```

## Notes

Parameters passed to `-MandelAgolTransit`: period 2.12345 d, T0 = 53725.174,
Rp/R* = 0.1, a/R* = 10.0, inclination 90 degrees (transit central), circular
orbit, quadratic limb darkening with coefficients (0.236, 0.391). The long
run of zeros are the `fitephem fitr fita fitinclterm fite fitomega fitmconst
fitldcoeff1 fitldcoeff2 fitRV correctlc` flags; everything is held fixed and
the LC is not corrected. The final `1 EXAMPLES/OUTDIR1` writes the model to
disk.

The CLI pipeline writes only the model, so a second step (`gawk` in the
original example, or `-Injecttransit` if you want a single-call workflow) is
needed to add that model onto the observed LC and save the result to
`EXAMPLES/3.transit`, which the next example uses as its input.

### Variation: one-step injection with `-Injecttransit`

`-Injecttransit` creates a noisy transit LC in a single step without the
external `gawk` call. It takes physical parameters (Rp, Mp, Mstar, Rstar)
rather than a/R*, and it adds the model to the LC in-place:

```bash
./vartools -i EXAMPLES/3 \
    -Injecttransit fix 2.12345 Rpfix 0.1 Mpfix 0.001 phasefix 0.0 \
        sinifix 1.0 eomega efix 0 ofix 0 Mstarfix 1.0 Rstarfix 1.0 \
        quad 0.236 0.391 0 \
    -o EXAMPLES/3.transit \
    -header
```

The Python equivalent uses `cmd.Injecttransit(...)` followed by `cmd.o(...)`.
