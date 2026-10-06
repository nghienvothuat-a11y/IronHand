"""Trees and shrubs.

Tree positions and crown sizes were detected on the aerial imagery
(data/site_vectors.json).  Each species is one closed-mesh template in a hidden
library collection; a geometry-nodes point cloud instances the templates, so
~3,400 plants stay light in the file and fast to render.
"""
import json
import math
import os
import random
import bmesh
import bpy
from mathutils import Vector, Matrix, noise
from lib_mesh import MeshBuilder


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def leaf_mat(name, c1, c2, scale=3.0):
    import materials
    m, nodes, links, bsdf = materials._new(name)
    tc = nodes.new("ShaderNodeTexCoord")
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = 4
    links.new(tc.outputs["Object"], nz.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    # per-instance tint so neighbouring plants differ
    oi = nodes.new("ShaderNodeObjectInfo")
    hs = nodes.new("ShaderNodeHueSaturation")
    mr = nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = 0.85; mr.inputs["To Max"].default_value = 1.15
    links.new(oi.outputs["Random"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], hs.inputs["Value"])
    links.new(ramp.outputs["Color"], hs.inputs["Color"])
    links.new(hs.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Subsurface Weight"].default_value = 0.15
    bsdf.inputs["Subsurface Radius"].default_value = (0.2, 0.4, 0.1)
    bsdf.inputs["Sheen Weight"].default_value = 0.2
    m.diffuse_color = (*c1, 1)
    return m


def bark_mat(name, c):
    import materials
    m, nodes, links, bsdf = materials._new(name)
    tc = nodes.new("ShaderNodeTexCoord")
    w = nodes.new("ShaderNodeTexWave"); w.wave_type = "RINGS"; w.inputs["Scale"].default_value = 6.0
    w.inputs["Distortion"].default_value = 2.0
    links.new(tc.outputs["Object"], w.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (c[0] * 0.6, c[1] * 0.6, c[2] * 0.6, 1)
    ramp.color_ramp.elements[1].color = (*c, 1)
    links.new(w.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.4
    links.new(w.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.9
    m.diffuse_color = (*c, 1)
    return m


# ---------------------------------------------------------------------------
# geometry helpers (all closed)
# ---------------------------------------------------------------------------
def tube(MB, path, radii, seg=8, mat=0):
    """Closed tube along a 3D polyline with per-point radius."""
    rings = []
    for i, p in enumerate(path):
        p = Vector(p)
        if i == 0:
            t = (Vector(path[1]) - p).normalized()
        elif i == len(path) - 1:
            t = (p - Vector(path[i - 1])).normalized()
        else:
            t = (Vector(path[i + 1]) - Vector(path[i - 1])).normalized()
        a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        u = t.cross(a).normalized()
        v = t.cross(u).normalized()
        r = radii[i]
        rings.append([MB.vnew(tuple(p + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r)) for k in range(seg)])
    for i in range(len(rings) - 1):
        for k in range(seg):
            j = (k + 1) % seg
            MB.f([rings[i][k], rings[i][j], rings[i + 1][j], rings[i + 1][k]], mat)
    MB.f(list(reversed(rings[0])), mat)
    MB.f(rings[-1], mat)


def blade(MB, base, direction, side, length, width, droop, thick=0.012, mat=0, segs=4):
    """Thin closed leaf blade (a flattened tapering box chain)."""
    d = Vector(direction).normalized()
    s = Vector(side).normalized()
    up = s.cross(d).normalized()
    top, bot = [], []
    for i in range(segs + 1):
        t = i / segs
        c = Vector(base) + d * (length * t) - up * (droop * t * t)
        w = width * math.sin(math.pi * (0.15 + 0.85 * t)) * (1 - 0.6 * t)
        w = max(w, 0.004)
        for sign, arr in ((1, top), (-1, bot)):
            arr.append((MB.vnew(tuple(c - s * w + up * thick * sign)), MB.vnew(tuple(c + s * w + up * thick * sign))))
    for i in range(segs):
        a0, a1 = top[i]; b0, b1 = top[i + 1]
        MB.f([a0, a1, b1, b0], mat)
        c0, c1 = bot[i]; e0, e1 = bot[i + 1]
        MB.f([c1, c0, e0, e1], mat)
        MB.f([c0, a0, b0, e0], mat)
        MB.f([a1, c1, e1, b1], mat)
    MB.f([bot[0][0], bot[0][1], top[0][1], top[0][0]], mat)
    MB.f([top[-1][0], top[-1][1], bot[-1][1], bot[-1][0]], mat)


def blob(MB, center, radius, squash=1.0, subdiv=2, mat=0, seed=0, rough=0.25):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    idx = {}
    for v in bm.verts:
        n = v.co.normalized()
        f = 1.0 + rough * noise.noise(n * 2.2 + off)
        p = Vector((n.x * radius * f, n.y * radius * f, n.z * radius * f * squash)) + Vector(center)
        idx[v.index] = MB.vnew(tuple(p))
    for f in bm.faces:
        MB.f([idx[v.index] for v in f.verts], mat)
    bm.free()


# ---------------------------------------------------------------------------
# species templates (origin at the base of the trunk, ~unit scale per type)
# ---------------------------------------------------------------------------
def coconut_palm(name, height, lean, seed):
    rng = random.Random(seed)
    MB = MeshBuilder(name)
    n = 10
    path, radii = [], []
    ang = rng.uniform(0, 2 * math.pi)
    for i in range(n + 1):
        t = i / n
        x = math.cos(ang) * lean * t * t
        y = math.sin(ang) * lean * t * t
        path.append((x, y, height * t))
        radii.append(0.22 * (1 - 0.35 * t) + (0.08 if i == 0 else 0))
    tube(MB, path, radii, seg=10, mat=0)
    top = Vector(path[-1])
    blob(MB, top + Vector((0, 0, 0.15)), 0.32, 1.2, 1, mat=0, seed=seed)
    for k in range(5):
        a = 2 * math.pi * k / 5 + rng.random()
        blob(MB, top + Vector((math.cos(a) * 0.28, math.sin(a) * 0.28, -0.15)), 0.12, 1.0, 1, mat=2, seed=seed + k, rough=0.05)
    fronds = 14
    for k in range(fronds):
        a = 2 * math.pi * k / fronds + rng.uniform(-0.15, 0.15)
        elev = rng.uniform(-0.15, 0.55) if k % 3 else rng.uniform(-0.6, -0.2)
        d = Vector((math.cos(a) * math.cos(elev), math.sin(a) * math.cos(elev), math.sin(elev)))
        L = rng.uniform(3.6, 4.6)
        # rachis
        pts, rr = [], []
        for i in range(7):
            t = i / 6
            p = top + d * (L * t) - Vector((0, 0, 1.4 * t * t))
            pts.append(tuple(p)); rr.append(0.035 * (1 - 0.7 * t))
        tube(MB, pts, rr, seg=4, mat=1)
        side = Vector((-math.sin(a), math.cos(a), 0))
        for i in range(2, 17):
            t = i / 17
            p = top + d * (L * t) - Vector((0, 0, 1.4 * t * t))
            ll = 0.9 * math.sin(math.pi * (0.1 + 0.9 * t)) + 0.15
            for sgn in (1, -1):
                ld = (side * sgn * 0.8 + d * 0.45 - Vector((0, 0, 0.35))).normalized()
                blade(MB, tuple(p), ld, d, ll, 0.05, 0.25 * ll, mat=1, segs=3)
    return MB


def short_palm(name, height, seed):
    rng = random.Random(seed)
    MB = MeshBuilder(name)
    for s in range(rng.randint(3, 5)):
        a = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.2, 0.7)
        h = height * rng.uniform(0.7, 1.0)
        path = [(math.cos(a) * lean * (i / 6) ** 2, math.sin(a) * lean * (i / 6) ** 2, h * i / 6) for i in range(7)]
        tube(MB, path, [0.08 * (1 - 0.3 * i / 6) for i in range(7)], seg=6, mat=0)
        top = Vector(path[-1])
        for k in range(9):
            b = 2 * math.pi * k / 9 + rng.random() * 0.3
            el = rng.uniform(0.1, 0.9)
            d = Vector((math.cos(b) * math.cos(el), math.sin(b) * math.cos(el), math.sin(el)))
            side = Vector((-math.sin(b), math.cos(b), 0))
            L = rng.uniform(1.4, 2.0)
            for i in range(1, 10):
                t = i / 10
                p = top + d * (L * t) - Vector((0, 0, 0.5 * t * t))
                for sgn in (1, -1):
                    blade(MB, tuple(p), (side * sgn * 0.85 + d * 0.5).normalized(), d, 0.45 * (1 - 0.5 * t), 0.03, 0.08, mat=1, segs=2)
    return MB


def broadleaf(name, height, crown, seed):
    """Trunk, five limbs and a lumpy canopy built from many small leaf clusters."""
    rng = random.Random(seed)
    MB = MeshBuilder(name)
    trunk_h = height * 0.38
    tube(MB, [(0, 0, 0), (0.05, 0.02, trunk_h * 0.5), (0.0, 0.08, trunk_h)], [0.22, 0.18, 0.15], seg=8, mat=0)
    for b in range(5):
        a = 2 * math.pi * b / 5 + rng.random() * 0.5
        end = (math.cos(a) * crown * 0.32, math.sin(a) * crown * 0.32, trunk_h + height * 0.3)
        tube(MB, [(0, 0.08, trunk_h * 0.9), end], [0.1, 0.04], seg=6, mat=0)
    cz = trunk_h + height * 0.38
    for k in range(26):
        u = rng.uniform(-1, 1)
        a = rng.uniform(0, 2 * math.pi)
        rr = math.sqrt(1 - u * u)
        c = (math.cos(a) * rr * crown * 0.42, math.sin(a) * rr * crown * 0.42, cz + u * height * 0.22)
        blob(MB, c, crown * rng.uniform(0.15, 0.24), squash=0.85, subdiv=2, mat=1, seed=seed * 31 + k, rough=0.45)
    return MB


def shrub(name, size, seed, mat=1):
    rng = random.Random(seed)
    MB = MeshBuilder(name)
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.1, 0.32) * size
        c = (math.cos(a) * r, math.sin(a) * r, size * rng.uniform(0.25, 0.45))
        blob(MB, c, size * rng.uniform(0.24, 0.36), squash=0.8, subdiv=2, mat=mat, seed=seed * 7 + k, rough=0.45)
    return MB


# ---------------------------------------------------------------------------
def instancer(name, coll, lib, pts):
    """One point-cloud object with a GN modifier instancing lib's children."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([p[0] for p in pts], [], [])
    va = me.attributes.new("variant", "INT", "POINT"); va.data.foreach_set("value", [p[1] for p in pts])
    sa = me.attributes.new("pscale", "FLOAT", "POINT"); sa.data.foreach_set("value", [p[2] for p in pts])
    ra = me.attributes.new("yaw", "FLOAT", "POINT"); ra.data.foreach_set("value", [p[3] for p in pts])
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ng = bpy.data.node_groups.new(name + "_GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N, Lk = ng.nodes, ng.links
    gi = N.new("NodeGroupInput"); go = N.new("NodeGroupOutput")
    ci = N.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = lib
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    iop = N.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
    v = N.new("GeometryNodeInputNamedAttribute"); v.data_type = "INT"; v.inputs["Name"].default_value = "variant"
    s = N.new("GeometryNodeInputNamedAttribute"); s.data_type = "FLOAT"; s.inputs["Name"].default_value = "pscale"
    y = N.new("GeometryNodeInputNamedAttribute"); y.data_type = "FLOAT"; y.inputs["Name"].default_value = "yaw"
    cx = N.new("ShaderNodeCombineXYZ")
    e2r = N.new("FunctionNodeEulerToRotation")
    Lk.new(y.outputs["Attribute"], cx.inputs["Z"])
    Lk.new(cx.outputs["Vector"], e2r.inputs["Euler"])
    Lk.new(gi.outputs[0], iop.inputs["Points"])
    Lk.new(ci.outputs["Instances"], iop.inputs["Instance"])
    Lk.new(v.outputs["Attribute"], iop.inputs["Instance Index"])
    Lk.new(e2r.outputs["Rotation"], iop.inputs["Rotation"])
    Lk.new(s.outputs["Attribute"], iop.inputs["Scale"])
    Lk.new(iop.outputs["Instances"], go.inputs[0])
    mod = ob.modifiers.new("Instance plants", "NODES")
    mod.node_group = ng
    return ob


def build(L, root):
    data = json.load(open(os.path.join(os.path.dirname(__file__), "data", "site_vectors.json")))
    coll = bpy.data.collections.new("EMP2_40_Planting")
    root.children.link(coll)
    lib = bpy.data.collections.new("EMP2_49_Plant_library")
    root.children.link(lib)
    trunk = bark_mat("EMP2_Palm_trunk", (0.42, 0.36, 0.28))
    bark = bark_mat("EMP2_Tree_bark", (0.30, 0.25, 0.20))
    frond = leaf_mat("EMP2_Palm_fronds", (0.10, 0.22, 0.04), (0.26, 0.38, 0.08))
    leaf = leaf_mat("EMP2_Broadleaf_canopy", (0.05, 0.16, 0.03), (0.18, 0.30, 0.06), 2.0)
    shrub_m = leaf_mat("EMP2_Shrub_foliage", (0.08, 0.20, 0.04), (0.22, 0.34, 0.07), 4.0)
    dune_m = leaf_mat("EMP2_Dune_scrub_foliage", (0.16, 0.20, 0.08), (0.30, 0.32, 0.14), 4.0)
    coconut = leaf_mat("EMP2_Coconuts", (0.35, 0.30, 0.08), (0.45, 0.38, 0.1), 8.0)
    templates = [
        ("00_coconut_palm_a", coconut_palm("t", 10.5, 1.2, 1), [trunk, frond, coconut]),
        ("01_coconut_palm_b", coconut_palm("t", 8.0, 0.6, 2), [trunk, frond, coconut]),
        ("02_coconut_palm_c", coconut_palm("t", 12.5, 2.0, 3), [trunk, frond, coconut]),
        ("03_clump_palm", short_palm("t", 4.5, 4), [trunk, frond]),
        ("04_broadleaf_tree", broadleaf("t", 7.0, 6.0, 5), [bark, leaf]),
        ("05_broadleaf_tree_b", broadleaf("t", 5.5, 4.5, 6), [bark, leaf]),
        ("06_garden_shrub", shrub("t", 1.6, 7), [shrub_m, shrub_m]),
        ("07_dune_scrub", shrub("t", 1.8, 8), [dune_m, dune_m]),
    ]
    for nm, MB, mats in templates:
        MB.name = f"EMP2_Plant_{nm}"
        ob = MB.to_object(lib, mats)
        ob.data.shade_smooth()
    pts = []
    rng = random.Random(4026)
    counts = {}
    import site_data as SD
    from lib_mesh import point_in_poly, chaikin
    (wa, wb, wr) = SD.WIND_POOL_PX
    (wc, wcr) = SD.WIND_SMALL_POOL_PX
    wind_pool = _capsule(SD.px(*wa), SD.px(*wb), (wr + 3) * SD.M_PER_PX)
    wind_plunge = [(SD.px(*wc)[0] + (wcr + 3) * SD.M_PER_PX * math.cos(2 * math.pi * k / 24),
                    SD.px(*wc)[1] + (wcr + 3) * SD.M_PER_PX * math.sin(2 * math.pi * k / 24)) for k in range(24)]
    water = ([p["outer"] for p in data["pool"]] + [chaikin(SD.pts(SD.LAGOON_RIM_PX), 2, closed=True)]
             + [chaikin(SD.pts(SD.WEST_LAKE_PX), 2, closed=True), wind_pool, wind_plunge])
    arena_c = SD.px(*SD.ARENA["centre_px"])
    planters = []
    for x, y, diam, inside, cls, district in data["trees"]:
        if math.hypot(x - arena_c[0], y - arena_c[1]) < SD.ARENA["grandstand_outer_m"] + 1.0:
            continue
        if any(point_in_poly((x, y), w) for w in water):
            continue
        if inside:
            if cls == 1:            # crown detected over a road surface: no trunk on the carriageway
                continue
            if district:
                planters.append((x, y))
            if diam < 2.6:
                var, sc = 6, diam / 1.6
            elif diam < 5.5:
                r = rng.random()
                var = 0 if r < 0.35 else 1 if r < 0.55 else 2 if r < 0.7 else 3 if r < 0.85 else 5
                sc = rng.uniform(0.85, 1.15)
            else:
                var = 4 if rng.random() < 0.55 else 2
                sc = diam / 6.0 if var == 4 else rng.uniform(0.95, 1.2)
            z = 0.24
        else:
            var = 7 if diam < 4.5 or rng.random() < 0.7 else 5
            sc = rng.uniform(0.55, 1.05) if var == 7 else min(diam / 4.5, 1.4)
            z = 0.0
        sc = max(0.5, min(sc, 2.4))
        counts[var] = counts.get(var, 0) + 1
        pts.append(((x, y, z), var, sc, rng.uniform(0, 2 * math.pi)))
    instancer("EMP2_Plants_scatter", coll, lib, pts)
    # raised square planters under the street trees of the shopvilla lanes
    import materials
    pcoll = bpy.data.collections.new("EMP2_41_Shopvilla_lane_planters")
    root.children.link(pcoll)
    PL = MeshBuilder("EMP2_Shopvilla_lane_planters")
    SO = MeshBuilder("EMP2_Shopvilla_planter_soil")
    a = math.radians(-SD.PARCEL_ROT_DEG)
    for (x, y) in planters:
        PL.box((x, y, 0.2 + 0.25), (2.0, 2.0, 0.5), mat=0, rot_z=-a)
        SO.box((x, y, 0.2 + 0.52), (1.7, 1.7, 0.06), mat=0, rot_z=-a)
    PL.to_object(pcoll, [L["curb"]])
    SO.to_object(pcoll, [materials.flat("EMP2_Planter_mulch", (0.16, 0.11, 0.07), rough=0.95)])
    # exclude the library from the view layer so only instances render
    for vl in bpy.context.scene.view_layers:
        lc = _find_layer_collection(vl.layer_collection, lib.name)
        if lc:
            lc.exclude = True
    return dict(plants=len(pts), by_template={templates[k][0]: v for k, v in sorted(counts.items())})


def _capsule(pa, pb, r, seg=12):
    ax = (pb[0] - pa[0], pb[1] - pa[1])
    a0 = math.atan2(ax[1], ax[0])
    ring = [(pb[0] + r * math.cos(a0 - math.pi / 2 + math.pi * k / seg), pb[1] + r * math.sin(a0 - math.pi / 2 + math.pi * k / seg)) for k in range(seg + 1)]
    ring += [(pa[0] + r * math.cos(a0 + math.pi / 2 + math.pi * k / seg), pa[1] + r * math.sin(a0 + math.pi / 2 + math.pi * k / seg)) for k in range(seg + 1)]
    return ring


def _find_layer_collection(lc, name):
    if lc.collection.name == name:
        return lc
    for ch in lc.children:
        r = _find_layer_collection(ch, name)
        if r:
            return r
    return None
