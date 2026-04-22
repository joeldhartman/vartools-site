# Transit search and fit

Detrend with TFA and then search for transits with BLS using a trapezoidal
in-transit fit. The input is `EXAMPLES/3.transit`, the LC created by the
[transit injection](transit-injection.md) example.

## Command line

```bash
./vartools -l EXAMPLES/lc_list_tfa \
    -rms \
    -TFA EXAMPLES/trendlist_tfa EXAMPLES/dates_tfa 25.0 1 0 0 \
    -BLS density 1.41 0.5 2.0 0.5 5.0 optimal 0.1 200 7 2 0 1 EXAMPLES/OUTDIR1 1 fittrap \
    -rms \
    -oneline
```

```
Name                         = EXAMPLES/3.transit
Mean_Mag_0                   =  10.16727
RMS_0                        =   0.00542
Expected_RMS_0               =   0.00104
Npoints_0                    =  3417
TFA_MeanMag_1                =  10.16714
TFA_RMS_1                    =   0.00471
BLS_Period_1_2               =     2.12402761
BLS_Tc_1_2                   = 53727.294878968052
BLS_SN_1_2                   =  69.00454
BLS_SDE_1_2                  =   4.41122
BLS_Depth_1_2                =   0.01186
BLS_Qtran_1_2                =   0.03586
BLS_Qingress_1_2             =   0.16670
BLS_Npointsintransit_1_2     =   161
BLS_Ntransits_1_2            =     4
BLS_SignaltoPinknoise_1_2    =  15.93733
BLS_Period_2_2               =     1.35229047
...
RMS_3                        =   0.00405
```

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd

pipe = (vt.Pipeline()
        .rms()
        .TFA(
            trendlist="EXAMPLES/trendlist_tfa",
            dates_file="EXAMPLES/dates_tfa",
            pixelsep=25.0,
            correct_lc=True,
            save_coeffs=False,
            save_model=False,
        )
        .BLS(
            density_mode=True,
            stellar_density=1.41,        # solar density, g/cm³
            min_exp_dur_frac=0.5,
            max_exp_dur_frac=2.0,
            minper=0.5, maxper=5.0,
            subsample=0.1,               # oversampling for "optimal" grid
            nbins=200,
            timezone=7, npeaks=2,
            save_periodogram=False,
            correct_lc=True,
            fittrap=True,
        )
        .rms())

result = pipe.run_filelist("EXAMPLES/lc_list_tfa")

row = result.vars.iloc[0]
for col in ["RMS_0", "TFA_RMS_1", "BLS_Period_1_2", "BLS_Tc_1_2",
            "BLS_SN_1_2", "BLS_SDE_1_2", "BLS_Depth_1_2",
            "BLS_Qtran_1_2", "BLS_SignaltoPinknoise_1_2",
            "BLS_Period_2_2", "RMS_3"]:
    print(f"{col:<30} = {row[col]}")
```

```
RMS_0                          = 0.00542
TFA_RMS_1                      = 0.00471
BLS_Period_1_2                 = 2.12402761
BLS_Tc_1_2                     = 53727.29487896805
BLS_SN_1_2                     = 69.00454
BLS_SDE_1_2                    = 4.41122
BLS_Depth_1_2                  = 0.01186
BLS_Qtran_1_2                  = 0.03586
BLS_SignaltoPinknoise_1_2      = 15.93733
BLS_Period_2_2                 = 1.35229047
RMS_3                          = 0.00405
```

## Notes

`-TFA` fits a linear combination of template trend light curves to remove
shared systematics. The template list is `EXAMPLES/trendlist_tfa` (paths +
pixel coordinates for each star); `EXAMPLES/dates_tfa` is the global cadence
file. The `25.0` is the minimum pixel separation between target and template
— templates within 25 pixels of `EXAMPLES/3.transit` are excluded, so the
target's own signal can't leak back into the detrending model. The three
final flags are `correctlc=1 save_coeffs=0 save_model=0`.

`-BLS` then searches for transits on the detrended LC:

- `density 1.41 0.5 2.0` — stellar density (g/cm³) plus min/max fractional
  scaling of the expected transit duration; BLS computes the per-trial-period
  duration bounds from the density assuming a circular orbit.
- `0.5 5.0` — period range in days.
- `optimal 0.1` — optimal frequency grid with a subsampling factor of 0.1
  (finer than the native optimal spacing by 10×).
- `200` — phase bins.
- `7` — local timezone offset in hours (used for the one-night-fraction
  statistic).
- `2` — number of peaks to report.
- `0 1 EXAMPLES/OUTDIR1` — skip periodogram output, write the BLS model LC
  to the output dir.
- `1 fittrap` — subtract the best-fit box before passing to the next
  command, and fit a trapezoidal transit at each peak (which adds the
  `Qingress` and `OOTmag` columns).

The final `-rms` captures the residual scatter after the transit model is
subtracted. For this LC the RMS drops from 0.00542 mag (raw) to 0.00471 mag
(post-TFA) to 0.00405 mag (post-TFA + transit removal). The best BLS period,
2.12403 d, matches the injected 2.12345 d; the 1.352 d secondary peak is a
harmonic alias.

`BLS_SignaltoPinknoise` is the most useful single-statistic indicator for
transit candidates; values above ~10 are strong candidates once the LC has
been properly detrended.

### Variation: Mandel-Agol fit at the BLS period

After BLS finds a candidate, we seed a Mandel-Agol physical transit fit
with the BLS period, transit center, depth, and fractional duration; the
initial impact parameter is 0.1. `ophcurve` writes the fitted model as a
phase curve from −0.5 to 0.5 so it can be overplotted directly on the
folded observations.

```bash
./vartools -i EXAMPLES/3.transit \
    -BLS density 1.41 0.5 2.0 0.5 5.0 optimal 0.1 200 7 1 0 0 0 fittrap \
    -MandelAgolTransit \
        expr BLS_Period_1_0 expr BLS_Tc_1_0 \
        expr 'sqrt(BLS_Depth_1_0)' expr '1.0/(BLS_Qtran_1_0*pi)' \
        b 0.1 0.0 0.0 -1 quad 0.3 0.3 \
        1 1 1 1 0 0 1 0 0 0 0 0 \
        ophcurve EXAMPLES/OUTDIR1 -0.5 0.5 0.001 \
    -oneline
```

`expr BLS_Period_1_0` etc. pull the BLS outputs from the prior command
into the MA init values; `b 0.1` initializes the impact parameter (which
is what the fit varies, via `fitinclterm=1`). `mconst0 = -1` tells
vartools to estimate the out-of-transit magnitude from the light curve.

```
Name                         = EXAMPLES/3.transit
BLS_Period_1_0               =     2.12402761
BLS_Tc_1_0                   = 53727.294970417119
BLS_SN_1_0                   =  66.76648
BLS_SDE_1_0                  =   4.34232
BLS_Depth_1_0                =   0.01139
BLS_Qtran_1_0                =   0.03603
BLS_SignaltoPinknoise_1_0    =  13.48275
...
MandelAgolTransit_Period_1   =     2.12339179
MandelAgolTransit_T0_1       = 53727.29676768
MandelAgolTransit_r_1        =   0.09810
MandelAgolTransit_a_1        =   9.66412
MandelAgolTransit_bimpact_1  =   0.27251
MandelAgolTransit_inc_1      =  88.38413
MandelAgolTransit_mconst_1   =  10.16686
MandelAgolTransit_chi2_1     =  27.06389
```

The Python equivalent mirrors the CLI: expressions reference the BLS
output columns, `bimpact=0.1` is the initial impact parameter, and
`save_phcurve=True` with `ophcurve_phmin/phmax/phstep` captures the
fitted model as a DataFrame. A `cmd.Phase(...)` step after the fit
folds the observations on the MA-optimized ephemeris and stores the
per-point phase in a new LC vector `ph_obs`, which is picked up directly
by `cmd.o(capture=True)`.

```python
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file("EXAMPLES/3.transit")

result = (vt.Pipeline()
        .BLS(
            density_mode=True, stellar_density=1.41,
            min_exp_dur_frac=0.5, max_exp_dur_frac=2.0,
            minper=0.5, maxper=5.0,
            subsample=0.1, nbins=200,
            timezone=7, npeaks=1,
            save_periodogram=False, correct_lc=False, fittrap=True,
        )
        .MandelAgolTransit(
            P0="expr BLS_Period_1_0",
            T00="expr BLS_Tc_1_0",
            r0="expr sqrt(BLS_Depth_1_0)",
            a0="expr 1.0/(BLS_Qtran_1_0*pi)",
            bimpact=0.1,
            mconst0=-1,                  # let vartools estimate the baseline
            ld_coeffs=[0.3, 0.3],
            fitephem=1, fitr=1, fita=1, fitinclterm=1,
            fite=0, fitomega=0, fitmconst=1, fitldcoeffs=[0, 0],
            save_phcurve=True,
            ophcurve_phmin=-0.5, ophcurve_phmax=0.5, ophcurve_phstep=0.001,
        )
        .Phase(
            period="fixcolumn MandelAgolTransit_Period_1",
            T0="fixcolumn MandelAgolTransit_T0_1",
            phasevar="ph_obs",
            startphase=-0.5,
        )
        .o(capture=True, key="folded")).run(lc)

fit    = result.varobjs.MandelAgolTransit
folded = result.files["folded"].to_dataframe()
model  = result.files["MandelAgolTransit_phcurve_1"]

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.plot(folded["ph_obs"], folded["mag"], ".", ms=1.5,
        color="0.6", label="observed")
ax.plot(model[0], model[1], "-", lw=1.3,
        color="C3", label="Mandel-Agol fit")
ax.set_xlim(-0.15, 0.15)
ax.invert_yaxis()
P, T0 = float(fit.Period), float(fit.T0)
ax.set_xlabel(f"Phase  (P = {P:.6f} d, T0 = {T0:.5f})")
ax.set_ylabel("mag")
ax.legend(loc="lower right")
fig.tight_layout()
fig.savefig("/tmp/mandel_agol_fit.png", dpi=120)

for name, val in [("P", float(fit.Period)),
                  ("T0", float(fit.T0)),
                  ("r", float(fit.r)),
                  ("a/R*", float(fit.a)),
                  ("bimpact", float(fit.bimpact)),
                  ("inc", float(fit.inc)),
                  ("mconst", float(fit.mconst)),
                  ("chi2", float(fit.chi2))]:
    print(f"{name:<8} = {val}")
```

```
P        = 2.12339179
T0       = 53727.29676768
r        = 0.0981
a/R*     = 9.66412
bimpact  = 0.27251
inc      = 88.38413
mconst   = 10.16686
chi2     = 27.06389
```

![Mandel-Agol transit fit on EXAMPLES/3.transit](../assets/examples/mandel_agol_fit.png)

The fitted period (2.12339 d) shifts by ~0.9 minutes from the BLS grid
value (2.12403 d) and the fitted T0 (BJD 53727.29677) by ~2.6 minutes
from the BLS transit centre. The red curve is the Mandel-Agol model
written by `ophcurve` (directly on a [−0.5, 0.5] phase grid); the gray
points are the observations folded on the fitted ephemeris via
`cmd.Phase(..., phasevar="ph_obs", startphase=-0.5)`.
