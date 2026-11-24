"""Build ray-cast objects for each organ and tumour stage (geometry is schematic, original)."""
import numpy as np
from tools.render3d import Ell, hexrgb

ORG = {
    "liver": dict(shells=[((0.8, 0, 0), (1.7, 1.1, 0.8), "#9C3F2B"), ((-1.1, 0.25, 0.05), (1.0, 0.7, 0.6), "#A8472F"), ((0.75, -0.95, -0.55), (0.28, 0.42, 0.26), "#6B8E23")],
                  shell_alpha=0.34, tex=0.10, extent=(2.75, 4.5),
                  vessels=[([(0.3, -1.1, -0.1), (0.1, -0.5, 0.0), (-0.3, 0.0, 0.05)], "#2F5FD0", 0.09, "pv"),
                           ([(0.1, -0.5, 0.0), (0.9, -0.1, 0.15), (1.6, 0.2, 0.2)], "#2F6FE0", 0.075, "pvr"),
                           ([(-0.3, 0.0, 0.05), (-1.0, 0.2, 0.1)], "#3B82F6", 0.065, "pvl"),
                           ([(0.4, -0.2, 0.7), (0.3, 0.0, 0.1), (0.2, 0.3, -0.2)], "#E23B4A", 0.06, "ha"),
                           ([(0.2, 0.5, 0.75), (0.5, 0.2, 0.3), (1.1, -0.2, 0.2)], "#22A7D8", 0.07, "hv")],
                  invade={2: ["pvr"], 3: ["pvr", "pv"], 4: ["pvr", "pv"]},
                  tumors={1: [((1.2, 0.1, 0.2), 0.28)], 2: [((1.2, 0.1, 0.2), 0.38), ((0.55, -0.2, 0.3), 0.2), ((1.75, 0.3, -0.1), 0.18)],
                          3: [((1.2, 0.1, 0.2), 0.55), ((0.45, -0.3, 0.2), 0.35), ((1.8, 0.4, -0.2), 0.3), ((-1.0, 0.3, 0.2), 0.25)]},
                  nodes=[(-0.1, -1.35, -0.2), (0.4, -1.45, -0.3), (-0.55, -1.25, -0.25)], node_from=3,
                  distant=[((1.0, 0.2, 3.3), 0.5), ((-2.8, 0.0, 2.2), 0.4)], anchor=(0.3, 0.0, 0.4), tilt=(0, 0)),
    "lung": dict(shells=[((1.35, 0, 0), (1.0, 0.8, 1.9), "#E69AA8"), ((-1.35, 0, 0), (0.9, 0.75, 1.8), "#EDAAB6")],
                 shell_alpha=0.36, tex=0.16, extent=(3.2, 5.3),
                 vessels=[([(0, 0, 2.6), (0, 0, 0.9)], "#B8C4D4", 0.14, "tr"), ([(0, 0, 0.9), (0.9, 0, 0.3), (1.5, 0, -0.5)], "#B8C4D4", 0.1, "br"),
                          ([(0, 0, 0.9), (-0.9, 0, 0.3), (-1.4, 0, -0.4)], "#B8C4D4", 0.1, "bl"),
                          ([(0, 0.2, -0.5), (0.8, 0.2, 0.1), (1.5, 0.2, 0.6)], "#E23B4A", 0.07, "pa"), ([(0, -0.2, -0.5), (-0.8, -0.2, 0.0), (-1.4, -0.2, 0.5)], "#2F6FE0", 0.07, "pvn")],
                 invade={}, tumors={1: [((1.6, 0.2, 0.9), 0.25)], 2: [((1.6, 0.2, 0.9), 0.4)], 3: [((1.5, 0.2, 0.8), 0.6)]},
                 nodes=[(0.55, 0.1, 0.3), (-0.55, 0.1, 0.3), (0.0, 0.1, 0.95), (0.0, 0.1, 1.35)], node_from=2,
                 distant=[((0.0, 0.0, 4.3), 0.5), ((3.0, 0.0, 0.2), 0.35)], anchor=(1.4, 0.2, 0.8), tilt=(0, 0)),
    "breast": dict(shells=[((0, 0, 0), (1.8, 1.8, 0.95), "#E6BC95", "clip"), ((0, 0, 0.93), (0.13, 0.13, 0.1), "#C97B63", "nip")],
                   shell_alpha=0.40, tex=0.05, extent=(4.0, 5.2), floor=((0, 0, -0.35), (3.3, 3.0, 0.3), "#B04A3C"),
                   vessels=[([(0, 0, 0.9), (0.9, 0.8, 0.35), (1.5, 1.3, 0.05)], "#F2A81D", 0.06, "d"), ([(0, 0, 0.9), (-0.9, 0.9, 0.35), (-1.4, 1.4, 0.05)], "#F2A81D", 0.06, "d"),
                            ([(0, 0, 0.9), (0.2, -1.0, 0.4), (0.4, -1.6, 0.05)], "#F2A81D", 0.06, "d"), ([(0, 0, 0.9), (-1.0, -0.6, 0.4), (-1.5, -1.0, 0.05)], "#F2A81D", 0.06, "d"),
                            ([(-1.6, 1.6, 0.1), (-0.6, 0.4, 0.35), (0.6, -0.8, 0.25)], "#2F6FE0", 0.05, "v"), ([(-1.4, 1.8, 0.0), (-0.4, 0.8, 0.3), (0.8, -0.4, 0.25)], "#E23B4A", 0.05, "a")],
                   invade={}, tumors={1: [((0.7, 0.5, 0.4), 0.22)], 2: [((0.7, 0.5, 0.4), 0.38)], 3: [((0.6, 0.4, 0.15), 0.6)]},
                   nodes=[(-2.6, 1.0, 0.2), (-2.9, 1.6, 0.25), (-2.3, 1.9, 0.2)], node_from=2, extra_nodes=[(0.2, -2.1, 0.1)],
                   distant=[((0.0, -3.4, -1.4), 0.45), ((3.2, -2.4, -1.5), 0.5)], anchor=(0.7, 0.4, 0.4), tilt=(0, 0)),
}


def bez(pts, step=0.11):
    p = np.array(pts, float)
    if len(p) == 2:
        p = np.array([p[0], (p[0] + p[1]) / 2, p[1]])
    n = max(int(np.linalg.norm(p[1] - p[0]) / step + np.linalg.norm(p[2] - p[1]) / step), 4)
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * p[0] + 2 * (1 - t) * t * p[1] + t ** 2 * p[2]


def build(organ, stage):
    m = ORG[organ]
    objs = []
    if "floor" in m:
        c, r, col = m["floor"]
        objs.append(Ell(c, r, col, 1.0, spec=0.25, shine=20, tex=0.12))
    for sh in m["shells"]:
        c, r, col = sh[:3]
        objs.append(Ell(c, r, col, m["shell_alpha"] if sh[2] != "#C97B63" else 1.0, spec=0.7, shine=60, tex=m["tex"], clip_z=-0.04 if len(sh) > 3 and sh[3] == "clip" else None))
    inv = m["invade"].get(stage, [])
    for pts, col, rad, name in m["vessels"]:
        dark = name in inv
        for q in bez(pts, 0.1):
            objs.append(Ell(q, (rad * (1.5 if dark else 1),) * 3, "#7F1230" if dark else col, 1.0, spec=0.9, shine=80))
    for i, (c, r) in enumerate(m["tumors"].get(min(stage, 3), []) if stage > 0 else []):
        objs.append(Ell(c, (r * 1.0,) * 3, "#E11D48", 1.0, spec=1.1, shine=55, tex=0.10, emit=0.35))
    for i, c in enumerate(m["nodes"]):
        inv_n = stage >= m["node_from"] and i < (1 if stage == 2 else len(m["nodes"]))
        objs.append(Ell(c, (0.13,) * 3, "#7C3AED" if inv_n else "#9AA7B8", 1.0, spec=0.8, shine=60, emit=0.3 if inv_n else 0))
    for c in m.get("extra_nodes", []):
        objs.append(Ell(c, (0.12,) * 3, "#9AA7B8", 1.0, spec=0.8, shine=60))
    if stage >= 4:
        for c, r in m["distant"]:
            objs.append(Ell(c, (r,) * 3, "#B3123A", 1.0, spec=1.0, shine=50, emit=0.4))
            a, b = np.array(m["anchor"]), np.array(c)
            for k in np.linspace(0.08, 0.92, 14):
                objs.append(Ell(a + (b - a) * k, (0.045,) * 3, "#FF5A7A", 1.0, spec=0.5, emit=0.6))
    return objs
