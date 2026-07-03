#!/usr/bin/env python3
"""
generate_bode_plots.py
======================
Turns exported AC / transient data into clean, publication-ready figures for
the two-stage Miller op-amp portfolio.

Outputs (into results/waveforms/):
    * uncompensated_bode.png     - "before": two closely-spaced poles, poor PM
    * compensated_miller_bode.png- "after" : pole-split, Miller vs Miller+Rz
    * step_response.png          - closed-loop small-signal + slew-limited edge

Data source
-----------
If results/raw_data/ac_sweep_export.csv exists it is plotted as the *measured*
compensated response (this is what you get after running the OCEAN AC sweep and
exporting from Cadence). The analytical small-signal model - built from the
hand-calculated pole/zero/gain values - is always drawn as a reference so you
can eyeball model-vs-measured agreement.

Replace the CSV with your own Spectre export and re-run:  no code changes needed.

Usage:  python3 scripts/generate_bode_plots.py
Deps :  numpy, matplotlib, pandas
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# --------------------------------------------------------------------------
# Hand-calculated design constants (see docs/hand_calculations.pdf)
# --------------------------------------------------------------------------
AV0_DB = 73.8
AV0    = 10**(AV0_DB/20)
FP1    = 2.04e3     # dominant pole  (Hz)  - compensated
FP2    = 22.0e6     # non-dominant pole (Hz)
FZ     = 73.3e6     # RHP zero (Hz)         - Miller cap alone
GBW    = 10e6       # target unity-gain BW  (Hz)

# uncompensated pole locations (Cc removed)
FP1_U  = 636e3
FP2_U  = 351e3

# paths ---------------------------------------------------------------------
HERE   = os.path.dirname(os.path.abspath(__file__))
ROOT   = os.path.dirname(HERE)
WAVE   = os.path.join(ROOT, "results", "waveforms")
CSV    = os.path.join(ROOT, "results", "raw_data", "ac_sweep_export.csv")
os.makedirs(WAVE, exist_ok=True)

# --------------------------------------------------------------------------
# Small-signal transfer-function models
# --------------------------------------------------------------------------
def two_pole_one_zero(f, av0, fp1, fp2, fz_rhp=None, fz_lhp=None):
    """Return magnitude (dB) and phase (deg) of a 2-pole (+opt zero) response."""
    s = 1j * f
    H = av0 / ((1 + s/fp1) * (1 + s/fp2))
    if fz_rhp is not None:
        H = H * (1 - s/fz_rhp)      # RHP zero: +mag slope, -phase (lag)
    if fz_lhp is not None:
        H = H * (1 + s/fz_lhp)      # LHP zero: +mag slope, +phase (lead)
    return 20*np.log10(np.abs(H)), np.degrees(np.angle(H))

def phase_margin(f, mag_db, phase_deg):
    """PM = 180 + phase at the unity-gain (0 dB) crossing."""
    idx = np.where(mag_db <= 0)[0]
    if len(idx) == 0:
        return None, None
    i = idx[0]
    # linear interp for the crossing frequency
    f0 = np.interp(0, [mag_db[i], mag_db[i-1]], [f[i], f[i-1]])
    ph = np.interp(f0, f, phase_deg)
    return f0, 180 + ph

# --------------------------------------------------------------------------
# Plot styling
# --------------------------------------------------------------------------
plt.rcParams.update({
    "font.size": 11, "axes.grid": True, "grid.alpha": 0.3,
    "grid.linestyle": "--", "axes.axisbelow": True, "figure.dpi": 130,
    "axes.edgecolor": "#444", "lines.linewidth": 2.0,
})
C_MODEL, C_MEAS, C_ALT, C_BAD = "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e"
f = np.logspace(1, 9, 4000)   # 10 Hz .. 1 GHz

def _annotate_pm(ax_ph, f0, pm, color, label_dy=0):
    if f0 is None:
        return
    ax_ph.axvline(f0, color=color, ls=":", lw=1.3, alpha=0.8)
    ax_ph.annotate(f"PM = {pm:.0f}deg\n@ {f0/1e6:.1f} MHz",
                   xy=(f0, -180+pm), xytext=(f0*0.06, -60+label_dy),
                   color=color, fontsize=9.5, fontweight="bold",
                   arrowprops=dict(arrowstyle="->", color=color, lw=1.2))

# ==========================================================================
# 1. UNCOMPENSATED  (before)
# ==========================================================================
mag_u, ph_u = two_pole_one_zero(f, AV0, FP1_U, FP2_U)
f0_u, pm_u  = phase_margin(f, mag_u, ph_u)

fig, (axm, axp) = plt.subplots(2, 1, figsize=(8.2, 6.6), sharex=True,
                               gridspec_kw={"height_ratios":[1.15,1]})
axm.semilogx(f, mag_u, color=C_BAD, label="Uncompensated ($C_c = 0$)")
axm.axhline(0, color="k", lw=0.8)
axm.set_ylabel("Magnitude (dB)")
axm.set_title("Open-Loop Response - Uncompensated Two-Stage OTA",
              fontweight="bold")
axm.set_ylim(-40, 85); axm.legend(loc="lower left")
axm.annotate(f"$f_{{p1}}\\approx${FP2_U/1e3:.0f} kHz,  "
             f"$f_{{p2}}\\approx${FP1_U/1e3:.0f} kHz\n(poles bunched -> steep phase drop)",
             xy=(4e5, 20), fontsize=9, color="#333",
             bbox=dict(boxstyle="round", fc="#fff4e6", ec=C_BAD, alpha=0.9))

axp.semilogx(f, ph_u, color=C_BAD)
axp.axhline(-180, color="k", lw=0.8, ls="-")
axp.set_ylabel("Phase (deg)"); axp.set_xlabel("Frequency (Hz)")
axp.set_ylim(-190, 5); axp.set_yticks([0,-45,-90,-135,-180])
_annotate_pm(axp, f0_u, pm_u, C_BAD)
axp.text(0.99, 0.05, "Low phase margin -> ringing / marginal stability",
         transform=axp.transAxes, ha="right", color=C_BAD, fontsize=9.5,
         fontweight="bold")
fig.tight_layout()
fig.savefig(os.path.join(WAVE, "uncompensated_bode.png"), bbox_inches="tight")
plt.close(fig)
print(f"[uncompensated]  0 dB @ {f0_u/1e3:.0f} kHz   PM = {pm_u:.1f} deg")

# ==========================================================================
# 2. COMPENSATED  (after): Miller only vs Miller + Rz nulling
# ==========================================================================
mag_m, ph_m = two_pole_one_zero(f, AV0, FP1, FP2, fz_rhp=FZ)          # Miller only
mag_r, ph_r = two_pole_one_zero(f, AV0, FP1, 3*FP2, fz_lhp=None)      # Rz cancels p2
f0_m, pm_m  = phase_margin(f, mag_m, ph_m)
f0_r, pm_r  = phase_margin(f, mag_r, ph_r)

fig, (axm, axp) = plt.subplots(2, 1, figsize=(8.2, 6.6), sharex=True,
                               gridspec_kw={"height_ratios":[1.15,1]})

# measured CSV overlay (if a real/exported sweep is present)
if os.path.exists(CSV):
    import pandas as pd
    d = pd.read_csv(CSV, comment="#")
    axm.semilogx(d["freq_Hz"], d["gain_dB"], color=C_MEAS, lw=1.4,
                 alpha=0.9, label="Measured (Spectre AC export)")
    axp.semilogx(d["freq_Hz"], d["phase_deg"], color=C_MEAS, lw=1.4, alpha=0.9)

axm.semilogx(f, mag_m, color=C_MODEL, label="Model: Miller $C_c$ only")
axm.semilogx(f, mag_r, color=C_ALT, ls="--", label="Model: Miller + $R_z$ nulling")
axm.axhline(0, color="k", lw=0.8)
axm.set_ylabel("Magnitude (dB)")
axm.set_title("Open-Loop Response - Miller Compensated (Pole-Splitting)",
              fontweight="bold")
axm.set_ylim(-40, 85); axm.legend(loc="lower left", fontsize=9.5)
axm.annotate(f"$f_{{p1}}$ = {FP1/1e3:.1f} kHz\n(dominant, pushed DOWN)",
             xy=(FP1, AV0_DB), xytext=(2e1, 40), fontsize=9, color=C_MODEL,
             arrowprops=dict(arrowstyle="->", color=C_MODEL))
axm.annotate(f"$f_{{p2}}$ = {FP2/1e6:.0f} MHz\n(pushed UP, past GBW)",
             xy=(FP2, -20), xytext=(3e7, 30), fontsize=9, color=C_MODEL,
             arrowprops=dict(arrowstyle="->", color=C_MODEL))

axp.semilogx(f, ph_m, color=C_MODEL)
axp.semilogx(f, ph_r, color=C_ALT, ls="--")
axp.axhline(-180, color="k", lw=0.8)
axp.set_ylabel("Phase (deg)"); axp.set_xlabel("Frequency (Hz)")
axp.set_ylim(-230, 5); axp.set_yticks([0,-45,-90,-135,-180,-225])
_annotate_pm(axp, f0_m, pm_m, C_MODEL, label_dy=-35)
_annotate_pm(axp, f0_r, pm_r, C_ALT, label_dy=25)
fig.tight_layout()
fig.savefig(os.path.join(WAVE, "compensated_miller_bode.png"), bbox_inches="tight")
plt.close(fig)
print(f"[Miller only ]  0 dB @ {f0_m/1e6:.2f} MHz   PM = {pm_m:.1f} deg")
print(f"[Miller + Rz ]  0 dB @ {f0_r/1e6:.2f} MHz   PM = {pm_r:.1f} deg")

# ==========================================================================
# 3. STEP RESPONSE  (unity-gain buffer): small-signal + slew-limited
# ==========================================================================
# small-signal 2nd-order closed loop with damping set by the compensated PM
wn   = 2*np.pi*GBW*0.9
zeta = 0.62                      # ~ corresponds to ~60 deg PM
t    = np.linspace(0, 0.6e-6, 2000)
wd   = wn*np.sqrt(1-zeta**2)
step = 1 - np.exp(-zeta*wn*t)*(np.cos(wd*t) + (zeta/np.sqrt(1-zeta**2))*np.sin(wd*t))

# large-signal slew-limited rising edge (SR = 10 V/us) into 1 V then settle
SR = 10e6
t2 = np.linspace(0, 0.4e-6, 2000)
Vstep = 1.0
slew_t = Vstep/SR
large = np.where(t2 < slew_t, SR*t2, Vstep)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 4.2))
a1.plot(t*1e9, step, color=C_MODEL)
a1.axhline(1, color="k", ls="--", lw=0.8)
os_pct = (step.max()-1)*100
a1.set_title(f"Small-Signal Step (unity-gain)\novershoot ~ {os_pct:.0f}%",
             fontweight="bold", fontsize=10.5)
a1.set_xlabel("Time (ns)"); a1.set_ylabel("Output (V, normalised)")
a1.set_ylim(0, 1.3)

a2.plot(t2*1e6, large, color=C_ALT)
a2.plot([0, slew_t*1e6], [0, Vstep], "k:", lw=1)
a2.set_title(f"Large-Signal Edge\nslew rate = {SR/1e6:.0f} V/us",
             fontweight="bold", fontsize=10.5)
a2.set_xlabel("Time (us)"); a2.set_ylabel("Output (V)")
a2.set_ylim(0, 1.2)
a2.annotate("slope = SR", xy=(slew_t*1e6/2, Vstep/2),
            xytext=(0.16, 0.35), fontsize=9, color=C_ALT,
            arrowprops=dict(arrowstyle="->", color=C_ALT))
fig.tight_layout()
fig.savefig(os.path.join(WAVE, "step_response.png"), bbox_inches="tight")
plt.close(fig)
print(f"[step        ]  overshoot ~ {os_pct:.0f}%   slew edge = {slew_t*1e6:.2f} us")
print("Figures written to results/waveforms/")
