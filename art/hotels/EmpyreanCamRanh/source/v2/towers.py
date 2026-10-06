"""Hotel towers: Light, Sea, Sand, Wind.

Each tower is generated from its traced outer (convex) and inner (pool-court)
edges.  Stations are spaced one room module apart along the inner edge and
projected to the outer edge, so every bay is a quad in plan.  Each bay gets its
own floor count, which produces the stepped terraces down both wings.

The shell is a single welded, closed mesh: façade cells share vertices with
their neighbours, roofs and terrace walls, and every window or balcony is an
inset pushed into the wall (frame, reveals, glass) rather than a painted quad.
Frames, mullions, railings, bands and rooftop plant are separate closed solids.
"""
import math
import random
import bpy
from lib_mesh import (MeshBuilder, sub, add, mul, length, norm, lerp, lerp3, perp, chaikin,
                      resample, ray_polyline, arclen_at, point_at_arclen, polyline_length,
                      offset_polyline, ensure_ccw)
import site_data as SD
from facade import CellWriter, prism_facade

BAY_M = 4.0           # inner room module
SAW_DEPTH = 1.35      # sawtooth bay projection on wing outer faces
SAW_SPLIT = 0.62
MAT_ORDER = ["wall_white", "wall_beige", "glass", "frame", "accent", "roof", "terrace",
             "soffit", "glass_shop", "wall_grey"]
MI = {k: i for i, k in enumerate(MAT_ORDER)}


def _nearest_station(stations, p):
    best, bi = 1e18, 0
    for i, s in enumerate(stations):
        d = (s[0] - p[0]) ** 2 + (s[1] - p[1]) ** 2
        if d < best:
            best, bi = d, i
    return bi


def compute_plan(T):
    outer = chaikin(SD.pts(T["outer"]), 2)
    inner = chaikin(SD.pts(T["inner"]), 2)
    Lin = polyline_length(inner)
    n_bays = max(4, int(round(Lin / BAY_M)))
    I = resample(inner, count=n_bays + 1)
    Lout = polyline_length(outer)
    s_out = []
    for i, p in enumerate(I):
        if i == 0:
            s_out.append(0.0)
            continue
        if i == n_bays:
            s_out.append(Lout)
            continue
        t = norm(sub(I[i + 1], I[i - 1]))
        right = (t[1], -t[0])
        hit = ray_polyline(p, right, outer)
        s = arclen_at(outer, hit[1], hit[2]) if hit else s_out[-1] + BAY_M
        s_out.append(s)
    # monotonic + light smoothing
    for i in range(1, len(s_out)):
        s_out[i] = max(s_out[i], s_out[i - 1] + 0.6)
    sm = s_out[:]
    for i in range(1, len(s_out) - 1):
        sm[i] = (s_out[i - 1] + 2 * s_out[i] + s_out[i + 1]) / 4
    sm[-1] = Lout
    for i in range(1, len(sm)):
        sm[i] = max(sm[i], sm[i - 1] + 0.6)
    scale = Lout / sm[-1]
    O = [point_at_arclen(outer, s * scale) for s in sm]

    # floors per bay
    mids_out = [lerp(O[j], O[j + 1], 0.5) for j in range(n_bays)]
    pa = _nearest_station(mids_out, SD.px(*T["plateau"][0]))
    pb = _nearest_station(mids_out, SD.px(*T["plateau"][1]))
    a, b = min(pa, pb), max(pa, pb)
    N, Nt = T["floors"], T["tip_floors"]
    p = 1.35 if N > 12 else 1.0
    floors = []
    for j in range(n_bays):
        if j < a:
            t = (a - j) / max(a, 1)
        elif j > b:
            t = (j - b) / max(n_bays - 1 - b, 1)
        else:
            t = 0.0
        floors.append(int(round(Nt + (N - Nt) * (1 - t) ** p)))
    hs = _nearest_station(O, SD.px(*T["head_px"][0]))
    he = _nearest_station(O, SD.px(*T["head_px"][1]))
    head = set(range(min(hs, he), max(hs, he)))
    return dict(O=O, I=I, floors=floors, plateau=(a, b), head=head, n=n_bays)


def z_of(T, k):
    if k <= 0:
        return 0.0
    return T["ground_h"] + (k - 1) * T["floor_h"]


# ---------------------------------------------------------------------------
class TowerShell(CellWriter):
    def __init__(self, T, plan):
        super().__init__(f"EMP2_{T['id']}", MI, seed=sum(map(ord, T["id"])))
        self.T, self.P = T, plan
        self.B.name = f"EMP2_{T['id']}_Tower_shell"

    # -- geometry lookups ----------------------------------------------------
    def outer_pts(self, j):
        """Outer edge points of bay j (station j .. station j+1) incl. sawtooth."""
        O = self.P["O"]
        a, b = O[j], O[j + 1]
        if j in self.P["head"]:
            Lo = length(sub(b, a))
            q = max(1, int(round(Lo / 2.5)))
            return [lerp(a, b, t / q) for t in range(q + 1)], "head"
        if j == 0 or j == self.P["n"] - 1:
            return [a, b], "tip"
        d = norm(sub(b, a))
        right = (d[1], -d[0])
        m = add(lerp(a, b, SAW_SPLIT), mul(right, SAW_DEPTH))
        return [a, m, b], "saw"

    def wall_pts(self, i):
        O, I = self.P["O"], self.P["I"]
        L = length(sub(I[i], O[i]))
        m = max(1, int(round(L / 4.2)))
        return [lerp(O[i], I[i], s / m) for s in range(m + 1)]

    # -- vertex keys ---------------------------------------------------------
    def vo(self, j, t, k, pts):
        z = z_of(self.T, k)
        q = len(pts) - 1
        if t == 0:
            return self.B.v((*pts[0], z), ("O", j, k))
        if t == q:
            return self.B.v((*pts[-1], z), ("O", j + 1, k))
        return self.B.v((*pts[t], z), ("Oq", j, t, k))

    def vi(self, i, k):
        return self.B.v((*self.P["I"][i], z_of(self.T, k)), ("I", i, k))

    def vp(self, i, s, k, wp):
        if s == 0:
            return self.B.v((*wp[0], z_of(self.T, k)), ("O", i, k))
        if s == len(wp) - 1:
            return self.vi(i, k)
        return self.B.v((*wp[s], z_of(self.T, k)), ("P", i, s, k))

    def pos(self, idx):
        return self.B.verts[idx]

    # -- façade specs ----------------------------------------------------------
    def spec_outer(self, kind, k, t, q):
        if k == 0:
            return dict(x0=0.04, x1=0.96, y0=0.03, y1=0.93, depth=0.35, glass="glass_shop",
                        mullions=2, transoms=[0.45, 0.78], prof=0.08, spandrel="wall_grey")
        if kind == "head":
            low = self.T["floors"] <= 10
            heads = sorted(self.P["head"])
            mid = heads[len(heads) // 2] if heads else -1
            if low and self.cur_j == mid:
                # full-height dark glazed strip down the middle of the drum (as photographed)
                return dict(x0=0.03, x1=0.97, y0=0.04, y1=0.96, depth=0.3, mullions=1, transoms=[0.5], prof=0.07,
                            glass="glass_shop", frame_mat=1, spandrel="wall_grey", pier="wall_grey", lintel="wall_grey")
            band = "wall_grey" if (low and k % 2 == 1) else self.wall_mat
            return dict(x0=0.27, x1=0.73, y0=0.28, y1=0.86, depth=0.22, mullions=1, transoms=[0.72], prof=0.06,
                        spandrel=band, lintel=band)
        if kind == "saw":
            if t == 0:   # glazed facet of the sawtooth bay
                return dict(x0=0.07, x1=0.93, y0=0.32, y1=0.88, depth=0.25, mullions=2, transoms=[], prof=0.06,
                            spandrel="wall_beige", pier="wall_white", lintel="wall_white")
            return None  # solid facet
        if kind == "tip":
            return dict(x0=0.35, x1=0.65, y0=0.30, y1=0.85, depth=0.2, mullions=0, prof=0.05)
        return None

    def spec_inner(self, k):
        if k == 0:
            return dict(x0=0.03, x1=0.97, y0=0.03, y1=0.93, depth=0.35, glass="glass_shop",
                        mullions=2, transoms=[0.45, 0.78], prof=0.08, spandrel="wall_grey")
        return dict(x0=0.11, x1=0.89, y0=0.05, y1=0.90, depth=1.55, spandrel="accent", lintel="wall_white",
                    sill="terrace", head="soffit", jamb="wall_white", mullions=1, transoms=[], prof=0.07, rail=0.12,
                    frame_mat=0)

    def spec_step(self, k):
        if k == 0:
            return dict(x0=0.08, x1=0.92, y0=0.03, y1=0.9, depth=0.3, glass="glass_shop", mullions=1, prof=0.07)
        return dict(x0=0.12, x1=0.88, y0=0.04, y1=0.88, depth=0.3, mullions=2, transoms=[], prof=0.06)

    # -- build -----------------------------------------------------------------
    def build(self):
        P, T = self.P, self.T
        n, Fl = P["n"], P["floors"]
        self.wall_mat = "wall_white"
        outer_cache = [self.outer_pts(j) for j in range(n)]

        def h(j):
            return Fl[j] if 0 <= j < n else 0

        # outer façade
        for j in range(n):
            pts, kind = outer_cache[j]
            q = len(pts) - 1
            self.cur_j = j
            for k in range(Fl[j]):
                for t in range(q):
                    a = self.vo(j, t, k, pts)
                    b = self.vo(j, t + 1, k, pts)
                    c = self.vo(j, t + 1, k + 1, pts)
                    d = self.vo(j, t, k + 1, pts)
                    if kind == "saw" and t == 1:
                        self.wall_mat = "wall_beige"
                    self.cell(a, b, c, d, self.spec_outer(kind, k, t, q))
                    self.wall_mat = "wall_white"
        # inner façade
        for j in range(n):
            for k in range(Fl[j]):
                a, b = self.vi(j + 1, k), self.vi(j, k)
                c, d = self.vi(j, k + 1), self.vi(j + 1, k + 1)
                self.cell(a, b, c, d, self.spec_inner(k))
        # step walls and tip walls at stations
        wall_cache = {}
        for i in range(n + 1):
            lo, hi = sorted((h(i - 1), h(i)))
            if lo == hi:
                continue
            wp = self.wall_pts(i)
            wall_cache[i] = wp
            forward = h(i) < h(i - 1)      # lower side ahead -> wall faces forward
            for k in range(lo, hi):
                for s in range(len(wp) - 1):
                    p0 = self.vp(i, s, k, wp)
                    p1 = self.vp(i, s + 1, k, wp)
                    p2 = self.vp(i, s + 1, k + 1, wp)
                    p3 = self.vp(i, s, k + 1, wp)
                    if forward:
                        self.cell(p0, p1, p2, p3, self.spec_step(k))
                    else:
                        self.cell(p1, p0, p3, p2, self.spec_step(k))
        # roofs and bottoms
        self.roof_rings = []
        for j in range(n):
            pts, kind = outer_cache[j]
            for k, is_top in ((Fl[j], True), (0, False)):
                ring = [self.vo(j, t, k, pts) for t in range(len(pts))]
                if (j + 1) in wall_cache:
                    wp = wall_cache[j + 1]
                    lo, hi = sorted((h(j), h(j + 1)))
                    if lo <= k <= hi:
                        ring += [self.vp(j + 1, s, k, wp) for s in range(1, len(wp) - 1)]
                ring += [self.vi(j + 1, k), self.vi(j, k)]
                if j in wall_cache:
                    wp = wall_cache[j]
                    lo, hi = sorted((h(j - 1), h(j)))
                    if lo <= k <= hi:
                        ring += [self.vp(j, s, k, wp) for s in range(len(wp) - 2, 0, -1)]
                if is_top:
                    plateau = P["plateau"][0] <= j <= P["plateau"][1]
                    self.B.f(ring, MI["roof" if plateau else "terrace"])
                    self.roof_rings.append((j, Fl[j], [self.B.verts[x] for x in ring]))
                else:
                    self.B.f(list(reversed(ring)), MI["soffit"])
        return self

    # -- terraces / parapets ----------------------------------------------------
    def terraces(self, MBglass, MBrail, MBparapet):
        P, T = self.P, self.T
        n, Fl = P["n"], P["floors"]
        O, I = P["O"], P["I"]
        a_pl, b_pl = P["plateau"]

        def h(j):
            return Fl[j] if 0 <= j < n else 0
        for j in range(n):
            z = z_of(T, Fl[j])
            pts, kind = self.outer_pts(j)
            plateau = a_pl <= j <= b_pl
            edges = []
            # outer and inner edges; balustrades sit 0.18 m inside the roof edge
            for e in range(len(pts) - 1):
                edges.append((pts[e], pts[e + 1], "out"))
            edges.append((I[j + 1], I[j], "in"))
            if h(j + 1) < Fl[j]:
                edges.append((O[j + 1], I[j + 1], "drop"))
            if h(j - 1) < Fl[j]:
                edges.append((I[j], O[j], "drop"))
            for p0, p1, kind_e in edges:
                d = norm(sub(p1, p0))
                inward = (-d[1], d[0])    # left of travel is inside the roof ring (CCW)
                q0 = add(p0, mul(inward, 0.18))
                q1 = add(p1, mul(inward, 0.18))
                if plateau:
                    c = add(p1, mul(inward, 0.25)); dd = add(p0, mul(inward, 0.25))
                    MBparapet.quad_box(p0, p1, c, dd, z, z + 1.2)
                else:
                    nrm = (-inward[0], -inward[1], 0.0)
                    self._panel(MBglass, (*q0, z), (*q1, z), 1.05, 0.02, nrm)
                    self._panel(MBrail, (q0[0], q0[1], z + 1.03), (q1[0], q1[1], z + 1.03), 0.06, 0.06, nrm)


def roof_plant(tower, plan, MBroof, MBsolar, MBplant):
    """Roof level (the '+ roof' storey), lift overruns and solar arrays."""
    T = tower
    O, I, Fl = plan["O"], plan["I"], plan["floors"]
    a_pl, b_pl = plan["plateau"]
    ztop = z_of(T, T["floors"])
    head = sorted(j for j in plan["head"] if a_pl <= j <= b_pl)
    if head:
        h0, h1 = head[0], head[-1] + 1
        outer_line = [lerp(O[i], I[i], 0.16) for i in range(h0, h1 + 1)]
        inner_line = [lerp(O[i], I[i], 0.84) for i in range(h0, h1 + 1)]
        ring = outer_line + list(reversed(inner_line))
        ring = ensure_ccw(ring)
        MBroof.prism(ring, ztop, ztop + T["roof_level_h"], mat_side=0, mat_top=1)
        # lift overruns
        mid = (h0 + h1) // 2
        for off in (-2, 2):
            i = min(max(mid + off, 0), len(O) - 1)
            c = lerp(O[i], I[i], 0.5)
            MBplant.box((c[0], c[1], ztop + T["roof_level_h"] + 1.4), (5.0, 5.0, 2.8))
    # solar arrays on the remaining plateau roof
    for j in range(a_pl, b_pl + 1):
        if j in plan["head"]:
            continue
        z = z_of(T, Fl[j])
        p0 = lerp(O[j], I[j], 0.18); p1 = lerp(O[j + 1], I[j + 1], 0.18)
        p2 = lerp(O[j + 1], I[j + 1], 0.78); p3 = lerp(O[j], I[j], 0.78)
        shrink = 0.4
        c = mul(add(add(p0, p1), add(p2, p3)), 0.25)
        quad = [lerp(c, p, 1 - shrink / 4) for p in (p0, p1, p2, p3)]
        MBsolar.quad_box(*ensure_ccw(quad), z + 0.5, z + 0.62)
        for p in quad:
            MBplant.box((p[0], p[1], z + 0.25), (0.12, 0.12, 0.5))


def entrance(T, plan, MBcanopy, MBcol, MBsign):
    """Drop-off canopy on the convex head facing the access road + name monolith."""
    O, I = plan["O"], plan["I"]
    e = SD.px(*T["entrance_px"])
    i = min(range(len(O)), key=lambda k: (O[k][0] - e[0]) ** 2 + (O[k][1] - e[1]) ** 2)
    i = min(max(i, 1), len(O) - 2)
    t = norm(sub(O[i + 1], O[i - 1]))
    out = (t[1], -t[0])
    c = O[i]
    w, d = 14.0, 8.0
    z = T["ground_h"] - 0.6
    a = add(add(c, mul(t, -w / 2)), mul(out, 0.2))
    b = add(add(c, mul(t, w / 2)), mul(out, 0.2))
    cc = add(b, mul(out, d))
    dd = add(a, mul(out, d))
    MBcanopy.quad_box(*ensure_ccw([a, b, cc, dd]), z, z + 0.55)
    for s in (-0.4, 0.4):
        p = add(add(c, mul(t, s * w)), mul(out, d - 0.8))
        MBcol.cylinder((p[0], p[1], 0.0), 0.28, z, seg=16)
    # name monolith 10 m beyond the canopy edge
    sp = add(add(c, mul(out, d + 10.0)), mul(t, w * 0.7))
    MBsign.box((sp[0], sp[1], 1.6), (1.4, 0.35, 3.2), rot_z=math.atan2(t[1], t[0]))
    return dict(canopy_center=add(c, mul(out, d / 2)), facing=out, sign=sp, tangent=t)


PODIUM_MI = {"wall_white": 0, "glass_shop": 1, "glass": 1, "frame": 2, "terrace": 3, "wall_grey": 4, "soffit": 0}


def podium(T, plan):
    """Single-storey lobby crescent on the court side of the head, curtain-walled."""
    O, I = plan["O"], plan["I"]
    head = sorted(plan["head"])
    if not head:
        return None
    pts = [SD.px(*p) for p in T["podium_px"]]
    h0, h1 = head[0] + 1, head[-1]
    inner_line = []
    for i in range(h0, h1 + 1):
        tt = norm(sub(I[min(i + 1, len(I) - 1)], I[max(i - 1, 0)]))
        inner_line.append(add(I[i], mul((tt[1], -tt[0]), 0.6)))   # tuck 0.6 m into the tower
    depth = sum(min(length(sub(p, q)) for q in inner_line) for p in pts) / len(pts)
    depth = max(6.0, min(depth, 16.0))
    out_line = []
    for k, i in enumerate(range(h0, h1 + 1)):
        t = norm(sub(I[min(i + 1, len(I) - 1)], I[max(i - 1, 0)]))
        left = (-t[1], t[0])
        taper = math.sin(math.pi * k / max(1, (h1 - h0)))
        out_line.append(add(I[i], mul(left, 1.0 + depth * (0.35 + 0.65 * taper))))
    ring = inner_line + list(reversed(out_line))
    cw = CellWriter(f"EMP2_{T['id']}_Lobby_podium", PODIUM_MI, seed=7)
    cw.wall_mat = "wall_white"
    spec = dict(x0=0.03, x1=0.97, y0=0.04, y1=0.86, depth=0.3, glass="glass_shop", mullions=1,
                transoms=[0.55], prof=0.08, spandrel="wall_grey", lintel="wall_white")
    prism_facade(cw, ring, [0.0, T["ground_h"] - 0.05], lambda e, s, k: spec, "terrace", "wall_white", cell_w=3.2)
    return cw


def build_towers(L, coll_root):
    import bpy
    results = {}
    accent_map = {"blue": "mosaic_blue", "terracotta": "mosaic_terracotta", "grey": "mosaic_grey"}
    for T in SD.TOWERS:
        coll = bpy.data.collections.new(f"EMP2_10_{T['id']}_Tower")
        coll_root.children.link(coll)
        plan = compute_plan(T)
        sh = TowerShell(T, plan).build()
        mats = [L[k] if k != "accent" else L[accent_map[T["accent"]]] for k in MAT_ORDER]
        shell = sh.B.to_object(coll, mats)
        sh.F.to_object(coll, [L["frame"], L["frame_dark"]])
        sh.R.to_object(coll, [L["rail_glass"]])
        sh.H.to_object(coll, [L["steel"]])
        TG = MeshBuilder(f"EMP2_{T['id']}_Terrace_balustrades")
        TR = MeshBuilder(f"EMP2_{T['id']}_Terrace_handrails")
        TP = MeshBuilder(f"EMP2_{T['id']}_Roof_parapets")
        sh.terraces(TG, TR, TP)
        TG.to_object(coll, [L["rail_glass"]])
        TR.to_object(coll, [L["steel"]])
        TP.to_object(coll, [L["wall_white"]])
        RL = MeshBuilder(f"EMP2_{T['id']}_Roof_level")
        SO = MeshBuilder(f"EMP2_{T['id']}_Solar_arrays")
        PL = MeshBuilder(f"EMP2_{T['id']}_Rooftop_plant")
        roof_plant(T, plan, RL, SO, PL)
        RL.to_object(coll, [L["wall_white"], L["roof"]])
        SO.to_object(coll, [L["solar"]])
        PL.to_object(coll, [L["machine"]])
        CA = MeshBuilder(f"EMP2_{T['id']}_Entrance_canopy")
        CO = MeshBuilder(f"EMP2_{T['id']}_Canopy_columns")
        SG = MeshBuilder(f"EMP2_{T['id']}_Name_monolith")
        ent = entrance(T, plan, CA, CO, SG)
        CA.to_object(coll, [L["soffit"]])
        CO.to_object(coll, [L["frame"]])
        SG.to_object(coll, [L["sign_blue"]])
        pcw = podium(T, plan)
        if pcw:
            pcw.B.to_object(coll, [L["wall_white"], L["glass_shop"], L["frame"], L["terrace"], L["wall_grey"]])
            pcw.F.to_object(coll, [L["frame"], L["frame_dark"]])
        bands(T, plan, sh, L[accent_map[T["accent"]]], coll)
        results[T["id"]] = dict(plan=plan, shell=shell, entrance=ent, windows=sh.windows,
                                height=z_of(T, T["floors"]) + T["roof_level_h"])
    return results


def bands(T, plan, sh, mat, coll):
    """Mosaic tile bands at slab level along the sawtooth wing faces."""
    MB = MeshBuilder(f"EMP2_{T['id']}_Mosaic_bands")
    n, Fl = plan["n"], plan["floors"]
    for k in range(2, max(Fl) + 1):
        run = []
        for j in range(n):
            pts, kind = sh.outer_pts(j)
            ok = kind == "saw" and Fl[j] >= k
            if ok:
                if run and run[-1] == pts[0]:
                    run += pts[1:]
                else:
                    if len(run) > 1:
                        _band(MB, run, z_of(T, k))
                    run = list(pts)
            elif len(run) > 1:
                _band(MB, run, z_of(T, k))
                run = []
        if len(run) > 1:
            _band(MB, run, z_of(T, k))
    MB.to_object(coll, [mat])


def _band(MB, run, z):
    MB.ribbon(run, 0.06, z - 0.12, z + 0.14, offset=-0.03)
