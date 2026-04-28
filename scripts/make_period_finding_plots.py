"""Generate figures for the period-finding command examples.

Each function recreates the matching figure from the canonical site
(www.astro.princeton.edu/~jhartman/vartools/EXAMPLE_HTML/) using the
*actual* output of the example command, rendered with the modernised
matplotlib house style defined in ``_plot_helpers``.

Outputs land in ``docs/assets/examples/``:

  - ``ls_ex1.png``                    Lomb-Scargle periodogram (Example 1)
  - ``ls_ex1_whitened.png``           LS periodogram after whitening (peak 2)
  - ``aov_ex1.png``                   AoV periodogram (Example 1, peak 1)
  - ``aov_harm_ex1.png``              Multi-harmonic AoV periodogram (Example 1)
  - ``bls_ex1.png``                   BLS spectrum (Example 1)
  - ``bls_ex1_phased.png``            Phased LC + BLS model (Example 1)
  - ``dftclean_ex1.png``              DFT power spectrum (Example 1)
  - ``dftclean_ex2_dirty.png``        DFT power spectrum (Example 2)
  - ``dftclean_ex2_clean.png``        Cleaned spectrum (Example 2)
  - ``dftclean_ex2_beam.png``         CLEAN beam (Example 2)
  - ``dftclean_ex2_window.png``       Window function (Example 2)
  - ``autocorrelation_ex1.png``       Discrete ACF (Example 1)
  - ``wwz_ex1.png``                   2-D WWZ heatmap (Example 1)
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from _plot_helpers import REPO, ASSETS, set_style, run_vt, read_periodogram, read_lc, save

set_style()
OUTDIR = REPO / "EXAMPLES" / "OUTDIR1"
OUTDIR.mkdir(parents=True, exist_ok=True)


# ---------- -LS Example 1 ---------------------------------------------------

def make_ls_ex1():
    """Run the canonical -LS example and plot before/after pre-whitening.

    vartools writes a single ``2.ls`` file with one column for each
    whitening cycle (cycle 0 = original; cycle 1 = after removing peak 1).
    """
    run_vt([
        "-i", "EXAMPLES/2", "-oneline", "-ascii",
        "-LS", "0.1", "10.", "0.1", "5", "1", "EXAMPLES/OUTDIR1",
        "whiten", "clip", "5.", "1",
    ])
    cols = ["freq",
            "power_c0", "logFAP_c0",
            "power_c1", "logFAP_c1",
            "power_c2", "logFAP_c2",
            "power_c3", "logFAP_c3",
            "power_c4", "logFAP_c4"]
    pg = read_periodogram(OUTDIR / "2.ls", names=cols)
    # Initial periodogram
    fig, ax = plt.subplots()
    ax.plot(pg["freq"], pg["power_c0"], "k-", lw=0.6)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel("L-S Power")
    ax.set_title("Lomb-Scargle periodogram (EXAMPLES/2)")
    ax.set_xlim(0, 10)
    save(fig, "ls_ex1.png")
    # After pre-whitening peak 1
    fig, ax = plt.subplots()
    ax.plot(pg["freq"], pg["power_c1"], "k-", lw=0.6)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel("L-S Power")
    ax.set_title("L-S periodogram after pre-whitening peak 1")
    ax.set_xlim(0, 10)
    save(fig, "ls_ex1_whitened.png")


# ---------- -aov / -aov_harm Example 1 --------------------------------------

def make_aov_ex1():
    run_vt([
        "-i", "EXAMPLES/2", "-oneline", "-ascii",
        "-aov", "Nbin", "20", "0.1", "10.", "0.1", "0.01",
        "5", "1", "EXAMPLES/OUTDIR1", "whiten", "clip", "5.", "1",
    ])
    # cols: period, theta_c0, theta_c1, ..., theta_c4
    pg = read_periodogram(OUTDIR / "2.aov",
                          names=["period", "t0", "t1", "t2", "t3", "t4"])
    freq = 1.0 / pg["period"]
    fig, ax = plt.subplots()
    ax.plot(freq, pg["t0"], "k-", lw=0.6)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel(r"$\theta_{\rm AoV}$")
    ax.set_title("Phase-binning AoV periodogram (EXAMPLES/2, Nbin=20)")
    ax.set_xlim(0, 10)
    save(fig, "aov_ex1.png")


def make_aov_harm_ex1():
    run_vt([
        "-i", "EXAMPLES/2", "-oneline", "-ascii",
        "-aov_harm", "1", "0.1", "10.", "0.1", "0.01",
        "5", "1", "EXAMPLES/OUTDIR1", "whiten", "clip", "5.", "1",
    ])
    # Cols: period, theta_c0, theta_c1, theta_c2, theta_c3, theta_c4
    # (one theta column per whiten cycle)
    pg = read_periodogram(
        OUTDIR / "2.aov_harm",
        names=["period", "t0", "t1", "t2", "t3", "t4"],
    )
    freq = 1.0 / pg["period"]
    fig, ax = plt.subplots()
    ax.plot(freq, pg["t0"], "k-", lw=0.6)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel(r"$\theta_{\rm AoV}$")
    ax.set_title("Multi-harmonic AoV periodogram (EXAMPLES/2, Nharm=1)")
    ax.set_xlim(0, 10)
    save(fig, "aov_harm_ex1.png")


# ---------- -BLS Example 1 (spectrum + phased model) ------------------------

def make_bls_ex1():
    run_vt([
        "-i", "EXAMPLES/3.transit", "-oneline",
        "-BLS", "q", "0.01", "0.1", "0.1", "20.0", "100000", "200",
        "0", "1",                            # timezone, Npeak
        "1", "EXAMPLES/OUTDIR1/",            # operiodogram + dir
        "1", "EXAMPLES/OUTDIR1/",            # omodel + dir
        "0", "fittrap",                      # correctlc, fittrap
        "nobinnedrms",
        "ophcurve", "EXAMPLES/OUTDIR1/", "-0.1", "1.1", "0.001",
    ])
    # 3.transit.bls cols: period, S/N, SR
    spec = read_periodogram(OUTDIR / "3.transit.bls",
                            names=["period", "sn", "sr"])
    fig, ax = plt.subplots()
    ax.plot(1.0 / spec["period"], spec["sn"], "k-", lw=0.5)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel("BLS S/N")
    ax.set_title("BLS spectrum (EXAMPLES/3.transit)")
    save(fig, "bls_ex1.png")

    # phased LC + BLS model.  3.transit.bls.model cols:
    #   time mag_obs mag_model error phase
    model = read_periodogram(OUTDIR / "3.transit.bls.model",
                             names=["t", "mag", "modelmag", "err", "phase"])
    # show ±0.3 of phase around transit; vartools writes phase 0..1 so wrap.
    ph = model["phase"].copy()
    ph = np.where(ph > 0.5, ph - 1.0, ph)
    sel = (ph > -0.3) & (ph < 0.3)
    fig, ax = plt.subplots()
    ax.plot(ph[sel], model["mag"][sel], ".", ms=2, color="0.4", alpha=0.6,
            label="data (phase-folded)")
    order = np.argsort(ph[sel])
    ax.plot(ph[sel].iloc[order] if hasattr(ph[sel], "iloc") else ph[sel][order],
            model["modelmag"][sel].iloc[order]
            if hasattr(model["modelmag"][sel], "iloc")
            else model["modelmag"][sel][order],
            "-", color="C3", lw=1.5, label="BLS model")
    ax.invert_yaxis()
    ax.set_xlabel("Phase (relative to transit centre)")
    ax.set_ylabel("Magnitude")
    ax.set_title("Phased LC + BLS model (EXAMPLES/3.transit)")
    ax.legend(loc="lower right")
    save(fig, "bls_ex1_phased.png")


# ---------- -dftclean Example 1 / 2 ----------------------------------------

def _plot_dft(spec: pd.DataFrame, title: str, fname: str,
              positive_only: bool = True) -> None:
    """Plot a DFT-CLEAN power spectrum.

    The output files run from ``-maxfreq`` to ``+maxfreq``; for the dirty
    and CLEAN spectra we restrict to the positive half (the negative
    frequencies are mirror images).  For the CLEAN beam and window
    function we keep the full range so the symmetry around zero is
    visible.
    """
    if positive_only:
        spec = spec[spec["freq"] >= 0]
    fig, ax = plt.subplots()
    ax.plot(spec["freq"], spec["power"], "k-", lw=0.6)
    ax.set_xlabel("Frequency [c/d]")
    ax.set_ylabel("Power")
    ax.set_title(f"{title} (EXAMPLES/2)")
    save(fig, fname)


def make_dftclean():
    # Example 1: simple DFT power spectrum (no CLEAN, just outdspec)
    run_vt([
        "-i", "EXAMPLES/2", "-oneline",
        "-dftclean", "4", "maxfreq", "10.",
        "outdspec", "EXAMPLES/OUTDIR1",
        "finddirtypeaks", "1", "clip", "5.", "1",
    ])
    sp = read_periodogram(OUTDIR / "2.dftclean.dspec", names=["freq", "power"])
    _plot_dft(sp, "DFT power spectrum", "dftclean_ex1.png")

    # Example 2: full CLEAN with all four output products
    run_vt([
        "-i", "EXAMPLES/2", "-oneline",
        "-dftclean", "4", "maxfreq", "10.",
        "outdspec", "EXAMPLES/OUTDIR1",
        "finddirtypeaks", "5", "clip", "5.", "1",
        "outwfunc", "EXAMPLES/OUTDIR1",
        "clean", "0.5", "3.0",
        "outcbeam", "EXAMPLES/OUTDIR1",
        "outcspec", "EXAMPLES/OUTDIR1",
        "findcleanpeaks", "3", "clip", "5.", "1",
        "verboseout",
    ])
    dirty = read_periodogram(OUTDIR / "2.dftclean.dspec", names=["freq", "power"])
    clean = read_periodogram(OUTDIR / "2.dftclean.cspec", names=["freq", "power"])
    beam  = read_periodogram(OUTDIR / "2.dftclean.cbeam", names=["freq", "power"])
    wfun  = read_periodogram(OUTDIR / "2.dftclean.wfunc", names=["freq", "power"])
    _plot_dft(dirty, "DFT power spectrum (dirty)",         "dftclean_ex2_dirty.png")
    _plot_dft(clean, "Spectrum after CLEAN deconvolution",  "dftclean_ex2_clean.png")
    _plot_dft(beam,  "CLEAN beam",                          "dftclean_ex2_beam.png",
              positive_only=False)
    _plot_dft(wfun,  "Window function",                     "dftclean_ex2_window.png",
              positive_only=False)


# ---------- -autocorrelation Example 1 -------------------------------------

def make_autocorrelation_ex1():
    run_vt([
        "-i", "EXAMPLES/2", "-oneline",
        "-autocorrelation", "0.0", "10.0", "0.05", "EXAMPLES/OUTDIR1",
    ])
    acf = read_periodogram(OUTDIR / "2.autocorr", names=["lag", "acf"])
    fig, ax = plt.subplots()
    ax.plot(acf["lag"], acf["acf"], "k-", lw=0.7)
    ax.axhline(0.0, color="0.6", lw=0.5)
    ax.set_xlabel("Lag [days]")
    ax.set_ylabel("ACF")
    ax.set_title("Discrete ACF (EXAMPLES/2)")
    save(fig, "autocorrelation_ex1.png")


# ---------- -wwz Example 1 -------------------------------------------------

def make_wwz_ex1():
    run_vt([
        "-i", "EXAMPLES/8", "-oneline",
        "-wwz", "maxfreq", "2.0", "freqsamp", "0.25",
        "tau0", "auto", "tau1", "auto", "dtau", "0.1",
        "outfulltransform", "EXAMPLES/OUTDIR1/", "pm3d",
        "outmaxtransform", "EXAMPLES/OUTDIR1",
    ])
    # pm3d format columns (per the file header):
    #   time_shift  frequency  WWZ  WWA  Neff  C  Ccos  Csin
    # blank lines separate constant-tau blocks.
    raw = pd.read_csv(OUTDIR / "8.wwz", sep=r"\s+",
                      comment="#", header=None, skip_blank_lines=True,
                      names=["tau", "freq", "z", "wwa", "neff",
                             "c0", "c1", "c2"])
    # Show tau relative to its minimum so the x-axis starts at 0.
    raw["tau_rel"] = raw["tau"] - raw["tau"].min()
    pivot = raw.pivot_table(index="freq", columns="tau_rel",
                            values="z", aggfunc="first")
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    extent = [pivot.columns.min(), pivot.columns.max(),
              pivot.index.min(), pivot.index.max()]
    im = ax.imshow(pivot.values, origin="lower", aspect="auto",
                   extent=extent, cmap="viridis")
    fig.colorbar(im, ax=ax, label="Z")
    ax.set_xlabel(r"Time-shift $\tau - \tau_0$ [days]")
    ax.set_ylabel("Frequency [c/d]")
    ax.set_title("WWZ 2-D transform (EXAMPLES/8)")
    save(fig, "wwz_ex1.png")


def main():
    make_ls_ex1();           print(" wrote ls_ex1.png + ls_ex1_whitened.png")
    make_aov_ex1();          print(" wrote aov_ex1.png")
    make_aov_harm_ex1();     print(" wrote aov_harm_ex1.png")
    make_bls_ex1();          print(" wrote bls_ex1.png + bls_ex1_phased.png")
    make_dftclean();         print(" wrote dftclean_ex1.png + ex2 quartet")
    make_autocorrelation_ex1(); print(" wrote autocorrelation_ex1.png")
    make_wwz_ex1();          print(" wrote wwz_ex1.png")


if __name__ == "__main__":
    main()
