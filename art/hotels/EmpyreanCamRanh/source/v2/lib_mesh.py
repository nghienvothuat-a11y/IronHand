"""Small mesh-building helpers for the v2 rebuild.

Every generator writes into a MeshBuilder: vertices are shared through keys or
exact positions, so façades, roofs and slabs come out as welded, closed solids
instead of loose quads.
"""
import math
import bpy
import bmesh
from mathutils import Vector


class MeshBuilder:
    def __init__(self, name):
        self.name = name
        self.verts = []
        self.faces = []
        self.mats = []
        self.pane = []
        self._keyed = {}
        self._posed = {}

    # -- vertices -----------------------------------------------------------
    def v(self, co, key=None):
        """Return a vertex index.  With a key the vertex is shared by key,
        otherwise it is shared by exact (rounded) position."""
        if key is not None:
            i = self._keyed.get(key)
            if i is None:
                i = len(self.verts)
                self.verts.append(tuple(co))
                self._keyed[key] = i
            return i
        k = (round(co[0], 4), round(co[1], 4), round(co[2], 4))
        i = self._posed.get(k)
        if i is None:
            i = len(self.verts)
            self.verts.append(tuple(co))
            self._posed[k] = i
        return i

    def vnew(self, co):
        self.verts.append(tuple(co))
        return len(self.verts) - 1

    # -- faces --------------------------------------------------------------
    def f(self, idx, mat=0, pane=0.0):
        # drop consecutive duplicates (degenerate edges)
        out = []
        for i in idx:
            if not out or out[-1] != i:
                out.append(i)
        if len(out) > 2 and out[0] == out[-1]:
            out.pop()
        if len(out) >= 3 and len(set(out)) == len(out):
            self.faces.append(out)
            self.mats.append(mat)
            self.pane.append(pane)

    # -- primitives ---------------------------------------------------------
    def box(self, center, size, mat=0, rot_z=0.0):
        cx, cy, cz = center
        sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
        c, s = math.cos(rot_z), math.sin(rot_z)
        p = []
        for dz in (-sz, sz):
            for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
                p.append(self.vnew((cx + dx * c - dy * s, cy + dx * s + dy * c, cz + dz)))
        b0, b1, b2, b3, t0, t1, t2, t3 = p
        self.f([b3, b2, b1, b0], mat)
        self.f([t0, t1, t2, t3], mat)
        self.f([b0, b1, t1, t0], mat)
        self.f([b1, b2, t2, t1], mat)
        self.f([b2, b3, t3, t2], mat)
        self.f([b3, b0, t0, t3], mat)

    def quad_box(self, a, b, c, d, z0, z1, mat=0, mats=None):
        """Closed prism over the planar quad a,b,c,d (CCW seen from +Z)."""
        bot = [self.vnew((p[0], p[1], z0)) for p in (a, b, c, d)]
        top = [self.vnew((p[0], p[1], z1)) for p in (a, b, c, d)]
        m_side = mats[0] if mats else mat
        m_top = mats[1] if mats else mat
        self.f(list(reversed(bot)), m_side)
        self.f(top, m_top)
        for i in range(4):
            j = (i + 1) % 4
            self.f([bot[i], bot[j], top[j], top[i]], m_side)

    def prism(self, ring, z0, z1, mat_side=0, mat_top=None, mat_bot=None):
        """Closed extrusion of a CCW polygon ring."""
        mat_top = mat_side if mat_top is None else mat_top
        mat_bot = mat_side if mat_bot is None else mat_bot
        bot = [self.vnew((p[0], p[1], z0)) for p in ring]
        top = [self.vnew((p[0], p[1], z1)) for p in ring]
        n = len(ring)
        self.f(list(reversed(bot)), mat_bot)
        self.f(top, mat_top)
        for i in range(n):
            j = (i + 1) % n
            self.f([bot[i], bot[j], top[j], top[i]], mat_side)

    def ribbon(self, path, width, z0, z1, mat=0, closed=False, offset=0.0):
        """Closed solid strip following a 2D polyline (width centred on path+offset)."""
        if len(path) < 2:
            return
        left, right = offset_polyline(path, offset + width / 2, closed), offset_polyline(path, offset - width / 2, closed)
        n = len(path)
        L0 = [self.vnew((p[0], p[1], z0)) for p in left]
        L1 = [self.vnew((p[0], p[1], z1)) for p in left]
        R0 = [self.vnew((p[0], p[1], z0)) for p in right]
        R1 = [self.vnew((p[0], p[1], z1)) for p in right]
        segs = n if closed else n - 1
        for i in range(segs):
            j = (i + 1) % n
            self.f([R1[i], R1[j], L1[j], L1[i]], mat)          # top
            self.f([L0[i], L0[j], R0[j], R0[i]], mat)          # bottom
            self.f([L0[i], L1[i], L1[j], L0[j]], mat)          # left side
            self.f([R0[j], R1[j], R1[i], R0[i]], mat)          # right side
        if not closed:
            self.f([R0[0], R1[0], L1[0], L0[0]], mat)
            self.f([L0[-1], L1[-1], R1[-1], R0[-1]], mat)

    def cylinder(self, base, radius, height, seg=10, mat=0, r_top=None):
        r_top = radius if r_top is None else r_top
        bx, by, bz = base
        b = [self.vnew((bx + radius * math.cos(2 * math.pi * i / seg), by + radius * math.sin(2 * math.pi * i / seg), bz)) for i in range(seg)]
        t = [self.vnew((bx + r_top * math.cos(2 * math.pi * i / seg), by + r_top * math.sin(2 * math.pi * i / seg), bz + height)) for i in range(seg)]
        self.f(list(reversed(b)), mat)
        self.f(t, mat)
        for i in range(seg):
            j = (i + 1) % seg
            self.f([b[i], b[j], t[j], t[i]], mat)

    # -- output -------------------------------------------------------------
    def to_object(self, collection, materials, recalc=True, smooth=False):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.verts, [], self.faces)
        for m in materials:
            me.materials.append(m)
        if self.mats:
            me.polygons.foreach_set("material_index", self.mats)
        if any(self.pane):
            at = me.attributes.new("pane_rand", "FLOAT", "FACE")
            at.data.foreach_set("value", self.pane)
        me.validate(clean_customdata=False)
        if recalc:
            bm = bmesh.new()
            bm.from_mesh(me)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            bm.to_mesh(me)
            bm.free()
        if smooth:
            me.shade_smooth()
        box_uv(me)
        me.update()
        ob = bpy.data.objects.new(self.name, me)
        collection.objects.link(ob)
        return ob


def box_uv(me):
    """World-metre box-projected UVs (1 UV unit = 1 m) so exports keep texture scale."""
    import numpy as np
    nl = len(me.loops)
    if nl == 0:
        return
    co = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    lv = np.empty(nl, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    np_ = len(me.polygons)
    ls = np.empty(np_, np.int32)
    lt = np.empty(np_, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    me.polygons.foreach_get("loop_total", lt)
    nrm = np.empty(np_ * 3, np.float32)
    me.polygons.foreach_get("normal", nrm)
    nrm = np.abs(nrm.reshape(-1, 3))
    axis = np.argmax(nrm, axis=1)
    loop_axis = np.repeat(axis, lt)
    p = co[lv]
    uv = np.empty((nl, 2), np.float32)
    m0 = loop_axis == 0
    m1 = loop_axis == 1
    m2 = loop_axis == 2
    uv[m0] = p[m0][:, [1, 2]]
    uv[m1] = p[m1][:, [0, 2]]
    uv[m2] = p[m2][:, [0, 1]]
    layer = me.uv_layers.new(name="UVMap")
    layer.data.foreach_set("uv", uv.ravel())


# ---------------------------------------------------------------------------
# 2D helpers
# ---------------------------------------------------------------------------
def sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def mul(a, s):
    return (a[0] * s, a[1] * s)


def length(a):
    return math.hypot(a[0], a[1])


def norm(a):
    l = length(a) or 1.0
    return (a[0] / l, a[1] / l)


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def perp(a):
    return (-a[1], a[0])


def polyline_length(p):
    return sum(length(sub(p[i + 1], p[i])) for i in range(len(p) - 1))


def resample(p, step=None, count=None):
    """Resample a polyline at equal arc length."""
    L = polyline_length(p)
    if count is None:
        count = max(2, int(round(L / step)) + 1)
    cum = [0.0]
    for i in range(len(p) - 1):
        cum.append(cum[-1] + length(sub(p[i + 1], p[i])))
    out = []
    j = 0
    for k in range(count):
        s = L * k / (count - 1)
        while j < len(p) - 2 and cum[j + 1] < s:
            j += 1
        seg = cum[j + 1] - cum[j]
        t = 0.0 if seg == 0 else (s - cum[j]) / seg
        out.append(lerp(p[j], p[j + 1], min(max(t, 0.0), 1.0)))
    return out


def chaikin(p, iters=2, closed=False):
    for _ in range(iters):
        q = [] if closed else [p[0]]
        n = len(p)
        rng = range(n) if closed else range(n - 1)
        for i in rng:
            a, b = p[i], p[(i + 1) % n]
            q.append(lerp(a, b, 0.25))
            q.append(lerp(a, b, 0.75))
        if not closed:
            q.append(p[-1])
        p = q
    return p


def offset_polyline(p, d, closed=False):
    """Offset to the left (CCW normal) by d.  Miter joins, clamped."""
    n = len(p)
    out = []
    for i in range(n):
        if closed:
            a, b, c = p[i - 1], p[i], p[(i + 1) % n]
        else:
            a = p[i - 1] if i > 0 else None
            b = p[i]
            c = p[i + 1] if i < n - 1 else None
        if a is None:
            t = norm(sub(c, b))
            nrm = perp(t)
            out.append(add(b, mul(nrm, d)))
            continue
        if c is None:
            t = norm(sub(b, a))
            nrm = perp(t)
            out.append(add(b, mul(nrm, d)))
            continue
        t0 = norm(sub(b, a))
        t1 = norm(sub(c, b))
        n0, n1 = perp(t0), perp(t1)
        m = norm(add(n0, n1))
        cosh = m[0] * n0[0] + m[1] * n0[1]
        cosh = max(cosh, 0.35)
        out.append(add(b, mul(m, d / cosh)))
    return out


def polygon_area(ring):
    a = 0.0
    for i in range(len(ring)):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % len(ring)]
        a += x0 * y1 - x1 * y0
    return a / 2


def ensure_ccw(ring):
    return ring if polygon_area(ring) > 0 else list(reversed(ring))


def point_in_poly(pt, ring):
    x, y = pt
    inside = False
    n = len(ring)
    for i in range(n):
        x0, y0 = ring[i]
        x1, y1 = ring[(i + 1) % n]
        if (y0 > y) != (y1 > y):
            xi = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if xi > x:
                inside = not inside
    return inside


def ray_polyline(origin, direction, poly):
    """Nearest positive intersection of a ray with a polyline.
    Returns (t_ray, seg_index, seg_param) or None."""
    best = None
    ox, oy = origin
    dx, dy = direction
    for i in range(len(poly) - 1):
        ax, ay = poly[i]
        bx, by = poly[i + 1]
        ex, ey = bx - ax, by - ay
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((ax - ox) * ey - (ay - oy) * ex) / den
        u = ((ax - ox) * dy - (ay - oy) * dx) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            if best is None or t < best[0]:
                best = (t, i, u)
    return best


def arclen_at(poly, seg, u):
    s = 0.0
    for i in range(seg):
        s += length(sub(poly[i + 1], poly[i]))
    return s + u * length(sub(poly[seg + 1], poly[seg]))


def point_at_arclen(poly, s):
    acc = 0.0
    for i in range(len(poly) - 1):
        l = length(sub(poly[i + 1], poly[i]))
        if acc + l >= s or i == len(poly) - 2:
            t = 0.0 if l == 0 else (s - acc) / l
            return lerp(poly[i], poly[i + 1], min(max(t, 0.0), 1.0))
        acc += l
    return poly[-1]
