# Light Curve Simulation

Inject signals or synthetic noise into a light curve, or duplicate the light curve for Monte-Carlo studies.

---

## `addnoise` — Add synthetic noise

```python
cmd.addnoise(noise_type="white", sig_white=0.001, rho=None,
             sig_red=None, nu=None, gamma=None, bintime=None)
```

Adds synthetic noise drawn from a specified covariance model. `noise_type` controls the model; all amplitude/timescale parameters accept either a float or a vartools variable-name string.

| `noise_type` | Parameters | Description |
|---|---|---|
| `"white"` | `sig_white` | Independent Gaussian noise. |
| `"squareexp"` | `rho`, `sig_red`, `sig_white`, `bintime` | Squared-exponential (Gaussian) covariance. `bintime` enables integrated covariance. |
| `"exp"` | `rho`, `sig_red`, `sig_white`, `bintime` | Exponential covariance. |
| `"matern"` | `nu`, `rho`, `sig_red`, `sig_white` | Matérn covariance with smoothness `nu`. |
| `"wavelet"` | `gamma`, `sig_red`, `sig_white` | Wavelet (1/f-like) noise. |

| Parameter | Type | Description |
|-----------|------|-------------|
| `sig_white` | `float` or `str` | White noise amplitude (all models). |
| `rho` | `float` or `str` or `None` | Correlation timescale (`"squareexp"`, `"exp"`, `"matern"`). |
| `sig_red` | `float` or `str` or `None` | Red noise amplitude (all correlated models). |
| `nu` | `float` or `str` or `None` | Matérn smoothness parameter (`"matern"` only). |
| `gamma` | `float` or `str` or `None` | Wavelet decay exponent (`"wavelet"` only). |
| `bintime` | `float` or `str` or `None` | Bin integration time (`"squareexp"`, `"exp"`). |

**Examples**

```python
import numpy as np
import pyvartools as vt
from pyvartools import commands as cmd

# Build a zero-magnitude light curve with EXAMPLES/1 time sampling
lc_ref = vt.LightCurve.from_file("EXAMPLES/1")
t = lc_ref.t
lc_blank = vt.LightCurve.from_arrays(t, np.zeros_like(t), np.full_like(t, 0.005))

# Simulate wavelet (1/f-like) red noise + white noise
# (`gamma` sets the spectral-slope exponent; 2 ≈ 1/f^2 random walk)
result = lc_blank.addnoise(noise_type="wavelet", gamma=2.0,
                           sig_red=0.005, sig_white=0.005)
noisy_lc = result.lc

# Squared-exponential red noise with 0.01-day correlation timescale
result2 = lc_blank.addnoise(noise_type="squareexp", rho=0.01,
                            sig_red=0.005, sig_white=0.001)
```

---

## `Injectharm` — Inject a harmonic signal

```python
cmd.Injectharm(period, amplitude, nharm=1, phase=0.0,
               nsubharm=0, save_model=False)
```

Injects a sinusoidal (or multi-harmonic) signal with the specified period and amplitude. Used for injection-recovery tests.

> **Design note**: This class exposes only the most common injection modes.
> *Amplitude*: `"ampfix"` and `"amplogrand"` only. For `"amprand"` or `"amplist"` use `cmd.Raw()`.
> *Period*: `"fix"` and `"logrand"` (via the `period` parameter). For `"list"` or `"rand"` period modes use `cmd.Raw()`.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3")

# Inject a sine wave at a random log-uniform period, then try to recover it.
# `logrand`, `amplogrand`, and `phaserand` are vartools-side random draws that
# create scalar variables on the LC — we use a single Pipeline so those
# variables stay in the same invocation as the recovery step.
result = vt.Pipeline([
    cmd.Injectharm(period="logrand 1.0 5.0",
                   amplitude="amplogrand 0.001 0.1",
                   nharm=0, phase="phaserand",
                   save_model=True),
    cmd.LS(0.5, 10.0, 0.1, npeaks=1),
]).run(lc)
print(result.vars["Injectharm_Period_0"])   # injected period
print(result.vars["LS_Period_1_1"])         # recovered period
```

---

## `Injecttransit` — Inject a transit signal

```python
cmd.Injecttransit(period, Rp, Mp, phase, sini, Mstar, Rstar,
                  e=0.0, omega=0.0,
                  hk=False, h=0.0, k=0.0,
                  dilute=None,
                  ld_type="quad", ld_coeffs=None, save_model=False)
```

All positional parameters accept floats (emits `{prefix}fix val`) or strings (passed through verbatim, e.g. `"Plogrand 0.2 2.0"`, `"phaserand"`, `"sinirand"`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | `float` or `str` | Orbital period. Float → `"Pfix val"`. String passthrough (e.g. `"Plogrand 0.2 2.0"`). |
| `Rp` | `float` or `str` | Planet-to-star radius ratio. Float → `"Rpfix val"`. String passthrough (e.g. `"Rplogrand 0.05 0.15"`). |
| `Mp` | `float` or `str` | Planet mass in solar masses. |
| `phase` | `float` or `str` | Orbital phase of transit centre (0–1). String e.g. `"phaserand"`. |
| `sini` | `float` or `str` | Sine of the orbital inclination. String e.g. `"sinirand"`. |
| `Mstar`, `Rstar` | `float` or `str` | Stellar mass (M☉) and radius (R☉). |
| `e` | `float` or `str` | Eccentricity (used in `eomega` mode, the default). |
| `omega` | `float` or `str` | Argument of periastron (used in `eomega` mode). |
| `hk` | `bool` | When `True`, use the `hk` eccentricity parameterisation (`h = e sin ω`, `k = e cos ω`) instead of `eomega`. |
| `h`, `k` | `float` or `str` | `h` and `k` eccentricity components. Used when `hk=True`. |
| `dilute` | `float`, `str`, or `None` | Dilution factor. Float → `["dilute", "fix", val]`. String passthrough (e.g. `"list"` or `"fix 0.5"`). |
| `ld_coeffs` | list | Limb-darkening coefficients. Default `[0.3, 0.3]`. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/4")

# Inject a Jupiter-sized transit at a random period, then search with BLS.
# As with Injectharm, the per-LC random draws (`Plogrand`, `phaserand`, …) are
# scalar-variables produced inside vartools, so we run inject + recover in a
# single Pipeline invocation.
result = vt.Pipeline([
    cmd.Injecttransit(
        period="Plogrand 0.2 2.0",
        Rp="Rpfix 0.1",     # Rp/R*
        Mp="Mpfix 0.001",   # M_sun
        phase="phaserand",
        sini="sinirand",
        Mstar="Mstarfix 1.0",
        Rstar="Rstarfix 1.0",
        ld_type="quad",
        ld_coeffs=[0.3471, 0.3180],
        save_model=True,
    ),
    cmd.BLS(0.1, 5.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=20000, npeaks=1),
]).run(lc)
print(result.vars["Injecttransit_Period_0"])   # injected period
print(result.vars["BLS_Period_1_1"])           # recovered period
```

---

## `copylc` — Duplicate the light curve in-memory

```python
cmd.copylc(ncopies)
```

`copylc` duplicates the current light curve `ncopies` times in the output
stream.  A common use is bootstrap / noise-replica Monte Carlo, where the same
input is shifted into many parallel replicas that can be analysed by the
downstream pipeline.

**Example**

```python
lc = vt.LightCurve.from_file("EXAMPLES/2")
pipe_bs = vt.Pipeline([
    cmd.LS(0.1, 10.0, 0.1, npeaks=1),
    cmd.copylc(100),
    cmd.expr("mag=err*gauss()"),
    cmd.LS(0.1, 10.0, 0.1, npeaks=1),
])
batch_bs = pipe_bs.run_batch([lc])
```

---
