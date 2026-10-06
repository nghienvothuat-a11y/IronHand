"""Normal saved scene, final daylight and reference-matched aerial views."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh');s=bpy.data.scenes['Empyrean_Exterior'];bpy.context.window.scene=s
s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.22
next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.17
c=bpy.data.objects['01_Aerial_from_land'];c.location=(-625,-690,410);c.rotation_euler=(Vector((15,0,18))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=47
c=bpy.data.objects['02_Sea_facing_aerial'];c.location=(620,-735,450);c.rotation_euler=(Vector((-3,-14,20))-c.location).to_track_quat('-Z','Y').to_euler();c.data.lens=49
# The .blend retains its GPU configuration; CPU gives a predictable portable render here.
s.camera=bpy.data.objects['01_Aerial_from_land'];s.render.resolution_x=3000;s.render.resolution_y=2000;s.cycles.samples=96
s.render.filepath=str(root/'renders'/'01_Aerial_from_land.png')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'source'/'Empyrean_CamRanh_Exterior.blend'),compress=True)
s.cycles.device='CPU';prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='CPU')
preview='--preview' in sys.argv
for name in (['01_Aerial_from_land'] if preview else ['01_Aerial_from_land','02_Sea_facing_aerial','06_North_sea_aerial']):
    s.camera=bpy.data.objects[name]
    s.render.resolution_x=1500 if preview else 3000;s.render.resolution_y=1000 if preview else 2000;s.cycles.samples=32 if preview else 96
    s.render.filepath=str(root/('qa' if preview else 'renders')/(('final_preview' if preview else name)+'.png'))
    bpy.ops.render.render(write_still=True)
    print('RENDER_DONE',name,s.render.filepath,flush=True)
