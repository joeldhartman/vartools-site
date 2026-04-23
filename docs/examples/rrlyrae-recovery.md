# RR Lyrae recovery

Inject a realistic RR Lyrae signal — a Fourier series fit to the M3 V006
light curve — at a grid of amplitudes into a clean LC and see how low the
amplitude can go before Lomb-Scargle and multi-harmonic AoV fail to recover
the period.

## Command line

### Step 1: fit a Fourier series to the template RR Lyrae

```bash
./vartools -i EXAMPLES/M3.V006.lc \
    -harmonicfilter fix 1 0.514333 10 0 1 EXAMPLES/OUTDIR1/ fitonly outRphi \
    -header
```

```
#Name HarmonicFilter_Mean_Mag_0 HarmonicFilter_Period_1_0 \
HarmonicFilter_Per1_Fundamental_Amp_0 HarmonicFilter_Per1_Fundamental_Phi_0 \
HarmonicFilter_Per1_Harm_R_2_1_0 HarmonicFilter_Per1_Harm_Phi_2_1_0 ... \
HarmonicFilter_Per1_Amplitude_0
EXAMPLES/M3.V006.lc  15.77123 0.51433300 0.38041 -0.07662 \
0.47077 0.60826 0.35917 0.26249 0.23631 -0.06843 0.16353 0.60682 \
0.10621 0.28738 0.06203 0.95751 0.03602 0.58867 0.02900 0.22322 \
0.01750 0.94258 0.00768 0.66560 1.11128
```

### Step 2: inject at 10 halving amplitudes and try to recover

```bash
echo EXAMPLES/4 \
  | gawk '{amp=0.25; for(i=1;i<=10;i++){print $1,amp; amp=amp*0.5;}}' \
  | ./vartools -l - \
      -Injectharm fix 0.514333 10 \
         amplist phaserand \
         ampfix 0.47077 amprel phasefix 0.60826 phaserel \
         ampfix 0.35916 amprel phasefix 0.26249 phaserel \
         ampfix 0.23631 amprel phasefix -0.06843 phaserel \
         ampfix 0.16353 amprel phasefix 0.60682 phaserel \
         ampfix 0.10621 amprel phasefix 0.28738 phaserel \
         ampfix 0.06203 amprel phasefix 0.95751 phaserel \
         ampfix 0.03602 amprel phasefix 0.58867 phaserel \
         ampfix 0.02900 amprel phasefix 0.22322 phaserel \
         ampfix 0.01750 amprel phasefix 0.94258 phaserel \
         ampfix 0.00768 amprel phasefix 0.66560 phaserel \
         0 0 \
      -LS 0.1 10.0 0.01 2 0 \
      -aov_harm 2 0.1 10.0 0.1 0.01 2 0 \
      -header -numbercolumns
```

```
#1_Name 2_Injectharm_Period_0 3_Injectharm_Fundamental_Amp_0 ... \
25_LS_Period_1_1 26_Log10_LS_Prob_1_1 27_LS_Periodogram_Value_1_1 ... \
33_Period_1_2 34_AOV_HARM_1_2 ...
EXAMPLES/4 0.51433300 0.25000 ... 0.51501823 -862.16710 0.70931 ... \
  0.51432840 4322.49 149.531 2969.03 ...
EXAMPLES/4 0.51433300 0.12500 ... 0.51408199 -846.91348 0.70291 ... \
  0.51432840 4609.61 137.471 3056.79 ...
...
EXAMPLES/4 0.51433300 0.00098 ... 0.99479057 -101.16218 0.13799 ... \
  1.99136298 166.558 9.40744 291.44 ...
EXAMPLES/4 0.51433300 0.00049 ... 0.99415471 -118.90869 0.15957 ... \
  0.99348763 199.742 13.8977 345.37 ...
```

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd
import pandas as pd

# Step 1: fit a Fourier series to the template RR Lyrae light curve
tmpl = vt.LightCurve.from_file("EXAMPLES/M3.V006.lc")
fit = (vt.Pipeline()
        .harmonicfilter(
            period=0.514333,
            nharm=10,
            nsubharm=0,
            save_model=True,
            fitonly=True,
            output_format="outRphi",
        )).run(tmpl)

# Pull the R_k1 and phi_k1 coefficients from the fit
row = fit.vars
Rphi = []
for k in range(2, 12):  # harmonic indices 2..11
    R = float(row[f"HarmonicFilter_Per1_Harm_R_{k}_1_0"])
    phi = float(row[f"HarmonicFilter_Per1_Harm_Phi_{k}_1_0"])
    Rphi.append((R, phi))

# Step 2: inject at 10 halving amplitudes and try to recover
rows = []
for i in range(10):
    amp = 0.25 * (0.5 ** i)

    # Use Raw to emit the amprel/phaserel harmonic block Injectharm's
    # typed wrapper does not cover.
    inject_args = ["-Injectharm", "fix", "0.514333", "10",
                   "ampfix", str(amp), "phaserand"]
    for R, phi in Rphi:
        inject_args += ["ampfix", str(R), "amprel",
                        "phasefix", str(phi), "phaserel"]
    inject_args += ["0", "0"]  # no sub-harmonics, no model output

    lc = vt.LightCurve.from_file("EXAMPLES/4")
    result = (vt.Pipeline()
            .Raw(inject_args)
            .LS(0.1, 10.0, 0.01, npeaks=2, save_periodogram=False)
            .aov_harm(nharm=2, minp=0.1, maxp=10.0, subsample=0.1,
                     finetune=0.01, npeaks=2, save_periodogram=False)).run(lc)

    rows.append({
        "inj_amp": amp,
        "LS_P1": float(result.vars["LS_Period_1_1"]),
        "LS_logFAP_1": float(result.vars["Log10_LS_Prob_1_1"]),
        "AOVh_P1": float(result.vars["Period_1_2"]),
        "AOVh_SNR_1": float(result.vars["AOV_HARM_SNR_1_2"]),
    })

print(pd.DataFrame(rows).to_string(index=False))
```

```
 inj_amp    LS_P1  LS_logFAP_1  AOVh_P1  AOVh_SNR_1
0.250000 0.515018   -862.16080 0.514328    149.5270
0.125000 0.515018   -858.95995 0.514328    149.0430
0.062500 0.515018   -851.68826 0.514328    147.6330
0.031250 0.515018   -833.92591 0.514328    143.2020
0.015625 0.514933   -788.14344 0.514328    128.0760
0.007812 0.514933   -673.82770 0.514328     96.0964
0.003906 1.067872   -463.55764 0.514328     51.9892
0.001953 1.067872   -260.69320 0.514243     23.2312
0.000977 1.069340   -118.56042 0.513988     11.2327
0.000488 1.169000    -88.47821 2.326459     10.9564
```

## Notes

Step 1 freezes the period at the known value (0.514333 d) and fits 10
harmonics. The `outRphi` keyword returns the Fourier coefficients as
`R_k1 = A_k / A_1` and `phi_k1 = phi_k - k*phi_1`, which is the natural
representation for reinjecting the same shape at a different amplitude.

Step 2 pipes a two-column stream (`name amp`) into vartools via `-l -`.
`-Injectharm` consumes the amplitude via `amplist` (second column of the
input list) for the fundamental, and reinjects the 10 harmonics with their
`R_k1` and `phi_k1` coefficients fixed and flagged `amprel` / `phaserel`
(so harmonic amplitude = R_k1 * amp_fundamental, and harmonic phase =
k*phi_fundamental + phi_k1). The fundamental phase is randomised by
`phaserand`.

Both LS and multi-harmonic AoV are run on each injected LC. AoV is better
suited to non-sinusoidal signals: it recovers the correct period down to
about 2 mmag fundamental amplitude (~5.7 mmag peak-to-peak), while LS starts
to fail around 4 mmag fundamental. The exact amplitude threshold where
recovery fails will vary run-to-run because the injection phase is random;
add `-randseed time` to the CLI (or use a fixed seed) if you want
reproducible runs.

The Python version uses `cmd.Raw(...)` for the injection because the
typed `cmd.Injectharm` wrapper doesn't expose the `amprel` / `phaserel`
multi-harmonic syntax — the gap is called out in `Injectharm`'s docstring.
