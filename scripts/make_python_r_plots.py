"""Generate figures for the -python and -R user-code example pages.

The figures here are produced by user code embedded in the canonical
examples (matplotlib via -python, R via -R), so we just run the
canonical commands and copy/render the resulting PNGs.

Outputs:
  - python_ex2.png            EXAMPLES/2.png produced by EXAMPLES/plotlc.py
  - R_arimamodel_2_data.png   EXAMPLES/2 with ARIMA model overplotted (Example 3)
  - R_arimamodel_2_resid.png  Residuals from the ARIMA fit (Example 3)
  - R_arimaforecast_2.png     Direct copy of the R-side forecast plot (Example 4)
  - R_arimaresiduals_2.png    Direct copy of the R-side residuals plot (Example 4)

Pre-conditions:
  - vartools is installed and on PATH;
  - vartools was built with -python and -R support;
  - the R packages `tseries` and `forecast` are available;
  - EXAMPLES/plotlc.py and EXAMPLES/Rexample4.R live in the source tree.
"""
from __future__ import annotations

import shutil
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from _plot_helpers import REPO, ASSETS, set_style, run_vt, save

set_style()
OUTDIR = REPO / "EXAMPLES" / "OUTDIR1"
OUTDIR.mkdir(parents=True, exist_ok=True)


# ---------- -python Example 2 ----------------------------------------------

def make_python_ex2():
    """Run Example 2 of -python and capture EXAMPLES/2.png."""
    # Clean up the per-LC PNGs (the example writes one per LC matching the
    # -if condition), then run with the canonical invocation.
    for p in (REPO / "EXAMPLES").glob("*.png"):
        p.unlink()
    run_vt([
        "-l", "EXAMPLES/lc_list", "-inputlcformat", "t:1,mag:2,err:3",
        "-header",
        "-LS", "0.1", "100.", "0.1", "1", "0",
        "-if", "Log10_LS_Prob_1_0<-100",
        "-Phase", "ls", "phasevar", "ph",
        "-python", 'plotlc(Name,"EXAMPLES/",t,ph,mag,LS_Period_1_0)',
        "init", "file", "EXAMPLES/plotlc.py",
        "-fi",
    ])
    src = REPO / "EXAMPLES" / "2.png"
    if not src.is_file():
        raise FileNotFoundError(f"plotlc.py did not produce {src}")
    shutil.copy(src, ASSETS / "python_ex2.png")
    print("  copied python_ex2.png")


# ---------- -R Example 3 (ARIMA model + residuals matplotlib plots) --------

def make_r_arimamodel_ex3():
    # Run R Example 3 to generate the .arimamodel ASCII file for EXAMPLES/2
    for p in OUTDIR.glob("*.arimamodel"):
        p.unlink()
    run_vt([
        "-l", "EXAMPLES/lc_list", "-inputlcformat", "t:1,mag:2,err:3",
        "-header",
        "-savelc",
        "-binlc", "average", "binsize", "0.05", "taverage",
        "-resample", "linear", "delt", "fix", "0.05",
        "-R",
        ('mag_ts <- ts(mag, start=1, end=length(t), frequency=1);'
         ' arima_model <- auto.arima(mag_ts);'
         ' mag_arima <- mag - as.vector(arima_model$residuals);'),
        "init", "library(tseries); library(forecast);",
        "invars", "mag,t", "outvars", "mag_arima",
        "-resample", "linear", "file", "list", "listcolumn", "1", "tcolumn", "1",
        "-restorelc", "1", "vars", "mag",
        "-o", "EXAMPLES/OUTDIR1", "nameformat", "%s.arimamodel",
        "columnformat", "t,mag,mag_arima",
    ])
    df = pd.read_csv(OUTDIR / "2.arimamodel", sep=r"\s+",
                     comment="#", header=None,
                     names=["t", "mag", "mag_arima"])
    # data + ARIMA model overplot (canonical Fig 1 of Example 3)
    fig, ax = plt.subplots()
    ax.plot(df["t"], df["mag"], ".", ms=1.5, color="0.4", alpha=0.6,
            label="EXAMPLES/2 data")
    ax.plot(df["t"], df["mag_arima"], "-", color="C3", lw=0.8,
            label="ARIMA model")
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Magnitude")
    ax.set_title("EXAMPLES/2 — ARIMA(p,d,q) fit (R Example 3)")
    ax.legend(loc="best")
    save(fig, "R_arimamodel_2_data.png")

    # residuals (canonical Fig 2 of Example 3)
    fig, ax = plt.subplots()
    ax.plot(df["t"], df["mag"] - df["mag_arima"], ".", ms=1.5,
            color="C0", alpha=0.7)
    ax.axhline(0.0, color="0.6", lw=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("Time [days]")
    ax.set_ylabel("Residual mag")
    ax.set_title("ARIMA model residuals — EXAMPLES/2")
    save(fig, "R_arimamodel_2_resid.png")


# ---------- -R Example 4 (R-generated forecast / residuals PNGs) ----------

def copy_r_example4_pngs():
    """Run -R Example 4 and copy the R-side .png files into the docs assets."""
    # The example needs both -python (for the basename) and -R (for the
    # auto.arima fit + matplotlib-style PNGs written by R).
    for p in OUTDIR.glob("*.arima*.png"):
        p.unlink()
    run_vt([
        "-l", "EXAMPLES/lc_list", "-inputlcformat", "t:1,mag:2,err:3",
        "-header",
        "-savelc",
        "-binlc", "average", "binsize", "0.05", "taverage",
        "-resample", "linear", "delt", "fix", "0.05",
        "-python", 'lcbasename = Name.split("/")[-1]',
        "invars", "Name", "outvars", "lcbasename",
        "-R", 'mag_arima <- DoArimaFitPlot(mag, "EXAMPLES/OUTDIR1/", lcbasename)',
        "init", "file", "EXAMPLES/Rexample4.R",
        "invars", "mag,t,lcbasename", "outvars", "mag_arima",
        "-resample", "linear", "file", "list", "listcolumn", "1", "tcolumn", "1",
        "-restorelc", "1", "vars", "mag",
        "-o", "EXAMPLES/OUTDIR1", "nameformat", "%s.arimamodel",
        "columnformat", "t,mag,mag_arima",
    ])
    fc = OUTDIR / "2.arimaforecast.png"
    rs = OUTDIR / "2.arimaresiduals.png"
    if fc.is_file():
        shutil.copy(fc, ASSETS / "R_arimaforecast_2.png")
        print("  copied R_arimaforecast_2.png")
    else:
        print("  (skipped) 2.arimaforecast.png not produced")
    if rs.is_file():
        shutil.copy(rs, ASSETS / "R_arimaresiduals_2.png")
        print("  copied R_arimaresiduals_2.png")
    else:
        print("  (skipped) 2.arimaresiduals.png not produced")


def main():
    make_python_ex2()
    make_r_arimamodel_ex3()
    print("  wrote R_arimamodel_2_data.png + R_arimamodel_2_resid.png")
    copy_r_example4_pngs()


if __name__ == "__main__":
    main()
