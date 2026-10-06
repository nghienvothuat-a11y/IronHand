"""PBR materials for the v2 rebuild.

Image textures are CC0 Poly Haven scans (see ../textures/licenses.json), box-
projected in object space so façades need no UV unwrap.  A few patterns that
only exist on this building (mosaic bands, villa pixel cladding, plaza checker,
solar panels) are generated procedurally into packed images.
"""
import math
import os
import random
import bpy
import numpy as np

TEX_DIR = None  # set by build.py


def _img(name, colorspace="sRGB"):
    path = os.path.join(TEX_DIR, name)
    im = bpy.data.images.get(name)
    if im is None:
        im = bpy.data.images.load(path, check_existing=True)
    im.colorspace_settings.name = colorspace
    return im


def _new(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def _mapping(nodes, links, size_m, coord="Object"):
    tc = nodes.new("ShaderNodeTexCoord")
    mp = nodes.new("ShaderNodeMapping")
    s = 1.0 / size_m
    mp.inputs["Scale"].default_value = (s, s, s)
    links.new(tc.outputs[coord], mp.inputs["Vector"])
    return mp


def _tex(nodes, links, image, vec, box=True, blend=0.25):
    t = nodes.new("ShaderNodeTexImage")
    t.image = image
    if box:
        t.projection = "BOX"
        t.projection_blend = blend
    links.new(vec.outputs["Vector"], t.inputs["Vector"])
    return t


def pbr(name, base, size_m, tint=(1, 1, 1), sat=0.6, bright=1.0, rough=(0.35, 0.95), nrm=0.6,
        metal=0.0, box=True, coat=0.0, coord="Object", spec=0.5):
    """Scanned texture material, tinted toward the measured façade colour."""
    m, nodes, links, bsdf = _new(name)
    vec = _mapping(nodes, links, size_m, coord)
    d = _tex(nodes, links, _img(f"{base}_diff_2k.jpg"), vec, box)
    hs = nodes.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = sat
    hs.inputs["Value"].default_value = bright
    links.new(d.outputs["Color"], hs.inputs["Color"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    links.new(hs.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (*tint, 1)
    links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    r = _tex(nodes, links, _img(f"{base}_rough_2k.jpg", "Non-Color"), vec, box)
    mr = nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = rough[0]
    mr.inputs["To Max"].default_value = rough[1]
    links.new(r.outputs["Color"], mr.inputs["Value"])
    links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])
    if nrm > 0:
        n = _tex(nodes, links, _img(f"{base}_nor_gl_2k.jpg", "Non-Color"), vec, box)
        nm = nodes.new("ShaderNodeNormalMap")
        nm.inputs["Strength"].default_value = nrm
        links.new(n.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Specular IOR Level"].default_value = spec
    if coat:
        bsdf.inputs["Coat Weight"].default_value = coat
    m.diffuse_color = (*[c * 0.75 for c in tint], 1)
    return m


def flat(name, color, rough=0.5, metal=0.0, transmission=0.0, ior=1.5, coat=0.0, thin=False, alpha=1.0):
    m, nodes, links, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Transmission Weight"].default_value = transmission
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Coat Weight"].default_value = coat
    if thin:
        bsdf.inputs["Thin Wall"].default_value = True
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
    m.diffuse_color = (*color, 1)
    return m


def glazing(name, base=(0.035, 0.07, 0.085), curtain=(0.66, 0.62, 0.54), sheer=(0.30, 0.33, 0.33),
            closed=0.18, half=0.22):
    """Reflective room glazing.  Each pane carries a random 'pane_rand' face
    attribute: most panes read as dark reflective glass, some show sheer or
    drawn curtains, so the façade is not a uniform tint."""
    m, nodes, links, bsdf = _new(name)
    at = nodes.new("ShaderNodeAttribute")
    at.attribute_type = "GEOMETRY"
    at.attribute_name = "pane_rand"
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    e = ramp.color_ramp.elements
    e[0].position = 0.0
    e[0].color = (*base, 1)
    e[1].position = 1.0 - closed - half
    e[1].color = (*sheer, 1)
    e3 = e.new(1.0 - closed)
    e3.color = (*curtain, 1)
    links.new(at.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    rr = nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value = 1.0 - closed - half
    rr.inputs["From Max"].default_value = 1.0
    rr.inputs["To Min"].default_value = 0.04
    rr.inputs["To Max"].default_value = 0.35
    links.new(at.outputs["Fac"], rr.inputs["Value"])
    links.new(rr.outputs["Result"], bsdf.inputs["Roughness"])
    bsdf.inputs["Specular IOR Level"].default_value = 0.75
    bsdf.inputs["Coat Weight"].default_value = 0.7
    bsdf.inputs["Coat Roughness"].default_value = 0.02
    m.diffuse_color = (*base, 1)
    return m


# ---------------------------------------------------------------------------
# Generated pattern images (packed into the .blend)
# ---------------------------------------------------------------------------
def _pack(name, arr):
    h, w, _ = arr.shape
    im = bpy.data.images.get(name)
    if im:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = arr
    im.pixels.foreach_set(rgba.ravel())
    im.pack()
    return im


def mosaic_image(name, palette, tiles=40, tile_px=12, grout=(0.86, 0.86, 0.84), seed=1):
    rng = np.random.default_rng(seed)
    n = tiles * tile_px
    arr = np.zeros((n, n, 3), np.float32)
    pal = np.array(palette, np.float32)
    idx = rng.integers(0, len(pal), size=(tiles, tiles))
    jitter = rng.uniform(0.9, 1.1, size=(tiles, tiles, 1))
    cols = pal[idx] * jitter
    arr[:] = np.repeat(np.repeat(cols, tile_px, 0), tile_px, 1)
    g = max(1, tile_px // 8)
    for k in range(tiles):
        arr[k * tile_px:k * tile_px + g, :, :] = grout
        arr[:, k * tile_px:k * tile_px + g, :] = grout
    return _pack(name, np.clip(arr, 0, 1))


def solar_image(name, cols=6, rows=10, cell_px=24):
    w, h = cols * cell_px, rows * cell_px
    arr = np.zeros((h, w, 3), np.float32)
    arr[:] = (0.035, 0.05, 0.11)
    for c in range(cols + 1):
        arr[:, min(c * cell_px, w - 1):min(c * cell_px + 1, w), :] = (0.55, 0.58, 0.62)
    for r in range(rows + 1):
        arr[min(r * cell_px, h - 1):min(r * cell_px + 1, h), :, :] = (0.55, 0.58, 0.62)
    return _pack(name, arr)


def image_material(name, image, size_m, rough=0.5, metal=0.0, nrm_noise=0.0, box=True, coat=0.0):
    m, nodes, links, bsdf = _new(name)
    vec = _mapping(nodes, links, size_m)
    t = _tex(nodes, links, image, vec, box, 0.1)
    t.interpolation = "Closest"
    links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    return m


# ---------------------------------------------------------------------------
def build_library():
    L = {}
    L["wall_white"] = pbr("EMP2_Wall_white_render", "painted_plaster_wall", 3.0, tint=(0.93, 0.92, 0.88), sat=0.15, bright=1.25, rough=(0.55, 0.9), nrm=0.35)
    L["wall_beige"] = pbr("EMP2_Wall_beige_render", "beige_wall_001", 2.5, tint=(0.90, 0.80, 0.66), sat=0.5, bright=1.05, rough=(0.6, 0.9), nrm=0.35)
    L["wall_grey"] = pbr("EMP2_Wall_light_grey", "painted_plaster_wall", 3.0, tint=(0.70, 0.71, 0.71), sat=0.1, bright=1.15, rough=(0.55, 0.9), nrm=0.3)
    L["soffit"] = pbr("EMP2_Soffit_white", "painted_plaster_wall", 3.0, tint=(0.88, 0.88, 0.86), sat=0.1, bright=1.2, rough=(0.7, 0.95), nrm=0.2)
    L["mosaic_blue"] = image_material("EMP2_Mosaic_blue_band", mosaic_image("EMP2_mosaic_blue.png", [[0.05, 0.12, 0.42], [0.08, 0.18, 0.55], [0.03, 0.08, 0.30], [0.12, 0.25, 0.62]], seed=3), 1.0, rough=0.25, coat=0.4)
    L["mosaic_terracotta"] = image_material("EMP2_Mosaic_terracotta_band", mosaic_image("EMP2_mosaic_terracotta.png", [[0.62, 0.25, 0.20], [0.72, 0.33, 0.26], [0.55, 0.20, 0.17], [0.80, 0.45, 0.38]], seed=4), 1.0, rough=0.3, coat=0.3)
    L["mosaic_grey"] = image_material("EMP2_Mosaic_grey_band", mosaic_image("EMP2_mosaic_grey.png", [[0.45, 0.47, 0.49], [0.55, 0.57, 0.58], [0.38, 0.40, 0.42]], seed=5), 1.0, rough=0.3, coat=0.3)
    L["glass"] = glazing("EMP2_Room_glazing")
    L["glass_shop"] = glazing("EMP2_Lobby_glazing", base=(0.05, 0.075, 0.08), curtain=(0.78, 0.76, 0.70), sheer=(0.16, 0.2, 0.21), closed=0.12, half=0.3)
    L["frame"] = flat("EMP2_Aluminium_white", (0.80, 0.81, 0.80), rough=0.35, metal=0.5)
    L["frame_dark"] = flat("EMP2_Aluminium_graphite", (0.09, 0.10, 0.11), rough=0.3, metal=0.75)
    L["rail_glass"] = flat("EMP2_Balustrade_glass", (0.78, 0.88, 0.88), rough=0.04, transmission=1.0, ior=1.5, thin=True)
    L["steel"] = flat("EMP2_Stainless_handrail", (0.78, 0.79, 0.80), rough=0.22, metal=1.0)
    L["roof"] = pbr("EMP2_Roof_concrete", "concrete_floor_02", 4.0, tint=(0.80, 0.80, 0.78), sat=0.2, bright=1.1, rough=(0.7, 0.95), nrm=0.5)
    L["terrace"] = pbr("EMP2_Terrace_tiles", "floor_tiles_06", 2.0, tint=(0.95, 0.92, 0.86), sat=0.4, bright=1.0, rough=(0.4, 0.8), nrm=0.5)
    L["deck"] = pbr("EMP2_Teak_deck", "wood_floor_deck", 2.5, tint=(1.0, 0.92, 0.82), sat=0.9, bright=0.95, rough=(0.45, 0.85), nrm=0.6)
    L["solar"] = image_material("EMP2_Solar_panel", solar_image("EMP2_solar.png"), 1.0, rough=0.12, metal=0.2, box=False, coat=0.8)
    L["machine"] = flat("EMP2_Rooftop_plant_grey", (0.52, 0.54, 0.55), rough=0.55, metal=0.3)
    L["asphalt"] = pbr("EMP2_Asphalt", "asphalt_02", 6.0, tint=(0.62, 0.63, 0.65), sat=0.2, bright=0.9, rough=(0.75, 0.98), nrm=0.6, coord="Object")
    L["pavers"] = pbr("EMP2_Concrete_pavers", "concrete_pavers_02", 3.0, tint=(0.95, 0.93, 0.88), sat=0.4, bright=1.0, rough=(0.6, 0.95), nrm=0.6)
    L["plaza_light"] = pbr("EMP2_Plaza_light_stone", "square_concrete_pavers", 3.0, tint=(0.98, 0.95, 0.90), sat=0.3, bright=1.12, rough=(0.55, 0.9), nrm=0.5)
    L["plaza_dark"] = pbr("EMP2_Plaza_dark_granite", "granite_tile", 2.0, tint=(0.55, 0.56, 0.58), sat=0.2, bright=0.85, rough=(0.4, 0.8), nrm=0.5)
    L["pool_tile"] = pbr("EMP2_Pool_tile", "blue_floor_tiles_01", 1.5, tint=(0.75, 0.95, 1.0), sat=1.0, bright=1.05, rough=(0.2, 0.5), nrm=0.4)
    L["curb"] = pbr("EMP2_Curb_concrete", "concrete_floor_02", 2.0, tint=(0.86, 0.86, 0.84), sat=0.1, bright=1.15, rough=(0.6, 0.9), nrm=0.4)
    L["sign_blue"] = flat("EMP2_Sign_blue", (0.06, 0.16, 0.48), rough=0.35)
    L["canvas"] = flat("EMP2_Shade_canvas", (0.93, 0.92, 0.88), rough=0.85)
    L["ballroom_roof"] = image_material("EMP2_Ballroom_roof_grid", solar_image("EMP2_ballroom_grid.png", 4, 4, 48), 6.0, rough=0.3, metal=0.4, box=False)
    return L
