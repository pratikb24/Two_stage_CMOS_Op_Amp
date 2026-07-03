---
title: "Two-Stage CMOS Op-Amp with Miller Compensation"
subtitle: "Hand Calculations & Design Derivation"
author: "Analog IC Design Portfolio"
date: "180 nm CMOS  |  VDD = 1.8 V"
geometry: margin=2.2cm
fontsize: 11pt
colorlinks: true
header-includes:
  - \usepackage{amsmath}
  - \usepackage{booktabs}
  - \usepackage{siunitx}
  - \renewcommand{\arraystretch}{1.25}
---

# 1. Specifications and process constants

The design follows the classic Allen--Holberg two-stage OTA methodology: a PMOS
differential input pair with an NMOS current-mirror load, driving an
NMOS common-source second stage with a PMOS current-source load, compensated by
a Miller capacitor $C_c$ and a series nulling resistor $R_z$.

| Target | Symbol | Value |
|---|---|---|
| DC open-loop gain | $A_{v0}$ | $\ge 60$ dB |
| Unity-gain bandwidth | $\text{GBW}$ | $10$ MHz |
| Phase margin | $\text{PM}$ | $\ge 60^\circ$ |
| Load capacitance | $C_L$ | $10$ pF |
| Slew rate | $\text{SR}$ | $\ge 10$ V/\textmu s |

**Process (generic 180 nm):**
$\mu_n C_{ox} = \SI{270}{\micro\ampere\per\volt\squared}$,
$\mu_p C_{ox} = \SI{70}{\micro\ampere\per\volt\squared}$,
$|V_{th}| = \SI{0.45}{\volt}$,
$\lambda = \SI{0.08}{\per\volt}$ at $L=\SI{0.5}{\micro\meter}$.

# 2. Compensation capacitor and tail current

For a phase margin of $60^\circ$ the standard rule requires
$C_c > 0.22\,C_L$. Choosing a comfortable $0.3\,C_L$:

$$C_c = 0.3\,C_L = 0.3 \times 10\,\text{pF} = \boxed{3\ \text{pF}}$$

The first-stage slew rate is set by how fast the tail current $I_5$ can charge
$C_c$:

$$\text{SR} = \frac{I_5}{C_c}\ \Rightarrow\
I_5 = \text{SR}\cdot C_c = (10\times10^{6})(3\times10^{-12}) = \boxed{30\ \text{\textmu A}}$$

Each input branch therefore carries $I_1 = I_2 = I_5/2 = \SI{15}{\micro\ampere}$.

# 3. Input pair transconductance from GBW

The unity-gain bandwidth of a Miller-compensated two-stage amplifier is

$$\text{GBW} = \frac{g_{m1}}{C_c}
\ \Rightarrow\
g_{m1} = 2\pi\,\text{GBW}\cdot C_c
= 2\pi(10^{7})(3\times10^{-12}) = \boxed{\SI{188.5}{\micro\siemens}}$$

Sizing the PMOS input pair from $g_m = \sqrt{2\,\mu_p C_{ox}\,(W/L)\,I_D}$:

$$\left(\frac{W}{L}\right)_{1,2}
= \frac{g_{m1}^2}{2\,\mu_p C_{ox}\,I_1}
= \frac{(188.5\times10^{-6})^2}{2(70\times10^{-6})(15\times10^{-6})}
\approx \boxed{17}$$

With $L=\SI{0.5}{\micro\meter}$ this gives $W_{1,2}\approx\SI{8.5}{\micro\meter}$.
The corresponding overdrive is $V_{ov1}=2I_1/g_{m1}\approx\SI{159}{\milli\volt}$.

# 4. Mirror load, tail and bias sizing

**Mirror load M3/M4 (NMOS)** — size for $V_{ov3}=\SI{0.2}{\volt}$:

$$\left(\frac{W}{L}\right)_{3,4}
= \frac{2 I_1}{\mu_n C_{ox}\,V_{ov3}^2}
= \frac{2(15\times10^{-6})}{(270\times10^{-6})(0.2)^2}
\approx \boxed{3},\qquad
g_{m3}=\frac{2 I_1}{V_{ov3}}=\SI{150}{\micro\siemens}$$

**Tail source M5 (PMOS)** — size for $V_{ov5}=\SI{0.3}{\volt}$:

$$\left(\frac{W}{L}\right)_{5}
= \frac{2 I_5}{\mu_p C_{ox}\,V_{ov5}^2}
= \frac{2(30\times10^{-6})}{(70\times10^{-6})(0.3)^2}
\approx \boxed{10}$$

**Bias diode M8** mirrors 1:1 from a $\SI{30}{\micro\ampere}$ reference, so
$(W/L)_8 = (W/L)_5 = 10$.

# 5. Second stage sizing for phase margin

To place the non-dominant pole at $p_2 = 2.2\cdot\omega_{\text{GBW}}$ (the
condition for $\approx 60^\circ$ PM), the second-stage transconductance must be

$$g_{m6} = 2.2\,\omega_{\text{GBW}}\,C_L
= 2.2\,(2\pi\cdot10^{7})(10\times10^{-12})
\approx \boxed{\SI{1.38}{\milli\siemens}}$$

For **zero systematic offset**, M6 shares its gate–source voltage with the
mirror (M3/M4), so $V_{ov6}=V_{ov3}=\SI{0.2}{\volt}$ and

$$I_6 = \tfrac{1}{2}g_{m6}V_{ov6}
= \tfrac{1}{2}(1.38\times10^{-3})(0.2) \approx \boxed{\SI{138}{\micro\ampere}}$$

$$\left(\frac{W}{L}\right)_6
= \left(\frac{W}{L}\right)_3\frac{I_6}{I_3}
= 3\cdot\frac{138}{15} \approx \boxed{26}\quad(W_6\approx\SI{13}{\micro\meter})$$

The PMOS load M7 carries the same $I_7=I_6=\SI{138}{\micro\ampere}$. Zero-offset
mirroring requires $(W/L)_7/(W/L)_5 = I_7/I_5$:

$$\left(\frac{W}{L}\right)_7
= \left(\frac{W}{L}\right)_5\frac{I_7}{I_5}
= 10\cdot\frac{138}{30} \approx \boxed{44}\quad(W_7\approx\SI{22}{\micro\meter})$$

# 6. Open-loop gain

Output resistances (using $r_o = 1/(\lambda I_D)$):

$$R_{o1}=r_{o2}\Vert r_{o4}=\frac{1}{2\lambda I_1}
=\frac{1}{2(0.08)(15\,\text{\textmu A})}\approx \SI{417}{\kilo\ohm}$$

$$R_{o2}=r_{o6}\Vert r_{o7}=\frac{1}{2\lambda I_6}
=\frac{1}{2(0.08)(138\,\text{\textmu A})}\approx \SI{45.3}{\kilo\ohm}$$

Stage gains:

$$A_{v1}=g_{m1}R_{o1}=(188.5\,\text{\textmu S})(417\,\text{k}\Omega)\approx 78.6\ (37.9\,\text{dB})$$
$$A_{v2}=g_{m6}R_{o2}=(1.38\,\text{mS})(45.3\,\text{k}\Omega)\approx 62.6\ (35.9\,\text{dB})$$

$$\boxed{A_{v0}=A_{v1}A_{v2}\approx 4920 \approx \SI{73.8}{\decibel}} \;\ge\; 60\,\text{dB}\ \checkmark$$

# 7. Pole splitting — the Miller effect

Without compensation the two high-impedance nodes sit at similar frequencies,
giving a poor phase margin. Connecting $C_c$ between the input and output of the
inverting second stage makes it appear $\big(1+g_{m6}R_{o2}\big)$ times larger at
the first-stage node (the **Miller multiplication**), pushing the dominant pole
*down* while pushing the second pole *up*:

$$\omega_{p1}\approx\frac{1}{R_{o1}\,g_{m6}R_{o2}\,C_c}
=\frac{1}{(417\text{k})(1.38\text{m})(45.3\text{k})(3\text{p})}
\approx 1.28\times10^{4}\ \text{rad/s}$$

$$\boxed{f_{p1}\approx \SI{2.0}{\kilo\hertz}}$$

$$\omega_{p2}\approx\frac{g_{m6}}{C_L}
=\frac{1.38\times10^{-3}}{10\times10^{-12}}
=1.38\times10^{8}\ \text{rad/s}
\ \Rightarrow\ \boxed{f_{p2}\approx \SI{22}{\mega\hertz}}$$

Sanity check on bandwidth:
$\text{GBW}=A_{v0}\,f_{p1}\approx 4920\times 2.0\,\text{kHz}\approx
\SI{10}{\mega\hertz}$ $\checkmark$ (equivalently $g_{m1}/C_c$).

# 8. The right-half-plane zero and the nulling resistor

The Miller capacitor also creates a feed-forward path that produces a
**right-half-plane (RHP) zero**:

$$\omega_z=\frac{g_{m6}}{C_c}
=\frac{1.38\times10^{-3}}{3\times10^{-12}}
=4.6\times10^{8}\ \text{rad/s}
\ \Rightarrow\ f_z\approx \SI{73}{\mega\hertz}$$

A RHP zero boosts magnitude but subtracts phase — it *degrades* stability. The
fix is a **series nulling resistor** $R_z$, which relocates the zero to

$$\omega_z=\frac{1}{C_c\left(\dfrac{1}{g_{m6}}-R_z\right)}.$$

Two useful design points:

- $R_z = 1/g_{m6} \approx \SI{725}{\ohm}$ pushes the zero to infinity.
- $R_z = \dfrac{1}{g_{m6}}\!\left(1+\dfrac{C_L}{C_c}\right)
= 725\,(1+10/3) \approx \boxed{\SI{3.1}{\kilo\ohm}}$
  places a **left-half-plane** zero exactly on $p_2$, cancelling it.

# 9. Phase margin

With the Miller cap alone (RHP zero present):

$$\text{PM}=180^\circ-\tan^{-1}\!\frac{\text{GBW}}{f_{p1}}
-\tan^{-1}\!\frac{\text{GBW}}{f_{p2}}
-\tan^{-1}\!\frac{\text{GBW}}{f_z}\approx 58^\circ$$

After adding $R_z$ (RHP zero removed, $p_2$ cancelled), the phase lag near the
crossover collapses and

$$\boxed{\text{PM} \approx 66^\circ\text{--}81^\circ}\ \ge 60^\circ\ \checkmark$$

# 10. Slew rate and power

$$\text{SR}=\frac{I_5}{C_c}=\frac{30\,\text{\textmu A}}{3\,\text{pF}}
= \boxed{\SI{10}{\volt\per\micro\second}}\quad
(\text{second stage: } I_7/C_L=\SI{13.8}{\volt\per\micro\second}>\text{SR}\ \checkmark)$$

$$P = V_{DD}\big(I_{\text{ref}}+I_5+I_7\big)
= 1.8\,(30+30+138)\,\text{\textmu A}
\approx \boxed{\SI{357}{\micro\watt}}$$

# 11. Summary

| Quantity | Symbol | Result |
|---|---|---|
| DC gain | $A_{v0}$ | 73.8 dB |
| Unity-gain BW | GBW | 10.0 MHz |
| Dominant pole | $f_{p1}$ | 2.0 kHz |
| Non-dominant pole | $f_{p2}$ | 22 MHz |
| RHP zero (no $R_z$) | $f_z$ | 73 MHz |
| Miller cap | $C_c$ | 3 pF |
| Nulling resistor | $R_z$ | 3.1 k$\Omega$ |
| Phase margin (final) | PM | $\ge 66^\circ$ |
| Slew rate | SR | 10 V/\textmu s |
| Power | $P$ | 0.36 mW |

These hand-calculated targets are the reference against which the Cadence
Spectre simulations (see `../results/`) are verified.
