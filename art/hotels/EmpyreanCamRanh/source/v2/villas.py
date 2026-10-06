"""Shopvillas (traced as 68 twin blocks; 126 units published), the ballroom and service blocks.

Twin blocks follow the traced roof rectangles on the parcel grid.  Each block is
one closed mass: shopfront glazing on the ground floor of the lane façades,
recessed windows with glass balconies above, and grey pixel-pattern cladding on
the gable ends (as photographed along the villa streets).
"""
import math
import random
import bpy
import numpy as np
from lib_mesh import MeshBuilder, lerp, sub, add, mul, length, norm, ensure_ccw
from facade import CellWriter, prism_facade
import site_data as SD
import materials

VMAT = ["wall_white", "glass", "frame", "pixel_clad", "glass_shop", "wall_grey", "roof", "terrace", "soffit"]
VMI = {k: i for i, k in enumerate(VMAT)}
LEVELS = [0.0, 4.5, 8.3, 12.1]
PARAPET = 1.2


def gradient_cladding_image(name="EMP2_villa_cladding.png", w_m=9.6, h_m=14.4, ppm=40, seed=11):
    """Horizontal grey panels, darker toward the top of the gable."""
    rng = np.random.default_rng(seed)
    W, H = int(w_m * ppm), int(h_m * ppm)
    arr = np.zeros((H, W, 3), np.float32)
    pw, ph = int(1.2 * ppm), int(0.6 * ppm)
    greys = np.array([0.86, 0.74, 0.60, 0.46, 0.34], np.float32)
    rows = H // ph
    for r in range(rows):
        z = 1.0 - (r + 0.5) / rows               # image row 0 is the top in numpy, Blender flips later
        hz = 1.0 - z                             # 0 top .. 1 bottom (numpy space)
        top = 1.0 - hz
        weights = np.array([0.35 - 0.3 * top, 0.3 - 0.1 * top, 0.2, 0.1 + 0.25 * top, 0.05 + 0.2 * top])
        weights = np.clip(weights, 0.01, None)
        weights /= weights.sum()
        offset = (r % 2) * pw // 2
        for c in range(-1, W // pw + 2):
            x0 = c * pw + offset
            g = greys[rng.choice(len(greys), p=weights)] * rng.uniform(0.97, 1.03)
            xa, xb = max(0, x0), min(W, x0 + pw)
            if xb > xa:
                arr[r * ph:(r + 1) * ph, xa:xb, :] = g
            if 0 <= x0 < W:
                arr[r * ph:(r + 1) * ph, x0:x0 + 1, :] *= 0.8
        arr[r * ph:r * ph + 1, :, :] *= 0.8
    arr = arr[::-1]                               # Blender images start at the bottom row
    return materials._pack(name, arr)


def _rect(x0, y0, x1, y1):
    return [SD.rot(x0, y0), SD.rot(x1, y0), SD.rot(x1, y1), SD.rot(x0, y1)]


def villa_block(cw, rect, rng, roof_mb, rail_mb, hand_mb, slab_mb, uid):
    ring = ensure_ccw(rect)
    lengths = [length(sub(ring[(i + 1) % 4], ring[i])) for i in range(4)]
    # shopfronts face the lanes, which run along the parcel axis; gables face across it
    U = (math.cos(math.radians(SD.PARCEL_ROT_DEG)), math.sin(math.radians(SD.PARCEL_ROT_DEG)))
    long_edges = {i for i in range(4)
                  if abs(norm(sub(ring[(i + 1) % 4], ring[i]))[0] * U[0] + norm(sub(ring[(i + 1) % 4], ring[i]))[1] * U[1]) > 0.7}
    gable_windows = {}

    def spec(e, s, k):
        if e in long_edges:
            if k == 0:
                return dict(x0=0.05, x1=0.95, y0=0.04, y1=0.86, depth=0.35, glass="glass_shop", mullions=1,
                            transoms=[0.72], prof=0.08, spandrel="wall_grey", frame_mat=1)
            return dict(x0=0.12, x1=0.88, y0=0.06, y1=0.88, depth=0.45, mullions=1, transoms=[], prof=0.06,
                        sill="terrace", head="soffit", jamb="wall_white", rail=0.1, frame_mat=1)
        key = (e, s, k)
        if key not in gable_windows:
            gable_windows[key] = rng.random() < 0.28 and k > 0
        if gable_windows[key]:
            return dict(x0=0.3, x1=0.7, y0=0.35, y1=0.8, depth=0.2, mullions=1, transoms=[0.5], prof=0.05,
                        spandrel="pixel_clad", pier="pixel_clad", lintel="pixel_clad", frame_mat=1)
        return None
    cw.wall_mat = "pixel_clad"
    # cell width so that long sides get 6 bays (two 8.8 m units x 3)
    prism_facade(cw, ring, LEVELS, lambda e, s, k: _wall(cw, e, long_edges) or spec(e, s, k), "roof", "soffit",
                 cell_w=2.9, key=("V", uid))
    # parapet, stair/lift pavilion and pergola on the roof
    z = LEVELS[-1]
    c = mul(add(add(ring[0], ring[1]), add(ring[2], ring[3])), 0.25)
    for i in range(4):
        a, b = ring[i], ring[(i + 1) % 4]
        d = norm(sub(b, a))
        inward = (-d[1], d[0])
        roof_mb.quad_box(*ensure_ccw([a, b, add(b, mul(inward, 0.25)), add(a, mul(inward, 0.25))]), z, z + PARAPET)
    u = norm(sub(ring[1], ring[0]))
    v = norm(sub(ring[3], ring[0]))
    for side in (-1, 1):
        p = add(c, mul(u, side * lengths[0] * 0.22))
        box = [add(add(p, mul(u, -1.6)), mul(v, -2.0)), add(add(p, mul(u, 1.6)), mul(v, -2.0)),
               add(add(p, mul(u, 1.6)), mul(v, 2.0)), add(add(p, mul(u, -1.6)), mul(v, 2.0))]
        roof_mb.quad_box(*ensure_ccw(box), z, z + 3.0)
    # cantilevered balcony slabs on the lane façades, floors 2-3
    for e in long_edges:
        a, b = ring[e], ring[(e + 1) % 4]
        d = norm(sub(b, a))
        out = (d[1], -d[0])
        for k in (1, 2):
            zb = LEVELS[k] - 0.18
            q = [add(a, mul(d, 0.6)), add(b, mul(d, -0.6)), add(add(b, mul(d, -0.6)), mul(out, 1.3)),
                 add(add(a, mul(d, 0.6)), mul(out, 1.3))]
            slab_mb.quad_box(*ensure_ccw(q), zb, zb + 0.2)
            p0 = add(q[3], mul(out, -0.08)); p1 = add(q[2], mul(out, -0.08))
            CellWriter._panel(rail_mb, (*p0, zb + 0.2), (*p1, zb + 0.2), 1.05, 0.02, (*out, 0))
            CellWriter._panel(hand_mb, (*p0, zb + 1.22), (*p1, zb + 1.22), 0.05, 0.06, (*out, 0))


def _wall(cw, e, long_edges):
    cw.wall_mat = "wall_white" if e in long_edges else "pixel_clad"
    return None


def build(L, root):
    coll = bpy.data.collections.new("EMP2_30_Shopvillas_and_ballroom")
    root.children.link(coll)
    L["villa_clad"] = materials.image_material("EMP2_Villa_pixel_cladding", gradient_cladding_image(), 1.0,
                                               rough=0.5, coat=0.15)
    L["villa_clad"].node_tree.nodes["Mapping"].inputs["Scale"].default_value = (1 / 9.6, 1 / 9.6, 1 / 14.4)
    rng = random.Random(126)
    cw = CellWriter("EMP2_Shopvillas", VMI, seed=126)
    roof_mb = MeshBuilder("EMP2_Shopvilla_roof_parapets_and_pavilions")
    rail_mb = MeshBuilder("EMP2_Shopvilla_balcony_glass")
    hand_mb = MeshBuilder("EMP2_Shopvilla_handrails")
    slab_mb = MeshBuilder("EMP2_Shopvilla_balcony_slabs")
    blocks = 0
    for r in SD.VILLA_BLOCKS_ROT:
        villa_block(cw, _rect(*r), rng, roof_mb, rail_mb, hand_mb, slab_mb, blocks)
        blocks += 1
    mats = [L[k] if k != "pixel_clad" else L["villa_clad"] for k in VMAT]
    cw.B.name = "EMP2_Shopvilla_blocks"
    cw.B.to_object(coll, mats)
    cw.F.to_object(coll, [L["frame"], L["frame_dark"]])
    cw.R.to_object(coll, [L["rail_glass"]])
    cw.H.to_object(coll, [L["steel"]])
    roof_mb.to_object(coll, [L["wall_white"]])
    rail_mb.to_object(coll, [L["rail_glass"]])
    hand_mb.to_object(coll, [L["steel"]])
    slab_mb.to_object(coll, [L["wall_white"]])
    # ballroom with dark gridded roof
    bw = CellWriter("EMP2_Ballroom", VMI, seed=3)
    ring = ensure_ccw(_rect(*SD.BALLROOM_ROT))
    lens = [length(sub(ring[(i + 1) % 4], ring[i])) for i in range(4)]

    def bspec(e, s, k):
        bw.wall_mat = "wall_white"
        if lens[e] > 50 and s % 3 != 1:
            return dict(x0=0.04, x1=0.96, y0=0.03, y1=0.7, depth=0.35, glass="glass_shop", mullions=2,
                        transoms=[0.6], prof=0.08, spandrel="wall_grey", frame_mat=1)
        return None
    prism_facade(bw, ring, [0.0, 9.0], bspec, "roof", "soffit", cell_w=3.6, key="BR")
    bw.B.name = "EMP2_Ballroom_Solis"
    mats_b = [L[k] for k in VMAT[:3]] + [L["villa_clad"]] + [L[k] for k in VMAT[4:]]
    bw.B.to_object(coll, mats_b)
    bw.F.to_object(coll, [L["frame"], L["frame_dark"]])
    roofgrid = MeshBuilder("EMP2_Ballroom_roof_grid")
    inset = [lerp(p, mul(add(add(ring[0], ring[1]), add(ring[2], ring[3])), 0.25), 0.03) for p in ring]
    roofgrid.quad_box(*ensure_ccw(inset), 9.0, 9.35)
    roofgrid.to_object(coll, [L["ballroom_roof"]])
    # service block
    sv = MeshBuilder("EMP2_Service_block")
    for r in SD.SERVICE_BLOCKS_ROT:
        sv.prism(ensure_ccw(_rect(*r)), 0.0, 7.5)
    sv.to_object(coll, [L["wall_white"]])
    return dict(twin_blocks=blocks, units=blocks * 2)
