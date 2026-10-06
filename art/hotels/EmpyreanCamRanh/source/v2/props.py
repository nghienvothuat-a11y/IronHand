"""Site furniture and small structures around the buildings.

Street lamps along the internal roads, loungers and parasols round the pools,
tensile shade sails, benches on the Arena ring, flagpoles at each tower drop-off,
beach parasols, parked cars (positions detected on the aerial), and the ribbed
fan pavilion beside Sand tower.  Every prop is a closed mesh; repeated props are
linked duplicates sharing one mesh.
"""
import json
import math
import os
import random
import bpy
from lib_mesh import MeshBuilder, ensure_ccw, add, sub, mul, norm, length, lerp, chaikin, resample, offset_polyline, point_in_poly
import site_data as SD
import materials


def _obj(name, mesh, coll, loc, yaw=0.0, color=None):
    ob = bpy.data.objects.new(name, mesh)
    ob.location = loc
    ob.rotation_euler = (0, 0, yaw)
    if color:
        ob.color = (*color, 1)
    coll.objects.link(ob)
    return ob


# ---------------------------------------------------------------------------
# templates
# ---------------------------------------------------------------------------
def lamp_mesh(L):
    MB = MeshBuilder("EMP2_Street_lamp")
    MB.cylinder((0, 0, 0), 0.2, 0.5, seg=12, mat=0)
    MB.cylinder((0, 0, 0.5), 0.08, 7.0, seg=10, mat=0, r_top=0.06)
    MB.box((0.6, 0, 7.4), (1.3, 0.08, 0.08), mat=0)
    MB.box((1.15, 0, 7.3), (0.6, 0.26, 0.14), mat=0)
    MB.box((1.15, 0, 7.21), (0.5, 0.2, 0.03), mat=1)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"], [L["frame_dark"], L["lamp_lens"]]).data


def lounger_mesh(L):
    MB = MeshBuilder("EMP2_Pool_lounger")
    MB.box((0, 0, 0.3), (1.95, 0.7, 0.08), mat=0)
    MB.box((-0.85, 0, 0.55), (0.55, 0.66, 0.06), mat=0, rot_z=0.0)
    for dx in (-0.85, 0.85):
        for dy in (-0.3, 0.3):
            MB.box((dx, dy, 0.13), (0.05, 0.05, 0.26), mat=1)
    MB.box((0.1, 0, 0.37), (1.5, 0.64, 0.06), mat=2)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"], [L["deck"], L["steel"], L["canvas"]]).data


def parasol_mesh(L, thatched=False):
    MB = MeshBuilder("EMP2_Beach_parasol" if thatched else "EMP2_Pool_parasol")
    MB.cylinder((0, 0, 0), 0.04, 2.5, seg=8, mat=0)
    r = 1.6 if thatched else 1.4
    MB.cylinder((0, 0, 2.15), r, 0.55, seg=16, mat=1, r_top=0.05)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"],
                        [L["deck"], L["thatch"] if thatched else L["canvas"]]).data


def bench_mesh(L):
    MB = MeshBuilder("EMP2_Bench")
    MB.box((0, 0, 0.42), (1.8, 0.45, 0.06), mat=0)
    MB.box((0, -0.2, 0.7), (1.8, 0.05, 0.4), mat=0)
    for dx in (-0.75, 0.75):
        MB.box((dx, 0, 0.2), (0.08, 0.45, 0.4), mat=1)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"], [L["deck"], L["frame_dark"]]).data


def flagpole_mesh(L):
    MB = MeshBuilder("EMP2_Flagpole")
    MB.cylinder((0, 0, 0), 0.25, 0.3, seg=12, mat=0)
    MB.cylinder((0, 0, 0.3), 0.06, 11.0, seg=10, mat=0, r_top=0.04)
    MB.box((0.75, 0.0, 10.4), (1.5, 0.02, 1.0), mat=1)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"], [L["steel"], L["sign_blue"]]).data


def car_mesh(L):
    MB = MeshBuilder("EMP2_Car")
    MB.quad_box((-2.25, -0.88), (2.25, -0.88), (2.25, 0.88), (-2.25, 0.88), 0.32, 0.95, mat=0)
    MB.quad_box((-1.2, -0.78), (1.05, -0.78), (1.05, 0.78), (-1.2, 0.78), 0.95, 1.45, mat=1)
    for dx in (-1.45, 1.45):
        for dy in (-0.82, 0.82):
            bm_r = 0.33
            seg = 12
            # wheel: short cylinder along Y
            ring0, ring1 = [], []
            for k in range(seg):
                a = 2 * math.pi * k / seg
                ring0.append(MB.vnew((dx + bm_r * math.cos(a), dy - 0.11, bm_r + bm_r * math.sin(a))))
                ring1.append(MB.vnew((dx + bm_r * math.cos(a), dy + 0.11, bm_r + bm_r * math.sin(a))))
            MB.f(ring0, 2)
            MB.f(list(reversed(ring1)), 2)
            for k in range(seg):
                j = (k + 1) % seg
                MB.f([ring0[k], ring1[k], ring1[j], ring0[j]], 2)
    return MB.to_object(bpy.data.collections["EMP2_48_Prop_library"], [L["car_paint"], L["glass"], L["tyre"]]).data


def shade_sail(MB, c, size, yaw):
    """Tensile sail: four masts and a warped (hypar) membrane slab."""
    cs, sn = math.cos(yaw), math.sin(yaw)
    h = size / 2
    corners = []
    for i, (dx, dy) in enumerate(((-h, -h), (h, -h), (h, h), (-h, h))):
        x = c[0] + dx * cs - dy * sn
        y = c[1] + dx * sn + dy * cs
        z = 6.5 if i % 2 == 0 else 3.6
        corners.append((x, y, z))
        MB.cylinder((x, y, 0.2), 0.1, z - 0.2 + 0.4, seg=10, mat=1)
    n = 8
    top, bot = {}, {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            p = [corners[0][k] * (1 - u) * (1 - v) + corners[1][k] * u * (1 - v) + corners[2][k] * u * v + corners[3][k] * (1 - u) * v for k in range(3)]
            top[i, j] = MB.vnew((p[0], p[1], p[2] + 0.02))
            bot[i, j] = MB.vnew((p[0], p[1], p[2] - 0.02))
    for i in range(n):
        for j in range(n):
            MB.f([top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]], 0)
            MB.f([bot[i, j + 1], bot[i + 1, j + 1], bot[i + 1, j], bot[i, j]], 0)
    for i in range(n):
        MB.f([bot[i, 0], bot[i + 1, 0], top[i + 1, 0], top[i, 0]], 0)
        MB.f([top[i, n], top[i + 1, n], bot[i + 1, n], bot[i, n]], 0)
        MB.f([top[0, i], top[0, i + 1], bot[0, i + 1], bot[0, i]], 0)
        MB.f([bot[n, i], bot[n, i + 1], top[n, i + 1], top[n, i]], 0)


def fan_pavilion(L, coll):
    """Ribbed fan pavilion beside Sand tower (white frames, dark roof panels)."""
    P = SD.SAND_PAVILION_PX
    outer = resample(chaikin(SD.pts(P["outer"]), 2), count=15)
    inner = resample(chaikin(SD.pts(P["inner"]), 2), count=15)
    MB = MeshBuilder("EMP2_Sand_fan_pavilion_frames")
    RF = MeshBuilder("EMP2_Sand_fan_pavilion_roof")
    for k in range(len(outer)):
        a, b = outer[k], inner[k]
        d = norm(sub(b, a))
        n = (-d[1] * 0.2, d[0] * 0.2)
        pts = []
        for s in range(9):
            t = s / 8
            p = lerp(a, b, t)
            z = 3.5 + 3.0 * math.sin(math.pi * t)
            pts.append((p, z))
        for s in range(8):
            (p0, z0), (p1, z1) = pts[s], pts[s + 1]
            q = [add(p0, mul(n, -1)), add(p1, mul(n, -1)), add(p1, n), add(p0, n)]
            MB.quad_box(*ensure_ccw(q), min(z0, z1) - 0.25, max(z0, z1) + 0.05)
        for t, z in ((0.0, 3.5), (1.0, 3.5)):
            p = lerp(a, b, t)
            MB.box((p[0], p[1], z / 2), (0.35, 0.35, z))
        if k < len(outer) - 1:
            a2, b2 = outer[k + 1], inner[k + 1]
            for s in range(1, 7, 2):
                t0, t1 = s / 8, (s + 1) / 8
                q = [lerp(a, b, t0), lerp(a2, b2, t0), lerp(a2, b2, t1), lerp(a, b, t1)]
                z = 3.5 + 3.0 * math.sin(math.pi * (t0 + t1) / 2) + 0.05
                RF.quad_box(*ensure_ccw([lerp(mul(add(add(q[0], q[1]), add(q[2], q[3])), 0.25), p, 0.92) for p in q]), z - 0.06, z)
    MB.to_object(coll, [L["wall_white"]])
    RF.to_object(coll, [L["solar"]])
    return len(outer)


# ---------------------------------------------------------------------------
def build(L, root):
    data = json.load(open(os.path.join(os.path.dirname(__file__), "data", "site_vectors.json")))
    coll = bpy.data.collections.new("EMP2_45_Site_furniture_and_small_structures")
    root.children.link(coll)
    lib = bpy.data.collections.new("EMP2_48_Prop_library")
    root.children.link(lib)
    L["lamp_lens"] = materials.flat("EMP2_Lamp_lens", (0.95, 0.93, 0.85), rough=0.2)
    L["thatch"] = materials.flat("EMP2_Thatch", (0.55, 0.43, 0.26), rough=0.95)
    L["tyre"] = materials.flat("EMP2_Tyre_rubber", (0.03, 0.03, 0.03), rough=0.8)
    cm, nodes, links, bsdf = materials._new("EMP2_Car_paint_object_colour")
    oi = nodes.new("ShaderNodeObjectInfo")
    links.new(oi.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Coat Weight"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.4
    L["car_paint"] = cm
    rng = random.Random(2026)
    counts = {}
    lamp = lamp_mesh(L)
    parcel = [tuple(p) for p in data["parcel"]]
    # street lamps along internal roads
    n = 0
    for poly in data["asphalt"]:
        ring = ensure_ccw([tuple(p) for p in poly["outer"]])
        if poly["area"] < 150:
            continue
        L_ = sum(length(sub(ring[(i + 1) % len(ring)], ring[i])) for i in range(len(ring)))
        cnt = int(L_ // 30)
        if cnt < 2:
            continue
        pts = resample(ring + [ring[0]], count=cnt + 1)[:-1]
        for i, p in enumerate(pts):
            if not point_in_poly(p, parcel):
                continue
            q = pts[(i + 1) % len(pts)]
            d = norm(sub(q, p))
            right = (d[1], -d[0])
            loc = add(p, mul(right, 1.1))
            _obj("EMP2_Street_lamp", lamp, coll, (loc[0], loc[1], 0.2), math.atan2(-right[1], -right[0]))
            n += 1
    counts["street_lamps"] = n
    # pool loungers and parasols
    lounger, parasol = lounger_mesh(L), parasol_mesh(L)
    n = 0
    pools = [p for p in data["pool"] if p["area"] > 150]
    for p in pools:
        ring = ensure_ccw([tuple(q) for q in p["outer"]])
        Lr = sum(length(sub(ring[(i + 1) % len(ring)], ring[i])) for i in range(len(ring)))
        pts = resample(ring + [ring[0]], count=max(4, int(Lr // 3.4)))[:-1]
        for i, q in enumerate(pts):
            if i % 5 == 4:
                continue
            nx = pts[(i + 1) % len(pts)]
            d = norm(sub(nx, q))
            out = (d[1], -d[0])
            loc = add(q, mul(out, 3.0))
            yaw = math.atan2(-out[1], -out[0])
            _obj("EMP2_Pool_lounger", lounger, coll, (loc[0], loc[1], 0.2), yaw)
            if i % 2 == 0:
                pl = add(q, mul(out, 4.6))
                _obj("EMP2_Pool_parasol", parasol, coll, (pl[0], pl[1], 0.2))
            n += 1
    counts["pool_loungers"] = n
    # shade sails in the gardens
    SS = MeshBuilder("EMP2_Garden_shade_sails")
    for (cpx, size) in SD.CANOPIES_PX:
        c = SD.px(*cpx)
        shade_sail(SS, c, size, rng.uniform(0, math.pi))
    SS.to_object(coll, [L["canvas"], L["steel"]])
    counts["shade_sails"] = len(SD.CANOPIES_PX)
    # benches on the Arena ring
    bench = bench_mesh(L)
    c = SD.px(*SD.ARENA["centre_px"])
    r = (SD.ARENA["ring_path_inner_m"] + SD.ARENA["ring_path_outer_m"]) / 2 - 3.6
    k = 0
    for i in range(36):
        a = 2 * math.pi * i / 36
        if i % 9 == 0:
            continue
        p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
        _obj("EMP2_Bench", bench, coll, (p[0], p[1], 0.2), a + math.pi / 2)
        k += 1
    counts["benches"] = k
    # flagpoles at each tower drop-off
    import towers
    flag = flagpole_mesh(L)
    k = 0
    for T in SD.TOWERS:
        plan = towers.compute_plan(T)
        ent = towers.entrance(T, plan, MeshBuilder("x"), MeshBuilder("x"), MeshBuilder("x"))
        base = add(ent["canopy_center"], mul(ent["facing"], 14.0))
        for s in (-1, 0, 1):
            p = add(base, mul(ent["tangent"], s * 3.0))
            _obj("EMP2_Flagpole", flag, coll, (p[0], p[1], 0.2), math.atan2(ent["tangent"][1], ent["tangent"][0]))
            k += 1
    counts["flagpoles"] = k
    # beach parasols with loungers, in front of Sea and Sand towers
    bpar = parasol_mesh(L, thatched=True)
    wl = [tuple(p) for p in data["waterline"]]
    k = 0
    for y0, y1 in ((150.0, 300.0), (-230.0, -80.0)):
        line = offset_polyline(wl, 38.0)   # 38 m landward of the waterline
        for p in resample(line, step=7.0):
            if not (y0 <= p[1] <= y1):
                continue
            for row in (0.0, 9.0):
                q = add(p, (-row * 0.88, -row * 0.47))
                _obj("EMP2_Beach_parasol", bpar, coll, (q[0], q[1], 0.0))
                for s in (-1.1, 1.1):
                    _obj("EMP2_Beach_lounger", lounger, coll, (q[0] + 0.47 * s, q[1] - 0.88 * s, 0.0), math.atan2(0.47, 0.88))
                k += 1
    counts["beach_parasols"] = k
    # parked and moving cars (positions/orientation/colour from the aerial)
    car = car_mesh(L)
    import cameras
    cam_xy = [v[0][:2] for v in cameras.CAMERAS.values()]
    for x, y, ang, col in data["cars"]:
        if any(math.hypot(x - cx, y - cy) < 12.0 for cx, cy in cam_xy):
            continue
        g = sum(col) / 3
        col = [min(1.0, max(0.03, c * 0.9)) for c in col] if g > 0.15 else [0.05, 0.05, 0.06]
        _obj("EMP2_Car", car, coll, (x, y, 0.08), math.radians(ang), color=col)
        counts["cars"] = counts.get("cars", 0) + 1
    counts["fan_pavilion_ribs"] = fan_pavilion(L, coll)
    for vl in bpy.context.scene.view_layers:
        for lc in vl.layer_collection.children:
            for ch in lc.children:
                if ch.collection == lib:
                    ch.exclude = True
    return counts
