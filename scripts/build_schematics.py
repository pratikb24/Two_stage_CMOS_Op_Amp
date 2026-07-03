"""Generate all schematic PDFs for the two-stage Miller op-amp project."""
import os, sys
import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from schematic_lib import (new_canvas, wire, dot, label, mos, cap, resistor,
                           isource, vdd_rail, gnd, term, title_block, route,
                           COL, FONT)

OUT = os.path.join(ROOT, "schematics")
os.makedirs(os.path.join(OUT, "testbenches"), exist_ok=True)
os.makedirs(OUT + "/testbenches", exist_ok=True)


# ==========================================================================
def core_opamp():
    fig, ax = new_canvas(10.5, 9)
    VDD, GND = 8.6, 0.85
    vdd_rail(ax, 1.4, 11.4, VDD)

    # ---------- tail current source M5 (PMOS) ----------
    m5 = mos(ax, 4.5, 7.5, kind="p", name="M5", w_over_l="5/0.5", gate_side="left")
    wire(ax, [m5["s"], (m5["s"][0], VDD)]); dot(ax, (m5["s"][0], VDD))

    # tail bus
    tail_y = m5["d"][1] - 0.3
    wire(ax, [m5["d"], (m5["d"][0], tail_y)]); dot(ax, (m5["d"][0], tail_y))
    label(ax, (m5["d"][0], tail_y+0.17), "tail", size=FONT-2, color="#777")

    # ---------- input pair M1, M2 (PMOS) ----------
    m1 = mos(ax, 3.3, 5.2, kind="p", name="M1", w_over_l="8.5/0.5", gate_side="left")
    m2 = mos(ax, 5.7, 5.2, kind="p", name="M2", w_over_l="8.5/0.5", gate_side="right")
    wire(ax, [(m1["s"][0], tail_y), (m2["s"][0], tail_y)])       # tail bus span
    wire(ax, [m1["s"], (m1["s"][0], tail_y)])
    wire(ax, [m2["s"], (m2["s"][0], tail_y)])

    # inputs
    term(ax, (1.5, 5.2), ""); route(ax, (1.5, 5.2), m1["g"], "h")
    label(ax, (1.32, 5.2), "V$_{in+}$", ha="right", weight="bold")
    term(ax, (7.5, 5.2), ""); route(ax, (7.5, 5.2), m2["g"], "h")
    label(ax, (7.68, 5.2), "V$_{in-}$", ha="left", weight="bold")

    # ---------- mirror load M3, M4 (NMOS) ----------
    m3 = mos(ax, 3.3, 2.15, kind="n", name="M3", w_over_l="1.5/0.5", gate_side="left")
    m4 = mos(ax, 5.7, 2.15, kind="n", name="M4", w_over_l="1.5/0.5", gate_side="right")
    wire(ax, [m3["s"], (m3["s"][0], GND)])
    wire(ax, [m4["s"], (m4["s"][0], GND)])
    wire(ax, [(2.9, GND), (10.8, GND)]); gnd(ax, 6.9, GND)

    # input-pair drains -> mirror drains (aligned x -> vertical)
    wire(ax, [m1["d"], m3["d"]]); dot(ax, m3["d"])
    wire(ax, [m2["d"], m4["d"]]); dot(ax, m4["d"])

    # M3 diode: gate tied up to its own drain
    diode_x = 2.3
    wire(ax, [m3["g"], (diode_x, m3["g"][1])])
    wire(ax, [(diode_x, m3["g"][1]), (diode_x, m3["d"][1])])
    wire(ax, [(diode_x, m3["d"][1]), m3["d"]]); dot(ax, (diode_x, m3["d"][1]))
    # mirror bus to M4 gate (routed below devices)
    busy = GND + 0.55
    wire(ax, [(diode_x, m3["g"][1]), (diode_x, busy)]); dot(ax, (diode_x, m3["g"][1]))
    wire(ax, [(diode_x, busy), (6.85, busy)])
    wire(ax, [(6.85, busy), (6.85, m4["g"][1])])
    wire(ax, [(6.85, m4["g"][1]), m4["g"]])

    # first-stage output vo1 = M2 drain / M4 drain
    vo1 = (m4["d"][0], 3.5); dot(ax, vo1)
    label(ax, (vo1[0]-0.15, vo1[1]+0.22), "v$_{o1}$", ha="right",
          weight="bold", color="#b00")

    # ================= SECOND STAGE =================
    m7 = mos(ax, 9.3, 7.5, kind="p", name="M7", w_over_l="22/0.5", gate_side="right")
    m6 = mos(ax, 9.3, 2.15, kind="n", name="M6", w_over_l="13/0.5", gate_side="left")
    wire(ax, [m7["s"], (m7["s"][0], VDD)]); dot(ax, (m7["s"][0], VDD))
    wire(ax, [m6["s"], (m6["s"][0], GND)])

    # vout bus
    vout_y = 4.7
    route(ax, m7["d"], (9.3, vout_y), "v")
    route(ax, m6["d"], (9.3, vout_y), "v")
    vout = (9.3, vout_y); dot(ax, vout)
    label(ax, (vout[0]-0.12, vout[1]+0.24), "v$_{out}$", ha="right",
          weight="bold", color="#b00")

    # M6 gate <- vo1
    route(ax, vo1, m6["g"], "h")

    # ---------- bias Vb to M5 & M7 gates (from bias network) ----------
    term(ax, (1.5, 7.5), ""); route(ax, (1.5, 7.5), m5["g"], "h")
    label(ax, (1.32, 7.5), "V$_b$", ha="right", weight="bold", color="#06c")
    term(ax, (11.5, 7.5), ""); route(ax, (11.5, 7.5), m7["g"], "h")
    label(ax, (11.68, 7.5), "V$_b$", ha="left", weight="bold", color="#06c")

    # ---------- Miller network: Rz + Cc between vo1 and vout ----------
    br = 6.2
    wire(ax, [vo1, (vo1[0], br)])
    rz1, rz2 = resistor(ax, 6.7, br, horiz=True, name="R$_z$", val="3.1 k$\\Omega$")
    wire(ax, [(vo1[0], br), rz1])
    cc1, cc2 = cap(ax, 8.15, br, horiz=True, name="C$_c$", val="3 pF")
    wire(ax, [rz2, cc1])
    wire(ax, [cc2, (8.8, br)]); wire(ax, [(8.8, br), (8.8, vout_y)])
    wire(ax, [(8.8, vout_y), vout]); dot(ax, (8.8, vout_y))

    # ---------- load capacitor CL ----------
    wire(ax, [vout, (10.5, vout_y)]); dot(ax, (10.5, vout_y))
    cl1, cl2 = cap(ax, 10.5, vout_y-1.0, horiz=False, name="C$_L$", val="10 pF")
    wire(ax, [(10.5, vout_y), cl1]); wire(ax, [cl2, (10.5, GND)]); dot(ax, (10.5, GND))

    # ---------- output port ----------
    term(ax, (11.6, vout_y), "")
    wire(ax, [(10.5, vout_y), (11.6, vout_y)])
    label(ax, (11.72, vout_y), "V$_{out}$", ha="left", weight="bold")

    ax.set_xlim(0.3, 12.7); ax.set_ylim(-0.5, 9.4)
    title_block(ax, "Two-Stage CMOS Op-Amp - Core Schematic",
                "Miller-compensated OTA  (PMOS input pair, NMOS mirror load, Rz-nulled)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/core_opamp_schematic.pdf", bbox_inches="tight")
    plt.close(fig)
    print("core_opamp_schematic.pdf")


# ==========================================================================
def bias_network():
    from schematic_lib import opamp
    fig, ax = new_canvas(7, 8)
    VDD, GND = 7.4, 0.9
    vdd_rail(ax, 1.0, 6.4, VDD)

    # --- reference branch: R -> diode NMOS M9 sets Iref ---
    rt1, rt2 = resistor(ax, 2.2, 6.2, horiz=False, name="R$_{set}$", val="~90 k$\\Omega$")
    wire(ax, [(2.2, VDD), rt1])
    m9 = mos(ax, 2.2, 4.0, kind="n", name="M9", w_over_l="4/0.5", gate_side="right")
    wire(ax, [rt2, m9["d"]])
    # M9 diode connect
    wire(ax, [m9["g"], (2.95, m9["g"][1])])
    wire(ax, [(2.95, m9["g"][1]), (2.95, m9["d"][1])])
    wire(ax, [(2.95, m9["d"][1]), m9["d"]]); dot(ax, m9["d"])
    wire(ax, [m9["s"], (m9["s"][0], GND)])
    label(ax, (2.2, 5.0), "I$_{ref}$", ha="right", color="#b00", weight="bold")

    # --- mirror NMOS M10 copies Iref, pulls from PMOS diode M8 ---
    m10 = mos(ax, 4.4, 4.0, kind="n", name="M10", w_over_l="4/0.5", gate_side="left")
    wire(ax, [m10["s"], (m10["s"][0], GND)])
    # tie M10 gate to M9 gate node
    wire(ax, [m10["g"], (2.95, m10["g"][1])]); 
    route(ax, (2.95, m9["g"][1]), m10["g"], "v")
    dot(ax, (2.95, m9["g"][1]))

    # --- PMOS diode M8 establishes Vb ---
    m8 = mos(ax, 4.4, 6.0, kind="p", name="M8", w_over_l="5/0.5", gate_side="right")
    wire(ax, [m8["s"], (m8["s"][0], VDD)]); dot(ax, (m8["s"][0], VDD))
    wire(ax, [m8["d"], m10["d"]]); dot(ax, m10["d"])
    # M8 diode connect (gate<->drain) = Vb
    vb_x = 5.3
    wire(ax, [m8["g"], (vb_x, m8["g"][1])])
    wire(ax, [(vb_x, m8["g"][1]), (vb_x, m8["d"][1])])
    wire(ax, [(vb_x, m8["d"][1]), m8["d"]]); dot(ax, (vb_x, m8["d"][1]))

    # GND rail
    wire(ax, [(1.6, GND), (6.0, GND)]); gnd(ax, 3.3, GND)

    # Vb output port
    term(ax, (6.2, m8["g"][1]), "")
    wire(ax, [(vb_x, m8["g"][1]), (6.2, m8["g"][1])]); dot(ax,(vb_x,m8["g"][1]))
    label(ax, (6.32, m8["g"][1]), "V$_b$", ha="left", weight="bold", color="#06c")
    label(ax, (5.0, m8["g"][1]+0.5), "to M5, M7 gates", size=FONT-2, color="#06c")

    ax.text(0.2, 0.2,
            "Mirror ratios (ref = 30 uA):  M5 1:1 -> 30 uA   |   "
            "M7 1:4.4 -> 138 uA",
            fontsize=FONT-1.5, color="#333")

    ax.set_xlim(0.0, 7.2); ax.set_ylim(-0.6, 8.0)
    title_block(ax, "Bias Network - Reference & Mirror",
                "Sets V$_b$ for the tail (M5) and second-stage load (M7)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/bias_network.pdf", bbox_inches="tight")
    plt.close(fig)
    print("bias_network.pdf")


# ==========================================================================
def _opamp_block(ax, cx, cy, size=1.3):
    from schematic_lib import opamp
    return opamp(ax, cx, cy, size=size, label_txt="A$_v$")


def tb_ac_response():
    fig, ax = new_canvas(8, 5.6)
    A = _opamp_block(ax, 5.0, 3.0, size=1.3)

    # + input: AC source (dc bias + ac 1V)
    wire(ax, [A["inp"], (3.2, A["inp"][1])])
    ax.add_patch(plt.Circle((3.2, A["inp"][1]-0.0), 0.0))
    # AC source symbol
    from matplotlib.patches import Circle
    src = (2.6, A["inp"][1])
    ax.add_patch(Circle(src, 0.34, fill=False, edgecolor=COL, lw=1.6))
    ax.plot([src[0]-0.16, src[0]+0.16],
            [src[1], src[1]], color=COL, lw=0)  # placeholder
    import numpy as np
    tt = np.linspace(-0.16, 0.16, 40)
    ax.plot(src[0]+tt, src[1]+0.12*np.sin(tt/0.16*np.pi*2), color=COL, lw=1.3)
    wire(ax, [(src[0]+0.34, src[1]), (3.2, A["inp"][1])])
    wire(ax, [(src[0], src[1]-0.34), (src[0], 0.9)])
    label(ax, (src[0]-0.5, src[1]+0.1), "V$_{in}$", ha="right", weight="bold")
    label(ax, (src[0]-0.5, src[1]-0.25), "dc=0.9 ac=1", ha="right",
          size=FONT-2.5, color="#555")

    # - input: tied to a DC common-mode (here: to output for stable bias) OR ground
    wire(ax, [A["inn"], (3.6, A["inn"][1])])
    wire(ax, [(3.6, A["inn"][1]), (3.6, 0.9)])
    dot(ax, (3.6, A["inn"][1]-0.0))
    label(ax, (3.35, A["inn"][1]-0.25), "V$_{CM}$=0.9V", ha="right",
          size=FONT-2.5, color="#555")

    # output + load
    wire(ax, [A["out"], (7.0, A["out"][1])]); dot(ax, (6.4, A["out"][1]))
    cl1, cl2 = cap(ax, 6.4, A["out"][1]-1.0, horiz=False, name="C$_L$", val="10 pF")
    wire(ax, [(6.4, A["out"][1]), cl1]); wire(ax, [cl2, (6.4, 0.9)])
    term(ax, (7.2, A["out"][1]), "")
    label(ax, (7.32, A["out"][1]), "V$_{out}$", ha="left", weight="bold")

    # ground bus
    wire(ax, [(2.2, 0.9), (6.9, 0.9)]); gnd(ax, 4.6, 0.9)

    ax.text(0.2, 0.05,
            "AC analysis:  sweep 1 Hz -> 1 GHz.  Measure dB20(V$_{out}$) and "
            "phase(V$_{out}$)\n-> DC gain, GBW (0 dB crossing) and phase margin.",
            fontsize=FONT-1, color="#222")
    ax.set_xlim(1.4, 8.0); ax.set_ylim(0.0, 4.8)
    title_block(ax, "Testbench - Open-Loop AC Response",
                "Gain / Bandwidth / Phase-Margin measurement")
    fig.tight_layout()
    fig.savefig(f"{OUT}/testbenches/tb_ac_response.pdf", bbox_inches="tight")
    plt.close(fig)
    print("tb_ac_response.pdf")


def tb_slew_rate():
    import numpy as np
    from matplotlib.patches import Circle
    fig, ax = new_canvas(8, 5.6)
    A = _opamp_block(ax, 5.0, 3.0, size=1.3)

    # unity-gain feedback: output -> - input
    wire(ax, [A["out"], (6.6, A["out"][1])]); dot(ax, (6.6, A["out"][1]))
    wire(ax, [(6.6, A["out"][1]), (6.6, 4.5)])
    wire(ax, [(6.6, 4.5), (3.4, 4.5)])
    wire(ax, [(3.4, 4.5), (3.4, A["inn"][1])])
    wire(ax, [(3.4, A["inn"][1]), A["inn"]])
    label(ax, (4.9, 4.62), "unity-gain feedback", size=FONT-2, color="#555")

    # + input: pulse source
    src = (2.7, A["inp"][1])
    ax.add_patch(Circle(src, 0.34, fill=False, edgecolor=COL, lw=1.6))
    ax.plot([src[0]-0.16, src[0]-0.16, src[0]+0.0, src[0]+0.0, src[0]+0.16],
            [src[1]-0.12, src[1]+0.12, src[1]+0.12, src[1]-0.12, src[1]-0.12],
            color=COL, lw=1.2)
    wire(ax, [(src[0]+0.34, src[1]), A["inp"]])
    wire(ax, [(src[0], src[1]-0.34), (src[0], 0.9)])
    label(ax, (src[0]-0.5, src[1]+0.12), "V$_{in}$", ha="right", weight="bold")
    label(ax, (src[0]-0.5, src[1]-0.28), "pulse 0->1V", ha="right",
          size=FONT-2.5, color="#555")

    # load
    dot(ax, (6.6, A["out"][1]))
    cl1, cl2 = cap(ax, 7.1, A["out"][1]-1.0, horiz=False, name="C$_L$", val="10 pF")
    wire(ax, [(6.6, A["out"][1]), (7.1, A["out"][1])]); wire(ax, [(7.1, A["out"][1]), cl1])
    wire(ax, [cl2, (7.1, 0.9)])
    term(ax, (7.8, A["out"][1]), "")
    wire(ax, [(6.6, A["out"][1]), (7.8, A["out"][1])])
    label(ax, (7.92, A["out"][1]), "V$_{out}$", ha="left", weight="bold")

    wire(ax, [(2.3, 0.9), (7.4, 0.9)]); gnd(ax, 4.6, 0.9)
    ax.text(0.2, 0.05,
            "Transient analysis: apply a large step; measure dV$_{out}$/dt on the "
            "rising and\nfalling edges  ->  slew rate (target >= 10 V/us).",
            fontsize=FONT-1, color="#222")
    ax.set_xlim(1.4, 8.6); ax.set_ylim(0.0, 5.0)
    title_block(ax, "Testbench - Slew Rate",
                "Unity-gain buffer, large-signal step")
    fig.tight_layout()
    fig.savefig(f"{OUT}/testbenches/tb_slew_rate.pdf", bbox_inches="tight")
    plt.close(fig)
    print("tb_slew_rate.pdf")


def tb_cmrr_psrr():
    import numpy as np
    from matplotlib.patches import Circle
    fig, ax = new_canvas(8.4, 5.8)
    A = _opamp_block(ax, 5.2, 3.0, size=1.3)

    # unity feedback (buffer) for CMRR/PSRR small-signal method
    wire(ax, [A["out"], (6.8, A["out"][1])]); dot(ax, (6.8, A["out"][1]))
    wire(ax, [(6.8, A["out"][1]), (6.8, 4.6)])
    wire(ax, [(6.8, 4.6), (3.5, 4.6)])
    wire(ax, [(3.5, 4.6), (3.5, A["inn"][1])]); wire(ax, [(3.5, A["inn"][1]), A["inn"]])

    # common-mode AC source on + input (for CMRR)
    src = (2.8, A["inp"][1])
    ax.add_patch(Circle(src, 0.34, fill=False, edgecolor=COL, lw=1.6))
    tt = np.linspace(-0.16, 0.16, 40)
    ax.plot(src[0]+tt, src[1]+0.12*np.sin(tt/0.16*np.pi*2), color=COL, lw=1.3)
    wire(ax, [(src[0]+0.34, src[1]), A["inp"]])
    wire(ax, [(src[0], src[1]-0.34), (src[0], 0.9)])
    label(ax, (src[0]-0.5, src[1]+0.12), "V$_{cm}$", ha="right", weight="bold")

    # VDD with AC ripple source (for PSRR)
    vdd_y = 4.9
    wire(ax, [A["vdd"], (A["vdd"][0], vdd_y)])
    ax.add_patch(Circle((A["vdd"][0], vdd_y+0.34), 0.34, fill=False, edgecolor=COL, lw=1.6))
    ax.plot(A["vdd"][0]+tt, vdd_y+0.34+0.12*np.sin(tt/0.16*np.pi*2), color=COL, lw=1.3)
    wire(ax, [(A["vdd"][0], vdd_y+0.68), (A["vdd"][0], 5.7)])
    vdd_rail(ax, 3.6, 6.8, 5.7)
    label(ax, (A["vdd"][0]+0.5, vdd_y+0.34), "v$_{dd,ac}$", ha="left",
          size=FONT-2, color="#b00")

    # output port
    term(ax, (7.6, A["out"][1]), "")
    wire(ax, [(6.8, A["out"][1]), (7.6, A["out"][1])])
    label(ax, (7.72, A["out"][1]), "V$_{out}$", ha="left", weight="bold")

    wire(ax, [(2.4, 0.9), (7.0, 0.9)]); gnd(ax, 4.6, 0.9)
    ax.text(0.15, 0.02,
            "CMRR = A$_{dm}$/A$_{cm}$ (drive both inputs common-mode).   "
            "PSRR = A$_{dm}$/A$_{vdd}$ (inject v$_{dd,ac}$).\n"
            "Both extracted from AC sweeps of V$_{out}$; target >= 60 dB.",
            fontsize=FONT-1.5, color="#222")
    ax.set_xlim(1.6, 8.4); ax.set_ylim(0.0, 6.2)
    title_block(ax, "Testbench - CMRR / PSRR",
                "Common-mode & supply-rejection measurement")
    fig.tight_layout()
    fig.savefig(f"{OUT}/testbenches/tb_cmrr_psrr.pdf", bbox_inches="tight")
    plt.close(fig)
    print("tb_cmrr_psrr.pdf")


if __name__ == "__main__":
    core_opamp()
    bias_network()
    tb_ac_response()
    tb_slew_rate()
    tb_cmrr_psrr()
