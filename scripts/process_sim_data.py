#!/usr/bin/env python3
"""
process_sim_data.py
===================
Reads the raw AC-sweep export from Cadence/Spectre and extracts the headline
op-amp figures of merit, so you never eyeball them off a plot:

    * DC open-loop gain              (dB)
    * Unity-gain bandwidth  (GBW)    (Hz)   - 0 dB crossing
    * Phase margin          (PM)     (deg)  = 180 + phase @ GBW
    * Gain margin           (GM)     (dB)   - gain where phase = -180 deg
    * -3 dB dominant-pole frequency  (Hz)

Input : results/raw_data/ac_sweep_export.csv  (freq_Hz, gain_dB, phase_deg)
Output: results/raw_data/measured_metrics.json  + a printed summary table.

This is deliberately format-agnostic: point --csv at any export with those
three columns (comment lines starting with '#' are skipped automatically).

Usage:  python3 scripts/process_sim_data.py [--csv path/to/export.csv]
Deps :  numpy, pandas
"""
import os
import json
import argparse
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DEFAULT_CSV = os.path.join(ROOT, "results", "raw_data", "ac_sweep_export.csv")
OUT_JSON    = os.path.join(ROOT, "results", "raw_data", "measured_metrics.json")


def load_sweep(path):
    """Load an AC export, tolerating comment lines and column-name variants."""
    df = pd.read_csv(path, comment="#")
    df.columns = [c.strip().lower() for c in df.columns]
    aliases = {
        "freq_hz": "freq", "freq": "freq", "frequency": "freq", "hz": "freq",
        "gain_db": "gain", "gain": "gain", "mag_db": "gain", "magnitude": "gain",
        "phase_deg": "phase", "phase": "phase", "phase_degrees": "phase",
    }
    df = df.rename(columns={c: aliases.get(c, c) for c in df.columns})
    df = df[["freq", "gain", "phase"]].dropna().sort_values("freq")
    return df.reset_index(drop=True)


def _crossing(x, y, target):
    """First x where y crosses `target`, linear interpolation in log-x."""
    yy = y - target
    sign = np.sign(yy)
    idx = np.where(np.diff(sign) != 0)[0]
    if len(idx) == 0:
        return None
    i = idx[0]
    lx = np.interp(0, [yy[i], yy[i+1]],
                   [np.log10(x[i]), np.log10(x[i+1])])
    return 10**lx


def extract_metrics(df):
    f = df["freq"].to_numpy()
    g = df["gain"].to_numpy()
    p = df["phase"].to_numpy()

    dc_gain = g[0]
    f_unity = _crossing(f, g, 0.0)                      # GBW
    pm = None
    if f_unity is not None:
        ph_at_unity = np.interp(np.log10(f_unity), np.log10(f), p)
        pm = 180.0 + ph_at_unity

    f_180 = _crossing(f, p, -180.0)                     # phase = -180
    gm = None
    if f_180 is not None:
        gm = -np.interp(np.log10(f_180), np.log10(f), g)

    f_3db = _crossing(f, g, dc_gain - 3.0)              # dominant pole

    return {
        "dc_gain_dB": round(float(dc_gain), 2),
        "gbw_Hz": None if f_unity is None else round(float(f_unity), 1),
        "gbw_MHz": None if f_unity is None else round(float(f_unity)/1e6, 3),
        "phase_margin_deg": None if pm is None else round(float(pm), 1),
        "gain_margin_dB": None if gm is None else round(float(gm), 1),
        "f_3dB_Hz": None if f_3db is None else round(float(f_3db), 1),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=DEFAULT_CSV)
    args = ap.parse_args()

    df = load_sweep(args.csv)
    m = extract_metrics(df)

    def fmt(v, unit):
        return f"{v:>8} {unit}" if v is not None else f"{'inf/n.a.':>8} {unit}"

    f3 = f"{m['f_3dB_Hz']/1e3:.2f}" if m['f_3dB_Hz'] else None
    print("=" * 52)
    print(" MEASURED PERFORMANCE  (from AC sweep)")
    print("=" * 52)
    print(f" DC open-loop gain    : {fmt(m['dc_gain_dB'], 'dB')}")
    print(f" Unity-gain BW (GBW)  : {fmt(m['gbw_MHz'], 'MHz')}")
    print(f" Phase margin         : {fmt(m['phase_margin_deg'], 'deg')}")
    print(f" Gain margin          : {fmt(m['gain_margin_dB'], 'dB')}")
    print(f" -3 dB (dominant pole): {fmt(f3, 'kHz')}")
    print("=" * 52)

    with open(OUT_JSON, "w") as f:
        json.dump(m, f, indent=2)
    print(f"metrics written to {os.path.relpath(OUT_JSON, ROOT)}")


if __name__ == "__main__":
    main()
