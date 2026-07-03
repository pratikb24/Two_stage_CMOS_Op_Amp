"""
schematic_lib.py  -  minimal transistor-level schematic primitives on matplotlib.
Coordinates are in abstract grid units. Each MOS returns its terminal points.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyArrow
import numpy as np

LW = 1.6
COL = "#1a1a1a"
FONT = 10


def new_canvas(w=9, h=11):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def wire(ax, pts, color=COL, lw=LW):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.add_line(Line2D(xs, ys, color=color, lw=lw, solid_capstyle="round"))


def dot(ax, p, r=0.055, color=COL):
    ax.add_patch(Circle(p, r, color=color, zorder=5))


def route(ax, p, q, first="h", color=COL, lw=LW):
    """Orthogonal (Manhattan) route from p to q via one corner."""
    if first == "h":
        corner = (q[0], p[1])
    else:
        corner = (p[0], q[1])
    wire(ax, [p, corner, q], color=color, lw=lw)
    return corner


def label(ax, p, text, dx=0, dy=0, ha="center", va="center",
          size=FONT, color=COL, weight="normal", style="normal"):
    ax.text(p[0]+dx, p[1]+dy, text, ha=ha, va=va, fontsize=size,
            color=color, weight=weight, style=style, zorder=6)


def mos(ax, cx, cy, kind="n", name="", w_over_l="", flip=False, gate_side="left"):
    """
    Draw a vertical MOSFET. Drain on top, source on bottom.
    cx,cy = centre of the channel bar.
    flip=True mirrors drain<->source (source on top) for PMOS-style pull-ups.
    Returns dict with 'g','d','s' terminal coordinates.
    """
    s = 1.0                      # scale
    gh = 0.5*s                   # half gate/channel height
    chx = cx                     # channel bar x
    gbx = cx - 0.22*s            # gate bar x
    lead = 0.5*s                 # gate lead length
    tap = 0.4*s                  # d/s horizontal tap length
    ext = 0.45*s                 # d/s vertical terminal extension

    mirror = -1 if gate_side == "right" else 1
    gbx = cx - mirror*0.22*s
    gate_lead_x = gbx - mirror*lead
    tap_x = cx + mirror*tap

    # channel bar (three-segment enhancement style)
    for yy0, yy1 in [(-gh, -0.18*s), (-0.1*s, 0.1*s), (0.18*s, gh)]:
        wire(ax, [(chx, cy+yy0), (chx, cy+yy1)])
    # gate bar
    wire(ax, [(gbx, cy-gh*0.9), (gbx, cy+gh*0.9)])
    # gate lead
    wire(ax, [(gbx, cy), (gate_lead_x, cy)])

    # drain (top) and source (bottom) taps + terminals
    d_y, s_y = (cy+gh, cy-gh)
    if flip:
        d_y, s_y = s_y, d_y
    # top terminal
    wire(ax, [(chx, cy+gh), (tap_x, cy+gh)])
    wire(ax, [(tap_x, cy+gh), (tap_x, cy+gh+ext)])
    # bottom terminal
    wire(ax, [(chx, cy-gh), (tap_x, cy-gh)])
    wire(ax, [(tap_x, cy-gh), (tap_x, cy-gh-ext)])

    top_term = (tap_x, cy+gh+ext)
    bot_term = (tap_x, cy-gh-ext)
    gate_term = (gate_lead_x, cy)

    # source arrow (indicates device type). NMOS arrow points INTO channel.
    if flip:   # PMOS pull-up: source on top
        src_y = cy+gh
        arr_dir = 1  # will set below
    # place arrow on the source tap
    if kind == "n":
        # NMOS: source at bottom, arrow pointing toward channel (up-left)
        ax_ = tap_x - mirror*0.0
        ay0 = cy-gh
        ax.add_patch(FancyArrow(tap_x, cy-gh, -mirror*0.0, 0.0,
                     width=0, head_width=0, head_length=0))
        # draw a small filled arrow on bottom tap pointing to channel
        ax.annotate("", xy=(chx+mirror*0.02, cy-gh), xytext=(tap_x-mirror*0.14, cy-gh),
                    arrowprops=dict(arrowstyle="-|>", color=COL, lw=1.3,
                                    mutation_scale=11))
        d_term, s_term = top_term, bot_term
    else:
        # PMOS: source at top, arrow pointing away from channel (out)
        ax.annotate("", xy=(tap_x-mirror*0.14, cy+gh), xytext=(chx+mirror*0.02, cy+gh),
                    arrowprops=dict(arrowstyle="-|>", color=COL, lw=1.3,
                                    mutation_scale=11))
        d_term, s_term = bot_term, top_term   # PMOS drain at bottom

    # labels
    nm_x = chx + mirror*0.30
    if name:
        label(ax, (nm_x, cy+0.16), name, ha="left" if mirror>0 else "right",
              size=FONT+0.5, weight="bold")
    if w_over_l:
        label(ax, (nm_x, cy-0.16), w_over_l, ha="left" if mirror>0 else "right",
              size=FONT-2.0, color="#555")

    return {"g": gate_term, "d": d_term, "s": s_term,
            "top": top_term, "bot": bot_term}


def cap(ax, x, y, horiz=False, name="", val=""):
    """Capacitor centred at (x,y). Returns two terminals."""
    g = 0.12
    if not horiz:
        wire(ax, [(x-0.28, y+g), (x+0.28, y+g)])
        wire(ax, [(x-0.28, y-g), (x+0.28, y-g)])
        t1, t2 = (x, y+g+0.0), (x, y-g)
        wire(ax, [(x, y+g), (x, y+0.5)]); wire(ax, [(x, y-g), (x, y-0.5)])
        t1, t2 = (x, y+0.5), (x, y-0.5)
        if name: label(ax, (x+0.34, y+g), name, ha="left", weight="bold")
        if val:  label(ax, (x+0.34, y-g), val, ha="left", size=FONT-2, color="#555")
    else:
        wire(ax, [(x-g, y-0.28), (x-g, y+0.28)])
        wire(ax, [(x+g, y-0.28), (x+g, y+0.28)])
        wire(ax, [(x-g, y), (x-0.5, y)]); wire(ax, [(x+g, y), (x+0.5, y)])
        t1, t2 = (x-0.5, y), (x+0.5, y)
        if name: label(ax, (x, y+0.34), name, weight="bold")
        if val:  label(ax, (x, y-0.34), val, size=FONT-2, color="#555")
    return t1, t2


def resistor(ax, x, y, horiz=True, name="", val=""):
    """Zig-zag resistor centred at (x,y). Returns two terminals."""
    n = 6; amp = 0.13; length = 0.8
    if horiz:
        xs = np.linspace(x-length/2, x+length/2, n*2+1)
        ys = y + amp*np.array([0]+[(-1)**i for i in range(n*2-1)]+[0])
        wire(ax, list(zip(xs, ys)))
        wire(ax, [(x-length/2, y), (x-length/2-0.35, y)])
        wire(ax, [(x+length/2, y), (x+length/2+0.35, y)])
        t1, t2 = (x-length/2-0.35, y), (x+length/2+0.35, y)
        if name: label(ax, (x, y+0.3), name, weight="bold")
        if val:  label(ax, (x, y-0.3), val, size=FONT-2, color="#555")
    else:
        ys = np.linspace(y-length/2, y+length/2, n*2+1)
        xs = x + amp*np.array([0]+[(-1)**i for i in range(n*2-1)]+[0])
        wire(ax, list(zip(xs, ys)))
        wire(ax, [(x, y-length/2), (x, y-length/2-0.35)])
        wire(ax, [(x, y+length/2), (x, y+length/2+0.35)])
        t1, t2 = (x, y+length/2+0.35), (x, y-length/2-0.35)
        if name: label(ax, (x+0.3, y), name, ha="left", weight="bold")
        if val:  label(ax, (x+0.3, y-0.25), val, ha="left", size=FONT-2, color="#555")
    return t1, t2


def isource(ax, x, y, name="", val="", down=True):
    """Current source (circle + arrow). Returns top & bottom terminals."""
    r = 0.32
    ax.add_patch(Circle((x, y), r, fill=False, edgecolor=COL, lw=LW))
    if down:
        ax.annotate("", xy=(x, y-0.16), xytext=(x, y+0.16),
                    arrowprops=dict(arrowstyle="-|>", color=COL, lw=1.4, mutation_scale=12))
    else:
        ax.annotate("", xy=(x, y+0.16), xytext=(x, y-0.16),
                    arrowprops=dict(arrowstyle="-|>", color=COL, lw=1.4, mutation_scale=12))
    wire(ax, [(x, y+r), (x, y+r+0.4)]); wire(ax, [(x, y-r), (x, y-r-0.4)])
    if name: label(ax, (x+r+0.12, y+0.12), name, ha="left", weight="bold")
    if val:  label(ax, (x+r+0.12, y-0.12), val, ha="left", size=FONT-2, color="#555")
    return (x, y+r+0.4), (x, y-r-0.4)


def vdd_rail(ax, x0, x1, y, text="VDD"):
    wire(ax, [(x0, y), (x1, y)], lw=LW+0.5)
    label(ax, ((x0+x1)/2, y+0.22), text, weight="bold", size=FONT+1)


def gnd(ax, x, y, text="GND"):
    wire(ax, [(x, y), (x, y-0.25)])
    for i, wdt in enumerate([0.34, 0.22, 0.10]):
        yy = y-0.25-i*0.09
        wire(ax, [(x-wdt, yy), (x+wdt, yy)])
    if text: label(ax, (x, y-0.72), text, size=FONT-1, color="#555")


def term(ax, p, text, kind="in", size=FONT):
    """Labelled port terminal (small open circle)."""
    ax.add_patch(Circle(p, 0.07, fill=False, edgecolor=COL, lw=LW))
    label(ax, p, text, dx=(-0.2 if kind=="in" else 0.2),
          ha="right" if kind=="in" else "left", weight="bold")


def opamp(ax, cx, cy, size=1.4, label_txt="A", inv_top=True):
    """Draw an op-amp triangle. Returns terminals dict."""
    h = size
    w = size*1.5
    # triangle pointing right
    p_left_top = (cx-w/2, cy+h)
    p_left_bot = (cx-w/2, cy-h)
    p_right    = (cx+w/2, cy)
    wire(ax, [p_left_top, p_left_bot])
    wire(ax, [p_left_bot, p_right])
    wire(ax, [p_right, p_left_top])
    # input leads
    yin_p = cy + h*0.45
    yin_n = cy - h*0.45
    if inv_top:
        yplus, yminus = yin_n, yin_p     # + at bottom
    else:
        yplus, yminus = yin_p, yin_n
    inp = (cx-w/2, yplus)
    inn = (cx-w/2, yminus)
    label(ax, (cx-w/2+0.16, yplus), "+", size=FONT+2, weight="bold")
    label(ax, (cx-w/2+0.16, yminus), "-", size=FONT+3, weight="bold")
    out = (cx+w/2, cy)
    label(ax, (cx-0.15, cy), label_txt, size=FONT+2, weight="bold", style="italic")
    vdd_t = (cx, cy+h*0.5)
    vss_t = (cx, cy-h*0.5)
    return {"inp": inp, "inn": inn, "out": out,
            "vdd": vdd_t, "vss": vss_t, "top": (cx, cy+h*0.5)}


def title_block(ax, title, subtitle="", proc="180 nm CMOS  |  VDD = 1.8 V"):
    ax.set_title(title, fontsize=FONT+5, weight="bold", pad=14)
    if subtitle:
        ax.text(0.5, 1.005, subtitle, transform=ax.transAxes,
                ha="center", va="bottom", fontsize=FONT, color="#555")
