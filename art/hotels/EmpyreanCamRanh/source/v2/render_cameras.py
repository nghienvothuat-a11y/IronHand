"""Render presentation cameras with Cycles (Metal GPU when available).

  blender -b source/Empyrean_CamRanh_Exterior_v2.blend -P source/v2/render_cameras.py -- renders/v2 01_Aerial_from_land,02_Sea_facing_aerial 2400 160
Arguments: output folder, comma-separated camera names, width in px (3:2 frame), samples.
"""
import bpy, sys, os
argv = sys.argv[sys.argv.index("--") + 1:]
out, cams, rx, spp = argv[0], argv[1].split(","), int(argv[2]), int(argv[3])
sc = bpy.context.scene
sc.render.engine = "CYCLES"
try:
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"; prefs.get_devices()
    for d in prefs.devices: d.use = True
    sc.cycles.device = "GPU"
except Exception as e:
    print("GPU setup failed", e)
sc.cycles.samples = spp
sc.cycles.use_denoising = True
sc.render.resolution_x = rx
sc.render.resolution_y = int(rx * 2 / 3)
sc.render.image_settings.file_format = "JPEG"; sc.render.image_settings.quality = 92
os.makedirs(out, exist_ok=True)
for c in cams:
    sc.camera = bpy.data.objects[c]
    sc.render.filepath = os.path.join(out, c + ".jpg")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath)
