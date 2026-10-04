import bpy
from pathlib import Path
from mathutils import Vector
R=Path('/Users/mrk/IronHand')
bpy.ops.wm.open_mainfile(filepath=str(R/'art/blender/IronHand_MK1_Source.blend'))
obj=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=obj; obj.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
scene=bpy.context.scene
scene.render.engine='BLENDER_WORKBENCH'
scene.render.resolution_x=900; scene.render.resolution_y=1000; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.display.shading.light='STUDIO'; scene.display.shading.studio_light='paint.sl'
scene.display.shading.color_type='SINGLE'; scene.display.shading.single_color=(.46,.53,.60)
scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True
scene.display.shading.cavity_type='BOTH'
scene.world=bpy.data.worlds.new('InspectionWorld'); scene.display.shading.background_type='WORLD'; scene.world.color=(.065,.065,.065)
camdata=bpy.data.cameras.new('InspectionCamera'); cam=bpy.data.objects.new('InspectionCamera',camdata);scene.collection.objects.link(cam);scene.camera=cam
camdata.type='ORTHO';camdata.ortho_scale=1.15
for name,loc in [('front',(0,-3,.50)),('back',(0,3,.50)),('side',(3,0,.50))]:
    cam.location=loc;cam.rotation_euler=(Vector((0,0,.5))-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(R/f'art/previews/source-{name}.png');bpy.ops.render.render(write_still=True)
