# Model Fitting

Parametric models fit to a light curve: transits, starspots, microlensing, generic linear / non-linear fits.

---

## `linfit` — Linear combination fitting

```python
cmd.linfit(function, paramlist,
           modelvar=None,
           reject=None, reject_usemad=False, reject_iter=False,
           reject_fixednum=None,
           correct_lc=False, save_model=False,
           model_nameformat=None, fitmask=None)
```

Fit a linear combination of analytic basis functions. `function` is a vartools expression string; `paramlist` is a comma-separated list of free parameter names and initial values.  `fitmask` is the name of a mask variable; observations where the variable is non-zero are excluded from the fit (CLI token: `fitmask`). `save_model` accepts `bool`, `str`, or `Output` — see [Auxiliary output files](index.md#auxiliary-output-files); the model file is captured as `result.files["linfit_model_N"]`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `modelvar` | `str` or `None` | Variable name used to store the best-fit model values on the light curve. |
| `reject` | `float` or `None` | Sigma-clipping threshold: fit, clip outliers beyond this threshold (in σ), then refit. |
| `reject_usemad` | `bool` | Use MAD instead of standard deviation for the scatter estimate during rejection. |
| `reject_iter` | `bool` | Iteratively reject and refit until no more points are clipped. |
| `reject_fixednum` | `int` or `None` | Maximum number of rejection/refit iterations (requires `reject_iter=True`). |
| `model_nameformat` | `str` or `None` | Format string for the model output filename (e.g. `"%s.linfit.model"`). |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/1")

# Fit a quadratic polynomial, using minimum time as reference epoch
pipe = (vt.Pipeline()
        .stats("t", ["min"])
        .expr("t0=STATS_t_MIN_0")
        .linfit("a*(t-t0)^2+b*(t-t0)+c", "a,b,c"))
result = pipe.run(lc)
print(result.vars["Linfit_a_2"])   # quadratic coefficient
print(result.vars["Linfit_b_2"])   # linear coefficient
print(result.vars["Linfit_c_2"])   # constant offset
```

---

## `nonlinfit` — Non-linear least-squares fitting

```python
cmd.nonlinfit(function, paramlist,
              optimizer="amoeba",
              linfit_params=None, errors=None,
              covariance=None, priors=None, constraints=None,
              amoeba_tolerance=None, amoeba_maxsteps=None,
              mcmc_naccept=None, mcmc_nlinkstotal=None,
              mcmc_fracburnin=None, mcmc_eps=None,
              mcmc_skipamoeba=False, mcmc_maxmemstore=None,
              mcmc_outchains=False, mcmc_chains_format=None,
              mcmc_chains_printevery=None,
              correct_lc=False, save_model=False,
              model_nameformat=None, modelvar=None,
              fitmask=None)
```

Fit an arbitrary analytic function using Nelder-Mead (`"amoeba"`) or MCMC (`"mcmc"`). `paramlist` has the form `name:initial[:step[:min:max]], ...`.  `fitmask` excludes non-zero-masked points from the fit. `save_model` accepts `bool`, `str`, or `Output` — see [Auxiliary output files](index.md#auxiliary-output-files); the model file is captured as `result.files["nonlinfit_model_N"]`. MCMC chains are captured as `result.files["nonlinfit_chains_N"]`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `linfit_params` | `str` or `None` | Space-separated list of parameter names to solve analytically (linear sub-problem solved exactly at each step). |
| `errors` | `str` or `None` | Expression or variable name providing per-point measurement errors (overrides the default error column). |
| `covariance` | `str` or `None` | Covariance model tokens, e.g. `"squareexp amp_v rho_v"` (passed verbatim after the `covariance` keyword). |
| `priors` | `str` or `None` | Prior expression string (passed verbatim after the `priors` keyword). |
| `constraints` | `str` or `None` | Constraint expression string (passed verbatim after `constraints`). |
| `amoeba_tolerance` | `float` or `None` | Convergence tolerance for the amoeba optimizer. |
| `amoeba_maxsteps` | `int` or `None` | Maximum number of steps for the amoeba optimizer. |
| `mcmc_naccept` | `int` or `None` | Number of accepted links to collect (mutually exclusive with `mcmc_nlinkstotal`). |
| `mcmc_nlinkstotal` | `int` or `None` | Total number of MCMC links (accepted + rejected). |
| `mcmc_fracburnin` | `float` or `None` | Fraction of links to discard as burn-in. |
| `mcmc_eps` | `float` or `None` | Initial step size for the MCMC proposal distribution. |
| `mcmc_skipamoeba` | `bool` | Skip the initial amoeba pre-optimisation in MCMC mode. |
| `mcmc_maxmemstore` | `int` or `None` | Maximum number of chain links to hold in memory simultaneously. |
| `mcmc_outchains` | `bool`, `str`, or `Output` | Write MCMC chain files. Captured as `result.files["nonlinfit_chains_N"]`. |
| `mcmc_chains_format` | `str` or `None` | Naming format string for chain output files. |
| `mcmc_chains_printevery` | `int` or `None` | Write every Nth accepted link to the chain file. |
| `model_nameformat` | `str` or `None` | Format string for the model output filename. |
| `modelvar` | `str` or `None` | Variable name used to store the best-fit model values on the light curve. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/1")

# Fit a sinusoid with free period using amoeba.
# paramlist format: "name=initial:step" (no spaces around commas)
result = lc.nonlinfit(
    "a*sin(2*pi*(t-t0)/P)+c",
    "a=0.01:0.001,P=1.23:0.01,t0=0.0:0.1,c=10.0:0.01",
    optimizer="amoeba",
    amoeba_tolerance=1e-8,
    amoeba_maxsteps=10000,
    save_model=True,
)
print(result.vars["Nonlinfit_P_BestFit_0"])   # best-fit period
model = result.files["nonlinfit_model_0"]

# MCMC posterior sampling (chains written to disk via mcmc_outchains)
result2 = lc.nonlinfit(
    "a*sin(2*pi*(t-t0)/P)+c",
    "a=0.01:0.001,P=1.23:0.01,t0=0.0:0.1,c=10.0:0.01",
    optimizer="mcmc",
    mcmc_naccept=1000,
    mcmc_fracburnin=0.2,
    mcmc_outchains="EXAMPLES/OUTDIR1",
)
print(result2.vars["Nonlinfit_P_MEDIAN_0"])   # posterior median period
```

---

## `decorr` — Decorrelation

```python
cmd.decorr(correct_lc=True, zeropointterm=1, subtractfirstterm=0,
           global_files=None, lc_columns=None, save_model=False,
           maskpoints=None)
```

Decorrelates the light curve against external trend vectors (polynomial fit). `global_files` is a list of `(filename, polynomial_order)` tuples for external trend files; `lc_columns` is a list of `(column_number, polynomial_order)` tuples for light-curve-internal trends. `save_model` accepts `bool`, `str`, or `Output` — see [Auxiliary output files](index.md#auxiliary-output-files); the model file is captured as `result.files["decorr_model_N"]`.

**Examples**

```python
lcs = [vt.LightCurve.from_file(f"EXAMPLES/{i}") for i in range(1, 11)]

# Decorrelate against the time column using a quadratic polynomial
pipe = (vt.Pipeline()
        .rms()
        .decorr(correct_lc=True, zeropointterm=1, subtractfirstterm=1,
               lc_columns=[(1, 2)])
        .rms())
batch = pipe.run_batch(lcs)
print(batch.vars[["Name", "RMS_0", "RMS_2"]])
```

---

## `MandelAgolTransit` — Mandel-Agol transit model

```python
cmd.MandelAgolTransit(P0, T00, r0=0.1, a0=10.0, inclination=90.0,
                      bimpact=None,
                      e0=0.0, omega0=0.0, mconst0=0.0,
                      ld_type="quad", ld_coeffs=None,
                      fitephem=1, fitr=1, fita=1,
                      fitinclterm=1, fite=0, fitomega=0,
                      fitmconst=1, fitldcoeffs=None,
                      rv_file=None, rv_model_file=None,
                      K0=None, gamma0=None, fitK=0, fitgamma=0,
                      correct_lc=False, save_model=False,
                      modelvar=None,
                      save_phcurve=False, save_jdcurve=False)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `P0`, `T00` | `float` or `str` | Initial period (days) and transit epoch (BJD). `P0` also accepts `"bls"` or `"blsfixper"` to seed the transit model from a prior BLS / BLSFixPer — see the admonition below. |
| `r0` | `float` | Initial planet-to-star radius ratio. |
| `a0` | `float` | Initial semi-major axis in stellar radii. |
| `inclination` | `float` | Initial orbital inclination in degrees. Used when `bimpact` is `None`. |
| `bimpact` | `float` or `None` | Initial impact parameter. When set, replaces `inclination` in the CLI (`"b" bimpact` instead of `"i" inclination`). |
| `ld_type` | `str` | Limb-darkening law: `"quad"` or `"nonlin"`. |
| `ld_coeffs` | list | Initial limb-darkening coefficients. Default `[0.3, 0.3]`. |
| `fitephem` | `int` | Fit the transit epoch and period together (0 = fixed, 1 = free).  The CLI `fitephem` flag controls both simultaneously — there is no separate period-only flag. |
| `fitr`, `fita`, `fitinclterm`, etc. | `int` | Toggle fitting of each parameter (0 = fixed, 1 = free). |
| `rv_file` | `str` or `None` | Path to an RV data file (columns: JD, RV, RV-error). When provided, simultaneous RV fitting is enabled. |
| `rv_model_file` | `str` or `None` | Output path for the best-fit RV model. |
| `K0` | `float` or `None` | Initial RV semi-amplitude (km/s). |
| `gamma0` | `float` or `None` | Initial systemic RV (km/s). |
| `fitK`, `fitgamma` | `int` | Fit K and γ respectively (0 = fixed, 1 = free). |
| `modelvar` | `str` or `None` | Variable name used to store the best-fit model on the light curve (requires `save_model` to be set). |
| `save_phcurve` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["MandelAgolTransit_phcurve_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |
| `save_jdcurve` | `bool`, `str`, or `Output` | Auxiliary file output. `True` captures as `result.files["MandelAgolTransit_jdcurve_N"]`. See [Auxiliary output files](index.md#auxiliary-output-files). |

!!! tip "Back-reference seeding from BLS / BLSFixPer"
    When `P0="bls"` (or `"blsfixper"`) is used after a prior `-BLS` / `-BLSFixPer` in the chain, pyvartools pulls Period, Tc, Depth, and Qtran from the prior result and seeds four fields at once: `P0 = BLS.Period_1`, `T00 = BLS.Tc_1`, `r0 = sqrt(BLS.Depth_1)`, `a0 = 1 / (π · BLS.Qtran_1)`. Any of those four values you pass explicitly override the seeded default. This resolves equally in a single `Pipeline` or across chain steps; in batch chains each LC gets its own seed values. Missing prior BLS → `LookupError`.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3.transit")

# 1. Run BLS to locate the transit, then 2. fit Mandel-Agol with numeric seeds.
r_bls = lc.BLS(0.5, 5.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=20000, npeaks=1)
P0  = float(r_bls.vars["BLS_Period_1_0"])
Tc0 = float(r_bls.vars["BLS_Tc_1_0"])

result = lc.MandelAgolTransit(
    P0=P0, T00=Tc0,
    r0=0.11, a0=10.0, inclination=90.0,
    ld_type="quad", ld_coeffs=[0.3471, 0.3180],
    fitephem=1, fitr=1, fita=1, fitinclterm=1,
    fite=0, fitomega=0, fitmconst=1,
    save_model=True, save_phcurve=True,
)
print(result.vars["MandelAgolTransit_Period_0"])   # 2.12328176
print(result.vars["MandelAgolTransit_r_0"])        # Rp/R* ~ 0.11
model   = result.files["MandelAgolTransit_model_0"]    # fitted model LC
phcurve = result.files["MandelAgolTransit_phcurve_0"]  # phase-folded model
```

---

## `SoftenedTransit` — Softened (trapezoidal) transit

```python
cmd.SoftenedTransit(init_params="bls", fitephem=1, fiteta=1,
                    fitcval=1, fitdelta=1, fitmconst=1,
                    correct_lc=False, save_model=False,
                    fit_harm=0, fit_harm_method=None,
                    fit_harm_nharm=None, fit_harm_nsubharm=None)
```

Fits a softened trapezoid transit model. `init_params` can be `"bls"` or `"blsfixper"` to initialise from a prior BLS / BLSFixPer result, `"ls"` or `"aov"` to seed the period from the corresponding periodogram, or a tuple `(P0, T00, eta0, delta0, mconst0, cval0)`.

!!! tip "Back-reference seeding from BLS / BLSFixPer"
    `init_params="bls"` (or `"blsfixper"`) seeds four fields from the prior result: period, T0, eta (= Qtran), and delta (= Depth). This works both in a single `Pipeline` and across chain steps. Batch-chain mode is **not** supported for the multi-field `"bls"` / `"blsfixper"` case (would require per-LC propagation of four fields); use a single `Pipeline` invocation for batch runs. `"ls"` and `"aov"` seed only the period and work in both single- and batch-chain modes. Missing prior command → `LookupError`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `fit_harm` | `int` | Harmonic fitting flag. `0` = no harmonic component (default). When > 0, a harmonic series is fitted simultaneously. |
| `fit_harm_method` | `str` or `None` | Method for harmonic fitting, e.g. `"aov"`. Only used when `fit_harm > 0`. |
| `fit_harm_nharm` | `int` or `None` | Number of harmonics for the harmonic component. |
| `fit_harm_nsubharm` | `int` or `None` | Number of sub-harmonics for the harmonic component. |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3.transit")

pipe = (vt.Pipeline()
        .BLS(0.5, 5.0, rmin=0.01, rmax=0.1, nbins=200, nfreq=20000, npeaks=1)
        .SoftenedTransit(init_params="bls",
                        fitephem=1, fiteta=1, fitcval=1,
                        fitdelta=1, fitmconst=1,
                        correct_lc=False, save_model=True))
result = pipe.run(lc)
print(result.vars["SoftenedTransit_Period_1"])     # 2.12322112
print(result.vars["SoftenedTransit_chi2perdof_1"])
model = result.files["SoftenedTransit_model_1"]   # SoftenedTransit is at index 1
```

---

## `Starspot` — Starspot model

```python
cmd.Starspot(period="ls",
             a0=0.1, b0=0.5, alpha0=20.0, i0=85.0,
             chi0=30.0, psi00=0.0, mconst0=0.0,
             fit_period=1, fit_a=1, fit_b=1, fit_alpha=1,
             fit_i=1, fit_chi=1, fit_psi=1, fit_mconst=1,
             correct_lc=False, save_model=False)
```

Fits a Dorren (1987) two-spot model to photometric variability.

| Parameter | Type | Description |
|-----------|------|-------------|
| `period` | `float` or `str` | Starting period. Can be a number or `"ls"`, `"aov"`, or `"fixcolumn NAME"` to inherit from a prior pipeline command. These back-references resolve correctly both in a single `Pipeline` and across chain steps (e.g. `lc.aov(...).Starspot(period="aov")`). Missing prior command → `LookupError`. |
| `a0` | `float` | Initial spot fractional radius (default `0.1`). |
| `b0` | `float` | Initial spot latitude in radians (default `0.5`). |
| `alpha0` | `float` | Initial spot longitude in degrees (default `20.0`). |
| `i0` | `float` | Initial stellar inclination in degrees (default `85.0`). |
| `chi0` | `float` | Initial spot contrast (default `30.0`). |
| `psi00` | `float` | Initial spot phase offset (default `0.0`). |
| `mconst0` | `float` | Initial magnitude offset (default `0.0`). |
| `fit_period` | `int` | Fit the period (0 = fixed, 1 = free; default `1`). |
| `fit_a`, `fit_b`, `fit_alpha`, `fit_i`, `fit_chi`, `fit_psi`, `fit_mconst` | `int` | Fit each model parameter (0 = fixed, 1 = free; all default `1`). |

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/3.starspot")

# Determine rotation period with AOV then fit Dorren starspot model
pipe = (vt.Pipeline()
        .aov(0.1, 10.0, 0.1, 0.01, npeaks=5, nbin=20)
        .Starspot(
            period="aov",
            a0=0.0298, b0=0.08745, alpha0=20.0, i0=85.0,
            chi0=30.0, psi00=0.0, mconst0=-1.0,
            fit_period=1, fit_a=1, fit_b=1, fit_alpha=1,
            fit_i=1, fit_chi=1, fit_psi=1, fit_mconst=1,
            correct_lc=False,
            save_model=True,
        ))
result = pipe.run(lc)
print(result.vars["Starspot_Period_1"])
print(result.vars["Starspot_chi2perdof_1"])
model = result.files["Starspot_model_1"]   # Starspot is at index 1
```

---

## `microlens` — Microlensing model

```python
cmd.microlens(f0=None, f1=None, u0=None, t0=None, tmax=None,
              correct_lc=False, save_model=False,
              f0_step=None, f0_novary=False,
              f1_step=None, f1_novary=False,
              u0_step=None, u0_novary=False,
              t0_step=None, t0_novary=False,
              tmax_step=None, tmax_novary=False)
```

Fits a standard Paczynski microlensing light curve. Each parameter (`f0`, `f1`, `u0`, `t0`, `tmax`) can be a float (free-fit initial value), `"auto"` (vartools auto-estimate), a string passthrough (e.g. `"fixcolumn colname"`, `"list column 3"`), or `None` (omit). Use `{name}_step` to set the initial step size and `{name}_novary=True` to hold a parameter fixed during fitting.

!!! tip "Back-reference via `fixcolumn`"
    Each of `f0`, `f1`, `u0`, `t0`, `tmax` accepts `"fixcolumn NAME"` to pull the initial value from an output column of a prior command. This resolves identically in a single `Pipeline` and across chain steps. In the chained form the column *name* (not a numeric column index) is required. Missing column in the prior result → `LookupError`.

**Examples**

```python
lc = vt.LightCurve.from_file("EXAMPLES/4.microlensinject")

result = lc.microlens(f0="auto", f1="auto", u0="auto",
                      t0="auto", tmax="auto", save_model=True)
print(result.vars["Microlens_u0_0"])
print(result.vars["Microlens_tmax_0"])
print(result.vars["Microlens_chi2perdof_0"])
model = result.files["microlens_model_0"]
```

---
