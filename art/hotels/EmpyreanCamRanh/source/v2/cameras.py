"""Sky, sun, render settings and the presentation cameras."""
import math
import bpy
from mathutils import Vector

# name: (location, target, lens mm)
CAMERAS = {
    "01_Aerial_from_land": ((-560.0, -330.0, 260.0), (40.0, 10.0, 0.0), 32),
    "02_Sea_facing_aerial": ((820.0, -120.0, 210.0), (60.0, 30.0, 10.0), 30),
    "03_Sea_court_pool": ((150.0, 250.0, 22.0), (60.0, 175.0, 18.0), 24),
    "04_Shopvilla_street": ((-158.0, -71.5, 1.7), (-102.8, -48.1, 6.0), 26),
    "05_Arena_Square": ((90.0, -95.0, 55.0), (0.0, 0.0, 2.0), 28),
    "06_North_sea_aerial": ((420.0, 420.0, 170.0), (40.0, 120.0, 20.0), 30),
    "07_Light_entrance": ((-310.0, 25.0, 6.0), (-255.0, 82.0, 25.0), 22),
    "08_Sand_water_park": ((330.0, -170.0, 60.0), (270.0, -60.0, 5.0), 26),
    "09_Masterplan_top": ((0.0, -20.0, 1500.0), (0.0, -20.0, 0.0), 0),
}

SUN_AZIMUTH_DEG = 112.0     # from north, clockwise: morning sun over the sea
SUN_ELEVATION_DEG = 38.0


def build(sc, root):
    coll = bpy.data.collections.new("EMP2_99_Cameras_and_light")
    root.children.link(coll)
    # world
    w = bpy.data.worlds.new("EMP2_Tropical_sky")
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_disc = False
    sky.sun_elevation = math.radians(SUN_ELEVATION_DEG)
    sky.sun_rotation = math.radians(-SUN_AZIMUTH_DEG)   # Cycles sky sun dir = (-sin r, cos r)
    sky.altitude = 10.0
    sky.air_density = 1.0
    sky.aerosol_density = 1.6
    sky.ozone_density = 1.0
    # below the horizon (beyond the 24 km ground plane) blend into a pale coastal haze
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = -0.02
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(mr.outputs["Result"], mix.inputs["Factor"])
    nt.links.new(sky.outputs["Color"], mix.inputs["A"])
    mix.inputs["B"].default_value = (1.1, 1.2, 1.3, 1.0)
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.32
    sc.world = w
    # sun
    a, e = math.radians(SUN_AZIMUTH_DEG), math.radians(SUN_ELEVATION_DEG)
    s = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
    ld = bpy.data.lights.new("EMP2_Sun", "SUN")
    ld.energy = 4.6
    ld.angle = math.radians(0.53)
    ld.color = (1.0, 0.97, 0.92)
    lo = bpy.data.objects.new("EMP2_Sun", ld)
    lo.rotation_euler = s.to_track_quat("Z", "Y").to_euler()
    coll.objects.link(lo)
    # cameras
    made = []
    for name, (loc, tgt, lens) in CAMERAS.items():
        cd = bpy.data.cameras.new(name)
        cd.clip_start = 0.5
        cd.clip_end = 8000
        if lens == 0:
            cd.type = "ORTHO"
            cd.ortho_scale = 820
        else:
            cd.lens = lens
            cd.sensor_width = 36
        co = bpy.data.objects.new(name, cd)
        co.location = loc
        co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        coll.objects.link(co)
        made.append(name)
    sc.camera = bpy.data.objects["01_Aerial_from_land"]
    # render
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 256
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 8
    sc.cycles.volume_bounces = 1
    sc.render.resolution_x = 3000
    sc.render.resolution_y = 2000
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.render.film_transparent = False
    return made
