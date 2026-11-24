"""Small numpy ray-caster: translucent organ shells, glossy solids, studio lighting. No GPU needed."""
import numpy as np

BG_RIM = np.array([0.35, 0.85, 0.95])
LIGHTS = [  # (direction toward light in camera space, colour, strength)
    (np.array([-0.55, 0.65, -0.55]), np.array([1.0, 0.96, 0.9]), 1.0),
    (np.array([0.75, 0.25, 0.65]), BG_RIM, 0.7),
    (np.array([0.6, -0.4, -0.5]), np.array([0.55, 0.65, 0.9]), 0.25)]
for i, (d, c, s) in enumerate(LIGHTS):
    LIGHTS[i] = (d / np.linalg.norm(d), c, s)


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


class Ell:
    def __init__(self, c, r, color, alpha=1.0, spec=0.5, shine=40, tex=0.0, clip_z=None, emit=0.0):
        self.c, self.r = np.array(c, float), np.array(r, float)
        self.color, self.alpha, self.spec, self.shine = hexrgb(color) if isinstance(color, str) else color, alpha, spec, shine
        self.tex, self.clip_z, self.emit = tex, clip_z, emit


def rot(yaw, pitch):
    ya, pi = np.radians(yaw), np.radians(pitch)
    Ry = np.array([[np.cos(ya), 0, np.sin(ya)], [0, 1, 0], [-np.sin(ya), 0, np.cos(ya)]])
    Rx = np.array([[1, 0, 0], [0, np.cos(pi), -np.sin(pi)], [0, np.sin(pi), np.cos(pi)]])
    Rbase = np.array([[-1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    return Rx @ Ry @ Rbase


def render(objs, yaw=0, pitch=10, size=640, extent=3.4, D=9.0):
    W = H = size
    M = rot(yaw, pitch)
    tan_half = extent / D
    u = (np.arange(W) + 0.5) / W * 2 - 1
    v = 1 - (np.arange(H) + 0.5) / H * 2
    dc = np.stack(np.broadcast_arrays(u[None, :] * tan_half, v[:, None] * tan_half, np.ones((H, W))), -1)
    dc /= np.linalg.norm(dc, axis=-1, keepdims=True)
    dobj = dc @ M                                    # row-vector form of M.T @ d
    o_obj = M.T @ np.array([0, 0, -D])
    rgb = np.zeros((H, W, 3))
    alpha = np.zeros((H, W))
    tbest = np.full((H, W), np.inf)
    shells = []

    def hit(o, sl):
        oc = (o_obj - o.c) / o.r
        dd = dobj[sl] / o.r
        a = (dd * dd).sum(-1)
        b = (dd * oc).sum(-1)
        cq = (oc * oc).sum() - 1
        disc = b * b - a * cq
        ok = disc > 0
        t = np.where(ok, (-b - np.sqrt(np.where(ok, disc, 0))) / a, 0.0)
        ok &= t > 0
        t = np.where(ok, t, 0.0)
        p = o_obj + t[..., None] * dobj[sl]
        if o.clip_z is not None:
            ok &= p[..., 2] > o.clip_z
        n = (p - o.c) / (o.r ** 2)
        n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
        return ok, np.where(ok, t, np.inf), p, n

    def shade(o, p, n, d):
        ncam = n @ M.T
        view = -(d @ M.T)
        ndv = np.clip((ncam * view).sum(-1), 0, 1)
        col = np.broadcast_to(o.color, p.shape).copy()
        if o.tex:
            q = np.sin(p[..., 0] * 5.3 + np.sin(p[..., 1] * 3.1) * 2) + np.sin(p[..., 1] * 6.7 + p[..., 2] * 2.2) + np.sin(p[..., 2] * 7.9 + p[..., 0] * 1.7)
            col *= (1 + o.tex * q / 3)[..., None]
        out = col * 0.16
        for L, lc, ls in LIGHTS:
            lam = (ncam @ L + 0.35) / 1.35
            out += col * lc * ls * np.clip(lam, 0, 1)[..., None] * 0.9
            hvec = L[None, None, :] + view
            hvec /= np.linalg.norm(hvec, axis=-1, keepdims=True) + 1e-9
            out += lc * ls * o.spec * (np.clip((ncam * hvec).sum(-1), 0, 1) ** o.shine)[..., None]
        fres = (1 - ndv) ** 3
        out += BG_RIM * (fres * 0.55)[..., None] + col * (o.emit * (0.6 + 0.4 * ndv))[..., None]
        return np.clip(out, 0, 1), ndv

    def window(o):
        cc = M @ o.c + np.array([0, 0, D])
        if cc[2] <= 0.5:
            return None
        pr = o.r.max() / (cc[2] * tan_half) * W / 2 * 1.15 + 3
        cx, cy = W / 2 + cc[0] / cc[2] / tan_half * W / 2, H / 2 - cc[1] / cc[2] / tan_half * H / 2
        x0, x1, y0, y1 = int(max(cx - pr, 0)), int(min(cx + pr, W)), int(max(cy - pr, 0)), int(min(cy + pr, H))
        if x1 <= x0 or y1 <= y0:
            return None
        return (slice(y0, y1), slice(x0, x1))

    for o in objs:
        sl = window(o)
        if sl is None:
            continue
        ok, t, p, n = hit(o, sl)
        if not ok.any():
            continue
        col, ndv = shade(o, p, n, dobj[sl])
        if o.alpha >= 0.999:
            better = ok & (t < tbest[sl])
            sub_rgb, sub_t = rgb[sl], tbest[sl]
            sub_rgb[better] = col[better]
            sub_t[better] = t[better]
            alpha[sl][better] = 1.0
        else:
            a = (o.alpha + (1 - o.alpha) * (1 - ndv) ** 2.0) * ok
            shells.append((t, sl, col, a, o))
    # translucent shells: composite over what is behind them, far to near (by centre depth)
    shells.sort(key=lambda s: -(M @ s[4].c)[2])
    for t, sl, col, a, o in shells:
        vis = (t < tbest[sl]) & (a > 0)
        a = np.where(vis, a, 0)[..., None]
        sub = rgb[sl]
        subA = alpha[sl][..., None]
        rgb[sl] = col * a + sub * (1 - a)
        alpha[sl] = (a + subA * (1 - a))[..., 0]
    straight = rgb / np.maximum(alpha, 1e-6)[..., None]
    out = np.dstack([np.clip(straight, 0, 1), np.clip(alpha, 0, 1)])
    return (out * 255).astype(np.uint8)
