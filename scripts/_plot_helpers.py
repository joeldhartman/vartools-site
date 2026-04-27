"""Helpers shared by the per-command-family figure scripts.

Each ``make_<family>_plots.py`` script imports ``_plot_helpers`` and:

  - sets the matplotlib house style (``set_style``);
  - runs vartools / pyvartools commands to produce the data the figure needs;
  - writes the resulting PNG into ``docs/assets/examples/``.

We deliberately keep matplotlib options light — the goal is a clean modern
look, not a pixel-faithful reproduction of the gnuplot figures on
www.astro.princeton.edu/~jhartman/vartools/.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # save-to-file backend
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path("/home/jhartman/SVN/HATreduc/HATpipe/source/vartools")
ASSETS = Path("/home/jhartman/src/vartools-site/docs/assets/examples")


def set_style() -> None:
    """Apply the house style for vartools-site figures."""
    plt.rcParams.update({
        "figure.figsize": (8.0, 4.5),
        "figure.dpi": 110,
        "savefig.dpi": 110,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "0.85",
        "grid.linewidth": 0.5,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "legend.frameon": False,
    })


def run_vt(args: List[str], cwd: Path = REPO,
           env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run vartools and raise if it fails.  Always operates in *cwd*."""
    proc = subprocess.run(
        ["vartools"] + args,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"vartools failed (rc={proc.returncode})\n"
            f"  args: {args}\n"
            f"  stderr: {proc.stderr.strip()[:1000]}"
        )
    return proc


def read_periodogram(path: Path,
                     names: List[str] = ("freq", "power")) -> pd.DataFrame:
    """Read a whitespace/comment-headed periodogram file.

    The vartools periodogram format is whitespace-delimited with the column
    layout depending on the command (LS, AoV, BLS, DFT-CLEAN, …) — pass the
    column names you want via ``names``.
    """
    return pd.read_csv(path, sep=r"\s+", comment="#",
                       header=None, names=list(names))


def save(fig: plt.Figure, fname: str) -> Path:
    """Save *fig* into the docs assets directory."""
    ASSETS.mkdir(parents=True, exist_ok=True)
    out = ASSETS / fname
    fig.savefig(out)
    plt.close(fig)
    return out


def read_lc(path: Path,
            cols: List[str] = ("t", "mag", "err")) -> pd.DataFrame:
    """Read a vartools-format ASCII light curve."""
    return pd.read_csv(path, sep=r"\s+", comment="#",
                       header=None, names=list(cols))
