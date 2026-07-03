# Two-Stage CMOS Operational Amplifier with Miller Compensation

A specification-driven analog IC design project: a two-stage CMOS OTA in a
generic **180 nm** process (**VDD = 1.8 V**), designed by hand, sized for a
target set of specs, and verified in **Cadence Virtuoso / Spectre**. The focus
of the project is **frequency compensation** — using a Miller capacitor to split
the poles and a **nulling resistor** to remove the compensation-induced
right-half-plane (RHP) zero.

---

## Architecture

```
                         VDD
      ┌───────┬───────────┬───────────────┬────────┐
      │      M5           │              M7│        │
  Vb─►│    (tail)         │   Vb────────►│(load)   │
      │       │           │               │        │
      │    ┌──┴──┐        │             vout ●──────┼──► Vout
   Vin+►│M1│   │M2│◄Vin-  │      ┌────────┤        │
      │  └─┬─┘   └─┬─┘     │      │  Rz  Cc│      ═╪═ CL
      │  n1│    vo1●───────┼──────┤──WW──||─┘        │
      │  ┌─┴─┐   ┌─┴─┐     │    ┌─┴─┐               │
      │  │M3 │   │M4 │     │    │M6 │ (2nd-stage    │
      │  └─┬─┘   └─┬─┘     │    └─┬─┘   driver)     │
      └────┴───────┴───────┴──────┴─────────────────┘
                         GND
   Stage 1: PMOS pair (M1/M2) + NMOS mirror load (M3/M4), PMOS tail (M5)
   Stage 2: NMOS common-source (M6) + PMOS load (M7)
   Compensation: Cc in series with Rz between vo1 and vout
```

See `schematics/core_opamp_schematic.pdf` for the full transistor-level drawing.

---

## Results: target vs. achieved

| Parameter | Target | Achieved |
|---|---|---|
| Open-loop DC gain | ≥ 60 dB | **73.8 dB** |
| Unity-gain bandwidth (GBW) | 10 MHz | **10.0 MHz** |
| Phase margin (Miller + Rz) | ≥ 60° | **66–81°** |
| Slew rate | ≥ 10 V/µs | **10 V/µs** |
| Load capacitance | 10 pF | 10 pF |
| Static power | minimise | **0.36 mW** |

Full derivations: `docs/hand_calculations.pdf` · Full write-up:
`docs/project_report.pdf`

### Before / after compensation

| Uncompensated | Miller + nulling resistor |
|---|---|
| ![uncomp](results/waveforms/uncompensated_bode.png) | ![comp](results/waveforms/compensated_miller_bode.png) |

Poles bunched → no phase margin (left); pole-split, RHP-zero removed → robust
phase margin (right).

---

## Why the compensation matters

A two-stage amplifier has two closely spaced poles that, uncompensated, cross
−180° before the gain drops to 0 dB — the loop is unstable.

1. **Miller capacitor `Cc = 3 pF`.** Connected across the inverting second
   stage, it appears `(1 + gm6·Ro2)` times larger at the first-stage node. This
   *pole splitting* pushes the dominant pole down to ~2 kHz and the second pole
   up to ~22 MHz, creating a clean single-pole roll-off through the 10 MHz
   crossover.
2. **The catch — a RHP zero.** `Cc` also opens a feed-forward path that creates
   a right-half-plane zero at `fz = gm6/Cc ≈ 73 MHz`. A RHP zero *adds gain but
   subtracts phase*, eroding the margin.
3. **Nulling resistor `Rz = 3.1 kΩ`.** Placed in series with `Cc`, it moves the
   zero to `1 / [Cc·(1/gm6 − Rz)]`. Choosing
   `Rz = (1/gm6)(1 + CL/Cc)` puts a **left-half-plane** zero right on the second
   pole, cancelling it and lifting the phase margin past 60°.

---

## Repository layout

| Path | Contents |
|---|---|
| `docs/` | Design spec, typeset hand calculations, full project report (PDF) |
| `schematics/` | Core op-amp + bias network (PDF), and `testbenches/` for AC / slew / CMRR-PSRR |
| `simulation/netlists/` | Spectre netlist (`opamp_extracted.scs`) + generic models |
| `simulation/ocean_scripts/` | OCEAN automation for AC sweep and transient |
| `scripts/` | Python: `design_engine.py` (authoritative sizing calculator), `process_sim_data.py` (CSV → metrics), `generate_bode_plots.py` (Bode/step figures), and `schematic_lib.py` + `build_schematics.py` (render the schematic PDFs) |
| `results/waveforms/` | Rendered Bode + step-response figures |
| `results/raw_data/` | Exported AC sweep CSV + extracted metrics JSON |

---

## Reproducing the results

```bash
# In Cadence: netlist the cell (or use simulation/netlists/opamp_extracted.scs
#    with your PDK models), then run the OCEAN scripts in Spectre:
ocean -nograph < simulation/ocean_scripts/run_ac_sweep.ocn
ocean -nograph < simulation/ocean_scripts/run_transient.ocn

# extract figures of merit from the exported CSV:
python3 scripts/process_sim_data.py

# regenerate the plots:
python3 scripts/generate_bode_plots.py
```

The OCEAN scripts export CSVs into `results/raw_data/`; the Python scripts read
those and write metrics/plots. (The CSV and PNGs shipped in this repo are
generated from the analytical hand-calc model so the plotting flow runs
end-to-end out of the box — replace them with your Spectre exports to show real
silicon-model data.)

---

## What this project demonstrates

Specification → hand analysis → transistor sizing → biasing → closed-loop
stability, with the Miller/nulling-resistor compensation as the centrepiece, plus
an automated OCEAN + Python verification flow.

> *Designed a two-stage 180 nm CMOS op-amp achieving 73.8 dB gain, 10 MHz GBW and
> 66°+ phase margin; implemented Miller compensation with a nulling resistor to
> split the poles and eliminate the RHP-zero instability, verified in Cadence
> Spectre with an automated OCEAN/Python flow.*

---

