# Kepler FITS

Read a Kepler FITS long-cadence light curve directly, convert flux to
magnitude, and run a Lomb-Scargle search. Demonstrates `-inputlcformat`
with FITS column selection, `-changevariable` to remap FITS column names
onto the standard `mag`/`err` variables, and `-fluxtomag` for the
flux-to-magnitude conversion.

The file `EXAMPLES/kplr000757076-2009166043257_llc.fits` is a Q1 Kepler
light curve stored as a FITS binary table.

## Command line

```bash
./vartools -i EXAMPLES/kplr000757076-2009166043257_llc.fits \
    -inputlcformat t:1,pdcsap_flux:8,pdcsap_flux_err:9 \
    -changevariable mag pdcsap_flux \
    -changevariable err pdcsap_flux_err \
    -fluxtomag 25.0 0 \
    -rms \
    -LS 0.1 30.0 0.1 4 0 \
    -o /tmp/tmp.lc \
    -oneline
```

```
Name                     = EXAMPLES/kplr000757076-2009166043257_llc.fits
Mean_Mag_3               =   3.26328
RMS_3                    =   0.00168
Expected_RMS_3           =   0.00006
Npoints_3                =  1626
LS_Period_1_4            =    27.89305336
Log10_LS_Prob_1_4        = -865.97910
LS_Periodogram_Value_1_4 =    0.23190
LS_SNR_1_4               = 3365.96782
LS_Period_2_4            =    11.54195311
Log10_LS_Prob_2_4        = -478.58086
LS_SNR_2_4               =  912.19832
LS_Period_3_4            =     8.36791601
Log10_LS_Prob_3_4        = -308.62169
LS_SNR_3_4               =  443.21162
LS_Period_4_4            =     4.78166629
Log10_LS_Prob_4_4        = -171.21465
LS_SNR_4_4               =   94.27330
```

## Python

```python
import pyvartools as vt
from pyvartools import commands as cmd

lc = vt.LightCurve.from_file(
    "EXAMPLES/kplr000757076-2009166043257_llc.fits",
    t_col="barytime", mag_col="ap_raw_flux", err_col="ap_raw_err",
)
result = (vt.Pipeline()
        .fluxtomag(25.0)
        .rms()
        .LS(0.1, 30.0, 0.1, npeaks=4, save_periodogram=False)).run(lc)
print(result.vars)
```

```
Name                        kplr000757076-2009166043257_llc
Mean_Mag_1                                          3.26328
RMS_1                                               0.00168
Expected_RMS_1                                      0.00006
Npoints_1                                              1626
LS_Period_1_2                                     27.893053
Log10_LS_Prob_1_2                                 -865.9791
LS_SNR_1_2                                       3365.96782
LS_Period_2_2                                     11.541953
Log10_LS_Prob_2_2                                -478.58086
LS_SNR_2_2                                        912.19832
LS_Period_3_2                                      8.367916
Log10_LS_Prob_3_2                                -308.62169
LS_SNR_3_2                                        443.21162
LS_Period_4_2                                      4.781666
Log10_LS_Prob_4_2                                -171.21465
LS_SNR_4_2                                        198.87399
```

## Notes

`-inputlcformat t:1,pdcsap_flux:8,pdcsap_flux_err:9` is the CLI form for
FITS column selection by position. The names on the left are arbitrary
labels; on this particular file column 8 is `ap_raw_flux` (the older Q1
SCP-style file contains aperture flux rather than PDCSAP-corrected flux
under its own column names). `-changevariable` then associates the named
labels with the standard `mag` and `err` variables vartools expects in
subsequent commands.

`-fluxtomag 25.0 0` applies `m = 25 - 2.5*log10(flux - 0)`. Zero point 25
is an arbitrary calibration offset; the RMS and periodogram are invariant
under a constant mag shift. `-o /tmp/tmp.lc` writes the processed LC back
out as an ASCII file (time, magnitude, uncertainty).

The Python version uses `LightCurve.from_file(..., t_col=..., mag_col=...,
err_col=...)` with the real FITS column names, which is the natural way to
do it. The flux-to-magnitude conversion and LS search are identical to
the CLI.

The LS search finds a very strong signal near 28 d, which for this Q1 LC
is dominated by long-timescale instrumental systematics (Kepler Q1 was the
first science quarter and has not been corrected for long-term trends in
the raw flux). Real Kepler workflows typically run PDCSAP flux through
additional detrending (TFA or SYSREM) before interpreting the periodogram.

### Variation: shifting Kepler BKJD to full BJD

Kepler's `TIME` column is BKJD = BJD - 2454833. If you need BJD-referenced
output (e.g. for cross-matching with other surveys), add an `-expr` step
before the period search:

```bash
./vartools -i mykepler.fits \
    -inputlcformat fits bjd:TIME mag:PDCSAP_FLUX err:PDCSAP_FLUX_ERR \
    -expr 't=t+2454833.0' \
    -fluxtomag 25.0 0 \
    -LS 0.1 30.0 0.1 1 0 \
    -oneline
```

TESS uses `TIME = BJD - 2457000`; the same pattern applies with the
appropriate offset.
