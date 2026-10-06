"""Ground, roads, paving, lawns, pools, Arena Square, west lagoon, beach and sea.

Landcover polygons in data/site_vectors.json were traced from the aerial
imagery (see README_V2.txt).  Each class is a closed slab at its own level so
kerbs read correctly: asphalt lowest, paving +12 cm, lawns +16 cm, pools cut
into the parcel slab with tiled basins under the water.
"""
import json
import math
import os
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from lib_mesh import (MeshBuilder, ensure_ccw, polygon_area, offset_polyline, chaikin, add, mul, sub, norm, length,
                      lerp, point_in_poly)
import site_data as SD
import materials

Z = dict(base=0.0, parcel=0.05, asphalt=0.08, scrub=0.10, paving=0.20, lawn=0.24, coping=0.30, water=0.18)


def _seg_dist(p, a, b):
    ab = sub(b, a)
    L2 = ab[0] ** 2 + ab[1] ** 2
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / L2))
    return length(sub(p, add(a, mul(ab, t))))


def _valid_holes(outer, holes, gap=0.08):
    """Keep holes fully inside the outer ring and clear of its edges and of each other."""
    keep = []
    n = len(outer)
    for h in holes:
        ok = all(point_in_poly(p, outer) for p in h)
        if ok:
            for p in h:
                if min(_seg_dist(p, outer[i], outer[(i + 1) % n]) for i in range(n)) < gap:
                    ok = False
                    break
        if ok:
            for k in keep:
                if any(point_in_poly(p, k) for p in h) or any(point_in_poly(p, h) for p in k):
                    ok = False
                    break
        if ok:
            keep.append(h)
    return keep


def _self_intersects(ring):
    n = len(ring)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            c, d = ring[j], ring[(j + 1) % n]
            if max(a[0], b[0]) < min(c[0], d[0]) or max(c[0], d[0]) < min(a[0], b[0]):
                continue
            if max(a[1], b[1]) < min(c[1], d[1]) or max(c[1], d[1]) < min(a[1], b[1]):
                continue
            d1, d2 = cross(c, d, a), cross(c, d, b)
            d3, d4 = cross(a, b, c), cross(a, b, d)
            if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
                return True
    return False


class BadPolygon(Exception):
    pass


def slab(MB, outer, holes, z_top, z_bot, mat_top=0, mat_side=0):
    """Closed slab with holes: tessellated top/bottom + side walls."""
    outer = ensure_ccw(outer)
    if _self_intersects(outer):
        raise BadPolygon("self-intersecting outline")
    holes = [h for h in holes if not _self_intersects(h)]
    holes = _valid_holes(outer, [ensure_ccw(h) for h in holes])
    rings = [outer] + [list(reversed(h)) for h in holes]
    flat = []
    vt, vb = [], []
    for r in rings:
        vt.append([MB.vnew((p[0], p[1], z_top)) for p in r])
        vb.append([MB.vnew((p[0], p[1], z_bot)) for p in r])
        flat.append(r)
    tris = tessellate_polygon([[Vector((p[0], p[1], 0)) for p in r] for r in flat])
    lut_t, lut_b = [], []
    for k, r in enumerate(flat):
        lut_t += vt[k]
        lut_b += vb[k]
    for tri in tris:
        a, b, c = tri
        pa, pb, pc = (MB.verts[lut_t[i]] for i in (a, b, c))
        cross = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0])
        if cross >= 0:
            MB.f([lut_t[a], lut_t[b], lut_t[c]], mat_top)
            MB.f([lut_b[c], lut_b[b], lut_b[a]], mat_side)
        else:
            MB.f([lut_t[c], lut_t[b], lut_t[a]], mat_top)
            MB.f([lut_b[a], lut_b[b], lut_b[c]], mat_side)
    for k in range(len(rings)):
        n = len(rings[k])
        for i in range(n):
            j = (i + 1) % n
            MB.f([vb[k][i], vb[k][j], vt[k][j], vt[k][i]], mat_side)


def _clean(poly, min_seg=0.05):
    out = []
    for p in poly:
        if not out or length(sub(p, out[-1])) > min_seg:
            out.append(tuple(p))
    if len(out) > 3 and length(sub(out[0], out[-1])) < min_seg:
        out.pop()
    return out


def sea_material():
    m, nodes, links, bsdf = materials._new("EMP2_South_China_Sea")
    geo = nodes.new("ShaderNodeNewGeometry")
    p0 = SD.px(2703, 411)
    n = norm((470.5, 255.5))
    dot = nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    dot.inputs[1].default_value = (n[0], n[1], 0.0)
    links.new(geo.outputs["Position"], dot.inputs[0])
    off = nodes.new("ShaderNodeMath"); off.operation = "SUBTRACT"
    off.inputs[1].default_value = p0[0] * n[0] + p0[1] * n[1]
    links.new(dot.outputs["Value"], off.inputs[0])
    mr = nodes.new("ShaderNodeMapRange"); mr.inputs["From Min"].default_value = 0.0; mr.inputs["From Max"].default_value = 260.0
    links.new(off.outputs["Value"], mr.inputs["Value"])
    ramp = nodes.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    e[0].position = 0.0; e[0].color = (0.30, 0.72, 0.64, 1)
    e[1].position = 0.35; e[1].color = (0.01, 0.36, 0.40, 1)
    e3 = e.new(1.0); e3.color = (0.005, 0.12, 0.24, 1)
    links.new(mr.outputs["Result"], ramp.inputs["Fac"])
    # surf foam close to the waterline
    foam_n = nodes.new("ShaderNodeTexNoise"); foam_n.inputs["Scale"].default_value = 0.35; foam_n.inputs["Detail"].default_value = 8
    links.new(geo.outputs["Position"], foam_n.inputs["Vector"])
    band = nodes.new("ShaderNodeMapRange"); band.inputs["From Min"].default_value = 0.0; band.inputs["From Max"].default_value = 12.0
    band.inputs["To Min"].default_value = 1.0; band.inputs["To Max"].default_value = 0.0
    links.new(off.outputs["Value"], band.inputs["Value"])
    fm = nodes.new("ShaderNodeMath"); fm.operation = "MULTIPLY"
    links.new(band.outputs["Result"], fm.inputs[0]); links.new(foam_n.outputs["Fac"], fm.inputs[1])
    fth = nodes.new("ShaderNodeMath"); fth.operation = "GREATER_THAN"; fth.inputs[1].default_value = 0.42
    links.new(fm.outputs["Value"], fth.inputs[0])
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    links.new(fth.outputs["Value"], mix.inputs["Factor"])
    links.new(ramp.outputs["Color"], mix.inputs["A"]); mix.inputs["B"].default_value = (0.9, 0.93, 0.92, 1)
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    rr = nodes.new("ShaderNodeMapRange"); rr.inputs["To Min"].default_value = 0.03; rr.inputs["To Max"].default_value = 0.6
    links.new(fth.outputs["Value"], rr.inputs["Value"]); links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    wave = nodes.new("ShaderNodeTexWave"); wave.inputs["Scale"].default_value = 0.08; wave.inputs["Distortion"].default_value = 6
    wave.inputs["Detail"].default_value = 6
    links.new(geo.outputs["Position"], wave.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
    links.new(wave.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.45
    m.diffuse_color = (0.02, 0.3, 0.35, 1)
    return m


def water_material():
    m, nodes, links, bsdf = materials._new("EMP2_Pool_water")
    bsdf.inputs["Base Color"].default_value = (0.75, 0.95, 0.97, 1)
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = 1.333
    vol = nodes.new("ShaderNodeVolumeAbsorption")
    vol.inputs["Color"].default_value = (0.55, 0.88, 0.92, 1)
    vol.inputs["Density"].default_value = 0.35
    out = nodes["Material Output"]
    links.new(vol.outputs["Volume"], out.inputs["Volume"])
    tc = nodes.new("ShaderNodeTexCoord")
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.9; nz.inputs["Detail"].default_value = 4
    links.new(tc.outputs["Object"], nz.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.08
    links.new(nz.outputs["Fac"], bump.inputs["Height"]); links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    m.diffuse_color = (0.2, 0.6, 0.7, 1)
    return m


def _lawn4k(name, tint, size=2.5, base="leafy_grass"):
    m, nodes, links, bsdf = materials._new(name)
    vec = materials._mapping(nodes, links, size)
    d = materials._tex(nodes, links, materials._img(f"{base}_diff_4k.jpg"), vec, False)
    hs = nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.0
    links.new(d.outputs["Color"], hs.inputs["Color"])
    mix = nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1.0
    links.new(hs.outputs["Color"], mix.inputs["A"]); mix.inputs["B"].default_value = (*tint, 1)
    # large-scale variation so lawns are not a uniform tile
    nz = nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.04; nz.inputs["Detail"].default_value = 3
    tc = nodes.new("ShaderNodeTexCoord"); links.new(tc.outputs["Object"], nz.inputs["Vector"])
    var = nodes.new("ShaderNodeMix"); var.data_type = "RGBA"; var.blend_type = "MULTIPLY"
    links.new(nz.outputs["Fac"], var.inputs["Factor"])
    links.new(mix.outputs["Result"], var.inputs["A"]); var.inputs["B"].default_value = (0.85, 0.9, 0.75, 1)
    links.new(var.outputs["Result"], bsdf.inputs["Base Color"])
    r = materials._tex(nodes, links, materials._img(f"{base}_rough_4k.jpg", "Non-Color"), vec, False)
    links.new(r.outputs["Color"], bsdf.inputs["Roughness"])
    n = materials._tex(nodes, links, materials._img(f"{base}_nor_gl_4k.jpg", "Non-Color"), vec, False)
    nm = nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.7
    links.new(n.outputs["Color"], nm.inputs["Color"]); links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    m.diffuse_color = (*tint, 1)
    return m


def build(L, root):
    data = json.load(open(os.path.join(os.path.dirname(__file__), "data", "site_vectors.json")))
    coll = bpy.data.collections.new("EMP2_20_Site_ground_roads_pools")
    root.children.link(coll)
    L["lawn"] = _lawn4k("EMP2_Lawn_irrigated", (0.50, 0.95, 0.30))
    L["scrub"] = _lawn4k("EMP2_Dune_scrub", (0.62, 0.62, 0.40), size=4.0)
    L["sand"] = _lawn4k("EMP2_Beach_sand", (1.0, 0.88, 0.70), size=30.0, base="aerial_beach_01")
    L["sea"] = sea_material()
    L["water"] = water_material()
    L["paint_white"] = materials.flat("EMP2_Road_paint_white", (0.86, 0.86, 0.84), rough=0.6)
    L["paint_yellow"] = materials.flat("EMP2_Road_paint_yellow", (0.85, 0.62, 0.08), rough=0.6)
    stats = {}
    # base terrain: big sand plane with a hole for the parcel
    parcel = [tuple(p) for p in data["parcel"]]
    R = 12000.0
    big = [(-R, -R), (R, -R), (R, R), (-R, R)]
    T = MeshBuilder("EMP2_Ground_terrain_sand")
    slab(T, big, [parcel], Z["base"], -1.0)
    T.to_object(coll, [L["sand"]])
    # sea: from the waterline out to the horizon
    wl = [tuple(p) for p in data["waterline"]]
    d0 = norm(sub(wl[0], wl[1])); d1 = norm(sub(wl[-1], wl[-2]))
    start = add(wl[0], mul(d0, 14000)); end = add(wl[-1], mul(d1, 14000))
    nrm = norm((470.5, 255.5))
    far1 = add(end, mul(nrm, 14000)); far0 = add(start, mul(nrm, 14000))
    sea_ring = [start] + wl + [end, far1, far0]
    S = MeshBuilder("EMP2_Sea_surface")
    slab(S, sea_ring, [], 0.03, -3.0)
    S.to_object(coll, [L["sea"]])
    # parcel slab (with pool holes)
    pools = [dict(outer=p["outer"], area=p["area"], kind="pool") for p in data["pool"]]
    (a, b, r) = SD.WIND_POOL_PX
    pa, pb = SD.px(*a), SD.px(*b)
    ax = norm(sub(pb, pa)); rr = r * SD.M_PER_PX
    cap = []
    ang0 = math.atan2(ax[1], ax[0])
    for k in range(17):
        t = ang0 - math.pi / 2 + math.pi * k / 16
        cap.append((pb[0] + rr * math.cos(t), pb[1] + rr * math.sin(t)))
    for k in range(17):
        t = ang0 + math.pi / 2 + math.pi * k / 16
        cap.append((pa[0] + rr * math.cos(t), pa[1] + rr * math.sin(t)))
    pools.append(dict(outer=cap, area=600, kind="pool"))
    (c0, r0) = SD.WIND_SMALL_POOL_PX
    cc = SD.px(*c0); rr = r0 * SD.M_PER_PX
    pools.append(dict(outer=[(cc[0] + rr * math.cos(2 * math.pi * k / 28), cc[1] + rr * math.sin(2 * math.pi * k / 28)) for k in range(28)], area=60, kind="pool"))
    rim = ensure_ccw(chaikin(SD.pts(SD.LAGOON_RIM_PX), 2, closed=True))
    lagoon_water = rim
    for d in (3.2, 2.4, 1.6, 0.8):
        cand = ensure_ccw(offset_polyline(rim, d, closed=True))
        if not _self_intersects(cand):
            lagoon_water = cand
            break
    pools.append(dict(outer=lagoon_water, area=6000, kind="lagoon"))
    explicit = pools[-3:]
    P = MeshBuilder("EMP2_Ground_parcel_base")
    slab(P, parcel, [_clean(p["outer"]) for p in pools], Z["parcel"], -0.4)
    P.to_object(coll, [L["pavers"]])
    skipped = {}
    for key, mat, z in (("asphalt", "asphalt", Z["asphalt"]), ("paving", "pavers", Z["paving"]),
                        ("lawn", "lawn", Z["lawn"]), ("scrub", "scrub", Z["scrub"])):
        MB = MeshBuilder(f"EMP2_Ground_{key}")
        cnt = 0
        for poly in data[key]:
            outer = _clean(poly["outer"])
            holes = [_clean(h) for h in poly["holes"] if len(h) >= 3]
            if len(outer) < 3:
                continue
            if key in ("paving", "lawn"):
                holes += [ensure_ccw(_clean(pp["outer"])) for pp in explicit
                          if all(point_in_poly(q, outer) for q in pp["outer"])]
            try:
                slab(MB, outer, [h for h in holes if len(h) >= 3], z, -0.35, 0, 1)
                cnt += 1
            except BadPolygon:  # skip self-intersecting traces rather than fail the build
                skipped[key] = skipped.get(key, 0) + 1
        side = L["curb"] if key in ("paving", "lawn") else L[mat]
        MB.to_object(coll, [L[mat], side])
        stats[key] = cnt
    # pools: tiled basin, water volume and stone coping
    basin = MeshBuilder("EMP2_Pool_basins")
    water = MeshBuilder("EMP2_Pool_water")
    coping = MeshBuilder("EMP2_Pool_coping")
    basin_rect = ensure_ccw(SD.pts(SD.LAGOON_BASIN_PX))
    deep = MeshBuilder("EMP2_Lagoon_deep_basin")
    for p in pools:
        ring = ensure_ccw(_clean(p["outer"]))
        if len(ring) < 3:
            continue
        depth = -1.4 if p["area"] > 40 else -0.9
        if p["kind"] == "lagoon":
            depth = -0.8
            slab(deep, basin_rect, [], depth - 1.6, depth - 1.8)
            deep.ribbon(basin_rect, 0.2, depth - 1.8, depth + 0.01, offset=-0.1, closed=True)
            slab(water, basin_rect, [], depth + 0.01, depth - 1.59)       # water filling the deep basin
        else:
            slab(basin, ring, [], depth, depth - 0.2)
        basin.ribbon(ring, 0.2, depth - 0.2, Z["water"] - 0.02, offset=-0.1, closed=True)
        slab(water, ring, [], Z["water"], depth + 0.01)
        coping.ribbon(ring, 0.42, Z["paving"] - 0.05, Z["coping"], closed=True, offset=-0.19)
    # the lagoon floor around the deep basin
    LF = MeshBuilder("EMP2_Lagoon_floor")
    slab(LF, lagoon_water, [offset_polyline(basin_rect, -0.05, closed=True)], -0.8, -1.0)
    LF.to_object(coll, [materials.flat("EMP2_Lagoon_floor_render", (0.72, 0.86, 0.86), rough=0.6)])
    deep.to_object(coll, [materials.flat("EMP2_Lagoon_basin_green_tile", (0.03, 0.22, 0.14), rough=0.4)])
    basin.to_object(coll, [L["pool_tile"]])
    water.to_object(coll, [L["water"]])
    coping.to_object(coll, [L["plaza_light"]])
    stats["pools"] = len(pools)
    stats["skipped_self_intersecting"] = skipped
    # road markings
    MK = MeshBuilder("EMP2_Road_markings")
    for m in data["markings"]:
        p0, p1 = m["p0"], m["p1"]
        d = norm(sub(p1, p0)); n = (-d[1] * m["w"] / 2, d[0] * m["w"] / 2)
        q = [add(p0, mul(n, -1)), add(p1, mul(n, -1)), add(p1, n), add(p0, n)]
        MK.quad_box(*ensure_ccw(q), Z["asphalt"], Z["asphalt"] + 0.006, mat=0 if m["c"] == "white" else 1)
    MK.to_object(coll, [L["paint_white"], L["paint_yellow"]])
    stats["markings"] = len(data["markings"])
    # west lagoon (dark water) by the main road
    lake = ensure_ccw(chaikin(SD.pts(SD.WEST_LAKE_PX), 2, closed=True))
    LW = MeshBuilder("EMP2_West_lagoon_water")
    slab(LW, offset_polyline(lake, -0.3, closed=True), [], Z["lawn"] - 0.08, -1.0)
    LW.to_object(coll, [materials.flat("EMP2_Lagoon_water", (0.03, 0.09, 0.07), rough=0.05, coat=1.0)])
    LE = MeshBuilder("EMP2_West_lagoon_edge")
    LE.ribbon(lake, 0.6, Z["lawn"] - 0.3, Z["lawn"] + 0.06, closed=True)
    LE.to_object(coll, [L["plaza_light"]])
    stats["arena"] = arena(L, coll)
    return stats


def arena(L, coll):
    """Arena Square: radial checker plaza, west grandstand, east stage, statue."""
    A = SD.ARENA
    c = SD.px(*A["centre_px"])
    r = A["plaza_radius_m"]
    focus = SD.px(*A["checker_focus_px"])
    # checker plaza as polar cells around the focus point, clipped to the disc
    MB = MeshBuilder("EMP2_Arena_Square_checker_paving")
    rings, sectors = 16, 40
    zt = Z["paving"] + 0.04
    cells = 0
    for i in range(rings):
        for j in range(sectors):
            pts = []
            for (ri, sj) in ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j)):
                ang = 2 * math.pi * sj / sectors
                rad = (ri / rings) ** 1.15
                # map unit polar coords from the focus to the plaza circle boundary
                d = (math.cos(ang), math.sin(ang))
                # distance from focus to circle along d
                fx, fy = focus[0] - c[0], focus[1] - c[1]
                b = fx * d[0] + fy * d[1]
                cc = fx * fx + fy * fy - r * r
                t = -b + math.sqrt(max(b * b - cc, 0.0))
                pts.append((focus[0] + d[0] * t * rad, focus[1] + d[1] * t * rad))
            mat = (i + j) % 2
            ring = ensure_ccw(pts)
            if abs(polygon_area(ring)) < 1e-3:
                continue
            MB.prism(ring, zt - 0.1, zt, mat_side=mat, mat_top=mat, mat_bot=mat)
            cells += 1
    MB.to_object(coll, [L["plaza_light"], L["plaza_dark"]])
    # grandstand: concentric steps on the west half
    GS = MeshBuilder("EMP2_Arena_grandstand_steps")
    steps = 8
    axis = 180.0 + SD.PARCEL_ROT_DEG          # boulevard entry from the shopvilla district
    for (a0d, a1d) in ((112.0, axis - 9.0), (axis + 9.0, 248.0)):
        a0, a1 = math.radians(a0d), math.radians(a1d)
        for s in range(steps):
            r0 = r + s * 1.0
            r1 = r0 + 1.0
            arc = [(c[0] + r0 * math.cos(a), c[1] + r0 * math.sin(a)) for a in [a0 + (a1 - a0) * k / 30 for k in range(31)]]
            arc2 = [(c[0] + r1 * math.cos(a), c[1] + r1 * math.sin(a)) for a in [a0 + (a1 - a0) * k / 30 for k in reversed(range(31))]]
            GS.prism(ensure_ccw(arc + arc2), Z["paving"], Z["paving"] + 0.45 * (s + 1), mat_side=0, mat_top=1)
    GS.to_object(coll, [L["plaza_light"], L["plaza_light"]])
    # stage: curved platform + canopy frame on the east edge
    st = SD.px(*A["stage_px"])
    ST = MeshBuilder("EMP2_Arena_water_music_stage")
    arc_o = [(c[0] + (r + 2) * math.cos(a), c[1] + (r + 2) * math.sin(a)) for a in [math.radians(-40 + 80 * k / 30) for k in range(31)]]
    arc_i = [(c[0] + (r - 9) * math.cos(a), c[1] + (r - 9) * math.sin(a)) for a in [math.radians(40 - 80 * k / 30) for k in range(31)]]
    ST.prism(ensure_ccw(arc_o + arc_i), Z["paving"], Z["paving"] + 1.2, mat_side=0, mat_top=1)
    for k in range(0, 31, 5):
        a = math.radians(-40 + 80 * k / 30)
        p = (c[0] + (r + 1) * math.cos(a), c[1] + (r + 1) * math.sin(a))
        ST.cylinder((p[0], p[1], Z["paving"] + 1.2), 0.25, 9.0, seg=12, mat=2)
    ST.ribbon(arc_o, 1.2, Z["paving"] + 10.0, Z["paving"] + 10.8, mat=2, offset=0.6)
    ST.to_object(coll, [L["plaza_dark"], L["deck"], L["frame"]])
    # Ali & Nino moving statue (two stylised stacked steel figures, 8.5 m)
    SDt = MeshBuilder("EMP2_Arena_Ali_and_Nino_statue")
    sp = SD.px(*A["statue_px"])
    for side, dx in ((0, -1.4), (1, 1.4)):
        for k in range(14):
            z0 = Z["paving"] + 0.6 + k * 0.56
            w = 0.7 + 0.5 * math.sin(k / 13 * math.pi) * (1.0 if side else 0.8)
            SDt.box((sp[0] + dx * (1 - k / 20), sp[1] + 0.12 * math.sin(k), z0 + 0.25), (w, 0.35, 0.5), rot_z=0.15 * k + side * 0.4)
    SDt.cylinder((sp[0], sp[1], Z["paving"]), 3.0, 0.6, seg=32, mat=1)
    SDt.to_object(coll, [L["steel"], L["plaza_dark"]])
    return dict(checker_cells=cells)
