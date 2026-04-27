"""Generate figures for the simulation example pages.

Outputs (under docs/assets/examples/):
  - addnoise_ex1.png            wavelet (1/f^0.99) red+white-noise sim
  - addnoise_ex2.png            squareexp red+white-noise sim
  - addnoise_ex2_zoom.png       same, zoomed to a single night
  - injectharm_ex1.png          phased EXAMPLES/3 before/after sinusoid injection
  - injectharm_ex2.png          high-amplitude RR Lyrae injection (LC vs time)
  - injectharm_ex2_low.png      lower-amplitude RR Lyrae injection (LC vs time)
  - injecttransit_ex1.png       LC with injected transit (time series + zoom)
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from _plot_helpers import REPO, ASSETS, set_style, run_vt, read_lc, save

set_style()
OUTDIR = REPO / "EXAMPLES" / "OUTDIR1"
OUTDIR.mkdir(parents=True, exist_ok=True)


def _shell_run(cmd: str) -> None:
    """Run a /bin/sh command (we need `gawk ... | vartools -i -`)."""
    proc = subprocess.run(
        ["/bin/sh", "-c", cmd], cwd=str(REPO),
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"shell cmd failed (rc={proc.returncode}):\n{cmd}\n"
            f"stderr: {proc.stderr.strip()[:1000]}"
        )


# ---------- -addnoise -------------------------------------------------------

def make_addnoise():
    # Example 1: wavelet 1/f^0.99 red noise + white noise, EXAMPLES/1 cadence
    _shell_run(
        "gawk '{print $1, 0., 0.005}' EXAMPLES/1 | "
        "vartools -i - -header -randseed 1 "
        "-addnoise wavelet gamma fix 0.99 sig_red fix 0.005 sig_white fix 0.005 "
        "-o EXAMPLES/OUTDIR1/noisesim_wavelet.txt"
    )
    lc = read_lc(OUTDIR / "noisesim_wavelet.txt")
    fig, ax = plt.subplots()
    ax.plot(lc["t"], lc["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("addnoise wavelet (γ=0.99, σ_red=σ_white=0.005)")
    save(fig, "addnoise_ex1.png")

    # Example 2: squareexp red noise (rho=0.01, sig_red=0.005) + white 0.001
    _shell_run(
        "gawk '{print $1, 0., 0.005}' EXAMPLES/1 | "
        "vartools -i - -header -randseed 1 "
        "-addnoise squareexp rho fix 0.01 sig_red fix 0.005 sig_white fix 0.001 "
        "-o EXAMPLES/OUTDIR1/noisesim_sqexp.txt"
    )
    lc = read_lc(OUTDIR / "noisesim_sqexp.txt")
    fig, ax = plt.subplots()
    ax.plot(lc["t"], lc["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("addnoise squareexp (ρ=0.01 d, σ_red=0.005, σ_white=0.001)")
    save(fig, "addnoise_ex2.png")

    # Example 2 zoom: the canonical site shows a single-night zoom that lets
    # the 0.01-d correlation timescale be visible at the per-point cadence.
    t0 = lc["t"].min()
    sel = (lc["t"] >= t0) & (lc["t"] < t0 + 0.05)
    fig, ax = plt.subplots()
    ax.plot(lc["t"][sel], lc["mag"][sel], "o-", ms=3,
            color="C0", lw=0.6, alpha=0.8)
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("addnoise squareexp — single-night view (~ρ resolved)")
    save(fig, "addnoise_ex2_zoom.png")


# ---------- -Injectharm -----------------------------------------------------

def make_injectharm():
    # Example 1: random sinusoid injection into EXAMPLES/3, recover with LS
    run_vt([
        "-i", "EXAMPLES/3", "-randseed", "1", "-oneline",
        "-Injectharm", "rand", "1.0", "5.0",
        "0", "amplogrand", "0.01", "0.1", "phaserand",
        "0", "1", "EXAMPLES/OUTDIR1",
        "-o", "EXAMPLES/OUTDIR1/3.injectharm_post.txt",
        "-LS", "0.1", "10.0", "0.1", "1", "0",
    ])
    raw = read_lc(REPO / "EXAMPLES" / "3")
    inj = read_lc(OUTDIR / "3.injectharm_post.txt")
    # the canonical figure is *phased*; phase the same data on the recovered period
    # by re-running with `-Phase ls`:
    run_vt([
        "-i", "EXAMPLES/OUTDIR1/3.injectharm_post.txt",
        "-LS", "0.1", "10.0", "0.1", "1", "0",
        "-Phase", "ls",
        "-o", "EXAMPLES/OUTDIR1/3.injectharm_phased.txt",
    ])
    inj_ph = read_lc(OUTDIR / "3.injectharm_phased.txt")
    # Phase the raw LC on the same period for direct comparison:
    inj_period_file = OUTDIR / "3.injectharm.model"
    # We don't easily have the injected period back — read the model file's
    # time spacing instead by phasing the raw data on the same LS period.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.0))
    ax1.plot(raw["t"], raw["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
    ax1.invert_yaxis()
    ax1.set_xlabel("Time [days]")
    ax1.set_ylabel("Magnitude")
    ax1.set_title("EXAMPLES/3 — original")
    ax2.plot(inj_ph["t"], inj_ph["mag"], ".", ms=1.5, color="C3", alpha=0.7)
    ax2.invert_yaxis()
    ax2.set_xlabel("Phase")
    ax2.set_ylabel("Magnitude")
    ax2.set_title("After Injectharm (phased at recovered LS period)")
    save(fig, "injectharm_ex1.png")

    # Example 2: high- and low-amplitude RR Lyrae injection into EXAMPLES/4
    # (the canonical site's "high" amp = 0.25 mag fundamental; "low" = 0.001-ish)
    for amp, fname, ttl in [
        (0.25,    "injectharm_ex2.png",
         "RR Lyrae injection into EXAMPLES/4 (fundamental amp 0.25)"),
        (0.001, "injectharm_ex2_low.png",
         "RR Lyrae injection into EXAMPLES/4 (fundamental amp 0.001)"),
    ]:
        # canonical RR-Lyrae harmonic coefficients (10 harmonics) from
        # the -example -Injectharm Example 2 spec.
        argv = [
            "-i", "EXAMPLES/4", "-randseed", "1",
            "-Injectharm", "fix", "0.514333", "10",
            "ampfix", str(amp), "phaserand",
            "ampfix", "0.47077", "amprel", "phasefix", "0.60826", "phaserel",
            "ampfix", "0.35916", "amprel", "phasefix", "0.26249", "phaserel",
            "ampfix", "0.23631", "amprel", "phasefix", "-0.06843", "phaserel",
            "ampfix", "0.16353", "amprel", "phasefix", "0.60682", "phaserel",
            "ampfix", "0.10621", "amprel", "phasefix", "0.28738", "phaserel",
            "ampfix", "0.06203", "amprel", "phasefix", "0.95751", "phaserel",
            "ampfix", "0.03602", "amprel", "phasefix", "0.58867", "phaserel",
            "ampfix", "0.02900", "amprel", "phasefix", "0.22322", "phaserel",
            "ampfix", "0.01750", "amprel", "phasefix", "0.94258", "phaserel",
            "ampfix", "0.00768", "amprel", "phasefix", "0.66560", "phaserel",
            "0", "0",
            "-Phase", "fix", "0.514333",
            "-o", f"EXAMPLES/OUTDIR1/4.rrlyrae_{amp}.txt",
        ]
        run_vt(argv)
        lc = read_lc(OUTDIR / f"4.rrlyrae_{amp}.txt")
        fig, ax = plt.subplots()
        ax.plot(lc["t"], lc["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
        ax.invert_yaxis()
        ax.set_xlabel("Phase")
        ax.set_ylabel("Magnitude")
        ax.set_title(ttl)
        save(fig, fname)


# ---------- -Injecttransit --------------------------------------------------

def make_injecttransit():
    run_vt([
        "-i", "EXAMPLES/3", "-oneline", "-randseed", "1",
        "-Injecttransit", "lograndfreq", "0.2", "2.0",
        "Rpfix", "1.0", "Mpfix", "1.0",
        "phaserand", "sinirand",
        "eomega", "efix", "0.", "ofix", "0.",
        "Mstarfix", "1.0", "Rstarfix", "1.0",
        "quad", "ldfix", "0.3471", "0.3180",
        "1", "EXAMPLES/OUTDIR1",
        "-o", "EXAMPLES/OUTDIR1/3.injecttransit_post.txt",
    ])
    lc = read_lc(OUTDIR / "3.injecttransit_post.txt")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.0))
    ax1.plot(lc["t"], lc["mag"], ".", ms=1.5, color="0.4", alpha=0.7)
    ax1.invert_yaxis()
    ax1.set_xlabel("Time [days]")
    ax1.set_ylabel("Magnitude")
    ax1.set_title("EXAMPLES/3 with injected transit — full LC")
    # zoom on the deepest part — find the minimum-magnitude window
    deepest = lc.iloc[lc["mag"].idxmax()]
    t0 = float(deepest["t"])
    win = (lc["t"] > t0 - 0.5) & (lc["t"] < t0 + 0.5)
    ax2.plot(lc["t"][win], lc["mag"][win], ".", ms=2, color="C3", alpha=0.8)
    ax2.invert_yaxis()
    ax2.set_xlabel("Time [days]")
    ax2.set_ylabel("Magnitude")
    ax2.set_title(f"Zoom around deepest transit (t≈{t0:.2f})")
    save(fig, "injecttransit_ex1.png")


def main():
    make_addnoise();        print(" addnoise")
    make_injectharm();      print(" injectharm")
    make_injecttransit();   print(" injecttransit")


if __name__ == "__main__":
    main()
