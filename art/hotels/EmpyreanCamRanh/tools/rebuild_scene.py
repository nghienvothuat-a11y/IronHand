"""Rebuild the editable study in a clean background Blender process.
Usage: Blender -b --factory-startup -P tools/rebuild_scene.py
It intentionally refuses to run when a scene with the output name already exists.
"""
import bpy
from pathlib import Path
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
if bpy.data.scenes.get('Empyrean_Exterior'):raise RuntimeError('Use a fresh background Blender process.')
s=bpy.data.scenes.new('Empyrean_Exterior');bpy.context.window.scene=s
s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
ns={}
for filename in ['00_common.py','11_towers_asbuilt.py','20_site.py','30_landscape.py','40_presentation.py','50_finish.py','60_polish.py','70_materials_and_context.py','80_final_detail.py','85_pavilion_clearance.py']:
    path=root/'source'/'stages'/filename
    exec(compile(path.read_text(),str(path),'exec'),ns)
exec(compile((root/'tools'/'package_scene.py').read_text(),'package_scene.py','exec'))
