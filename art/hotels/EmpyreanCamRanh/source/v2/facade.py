"""Façade cell writer shared by towers, podiums and shopvillas.

A cell is one wall panel between four shared vertices.  An opening is inset
into it: four frame faces stay in the wall plane, four reveal faces step back by
the recess depth, and the glass closes the back.  The result stays welded to the
neighbouring cells, so a façade built from cells is one closed surface.
"""
import math
import random
from lib_mesh import MeshBuilder, lerp, lerp3, ensure_ccw, length, sub


class CellWriter:
    def __init__(self, prefix, mi, seed=1):
        self.B = MeshBuilder(f"{prefix}_Shell")
        self.F = MeshBuilder(f"{prefix}_Window_frames")
        self.R = MeshBuilder(f"{prefix}_Balustrades")
        self.H = MeshBuilder(f"{prefix}_Handrails")
        self.mi = mi
        self.wall_mat = "wall_white"
        self.windows = 0
        self.rng = random.Random(seed)

    # -- cells ---------------------------------------------------------------
    def cell(self, a, b, c, d, spec):
        B = self.B
        pa, pb, pc, pd = (B.verts[x] for x in (a, b, c, d))
        if spec is None:
            B.f([a, b, c, d], self.mi[self.wall_mat])
            return
        x0, x1, y0, y1, depth = spec["x0"], spec["x1"], spec["y0"], spec["y1"], spec["depth"]

        def bil(u, v):
            bot = lerp3(pa, pb, u)
            top = lerp3(pd, pc, u)
            return lerp3(bot, top, v)
        ex = [pb[i] - pa[i] for i in range(3)]
        ey = [pd[i] - pa[i] for i in range(3)]
        n = (ex[1] * ey[2] - ex[2] * ey[1], ex[2] * ey[0] - ex[0] * ey[2], ex[0] * ey[1] - ex[1] * ey[0])
        nl = math.sqrt(sum(c_ * c_ for c_ in n)) or 1.0
        n = [c_ / nl for c_ in n]
        W = [bil(x0, y0), bil(x1, y0), bil(x1, y1), bil(x0, y1)]
        R = [tuple(w[i] - n[i] * depth for i in range(3)) for w in W]
        wa, wb, wc, wd = (B.vnew(p) for p in W)
        ra, rb, rc, rd = (B.vnew(p) for p in R)
        B.f([a, b, wb, wa], self.mi[spec.get("spandrel", self.wall_mat)])
        B.f([b, c, wc, wb], self.mi[spec.get("pier", self.wall_mat)])
        B.f([c, d, wd, wc], self.mi[spec.get("lintel", self.wall_mat)])
        B.f([d, a, wa, wd], self.mi[spec.get("pier", self.wall_mat)])
        B.f([wa, wb, rb, ra], self.mi[spec.get("sill", "frame")])
        B.f([wb, wc, rc, rb], self.mi[spec.get("jamb", "frame")])
        B.f([wc, wd, rd, rc], self.mi[spec.get("head", "frame")])
        B.f([wd, wa, ra, rd], self.mi[spec.get("jamb", "frame")])
        B.f([ra, rb, rc, rd], self.mi[spec.get("glass", "glass")], pane=0.001 + 0.998 * self.rng.random())
        self.windows += 1
        self.add_frames(R, n, spec)
        if spec.get("rail"):
            self.add_rail(W, n, spec["rail"])

    def add_frames(self, R, n, spec):
        """Mullions/transoms just in front of the glass plane."""
        F = self.F
        ra, rb, rc, rd = R
        off = [n[i] * 0.04 for i in range(3)]
        w = math.dist(ra, rb)
        h = math.dist(ra, rd)
        ux = [(rb[i] - ra[i]) / (w or 1) for i in range(3)]
        uy = [(rd[i] - ra[i]) / (h or 1) for i in range(3)]
        prof = spec.get("prof", 0.06)
        vcount = spec.get("mullions", 1)
        hlevels = spec.get("transoms", [])

        def bar(p0, p1, along, across_w):
            # closed box between p0 and p1 (centre line), cross-section prof x across_w
            c = [(p0[i] + p1[i]) / 2 + off[i] for i in range(3)]
            L = math.dist(p0, p1)
            # build orthonormal frame
            ax = along
            az = n
            ay = (az[1] * ax[2] - az[2] * ax[1], az[2] * ax[0] - az[0] * ax[2], az[0] * ax[1] - az[1] * ax[0])
            hx, hy, hz = L / 2, across_w / 2, prof / 2
            corners = []
            for sz in (-1, 1):
                for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    corners.append(F.vnew(tuple(c[i] + ax[i] * sx * hx + ay[i] * sy * hy + az[i] * sz * hz for i in range(3))))
            b0, b1, b2, b3, t0, t1, t2, t3 = corners
            fm = spec.get("frame_mat", 1)
            F.f([b3, b2, b1, b0], fm); F.f([t0, t1, t2, t3], fm)
            F.f([b0, b1, t1, t0], fm); F.f([b1, b2, t2, t1], fm); F.f([b2, b3, t3, t2], fm); F.f([b3, b0, t0, t3], fm)
        # perimeter frame
        bar(ra, rb, ux, prof); bar(rd, rc, ux, prof)
        bar(ra, rd, uy, prof); bar(rb, rc, uy, prof)
        for m in range(1, vcount + 1):
            t = m / (vcount + 1)
            p0 = [ra[i] + (rb[i] - ra[i]) * t for i in range(3)]
            p1 = [rd[i] + (rc[i] - rd[i]) * t for i in range(3)]
            bar(p0, p1, uy, prof * 0.8)
        for tlev in hlevels:
            p0 = [ra[i] + (rd[i] - ra[i]) * tlev for i in range(3)]
            p1 = [rb[i] + (rc[i] - rb[i]) * tlev for i in range(3)]
            bar(p0, p1, ux, prof * 0.8)

    def add_rail(self, W, n, inset):
        wa, wb, wc, wd = W
        h = 1.1
        base = [wa[i] - n[i] * inset for i in range(3)]
        endb = [wb[i] - n[i] * inset for i in range(3)]
        self._panel(self.R, base, endb, h, 0.02, n)
        top0 = (base[0], base[1], base[2] + h)
        top1 = (endb[0], endb[1], endb[2] + h)
        self._panel(self.H, (top0[0], top0[1], top0[2] - 0.03), (top1[0], top1[1], top1[2] - 0.03), 0.06, 0.06, n)

    @staticmethod
    def _panel(MB, p0, p1, h, t, n):
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        ox, oy = n[0] * t / 2, n[1] * t / 2
        a = (p0[0] - ox, p0[1] - oy)
        b = (p1[0] - ox, p1[1] - oy)
        c = (p1[0] + ox, p1[1] + oy)
        d = (p0[0] + ox, p0[1] + oy)
        MB.quad_box(a, b, c, d, p0[2], p0[2] + h)



def prism_facade(cw, ring, levels, spec_fn, roof_mat, bottom_mat, cell_w=3.0, key="R"):
    """Closed prism over a CCW ring with façade cells on every side.
    levels: list of z values (z0 < z1 < ...).  spec_fn(edge, s, k) -> spec or None."""
    ring = ensure_ccw(ring)
    n = len(ring)
    B = cw.B
    edges = []
    for e in range(n):
        a, b = ring[e], ring[(e + 1) % n]
        m = max(1, int(round(length(sub(b, a)) / cell_w)))
        edges.append([lerp(a, b, s / m) for s in range(m + 1)])

    def vid(e, s, k):
        pts = edges[e]
        z = levels[k]
        if s == 0:
            return B.v((*pts[0], z), (key, "C", e, k))
        if s == len(pts) - 1:
            return B.v((*pts[-1], z), (key, "C", (e + 1) % n, k))
        return B.v((*pts[s], z), (key, "E", e, s, k))
    for e in range(n):
        for s in range(len(edges[e]) - 1):
            for k in range(len(levels) - 1):
                a, b = vid(e, s, k), vid(e, s + 1, k)
                c, d = vid(e, s + 1, k + 1), vid(e, s, k + 1)
                cw.cell(a, b, c, d, spec_fn(e, s, k))
    top = len(levels) - 1
    roof = []
    bot = []
    for e in range(n):
        for s in range(len(edges[e]) - 1):
            roof.append(vid(e, s, top))
            bot.append(vid(e, s, 0))
    B.f(roof, cw.mi[roof_mat])
    B.f(list(reversed(bot)), cw.mi[bottom_mat])
    return edges
