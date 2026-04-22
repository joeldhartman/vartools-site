# Batch variability search

Run a battery of variability-selection algorithms — LS, AoV, multi-harmonic
AoV, BLS, autocorrelation — on a list of light curves using four threads in
parallel. Save and restore LC states let us chain differently-clipped copies
through different algorithms without losing points.

## Command line

```bash
./vartools -l EXAMPLES/lc_list -parallel 4 \
    -savelc \
    -clip 5.0 1 \
    -savelc \
    -LS 0.1 100.0 0.1 3 0 clip 5.0 1 \
    -aov 0.1 100.0 0.1 0.01 1 0 clip 5.0 1 \
    -aov_harm 1 0.1 100.0 0.1 0.01 1 0 clip 5.0 1 \
    -restorelc 1 \
    -clip 10.0 1 \
    -BLS q 0.01 0.1 0.1 20. 10000 200 7 2 0 0 0 \
    -restorelc 2 \
    -changeerror \
    -autocorrelation 0.0 30.0 0.1 EXAMPLES/OUTDIR1/ \
    -header
```

```
#Name Nclip_1 LS_Period_1_3 ... Period_1_4 AOV_1_4 ... \
BLS_Period_1_8 BLS_SignaltoPinknoise_1_8 ... RMS_10
EXAMPLES/2   0  1.23440877 ... 1.23583047  9274.25316 ... \
 4.94437027  8.09875 ... 0.03663
EXAMPLES/4   6  0.99383709 ... 34.70790113   92.61914 ... \
 2.32488927  7.53376 ... 0.00204
EXAMPLES/1   0 77.76775250 ... 34.52470117 46218.43332 ... \
 3.05219780  6.02552 ... 0.15944
...
```

(Full output has 60+ columns per LC and 10 rows — one per input LC. Output
row order depends on which thread finishes first.)

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd

lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

pipeline = vt.Pipeline([
    cmd.savelc(),
    cmd.clip(5.0, iterative=True),
    cmd.savelc(),
    cmd.LS(0.1, 100.0, 0.1, npeaks=3, save_periodogram=False,
           clip=5.0, clipiter=1),
    cmd.aov(minp=0.1, maxp=100.0, subsample=0.1, finetune=0.01,
            npeaks=1, save_periodogram=False, clip=5.0, clipiter=1),
    cmd.aov_harm(nharm=1, minp=0.1, maxp=100.0, subsample=0.1,
                 finetune=0.01, npeaks=1, save_periodogram=False,
                 clip=5.0, clipiter=1),
    cmd.restorelc(1),
    cmd.clip(10.0, iterative=True),
    cmd.BLS(qmin=0.01, qmax=0.1, minper=0.1, maxper=20.0,
            nfreq=10000, nbins=200, timezone=7, npeaks=2,
            save_periodogram=False),
    cmd.restorelc(2),
    cmd.changeerror(),
    cmd.autocorrelation(start=0.0, stop=30.0, step=0.1,
                        save_result="EXAMPLES/OUTDIR1/"),
])

batch = pipeline.run_batch(lcs, nthreads=4)

print(batch.vars[["Name", "LS_Period_1_3", "Period_1_4",
                  "BLS_Period_1_8", "BLS_SignaltoPinknoise_1_8",
                  "RMS_10"]].to_string(index=False))
```

```
Name  LS_Period_1_3  Period_1_4  BLS_Period_1_8  BLS_SignaltoPinknoise_1_8  RMS_10
   1      77.767753   34.524701        3.052198                    6.02552 0.15944
   2       1.234409    1.235830        4.944370                    8.09875 0.03663
   3      18.298295   17.564611       16.407942                    4.03820 0.00486
   4       0.993837   34.707901        2.324889                    7.53376 0.00204
   5       7.069796    8.376121       20.000000                    3.29551 0.00287
   6      22.219358   22.855895        0.372989                    6.03064 0.00208
   7       0.147471    1.806541        3.637786                    7.13566 0.00348
   8       0.936961   12.290390        3.732363                    4.79817 0.00225
   9       7.069796    6.973107        7.485682                    4.85598 0.00187
  10       0.969069   22.249379        0.373128                    5.87482 0.00236
```

## Notes

The pipeline uses two nested `savelc` states. State 1 is the raw LC; state 2
is the 5-sigma clipped version. After running LS/AoV/AoV-harm (each with
its own internal 5-sigma clip), `-restorelc 1` brings back the raw LC,
`-clip 10.0 1` applies a looser clip (aggressive clipping can remove the
very transits BLS is looking for), and BLS runs on that. `-restorelc 2`
then returns to the 5-sigma-clipped LC for the autocorrelation analysis,
which first needs the per-point errors replaced with the light curve RMS
via `-changeerror`.

Parallelism uses vartools' built-in `-parallel N` for the CLI and the
`nthreads=N` argument to `Pipeline.run_batch(...)` in Python. No external
`pexec`, `ProcessPoolExecutor`, or shell wrappers are needed. Output rows
are written in the order threads finish, so the `Name` column identifies
each row — pandas `sort_values` is convenient if you want a deterministic
row order.

`EXAMPLES/2` is a recognisable LS detection (period 1.234 d), `EXAMPLES/4`
yields a strong BLS candidate at 2.32 d (the transit injected in the
transit-injection example has been clipped slightly by the 10-sigma clip
so the period is off by a factor of two from the true 2.12 d — the second
BLS peak would catch it), and `EXAMPLES/1` has its RMS dominated by the
quadratic trend, which shows up as a long LS period near 78 d.
`EXAMPLES/OUTDIR1/2.autocorr` — the autocorrelation function for LC 2 —
shows a clear first peak at 1.23 d.
