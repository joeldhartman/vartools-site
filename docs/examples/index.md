# Examples

Worked end-to-end examples of common VARTOOLS workflows. Each page shows a
command-line invocation, the real output it produces, the equivalent
pyvartools script, and short notes on what's going on.

All examples use data files shipped with VARTOOLS in the `EXAMPLES/`
subdirectory of the source tree. Commands assume that directory is your
current working directory.

## Overview

| Topic | Page | What it covers |
|-------|------|----------------|
| Polynomial detrending | [polynomial-detrending.md](polynomial-detrending.md) | Fit a quadratic in `(t - tzero)` and subtract it; RMS before vs. after. |
| Period finding | [period-finding.md](period-finding.md) | Lomb-Scargle period search chained into a harmonic fit at the recovered period. |
| Transit injection | [transit-injection.md](transit-injection.md) | Generate a Mandel-Agol transit model and add it onto a clean LC. |
| Transit search and fit | [transit-search-and-fit.md](transit-search-and-fit.md) | TFA detrending followed by BLS with a trapezoidal transit fit. |
| RR Lyrae recovery | [rrlyrae-recovery.md](rrlyrae-recovery.md) | Fit a real RR Lyrae template and inject it at halving amplitudes to test LS vs. multi-harmonic AoV recovery. |
| Batch variability | [batch-variability.md](batch-variability.md) | Parallel run of LS / AoV / AoV-harm / BLS / autocorrelation on a list of LCs. |
| Kepler FITS | [kepler-fits.md](kepler-fits.md) | Read a Kepler long-cadence FITS file, convert flux to magnitude, and run LS. |
