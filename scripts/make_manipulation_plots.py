"""Generate figures for the manipulation/filtering example pages.

Outputs:
  - binlc_ex1.png             Median-binned LC overlaid on input (Example 1)
  - binlc_ex2.png             Phase-binned LC at LS period (Example 2)
  - phase_ex1.png             Phase-folded EXAMPLES/2 at P=1.2354 d
  - phase_ex2.png             Phase-folded + phase-binned (Example 2)
  - clip_ex1.png              Pre/post 3σ-clipped LC (Example 1)
  - medianfilter_ex1.png      LC before/after high-pass median filter
  - medianfilter_ex2.png      LC before/after low-pass median filter (replace)
  - fluxtomag_ex1.png         Kepler Q1 LC converted to magnitudes
  - restricttimes_ex2.png     EXAMPLES/3.transit phased before / after transit cut
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from _plot_helpers import REPO, ASSETS, set_style, run_vt, read_lc, save

set_style()
OUTDIR = REPO / "EXAMPLES" / "OUTDIR1"
OUTDIR.mkdir(parents=True, exist_ok=True)


def _plot_lc_overlay(lcs, title, fname, *, ms=2, alpha=0.7,
                     ylabel="Magnitude", invert=True):
    """Plot one or more (label, t, mag, color) tuples on a magnitude vs time axis."""
    fig, ax = plt.subplots()
    for label, t, mag, color in lcs:
        ax.plot(t, mag, ".", ms=ms, color=color, alpha=alpha, label=label)
    if invert:
        ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(loc="best", markerscale=2)
    save(fig, fname)


def make_binlc():
    # Example 1: median-bin EXAMPLES/2 with binsize=0.01
    run_vt([
        "-i", "EXAMPLES/2", "-header",
        "-binlc", "median", "binsize", "0.01", "tcenter",
        "-o", "EXAMPLES/OUTDIR1/2.bin.txt",
    ])
    raw = read_lc(REPO / "EXAMPLES" / "2")
    binned = read_lc(OUTDIR / "2.bin.txt")
    fig, ax = plt.subplots()
    ax.plot(raw["t"], raw["mag"], ".", ms=1.5, color="0.7", alpha=0.5,
            label="raw (EXAMPLES/2)")
    ax.plot(binned["t"], binned["mag"], "+", ms=4, color="C3", lw=0.8,
            label="median-binned (0.01 d)")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/2 — median binning at 0.01-day cadence")
    ax.legend(loc="best", markerscale=1.0)
    save(fig, "binlc_ex1.png")

    # Example 2: phase-fold then bin into 100 equal phase bins
    run_vt([
        "-i", "EXAMPLES/2", "-header",
        "-LS", "0.1", "10.", "0.1", "1", "0",
        "-Phase", "ls",
        "-binlc", "median", "nbins", "100", "tcenter",
        "-o", "EXAMPLES/OUTDIR1/2.phasebin.txt",
    ])
    pb = read_lc(OUTDIR / "2.phasebin.txt")
    # Get the phased LC for the comparison (re-run phase)
    run_vt([
        "-i", "EXAMPLES/2",
        "-LS", "0.1", "10.", "0.1", "1", "0",
        "-Phase", "ls",
        "-o", "EXAMPLES/OUTDIR1/2.phased_full.txt",
    ])
    full = read_lc(OUTDIR / "2.phased_full.txt")
    fig, ax = plt.subplots()
    ax.plot(full["t"], full["mag"], ".", ms=1.5, color="0.7", alpha=0.5,
            label="phase-folded data")
    ax.plot(pb["t"], pb["mag"], "+", ms=5, color="C3",
            label="binned (100 phase bins)")
    ax.invert_yaxis()
    ax.set_xlabel("Phase")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/2 — phase-folded at the LS period, binned into 100 bins")
    ax.legend(loc="best")
    save(fig, "binlc_ex2.png")


def make_phase():
    # Example 1: fix-period phase fold of EXAMPLES/2
    run_vt([
        "-i", "EXAMPLES/2", "-header",
        "-Phase", "fix", "1.2354",
        "-o", "EXAMPLES/OUTDIR1/2.phase.txt",
    ])
    ph = read_lc(OUTDIR / "2.phase.txt")
    fig, ax = plt.subplots()
    ax.plot(ph["t"], ph["mag"], ".", ms=2, color="0.4", alpha=0.7)
    ax.invert_yaxis()
    ax.set_xlabel("Phase")
    ax.set_ylabel("Magnitude")
    ax.set_title(r"EXAMPLES/2 phase-folded at $P=1.2354$ d")
    save(fig, "phase_ex1.png")

    # Example 2: BLS-period phase fold of 3.transit + bin into 200
    run_vt([
        "-i", "EXAMPLES/3.transit",
        "-BLS", "q", "0.01", "0.1", "0.1", "20.0", "100000", "200",
        "0", "1", "0", "0", "0", "fittrap",
        "-Phase", "bls", "T0", "bls", "0.5",
        "-o", "EXAMPLES/OUTDIR1/3.transit.phase_full.txt",
    ])
    full = read_lc(OUTDIR / "3.transit.phase_full.txt")
    run_vt([
        "-i", "EXAMPLES/3.transit",
        "-BLS", "q", "0.01", "0.1", "0.1", "20.0", "100000", "200",
        "0", "1", "0", "0", "0", "fittrap",
        "-Phase", "bls", "T0", "bls", "0.5",
        "-binlc", "median", "nbins", "200", "tcenter",
        "-o", "EXAMPLES/OUTDIR1/3.transit.phasebin.txt",
    ])
    pb = read_lc(OUTDIR / "3.transit.phasebin.txt")
    fig, ax = plt.subplots()
    ax.plot(full["t"], full["mag"], ".", ms=1.5, color="0.7", alpha=0.5,
            label="phased (BLS period)")
    ax.plot(pb["t"], pb["mag"], "+", ms=5, color="C3",
            label="phase-binned (200 bins)")
    ax.invert_yaxis()
    ax.set_xlabel("Phase (transit at 0.5)")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/3.transit — BLS-period phase fold + binning")
    ax.legend(loc="lower right")
    save(fig, "phase_ex2.png")


def make_clip():
    # 3-sigma iterative clip on EXAMPLES/5
    run_vt([
        "-header", "-i", "EXAMPLES/5",
        "-rms",
        "-clip", "3.", "1",
        "-rms",
        "-o", "EXAMPLES/OUTDIR1/5.clip.txt",
    ])
    raw = read_lc(REPO / "EXAMPLES" / "5")
    clipped = read_lc(OUTDIR / "5.clip.txt")
    # show pre/post clip with the clipped points highlighted
    raw_set = set(zip(raw["t"], raw["mag"]))
    keep_set = set(zip(clipped["t"], clipped["mag"]))
    clipped_pts = raw[~raw[["t", "mag"]].apply(tuple, axis=1).isin(keep_set)]
    fig, ax = plt.subplots()
    ax.plot(clipped["t"], clipped["mag"], ".", ms=2, color="0.4", alpha=0.7,
            label="kept after clip")
    ax.plot(clipped_pts["t"], clipped_pts["mag"], "x", ms=6,
            color="C3", label="clipped points")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/5 — iterative 3σ clipping")
    ax.legend(loc="best", markerscale=1.5)
    save(fig, "clip_ex1.png")


def make_medianfilter():
    # Example 1: high-pass (subtract running median) on EXAMPLES/1
    run_vt([
        "-i", "EXAMPLES/1", "-header", "-chi2",
        "-savelc",
        "-medianfilter", "0.05",
        "-chi2", "-o", "EXAMPLES/OUTDIR1/1.medianhighpass",
        "-restorelc", "1",
        "-medianfilter", "0.05", "replace",
        "-chi2", "-o", "EXAMPLES/OUTDIR1/1.medianlowpass",
    ])
    raw = read_lc(REPO / "EXAMPLES" / "1")
    high = read_lc(OUTDIR / "1.medianhighpass")
    low = read_lc(OUTDIR / "1.medianlowpass")
    # high-pass: residuals (centered around zero) — separate panel
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.0, 5.5), sharex=True)
    ax1.plot(raw["t"], raw["mag"], ".", ms=1.5, color="0.4", alpha=0.6)
    ax1.invert_yaxis()
    ax1.set_ylabel("Magnitude")
    ax1.set_title("EXAMPLES/1 — original")
    ax2.plot(high["t"], high["mag"], ".", ms=1.5, color="C0", alpha=0.7)
    ax2.axhline(0, color="0.6", lw=0.5)
    ax2.invert_yaxis()
    ax2.set_xlabel("Time [days]")
    ax2.set_ylabel("Residual mag")
    ax2.set_title("After 0.05-d high-pass median filter")
    save(fig, "medianfilter_ex1.png")

    # low-pass (replace mode): smoothed running-median
    fig, ax = plt.subplots()
    ax.plot(raw["t"], raw["mag"], ".", ms=1.5, color="0.7", alpha=0.5,
            label="EXAMPLES/1 raw")
    ax.plot(low["t"], low["mag"], "-", color="C3", lw=1.0,
            label="0.05-d running median (replace)")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/1 — low-pass median filter")
    ax.legend(loc="best")
    save(fig, "medianfilter_ex2.png")


def make_fluxtomag():
    # Convert the bundled Kepler Q1 LC to magnitudes
    run_vt([
        "-i", "EXAMPLES/kplr000757076-2009166043257_llc.fits",
        "-readformat", "0", "1", "10", "11",
        "-fluxtomag", "25.0", "0",
        "-o", "EXAMPLES/OUTDIR1/kplr.fluxtomag.txt",
    ])
    lc = read_lc(OUTDIR / "kplr.fluxtomag.txt")
    fig, ax = plt.subplots()
    ax.plot(lc["t"], lc["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
    ax.invert_yaxis()
    ax.set_xlabel("BJD")
    ax.set_ylabel("Magnitude (zero-point 25.0)")
    ax.set_title("KIC 757076 (Kepler Q1) flux → mag conversion")
    save(fig, "fluxtomag_ex1.png")


def make_restricttimes():
    # Example 2: phased EXAMPLES/3.transit before/after a JD restrictions cut
    # that removes the transit window.
    # The canonical example uses ophcurve to write the BLS model — we just
    # show pre- and post-cut phased LCs.
    run_vt([
        "-i", "EXAMPLES/3.transit",
        "-BLS", "q", "0.01", "0.1", "0.1", "20.0", "100000", "200",
        "0", "1", "0", "0", "0", "fittrap",
        "-Phase", "bls", "T0", "bls", "0.5",
        "-o", "EXAMPLES/OUTDIR1/3.transit.before.txt",
    ])
    before = read_lc(OUTDIR / "3.transit.before.txt")
    # Now restrict to outside the transit window (mask the in-transit phase)
    run_vt([
        "-i", "EXAMPLES/3.transit",
        "-BLS", "q", "0.01", "0.1", "0.1", "20.0", "100000", "200",
        "0", "1", "0", "0", "0", "fittrap",
        "-Phase", "bls", "T0", "bls", "0.5",
        "-restricttimes", "expr", "(t<0.48)||(t>0.52)",
        "-o", "EXAMPLES/OUTDIR1/3.transit.after.txt",
    ])
    after = read_lc(OUTDIR / "3.transit.after.txt")
    fig, ax = plt.subplots()
    ax.plot(before["t"], before["mag"], ".", ms=1.5, color="C0", alpha=0.7,
            label="before — full phased LC")
    ax.plot(after["t"], after["mag"], ".", ms=1.5, color="C3", alpha=0.7,
            label="after — transit window removed")
    ax.invert_yaxis()
    ax.set_xlabel("Phase (transit at 0.5)")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/3.transit — before vs after restricttimes (transit cut)")
    ax.legend(loc="lower right")
    save(fig, "restricttimes_ex2.png")


def main():
    make_binlc();         print(" binlc")
    make_phase();         print(" phase")
    make_clip();          print(" clip")
    make_medianfilter();  print(" medianfilter")
    make_fluxtomag();     print(" fluxtomag")
    make_restricttimes(); print(" restricttimes")


if __name__ == "__main__":
    main()
