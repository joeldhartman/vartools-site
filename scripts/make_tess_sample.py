"""Generate a TESS-like single-sector LC for -fourierfilter examples
4 and 5 in the docs.

Takes the existing dense uniformly-sampled example LC
(EXAMPLES/2.simuniformsample) — which is what examples 1-3 use — and
re-samples it at TESS short-cadence-binned-to-2-min cadence, then drops
a ~1-day interval near the middle of the sector to emulate the
data-downlink gap that occurs once per TESS sector.

Same signal and noise structure as examples 1-3, so the filter behavior
is directly comparable across examples.

Output: /home/jhartman/GIT/vartools/EXAMPLES/2.simtesssample
        and the SVN tree mirror.
"""
import numpy as np

SRC_PATH = "/home/jhartman/GIT/vartools/EXAMPLES/2.simuniformsample"
OUT_PATHS = [
    "/home/jhartman/GIT/vartools/EXAMPLES/2.simtesssample",
    "/home/jhartman/SVN/HATpipe/source/vartools/EXAMPLES/2.simtesssample",
]

# TESS short-cadence is ~2 min; binned products are 10 min, 30 min.
# We use 2 min to give a realistic short-cadence sampling rate.
DT_TESS = 2.0 / 60.0 / 24.0           # 2-min cadence (days) ≈ 0.001389
GAP_START_FRAC = 13.0 / 27.4          # downlink gap roughly mid-sector
GAP_END_FRAC   = 14.0 / 27.4          # ~1-day gap

# Load source: 3 columns (t, mag, err) at ~0.5-min cadence over 31 days.
src = np.loadtxt(SRC_PATH)
t_src, mag_src, err_src = src[:,0], src[:,1], src[:,2]

# Build TESS sample times: uniform stride of 2 min over the same time
# span, then drop the data-downlink gap interval.
t0, tend = t_src[0], t_src[-1]
T_span = tend - t0
n_full = int(np.floor(T_span / DT_TESS)) + 1
t_tess = t0 + np.arange(n_full) * DT_TESS
gap_lo = t0 + GAP_START_FRAC * T_span
gap_hi = t0 + GAP_END_FRAC   * T_span
keep = (t_tess < gap_lo) | (t_tess > gap_hi)
t_tess = t_tess[keep]

# Sample the source LC at the TESS times by linear interpolation —
# the source is dense enough (0.5-min cadence) that this is essentially
# loss-free for our injected signal.
mag_tess = np.interp(t_tess, t_src, mag_src)
err_tess = np.interp(t_tess, t_src, err_src)

for p in OUT_PATHS:
    with open(p, "w") as f:
        for ti, mi, ei in zip(t_tess, mag_tess, err_tess):
            f.write(f"{ti:18.9f}  {mi:9.5f}   {ei:7.5f}\n")
    print(f"wrote {p}")

print(f"  N={len(t_tess)}  T={t_tess[-1]-t_tess[0]:.3f}")
print(f"  median(dt)={np.median(np.diff(t_tess)):.5f}  "
      f"max(dt)={np.max(np.diff(t_tess)):.4f}")
