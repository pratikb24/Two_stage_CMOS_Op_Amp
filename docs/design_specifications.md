# Design Specifications

**Project:** Two-Stage CMOS Operational Amplifier with Miller Compensation
**Technology:** Generic 180 nm CMOS
**Supply:** VDD = 1.8 V (single supply, VSS = 0 V)
**Common-mode input:** 0.9 V (VDD/2)

---

## 1. Target vs. Achieved

| Parameter | Symbol | Target | Achieved (design) | Status |
|---|---|---|---|---|
| Open-loop DC gain | A_v0 | ≥ 60 dB | **73.8 dB** | ✅ |
| Unity-gain bandwidth | GBW | 10 MHz | **10.0 MHz** | ✅ |
| Phase margin (Miller only) | PM | ≥ 60° | **~58°** | ⚠️ near |
| Phase margin (Miller + Rz) | PM | ≥ 60° | **~66–81°** | ✅ |
| Gain margin | GM | ≥ 10 dB | **> 15 dB** | ✅ |
| Slew rate | SR | ≥ 10 V/µs | **10 V/µs** | ✅ |
| Load capacitance | C_L | 10 pF | 10 pF | — |
| CMRR (DC) | — | ≥ 60 dB | target | — |
| PSRR (DC) | — | ≥ 60 dB | target | — |
| Static power | P | minimise | **~0.36 mW** | ✅ |

> The Miller-only phase margin lands slightly under 60° because the
> compensation capacitor introduces a right-half-plane (RHP) zero. Adding the
> series **nulling resistor R_z** removes that zero and lifts the phase margin
> comfortably past the target — this is the headline result of the project.

---

## 2. Compensation network

| Component | Value | Purpose |
|---|---|---|
| Miller cap C_c | 3 pF (0.3·C_L) | Splits the two poles apart |
| Nulling resistor R_z | 3.1 kΩ | Moves the RHP zero to the LHP to cancel p2 |

---

## 3. Transistor sizing (L = 0.5 µm throughout)

| Device | Role | W/L | W (µm) | Drain current |
|---|---|---|---|---|
| M1, M2 | PMOS input pair | 17 | 8.5 | 15 µA each |
| M3, M4 | NMOS mirror load | 3 | 1.5 | 15 µA each |
| M5 | PMOS tail source | 10 | 5.0 | 30 µA |
| M6 | NMOS 2nd-stage driver | 26 | 13.0 | 138 µA |
| M7 | PMOS 2nd-stage load | 44 | 22.0 | 138 µA |
| M8 | PMOS bias diode | 10 | 5.0 | 30 µA (ref) |

---

## 4. Process constants used in hand calculations

| Constant | Symbol | Value |
|---|---|---|
| NMOS transconductance param | µ_n·C_ox | 270 µA/V² |
| PMOS transconductance param | µ_p·C_ox | 70 µA/V² |
| Threshold voltage | \|V_th\| | 0.45 V |
| Channel-length modulation | λ | 0.08 V⁻¹ (at L = 0.5 µm) |

These are representative first-order values for a generic 180 nm node. Re-run
the hand calculations with your PDK's extracted parameters before committing to
silicon.
