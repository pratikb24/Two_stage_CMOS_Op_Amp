"""
design_engine.py
================
Single source of truth for the Two-Stage CMOS Op-Amp with Miller Compensation.

Runs the Allen-Holberg design procedure end-to-end, prints a self-consistent
sizing table, and generates the analytical reference waveforms plus a synthetic
AC-sweep CSV (in the same format an OCEAN/Spectre export would produce).

The equations here are the SAME ones written up in docs/hand_calculations.pdf,
so the report, netlist and plots never disagree.

NOTE: these are analytical / small-signal model plots used as design references.
      Replace results/raw_data/ac_sweep_export.csv with your real Spectre export
      and the plotting script will happily plot the measured data instead.
"""
import json
import numpy as np

# ----------------------------------------------------------------------------
# 0. Process + target specifications  (generic 180 nm CMOS, VDD = 1.8 V)
# ----------------------------------------------------------------------------
PROC = dict(
    VDD=1.8,          # V
    VTN=0.45, VTP=0.45,   # |Vth|, V
    KPn=270e-6,       # mu_n Cox, A/V^2
    KPp=70e-6,        # mu_p Cox, A/V^2
    lam=0.08,         # channel-length modulation at chosen L (1/V)
    L=0.5e-6,         # channel length used throughout, m
)

SPEC = dict(
    Av_dB_min=60.0,   # open-loop DC gain
    GBW=10e6,         # unity-gain bandwidth, Hz
    PM_min=60.0,      # phase margin, deg
    CL=10e-12,        # load cap, F
    SR=10e6,          # slew rate, V/s  (10 V/us)
    Vov=0.2,          # nominal overdrive target, V
)

# ----------------------------------------------------------------------------
# 1. Compensation cap, tail current (slew), gm of input pair (GBW)
# ----------------------------------------------------------------------------
Cc  = 3e-12                       # 0.3*CL  > 0.22*CL rule for 60 deg PM
I5  = SPEC['SR'] * Cc             # tail current from SR = I5/Cc
I1  = I5 / 2.0                    # per-branch input current
gm1 = 2*np.pi*SPEC['GBW'] * Cc    # from GBW = gm1/Cc

# ----------------------------------------------------------------------------
# 2. Size input pair M1,M2 (PMOS)   gm = sqrt(2*KPp*(W/L)*I)
# ----------------------------------------------------------------------------
WL1 = gm1**2 / (2*PROC['KPp']*I1)
Vov1 = 2*I1/gm1

# ----------------------------------------------------------------------------
# 3. Mirror load M3,M4 (NMOS) sized for Vov3 = 0.2 V
# ----------------------------------------------------------------------------
Vov3 = SPEC['Vov']
WL3  = 2*I1/(PROC['KPn']*Vov3**2)
gm3  = 2*I1/Vov3

# ----------------------------------------------------------------------------
# 4. Tail source M5 (PMOS) sized for Vov5 = 0.3 V
# ----------------------------------------------------------------------------
Vov5 = 0.3
WL5  = 2*I5/(PROC['KPp']*Vov5**2)

# ----------------------------------------------------------------------------
# 5. Second stage: gm6 for 60 deg PM  ->  p2 = 2.2*GBW  ->  gm6 = 2.2*GBW*CL
# ----------------------------------------------------------------------------
gm6 = 2.2 * (2*np.pi*SPEC['GBW']) * SPEC['CL'] / (2*np.pi)  # keep in S (rad cancels)
gm6 = 2.2 * SPEC['GBW'] * 2*np.pi * SPEC['CL'] / (2*np.pi)  # == 2.2*2pi*GBW*CL/(2pi)
# Cleaner: p2(rad) = gm6/CL, want p2 = 2.2 * wGBW  -> gm6 = 2.2*wGBW*CL
wGBW = 2*np.pi*SPEC['GBW']
gm6  = 2.2 * wGBW * SPEC['CL']

# M6 (NMOS) shares VGS with M3 for zero systematic offset -> Vov6 = Vov3
Vov6 = Vov3
I6   = gm6 * Vov6 / 2.0
WL6  = WL3 * (I6/I1)                  # same VGS, same device type -> ratio = current ratio

# ----------------------------------------------------------------------------
# 6. Second stage load M7 (PMOS), zero systematic offset: WL7/WL5 = I7/I5
# ----------------------------------------------------------------------------
I7  = I6
WL7 = WL5 * (I7/I5)

# ----------------------------------------------------------------------------
# 7. Bias reference M8 (PMOS diode) 1:1 to tail
# ----------------------------------------------------------------------------
Iref = I5
WL8  = WL5

# ----------------------------------------------------------------------------
# 8. Output resistances, gains
# ----------------------------------------------------------------------------
def ro(I):  return 1.0/(PROC['lam']*I)
Rout1 = ro(I1) / 2.0            # ro2 || ro4  (both = 1/(lam*I1))
Rout2 = ro(I6) / 2.0           # ro6 || ro7  (both = 1/(lam*I6))
Av1 = gm1 * Rout1
Av2 = gm6 * Rout2
Av0 = Av1 * Av2
Av0_dB = 20*np.log10(Av0)

# ----------------------------------------------------------------------------
# 9. Poles / zero (compensated)
# ----------------------------------------------------------------------------
wp1 = 1.0/(Rout1 * gm6 * Rout2 * Cc)      # dominant pole (rad/s)
wp2 = gm6 / SPEC['CL']                      # non-dominant pole (rad/s)
wz  = gm6 / Cc                              # RHP zero (rad/s)
fp1, fp2, fz = wp1/2/np.pi, wp2/2/np.pi, wz/2/np.pi
GBW_calc = Av0 * fp1                         # check ~ 10 MHz

# Nulling resistor to move zero (two design points):
Rz_null   = 1.0/gm6                          # zero -> infinity
Rz_cancel = (1.0/gm6)*(1 + SPEC['CL']/Cc)    # LHP zero cancels p2

# ----------------------------------------------------------------------------
# 10. Uncompensated node caps (for the "before" plot)
# ----------------------------------------------------------------------------
C1_uncomp = 0.5e-12                          # parasitic at stage-1 output node
wp1_u = 1.0/(Rout1 * C1_uncomp)
wp2_u = 1.0/(Rout2 * SPEC['CL'])
fp1_u, fp2_u = wp1_u/2/np.pi, wp2_u/2/np.pi

# ----------------------------------------------------------------------------
# 11. Phase margin bookkeeping
# ----------------------------------------------------------------------------
def phase_deg(f, poles_hz, zeros_hz_rhp):
    ph = 0.0
    for p in poles_hz:
        ph -= np.degrees(np.arctan(f/p))
    for z in zeros_hz_rhp:
        ph -= np.degrees(np.arctan(f/z))   # RHP zero adds lag
    return ph

# PM with Miller only (RHP zero present)
PM_miller = 180.0 + phase_deg(SPEC['GBW'], [fp1, fp2], [fz])
# PM with nulling resistor (zero cancels p2)  -> only p1 and a far pole p3
fp3 = 3.0*fp2   # a representative higher-order pole
PM_nulled = 180.0 + phase_deg(SPEC['GBW'], [fp1, fp3], [])

# ----------------------------------------------------------------------------
# 12. Power
# ----------------------------------------------------------------------------
Itot = Iref + I5 + I7
Ptot = PROC['VDD'] * Itot

# ----------------------------------------------------------------------------
# Assemble result dict
# ----------------------------------------------------------------------------
R = dict(
    proc=PROC, spec=SPEC,
    Cc=Cc, I5=I5, I1=I1, gm1=gm1, Vov1=Vov1,
    WL1=WL1, WL3=WL3, gm3=gm3, WL5=WL5, gm6=gm6,
    Vov6=Vov6, I6=I6, WL6=WL6, I7=I7, WL7=WL7, Iref=Iref, WL8=WL8,
    Rout1=Rout1, Rout2=Rout2, Av1=Av1, Av2=Av2, Av0=Av0, Av0_dB=Av0_dB,
    fp1=fp1, fp2=fp2, fz=fz, GBW_calc=GBW_calc,
    Rz_null=Rz_null, Rz_cancel=Rz_cancel,
    fp1_u=fp1_u, fp2_u=fp2_u,
    PM_miller=PM_miller, PM_nulled=PM_nulled,
    Itot=Itot, Ptot=Ptot,
)

def W(wl):  # width in um for chosen L
    return wl*PROC['L']*1e6

if __name__ == "__main__":
    print("="*64)
    print(" TWO-STAGE MILLER OTA  -  DESIGN SUMMARY (180 nm, VDD=1.8 V)")
    print("="*64)
    print(f" Cc  = {Cc*1e12:.2f} pF     CL = {SPEC['CL']*1e12:.0f} pF")
    print(f" I5(tail) = {I5*1e6:.1f} uA   I6=I7 = {I6*1e6:.1f} uA   Iref = {Iref*1e6:.1f} uA")
    print(f" gm1 = {gm1*1e6:.1f} uS    gm6 = {gm6*1e3:.2f} mS")
    print("-"*64)
    print(" Device        W/L      W(um)/L(um)     I(uA)")
    L_um = PROC['L']*1e6
    for name, wl, I in [
        ("M1,M2 (in)", WL1, I1), ("M3,M4 (load)", WL3, I1),
        ("M5 (tail)", WL5, I5), ("M6 (2nd)", WL6, I6),
        ("M7 (2nd ld)", WL7, I7), ("M8 (bias)", WL8, Iref)]:
        print(f" {name:14s} {wl:6.1f}   {W(wl):6.2f}/{L_um:.2f}     {I*1e6:6.1f}")
    print("-"*64)
    print(f" DC gain  Av0 = {Av0_dB:.1f} dB   (Av1={20*np.log10(Av1):.1f} dB, Av2={20*np.log10(Av2):.1f} dB)")
    print(f" fp1 = {fp1/1e3:.2f} kHz   fp2 = {fp2/1e6:.2f} MHz   fz(RHP) = {fz/1e6:.2f} MHz")
    print(f" GBW(check) = {GBW_calc/1e6:.2f} MHz")
    print(f" PM (Miller only)   = {PM_miller:.1f} deg")
    print(f" PM (with Rz null)  = {PM_nulled:.1f} deg")
    print(f" Rz (null zero)     = {Rz_null:.0f} ohm")
    print(f" Rz (cancel p2)     = {Rz_cancel:.0f} ohm")
    print(f" SR = {SPEC['SR']/1e6:.1f} V/us   Power = {Ptot*1e6:.0f} uW")
    print("="*64)

    with open("design_values.json", "w") as f:
        json.dump({k: (v if not isinstance(v, dict) else v)
                   for k, v in R.items()}, f, indent=2, default=float)
    print("wrote design_values.json")
