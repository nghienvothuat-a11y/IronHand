"""Export the v2 core (buildings, ground, pools, props) to GLB.

  blender -b source/Empyrean_CamRanh_Exterior_v2.blend -P source/v2/export_glb.py -- exports/Empyrean_Exterior_v2_Core.glb

Plants are geometry-node instances of a hidden library and the 24 km ground and
sea planes are presentation context; both are left out of the exchange file.
Meshes carry metre-scale box UVs and use Draco compression; procedural shader detail is BLEND-only.
"""
import os
import sys
import bpy

out = sys.argv[sys.argv.index("--") + 1]
SKIP_COLL = ("EMP2_40_Planting", "EMP2_49_Plant_library", "EMP2_48_Prop_library", "EMP2_99_Cameras_and_light")
SKIP_OBJ = ("EMP2_Ground_terrain_sand", "EMP2_Sea_surface")

bpy.ops.object.select_all(action="DESELECT")
n = 0
for ob in bpy.context.scene.objects:
    if ob.type != "MESH" or ob.name in SKIP_OBJ:
        continue
    if any(c.name in SKIP_COLL for c in ob.users_collection):
        continue
    ob.select_set(True)
    n += 1
# exchange copy: textures at 1K (the .blend keeps the 2K/4K sources); nothing is saved back
for im in bpy.data.images:
    if im.size[0] > 1024 and im.has_data:
        im.scale(1024, max(1, int(1024 * im.size[1] / im.size[0])))
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_apply=False,
                          export_yup=True, export_texcoords=True, export_normals=True, export_materials="EXPORT",
                          export_image_format="JPEG", export_jpeg_quality=85,
                          export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6)
print("EXPORTED", out, n, os.path.getsize(out))
