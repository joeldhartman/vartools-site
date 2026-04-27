"""Generate figures for the model-fitting example pages.

Outputs:
  - killharm_ex2.png            RR Lyrae harmonic-series fit (M3.V006.lc, 10 harmonics)
  - mandelagoltransit_ex1.png   Mandel-Agol fit (3.transit, BLS-initialised)
  - softenedtransit_ex1.png     Protopapas softened transit fit (3.transit)
  - starspot_ex1.png            Dorren single-spot fit (3.starspot)
  - microlens_ex1.png           Simple microlens model fit (4.microlensinject)
  - macula_ex1.png              Injected macula model + fitted overplot (3 LC base)
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

MACULA_SO = REPO / "USERLIBS/src/.libs/macula.so"


def _read_model_lc(path: Path) -> pd.DataFrame:
    """Most model-output LCs follow ``# t mag mag_model err [phase]``."""
    return pd.read_csv(path, sep=r"\s+", comment="#", header=None)


def make_killharm():
    # canonical Example 2 — fit a 10-harmonic series at fixed P=0.514333 to the
    # M3 RR Lyrae LC, write the model, plot data + model phased.
    run_vt([
        "-i", "EXAMPLES/M3.V006.lc", "-oneline",
        "-Killharm", "fix", "1", "0.514333", "10", "0", "1",
        "EXAMPLES/OUTDIR1/", "fitonly", "outRphi",
    ])
    # The Killharm model is written to <basename>.killharm.model
    # Columns: t mag err model
    df = pd.read_csv(OUTDIR / "M3.V006.lc.killharm.model",
                     sep=r"\s+", comment="#", header=None,
                     names=["t", "mag", "model", "err"])
    P = 0.514333
    ph = ((df["t"] - df["t"].iloc[0]) / P) % 1.0
    fig, ax = plt.subplots()
    ax.plot(ph, df["mag"], ".", ms=2, color="0.4", alpha=0.6, label="data")
    order = np.argsort(ph.values)
    ax.plot(ph.values[order], df["model"].values[order], "-",
            color="C3", lw=1.0, label="10-harmonic fit")
    ax.invert_yaxis()
    ax.set_xlabel("Phase")
    ax.set_ylabel("Magnitude")
    ax.set_title("M3.V006.lc — 10-harmonic Fourier series fit (Example 2)")
    ax.legend(loc="lower right")
    save(fig, "killharm_ex2.png")


def _phase_fold_against_bls(model_t, period, Tc):
    """Compute phase of *model_t* using BLS period and Tc, wrapped to [-0.5, 0.5)."""
    ph = ((np.asarray(model_t) - Tc) / period) % 1.0
    return np.where(ph > 0.5, ph - 1.0, ph)


def _read_bls_period_tc(stdout: str):
    """Extract BLS_Period_1_0 and BLS_Tc_1_0 from a -oneline output stream."""
    period = Tc = None
    for line in stdout.splitlines():
        if "BLS_Period_1_" in line and "=" in line:
            period = float(line.split("=")[-1])
        elif "BLS_Tc_1_" in line and "=" in line:
            Tc = float(line.split("=")[-1])
    return period, Tc


def make_mandelagol():
    run_vt([
        "-i", "EXAMPLES/3.transit", "-oneline",
        "-BLS", "q", "0.01", "0.1", "0.5", "5.0", "20000", "200",
        "7", "1", "0", "0", "0",
        "-MandelAgolTransit", "bls", "quad", "0.3471", "0.3180",
        "1", "1", "1", "1", "0", "0", "1", "0", "0", "0", "0",
        "1", "EXAMPLES/OUTDIR1",
    ])
    # Columns: t mag model err phase
    df = pd.read_csv(OUTDIR / "3.transit.mandelagoltransit.model",
                     sep=r"\s+", comment="#", header=None,
                     names=["t", "mag", "model", "err", "phase"])
    ph = df["phase"].values
    ph = np.where(ph > 0.5, ph - 1.0, ph)
    sel = (ph > -0.05) & (ph < 0.05)
    fig, ax = plt.subplots()
    ax.plot(ph[sel], df["mag"].values[sel], ".", ms=2, color="0.4",
            alpha=0.6, label="data")
    order = np.argsort(ph[sel])
    ax.plot(ph[sel][order], df["model"].values[sel][order], "-",
            color="C3", lw=1.5, label="Mandel-Agol fit")
    ax.invert_yaxis()
    ax.set_xlabel("Phase (relative to transit centre)")
    ax.set_ylabel("Magnitude")
    ax.set_title("3.transit — Mandel-Agol transit fit")
    ax.legend(loc="lower right")
    save(fig, "mandelagoltransit_ex1.png")


def make_softenedtransit():
    run_vt([
        "-i", "EXAMPLES/3.transit", "-oneline",
        "-BLS", "q", "0.01", "0.1", "0.5", "5.0", "20000", "200",
        "7", "1", "0", "0", "0",
        "-SoftenedTransit", "bls",
        "1", "1", "1", "1", "1", "0",
        "1", "EXAMPLES/OUTDIR1", "0",
    ])
    # Columns: t mag model err phase
    df = pd.read_csv(OUTDIR / "3.transit.softenedtransit.model",
                     sep=r"\s+", comment="#", header=None,
                     names=["t", "mag", "model", "err", "phase"])
    ph = df["phase"].values
    ph = np.where(ph > 0.5, ph - 1.0, ph)
    sel = (ph > -0.05) & (ph < 0.05)
    fig, ax = plt.subplots()
    ax.plot(ph[sel], df["mag"].values[sel], ".", ms=2, color="0.4",
            alpha=0.6, label="data")
    order = np.argsort(ph[sel])
    ax.plot(ph[sel][order], df["model"].values[sel][order], "-",
            color="C3", lw=1.5, label="softened-transit fit")
    ax.invert_yaxis()
    ax.set_xlabel("Phase (relative to transit centre)")
    ax.set_ylabel("Magnitude")
    ax.set_title("3.transit — Protopapas softened-transit fit")
    ax.legend(loc="lower right")
    save(fig, "softenedtransit_ex1.png")


def make_starspot():
    run_vt([
        "-i", "EXAMPLES/3.starspot", "-oneline",
        "-aov", "Nbin", "20", "0.1", "10.", "0.1", "0.01", "5", "0",
        "-Starspot", "aov", "0.0298", "0.08745", "20.", "85.", "30.", "0.", "-1",
        "1", "0", "0", "1", "1", "1", "1", "1", "0",
        "1", "EXAMPLES/OUTDIR1/",
    ])
    df = pd.read_csv(OUTDIR / "3.starspot.starspot.model",
                     sep=r"\s+", comment="#", header=None,
                     names=["t", "mag", "model", "err"])
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    ax.plot(df["t"], df["mag"], ".", ms=1.5, color="0.4", alpha=0.6,
            label="data")
    order = np.argsort(df["t"].values)
    ax.plot(df["t"].values[order], df["model"].values[order], "-",
            color="C3", lw=0.8, label="Dorren single-spot fit")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("3.starspot — Dorren single-spot model fit")
    ax.legend(loc="best")
    save(fig, "starspot_ex1.png")


def make_microlens():
    run_vt([
        "-i", "EXAMPLES/4.microlensinject", "-oneline",
        "-microlens", "f0", "auto", "f1", "auto",
        "u0", "auto", "t0", "auto", "tmax", "auto",
        "omodel", "EXAMPLES/OUTDIR1",
    ])
    df = pd.read_csv(OUTDIR / "4.microlensinject.microlens",
                     sep=r"\s+", comment="#", header=None,
                     names=["t", "mag", "model", "err"])
    fig, ax = plt.subplots()
    ax.plot(df["t"], df["mag"], ".", ms=1.5, color="0.4", alpha=0.6,
            label="data")
    order = np.argsort(df["t"].values)
    ax.plot(df["t"].values[order], df["model"].values[order], "-",
            color="C3", lw=1.0, label="microlens fit")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("4.microlensinject — single-lens point-source fit")
    ax.legend(loc="best")
    save(fig, "microlens_ex1.png")


def make_macula():
    # First inject a model into EXAMPLES/3 (Macula example 1)
    run_vt([
        "-i", "EXAMPLES/3", "-L", str(MACULA_SO),
        "-stats", "t", "min",
        "-expr", "mag=10.0+err*gauss()",
        "-macula", "inject",
            "Prot", "fix", "1.234567",
            "istar", "fix", "1.4567",
            "kappa2", "fix", "0.0",
            "kappa4", "fix", "0.0",
            "c1", "fix", "0.2", "c2", "fix", "0.1",
            "c3", "fix", "0.0", "c4", "fix", "0.0",
            "d1", "fix", "0.2", "d2", "fix", "0.1",
            "d3", "fix", "0.0", "d4", "fix", "0.0",
            "blend", "fix", "1.0",
            "Nspot", "1",
                "Lambda0", "fix", "0.0",
                "Phi0", "fix", "1.2345",
                "alphamax", "fix", "0.2",
                "fspot", "fix", "0.1",
                "tmax", "fixcolumn", "STATS_t_MIN_0",
                "life", "fix", "1000.0",
                "ingress", "fix", "0.1",
                "egress", "fix", "0.1",
        "-o", "EXAMPLES/OUTDIR1/3.maculainject",
    ])
    inj = read_lc(OUTDIR / "3.maculainject")
    # Then fit and overplot the model curve (Macula example 2)
    run_vt([
        "-i", "EXAMPLES/OUTDIR1/3.maculainject", "-L", str(MACULA_SO),
        "-stats", "t", "min",
        "-LS", "0.1", "100", "0.1", "1", "0",
        "-macula", "fit", "amoeba",
            "Prot", "fixcolumn", "LS_Period_1_1", "vary",
            "istar", "fix", "1.6", "vary",
            "kappa2", "fix", "0.0",
            "kappa4", "fix", "0.0",
            "c1", "fix", "0.2", "c2", "fix", "0.1",
            "c3", "fix", "0.0", "c4", "fix", "0.0",
            "d1", "fix", "0.2", "d2", "fix", "0.1",
            "d3", "fix", "0.0", "d4", "fix", "0.0",
            "blend", "fix", "1.0",
            "Nspot", "1",
                "Lambda0", "fix", "0.0",
                "Phi0", "fix", "1.2345",
                "alphamax", "fix", "0.2",
                "fspot", "fix", "0.1",
                "tmax", "fixcolumn", "STATS_t_MIN_0",
                "life", "fix", "1000.0",
                "ingress", "fix", "0.1",
                "egress", "fix", "0.1",
            "omodel", "EXAMPLES/OUTDIR1",
            "ocurve", "EXAMPLES/OUTDIR1",
    ])
    # Macula writes:
    #   <name>.macula.model     — at the data times (t, mag, err, model)
    #   <name>.maculacurve      — uniform-grid curve for plotting (t, model)
    model_files = list(OUTDIR.glob("3.maculainject.macula*"))
    curve_files = list(OUTDIR.glob("3.maculainject.macula*curve"))
    if not curve_files:
        curve_files = list(OUTDIR.glob("3.maculainject.maculacurve"))
    # use the smooth model curve for plotting
    curve = pd.read_csv(curve_files[0], sep=r"\s+", comment="#", header=None,
                        names=["t", "model"])
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    ax.plot(inj["t"], inj["mag"], ".", ms=1.5, color="0.4", alpha=0.6,
            label="injected (3.maculainject)")
    order = np.argsort(curve["t"].values)
    ax.plot(curve["t"].values[order], curve["model"].values[order], "-",
            color="C3", lw=1.2, label="Macula fit (Example 2)")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/3 with macula spot injected → fitted model overplot")
    ax.legend(loc="best")
    save(fig, "macula_ex1.png")


def main():
    make_killharm();          print(" killharm")
    make_mandelagol();        print(" mandelagoltransit")
    make_softenedtransit();   print(" softenedtransit")
    make_starspot();          print(" starspot")
    make_microlens();         print(" microlens")
    make_macula();            print(" macula")


if __name__ == "__main__":
    main()
