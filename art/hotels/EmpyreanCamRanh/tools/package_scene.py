"""Run in a BACKGROUND Blender instance, never over the user's active file."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
s=bpy.data.scenes['Empyrean_Exterior'];bpy.context.window.scene=s
for other in list(bpy.data.scenes):
    if other!=s:bpy.data.scenes.remove(other)
s.camera=bpy.data.objects['01_Aerial_from_land']
s.render.resolution_x=3000;s.render.resolution_y=2000;s.cycles.samples=96
s.render.filepath=str(root/'renders'/'01_Aerial_from_land.png')
for o in s.objects:o.select_set(False)
# Remove orphan meshes left by iterating the procedural source, not used assets.
for _ in range(3):bpy.data.orphans_purge(do_recursive=True)
for im in bpy.data.images:
    if im.source=='FILE' and not im.packed_file:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(root/'source'/'Empyrean_CamRanh_Exterior.blend'),compress=True)
stats={'scene':s.name,'units':'metres','photo_based_not_surveyed':True,'objects':len(s.objects),'meshes':len({o.data for o in s.objects if o.type=='MESH'}),'towers':{}}
for c in bpy.data.collections:
    if c.name.startswith('EMP_10_'):
        points=[o.matrix_world@Vector(p) for o in c.objects if o.type=='MESH' for p in o.bound_box]
        stats['towers'][c.name]={'objects':len(c.objects),'bounds_min':[min(p[a] for p in points) for a in range(3)],'bounds_max':[max(p[a] for p in points) for a in range(3)],'mesh_faces':sum(len(o.data.polygons) for o in c.objects if o.type=='MESH')}
stats['unique_mesh_faces']=sum(len(m.polygons) for m in {o.data for o in s.objects if o.type=='MESH'})
stats['rendered_mesh_faces']=sum(len(o.data.polygons) for o in s.objects if o.type=='MESH')
stats['packed_textures']=[im.name for im in bpy.data.images if im.packed_file]
(root/'qa'/'scene_audit.json').write_text(json.dumps(stats,indent=2))
print('NORMAL_BLEND_SAVED',stats,flush=True)
# Portable core asset: omit distant terrain, sea, lighting and perspective cameras.
for o in s.objects:
    core=any(c.name.startswith(('EMP_10_','EMP_20_','EMP_30_','EMP_40_','EMP_45_')) for c in o.users_collection)
    o.select_set(core and o.type=='MESH')
# glTF cannot represent the Cycles color remapping of the lawn photograph.
# Keep the packed originals in the .blend; the portable GLB uses a neutral lawn tint.
m=bpy.data.materials.get('EMP_Irrigated_lawn')
if m:
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
    bs.inputs['Base Color'].default_value=(.10,.18,.022,1)
bpy.ops.export_scene.gltf(filepath=str(root/'exports'/'Empyrean_Exterior_Core.glb'),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_cameras=False,export_lights=False,export_materials='EXPORT')
print('GLB_EXPORTED',flush=True)
