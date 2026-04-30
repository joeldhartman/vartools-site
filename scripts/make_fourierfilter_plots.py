"""Generate before/after light-curve + power-spectrum figures for the
five -fourierfilter examples shown in the python webdocs.

For each example, the spectrum panel is computed by writing out the
Fourier coefficients via the command's own `ofourier` keyword (one
auxiliary call to vartools per spectrum) and then computing
power = a^2 + b^2 from those coefficients in Python.  This guarantees
that the spectrum shown is exactly the FFT that -fourierfilter
computes internally — no external library, no astropy, no separate
DFT — using the same time grid, the same df_fft, and the same FFT
implementation.

Two pipeline calls per example:
  1. The actual filter (capture filtered LC + dump output spectrum
     via `save_fouriercoeffs`)
  2. mode="full" with save_fouriercoeffs (no mask) on the input LC,
     just to dump the pre-filter spectrum.

For non-uniform input (examples 4-5) both auxiliary calls also need
`resample` (since path 1 isn't applicable to non-uniform data).

Output: 5 PNG files in /home/jhartman/src/vartools-site/docs/assets/examples/
named fourierfilter_ex1.png through fourierfilter_ex5.png.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

import pyvartools as vt

OUT_DIR = "/home/jhartman/src/vartools-site/docs/assets/examples"
os.makedirs(OUT_DIR, exist_ok=True)

LC_UNIFORM_PATH = "/home/jhartman/GIT/vartools/EXAMPLES/2.simuniformsample"
LC_TESS_PATH    = "/home/jhartman/GIT/vartools/EXAMPLES/2.simtesssample"


def coeffs_to_power(df, fmax_plot=None):
    """The fouriercoeffs DataFrame has columns:
    [Frequency, CosCoeff, SinCoeff]  (no filterexpr)  or
    [Frequency, CosCoeff_orig, SinCoeff_orig, CosCoeff_filter, SinCoeff_filter]
    Returns (frequency, power) using the *_orig (or sole) columns,
    optionally truncated to f <= fmax_plot.  We exclude the DC bin
    (k=0) from the plot since power(DC) = lcave^2 dominates the y-axis."""
    f = df.iloc[:, 0].to_numpy()
    a = df.iloc[:, 1].to_numpy()
    b = df.iloc[:, 2].to_numpy()
    p = a*a + b*b
    sel = (f > 0)
    if fmax_plot is not None:
        sel &= (f <= fmax_plot)
    return f[sel], p[sel]


def get_input_spectrum(lc_path, *, resample=None, fmax_plot=None):
    """Use a `mode='full'` -fourierfilter call (no mask) with
    save_fouriercoeffs to dump the input spectrum that the filter
    would see, then read it back."""
    lc = vt.LightCurve.from_file(lc_path)
    pipe = vt.Pipeline().fourierfilter(
        mode="full", resample=resample, save_fouriercoeffs=True)
    r = pipe.run(lc)
    return coeffs_to_power(r.files["fourierfilter_fouriercoeffs_0"],
                           fmax_plot=fmax_plot)


# --- Mask functions: Python mirror of _fourierfilter_mask in fourierfilter.c.
# The "filtered" spectrum is the input spectrum multiplied bin-by-bin by
# this mask — exactly what the kernel does in frequency space.  Computing
# it analytically here (instead of by re-FFT-ing the time-domain output)
# avoids the gap-interpolation artifact that contaminates the
# resample-path output's spectrum on heavily-clustered LCs.

def _edge_taper(f, edge, direction, taper_type, delta, beta):
    if delta <= 0.0 or taper_type is None:
        if direction > 0:
            return np.where(f >= edge, 1.0, 0.0)
        return np.where(f <= edge, 1.0, 0.0)
    x = direction * (f - edge)
    u = np.clip((x + delta) / (2.0 * delta), 0.0, 1.0)
    if taper_type == "linear":
        out = u
    elif taper_type in ("cosine", "tukey", "hann"):
        out = 0.5 * (1.0 - np.cos(np.pi * u))
    elif taper_type == "blackman":
        out = 0.42 - 0.5 * np.cos(np.pi * u) + 0.08 * np.cos(2 * np.pi * u)
    elif taper_type == "kaiser":
        from scipy.special import i0
        out = i0(beta * np.sqrt(1.0 - (1.0 - u) ** 2)) / i0(beta)
    else:
        out = u
    out = np.where(x <= -delta, 0.0, out)
    out = np.where(x >=  delta, 1.0, out)
    return out


def fourierfilter_mask_py(freqs, *, mode, minfreq=None, maxfreq=None,
                          taper=None, taper_deltafreq=0.0, taper_beta=0.0):
    """Mirror of the C `_fourierfilter_mask` for plotting purposes."""
    f = np.asarray(freqs)
    if mode == "full":
        return np.ones_like(f)
    if mode == "highpass":
        return _edge_taper(f, minfreq, +1, taper, taper_deltafreq, taper_beta)
    if mode == "lowpass":
        return _edge_taper(f, maxfreq, -1, taper, taper_deltafreq, taper_beta)
    if mode == "bandpass":
        lo = _edge_taper(f, minfreq, +1, taper, taper_deltafreq, taper_beta)
        hi = _edge_taper(f, maxfreq, -1, taper, taper_deltafreq, taper_beta)
        return lo * hi
    if mode == "bandcut":
        lo = _edge_taper(f, minfreq, -1, taper, taper_deltafreq, taper_beta)
        hi = _edge_taper(f, maxfreq, +1, taper, taper_deltafreq, taper_beta)
        return 1.0 - (1.0 - lo) * (1.0 - hi)
    return np.ones_like(f)


def get_output_spectrum(lc_in, *, fourierfilter_kwargs, resample_for_spec=None,
                        fmax_plot=None):
    """Filtered LC + filtered spectrum.  The filtered spectrum is the
    input spectrum (from save_fouriercoeffs) multiplied bin-by-bin by
    the filter mask (band + taper + filterexpr) — exactly what
    -fourierfilter does in frequency space.  This is more faithful
    than re-FFT-ing the time-domain output, which on the resample
    path has to interpolate across gaps and contaminates the
    spectrum."""
    # Filtered LC
    pipe = vt.Pipeline().fourierfilter(**fourierfilter_kwargs)
    r = pipe.run(lc_in, capture_lc=True)
    out_lc_mag = np.asarray(r.lc.mag)

    # Input coeffs — same call as get_input_spectrum but we need the
    # full DataFrame, not just power.
    pipe2 = vt.Pipeline().fourierfilter(
        mode="full", resample=resample_for_spec, save_fouriercoeffs=True)
    df = pipe2.run(lc_in).files["fourierfilter_fouriercoeffs_0"]
    f_in = df.iloc[:, 0].to_numpy()
    a_in = df.iloc[:, 1].to_numpy()
    b_in = df.iloc[:, 2].to_numpy()

    # Apply the mask (band + taper) analytically.
    mode      = fourierfilter_kwargs.get("mode", "full")
    minfreq   = fourierfilter_kwargs.get("minfreq")
    maxfreq   = fourierfilter_kwargs.get("maxfreq")
    taper     = fourierfilter_kwargs.get("taper")
    delta_t   = fourierfilter_kwargs.get("taper_deltafreq", 0.0) or 0.0
    beta_t    = fourierfilter_kwargs.get("taper_beta", 0.0) or 0.0
    mask = fourierfilter_mask_py(f_in, mode=mode, minfreq=minfreq,
                                 maxfreq=maxfreq, taper=taper,
                                 taper_deltafreq=delta_t, taper_beta=beta_t)
    # filterexpr (only ex3 here).  Evaluate in Python.
    fe = fourierfilter_kwargs.get("filterexpr")
    if fe is not None:
        mask = mask * eval(fe.replace("^", "**"),
                           {"exp": np.exp, "f": f_in})

    a_out = a_in * mask
    b_out = b_in * mask
    p_out = a_out**2 + b_out**2
    sel = (f_in > 0)
    if fmax_plot is not None:
        sel &= (f_in <= fmax_plot)
    return out_lc_mag, f_in[sel], p_out[sel]


def plot(lc_path, *, fourierfilter_kwargs, title, fname, fmax_plot=2.0,
         t_window=None, mark_freqs=(), resample_for_spec=None):
    """Make the before/after figure for one example."""
    lc = vt.LightCurve.from_file(lc_path)
    t   = np.asarray(lc.t)
    mag = np.asarray(lc.mag)

    # Input spectrum from the command's ofourier
    f_in, p_in = get_input_spectrum(lc_path, resample=resample_for_spec,
                                    fmax_plot=fmax_plot)

    # Output LC + spectrum
    out_mag, f_out, p_out = get_output_spectrum(
        lc, fourierfilter_kwargs=fourierfilter_kwargs,
        resample_for_spec=resample_for_spec, fmax_plot=fmax_plot)

    # Figure
    fig, (ax_lc, ax_ps) = plt.subplots(2, 1, figsize=(7, 5),
                                       constrained_layout=True)
    if t_window is None:
        sel = np.ones_like(t, dtype=bool)
    else:
        sel = (t >= t_window[0]) & (t <= t_window[1])
    ax_lc.plot(t[sel], mag[sel], '.', color='0.7', ms=2, label='input',
               rasterized=True)
    ax_lc.plot(t[sel], out_mag[sel], '.', color='C0', ms=2,
               label='filtered', rasterized=True)
    ax_lc.set_xlabel("Time (days)")
    ax_lc.set_ylabel("mag")
    ax_lc.legend(loc='best', fontsize=8, markerscale=3)
    ax_lc.invert_yaxis()
    suffix = ""
    if t_window is not None:
        suffix = (f"  (showing {t_window[1]-t_window[0]:.1f} d of "
                  f"{t[-1] - t[0]:.0f} d)")
    ax_lc.set_title(title + suffix, fontsize=9)

    ax_ps.plot(f_in,  p_in,  color='0.7', lw=0.8, label='input')
    ax_ps.plot(f_out, p_out, color='C0',  lw=0.8, label='filtered')
    for f_mark in mark_freqs:
        ax_ps.axvline(f_mark, color='C3', ls='--', lw=0.8, alpha=0.7)
    ax_ps.set_xlabel("Frequency (cyc/day)")
    ax_ps.set_ylabel("Power = a$^2$ + b$^2$")
    ax_ps.set_yscale('log')
    pmax = max(p_in.max(), p_out.max())
    ax_ps.set_ylim(1e-7 * pmax, 3 * pmax)
    ax_ps.set_xlim(0, fmax_plot)
    ax_ps.legend(loc='best', fontsize=8)

    fig.savefig(os.path.join(OUT_DIR, fname), dpi=110)
    plt.close(fig)
    print(f"  saved {fname}")


# Visual windows: zoom into ~1.5 days where there's clear sub-day structure
_t0_uniform = vt.LightCurve.from_file(LC_UNIFORM_PATH).t[0]
_t0_tess    = vt.LightCurve.from_file(LC_TESS_PATH).t[0]
WIN_U = (_t0_uniform, _t0_uniform + 1.5)
WIN_T = (_t0_tess,    _t0_tess    + 1.5)


print("Example 1: lowpass + cosine taper (uniform)")
plot(LC_UNIFORM_PATH,
     fourierfilter_kwargs=dict(mode="lowpass", maxfreq=1.0,
                               taper="cosine", taper_deltafreq=0.1),
     title="Ex 1: lowpass maxfreq=1.0 cyc/day, cosine taper deltafreq=0.1",
     fname="fourierfilter_ex1.png",
     fmax_plot=3.0, t_window=WIN_U, mark_freqs=[1.0])

print("Example 2: bandpass [0.5, 1.25] (uniform)")
plot(LC_UNIFORM_PATH,
     fourierfilter_kwargs=dict(mode="bandpass", minfreq=0.5, maxfreq=1.25),
     title="Ex 2: bandpass minfreq=0.5, maxfreq=1.25 cyc/day",
     fname="fourierfilter_ex2.png",
     fmax_plot=2.5, t_window=WIN_U, mark_freqs=[0.5, 1.25])

print("Example 3: full + filterexpr (uniform)")
plot(LC_UNIFORM_PATH,
     fourierfilter_kwargs=dict(mode="full", filterexpr="exp(-(f/0.5)^2)"),
     title="Ex 3: full + filterexpr W(f)=exp(-(f/0.5)^2)",
     fname="fourierfilter_ex3.png",
     fmax_plot=2.5, t_window=WIN_U, mark_freqs=[0.5])

print("Example 4: lowpass + cosine taper + resample (TESS-like sampling)")
plot(LC_TESS_PATH,
     fourierfilter_kwargs=dict(mode="lowpass", maxfreq=1.0,
                               taper="cosine", taper_deltafreq=0.1,
                               resample="delmin"),
     title="Ex 4: same filter as Ex 1 on a TESS-like LC + resample delmin",
     fname="fourierfilter_ex4.png",
     fmax_plot=3.0, t_window=WIN_T, mark_freqs=[1.0],
     resample_for_spec="delmin")

print("Example 5: highpass + resample + gapbreak (TESS-like sampling)")
plot(LC_TESS_PATH,
     fourierfilter_kwargs=dict(mode="highpass", minfreq=2.0,
                               taper="cosine", taper_deltafreq=0.1,
                               resample="delmin",
                               gapbreak_type="frac_med_sep",
                               gapbreak_value=100),
     title="Ex 5: highpass minfreq=2.0 + resample delmin + gapbreak",
     fname="fourierfilter_ex5.png",
     fmax_plot=5.0, t_window=WIN_T, mark_freqs=[2.0],
     resample_for_spec="delmin")

print("\nDone.")
