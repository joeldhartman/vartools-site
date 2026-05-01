"""Generate the plot for examples/hatpi-flare-detection.md.

Runs the full vartools pipeline on the bundled HATPI subphot LC
EXAMPLES/Gaia-DR2-5481843025342799104_subphot.fits, then plots:
  - Top:    flag-filtered raw TFA2 magnitudes (full baseline).
  - Middle: medianfilter(1 d) high-pass residual with shaded windows
            for changepoints flagged as flare candidates (negative
            cp_dmag AND positive dchi2 from the per-flare nonlinfit).
  - Bottom: per-flare zoom panels showing the data + the fitted
            exp-decay model overlay.

Output: docs/assets/examples/hatpi_flare_ex1.png
"""
from __future__ import annotations
import os, time

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from astropy.io import fits

import pyvartools as vt

PATH = "EXAMPLES/Gaia-DR2-5481843025342799104_subphot.fits"
OUT  = os.path.join(os.path.dirname(__file__), "..",
                     "docs", "assets", "examples", "hatpi_flare_ex1.png")
KNOWN_FLARE = 2460695.61505

N = 30                          # max changepoints to fit

# ---- R: detect cps with PELT, keep top-N brightenings by |cp_dmag|.
#         Also emit a per-cp "duration" = time-gap to the next cp in
#         time order; used as a smart initial value for the decay
#         timescale c. ----
R_CODE = f"N <- {N}L\n"
R_CODE += r"""
cp <- cpt.meanvar(mag, method="PELT", penalty="Manual", pen.value=20)
allcps <- cpts(cp)
mu     <- param.est(cp)$mean
alldmag <- mu[2:length(mu)] - mu[1:(length(mu)-1)]
brighten <- which(alldmag < 0)
ord      <- order(abs(alldmag[brighten]), decreasing=TRUE)
top      <- head(brighten[ord], N)
cps      <- allcps[top]
top_dmag <- alldmag[top]
# Time gap from each kept cp to the next cp in time order (= rough
# segment duration; for a clean exp-decay flare this is ~3-4 decay
# timescales).
top_dur <- numeric(length(top))
for (j in seq_along(top)) {
  i <- top[j]
  next_t <- if (i < length(allcps)) t[allcps[i+1]] else t[length(t)]
  top_dur[j] <- next_t - t[allcps[i]]
}
# Smart inits + steps for the per-cp nonlinfit, pre-computed here so
# the paramlist can reference them by name (vartools' paramlist parser
# splits on ',' so we can't use min(...,...) inline).
#   - b = 2 * cp_dmag   (segment-mean shift underestimates the peak)
#     b_step = 0.5 * |cp_dmag|
#   - c = top_dur/4 clamped to [0.003, 0.025] d (~4-36 min)
#     c_step = top_dur/8 clamped to [0.0015, 0.0125] d
top_b_init <- 2 * top_dmag
top_b_step <- 0.5 * abs(top_dmag)
top_c_init <- pmax(0.003,  pmin(0.025,  top_dur / 4))
top_c_step <- pmax(0.0015, pmin(0.0125, top_dur / 8))
n_cp <- length(cps)
pad_t      <- function(k) if (k <= n_cp) t[cps[k]]      else NA_real_
pad_dmag   <- function(k) if (k <= n_cp) top_dmag[k]    else NA_real_
pad_b_init <- function(k) if (k <= n_cp) top_b_init[k]  else NA_real_
pad_b_step <- function(k) if (k <= n_cp) top_b_step[k]  else NA_real_
pad_c_init <- function(k) if (k <= n_cp) top_c_init[k]  else NA_real_
pad_c_step <- function(k) if (k <= n_cp) top_c_step[k]  else NA_real_
n_cp_v <- as.numeric(n_cp)
"""
for k in range(1, N + 1):
    R_CODE += (
        f"cp_t_{k}      <- pad_t({k});      "
        f"cp_dmag_{k}   <- pad_dmag({k});\n"
        f"cp_b_init_{k} <- pad_b_init({k}); "
        f"cp_b_step_{k} <- pad_b_step({k});\n"
        f"cp_c_init_{k} <- pad_c_init({k}); "
        f"cp_c_step_{k} <- pad_c_step({k});\n"
    )

R_OUTVARS = ",".join(["n_cp_v"]
        + [f"cp_t_{k}"      for k in range(1, N + 1)]
        + [f"cp_dmag_{k}"   for k in range(1, N + 1)]
        + [f"cp_b_init_{k}" for k in range(1, N + 1)]
        + [f"cp_b_step_{k}" for k in range(1, N + 1)]
        + [f"cp_c_init_{k}" for k in range(1, N + 1)]
        + [f"cp_c_step_{k}" for k in range(1, N + 1)])

# ---- build the pipeline ----
pipe = (vt.Pipeline()
        .restricttimes(mode="expr", expression="(flag & 61) == 0")
        .medianfilter(time=1.0, method="median", replace=False)
        .R(R_CODE,
           init="library(changepoint)",
           invars="t,mag",
           outvars=R_OUTVARS,
           outputcolumns=R_OUTVARS))

for k in range(1, N + 1):
    pipe = (pipe
        .ifcmd(condition=f"!isnan(cp_t_{k})")
        .expr(f"flare_mask_{k}=(abs(t-cp_t_{k})<0.1)")
        .expr(
            f"chi2_pre_{k}="
            f"sum(((mag-mean(mag,flare_mask_{k}>0.5))^2)/err^2,flare_mask_{k}>0.5)",
            vartype="listvar", outputcolumn=True)
        .nonlinfit(
            function="a*(t<t0) + (b*(t>=t0)*exp(-(t-t0)*(t>=t0)/c) + d)",
            paramlist=(f"a=0:0.005,"
                       f"b=cp_b_init_{k}:cp_b_step_{k},"
                       f"c=cp_c_init_{k}:cp_c_step_{k},"
                       f"d=0:0.005,"
                       f"t0=cp_t_{k}:0.001"),
            optimizer="amoeba",
            amoeba_tolerance=1e-4, amoeba_maxsteps=10000,
            fitmask=f"flare_mask_{k}",
        )
        .ficmd())

t_start = time.time()
result = pipe.run_file(PATH,
        columns={"t":    "TIME",
                 "mag":  "TFA2",
                 "err":  "ERR2",
                 "flag": vt.LCColumn(col="FLAG2", type="int")})
print(f"pipeline: {time.time()-t_start:.2f} s")

# ---- collect per-cp fit results ----
candidates = []   # list of dicts with cp/fit info for the flare candidates
for k in range(1, N + 1):
    cp_t = result.vars.get(f"R_cp_t_{k}_2", np.nan)
    cp_d = result.vars.get(f"R_cp_dmag_{k}_2", np.nan)
    if np.isnan(cp_t):
        continue
    chi2_idx = 5 * k
    nlf_idx  = 5 * k + 1
    chi2_pre  = float(result.vars.get(f"Expr_chi2_pre_{k}_{chi2_idx}", np.nan))
    chi2_post = float(result.vars.get(f"Nonlinfit_BestFit_Chi2_{nlf_idx}", np.nan))
    fit = {
        "k":         k,
        "cp_t":      float(cp_t),
        "cp_dmag":   float(cp_d),
        "chi2_pre":  chi2_pre,
        "chi2_post": chi2_post,
        "dchi2":     chi2_pre - chi2_post,
        "a":  float(result.vars.get(f"Nonlinfit_a_BestFit_{nlf_idx}",  np.nan)),
        "b":  float(result.vars.get(f"Nonlinfit_b_BestFit_{nlf_idx}",  np.nan)),
        "c":  float(result.vars.get(f"Nonlinfit_c_BestFit_{nlf_idx}",  np.nan)),
        "d":  float(result.vars.get(f"Nonlinfit_d_BestFit_{nlf_idx}",  np.nan)),
        "t0": float(result.vars.get(f"Nonlinfit_t0_BestFit_{nlf_idx}", np.nan)),
    }
    if fit["dchi2"] > 0 and fit["cp_dmag"] < 0:
        candidates.append(fit)

candidates.sort(key=lambda f: f["dchi2"], reverse=True)
print(f"\n{len(candidates)} flare candidate(s) (dchi2>0 AND cp_dmag<0), sorted:")
for f in candidates:
    flag = "  *** matches known flare" if abs(f["t0"] - KNOWN_FLARE) < 0.01 else ""
    print(f"  cp{f['k']:2d}  t0={f['t0']:.5f}  b={f['b']:+.4f}  "
          f"c={f['c']*24*60:.2f} min  dchi2={f['dchi2']:+.1f}{flag}")

# Show the top-6 by dchi2 in the figure.
TOP_N_FIG = 6
to_plot = candidates[:TOP_N_FIG]

# ---- raw + residual LCs for plotting ----
with fits.open(PATH) as h:
    bt      = h[1].data
    raw_t   = np.array(bt["TIME"], dtype=float)
    raw_mag = np.array(bt["TFA2"], dtype=float)
    raw_fl  = np.array(bt["FLAG2"], dtype=int)
keep = ((raw_fl & 0b111101) == 0) & np.isfinite(raw_mag)
raw_t, raw_mag = raw_t[keep], raw_mag[keep]

res = (vt.Pipeline()
       .restricttimes(mode="expr", expression="(flag & 61) == 0")
       .medianfilter(time=1.0, method="median", replace=False)
).run_file(PATH,
           columns={"t": "TIME", "mag": "TFA2", "err": "ERR2",
                    "flag": vt.LCColumn(col="FLAG2", type="int")},
           capture_lc=True)
out = res.lc

# ---- plot: top-2 rows are full LC + residual; bottom 2 rows are a
#           2x3 grid of the top 6 candidates by dchi2.
n_zoom = max(len(to_plot), 1)
ncols = min(3, n_zoom)
nrows_zoom = (n_zoom + ncols - 1) // ncols
fig = plt.figure(figsize=(13.5, 4 + 2.5 * nrows_zoom))
gs = fig.add_gridspec(2 + nrows_zoom, ncols,
                       height_ratios=[1, 1] + [1.05] * nrows_zoom,
                       hspace=0.45, wspace=0.22)
ax_raw = fig.add_subplot(gs[0, :])
ax_res = fig.add_subplot(gs[1, :], sharex=ax_raw)
ax_zooms = [fig.add_subplot(gs[2 + i // ncols, i % ncols])
            for i in range(n_zoom)]

ax_raw.plot(raw_t, raw_mag, ".", ms=0.9, color="0.55",
              label="TFA2 (flag-filtered)")
ax_raw.invert_yaxis()
ax_raw.set_ylabel("mag")
ax_raw.set_title("Full baseline")
ax_raw.legend(loc="upper right")

ax_res.plot(out.t, out.mag, ".", ms=0.8, color="C0",
              label="medianfilter(1 d) residual")
for f in candidates:
    ax_res.axvspan(f["t0"] - 5*f["c"], f["t0"] + 5*f["c"],
                     color="C3", alpha=0.20)
ax_res.invert_yaxis()
ax_res.set_xlabel("BJD")
ax_res.set_ylabel("residual mag")
ax_res.legend(loc="upper right")

# Per-flare zooms (±0.1 d around fitted t0) with model overlay.
# Horizontal axis is (t - t0); axis label encodes the integer BJD
# offset so the absolute time is recoverable.
ZOOM_HW = 0.1
for i, f in enumerate(to_plot):
    t0 = f["t0"]
    keep = (out.t > t0 - ZOOM_HW) & (out.t < t0 + ZOOM_HW)
    ax = ax_zooms[i]
    ax.plot(out.t[keep] - t0, out.mag[keep], ".", ms=4, color="C0")
    tg = np.linspace(-ZOOM_HW, ZOOM_HW, 400)
    pre  = (tg < 0).astype(float)
    post = (tg >= 0).astype(float)
    model = (f["a"] * pre
             + f["b"] * post * np.exp(-tg * post / f["c"])
             + f["d"])
    ax.plot(tg, model, "-", lw=1.5, color="C3")
    ax.axvline(0, color="0.7", ls=":", lw=0.8)
    ax.invert_yaxis()
    ax.set_xlim(-ZOOM_HW, ZOOM_HW)
    ax.set_xlabel(f"BJD − {t0:.3f}")
    ax.set_title(f"b={f['b']*1000:+.1f} mmag, "
                  f"τ={f['c']*24*60:.1f} min, "
                  f"Δχ²={f['dchi2']:+.0f}")
for i in range(0, n_zoom, ncols):
    ax_zooms[i].set_ylabel("residual mag")

fig.suptitle("HATPI Gaia-DR2-5481843025342799104 — TFA2 + medianfilter(1 d) "
             "+ R cpt.meanvar + per-cp exp-decay nonlinfit")
fig.tight_layout()
fig.savefig(OUT, dpi=110)
print(f"plot -> {OUT}")
