"""Render the corrected pavilion and refresh the existing delivery perspectives."""
import bpy
from pathlib import Path
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh');s=bpy.data.scenes['Empyrean_Exterior'];bpy.context.window.scene=s
s.cycles.device='GPU';prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
s.render.resolution_x=3000;s.render.resolution_y=2000;s.render.resolution_percentage=100;s.cycles.samples=96
for name in ['07_Pavilion_direction_detail','02_Sea_facing_aerial','01_Aerial_from_land','06_North_sea_aerial']:
    s.camera=bpy.data.objects[name];s.render.filepath=str(root/'renders'/(name+'.png'))
    bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
