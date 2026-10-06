import bpy,json,math
from pathlib import Path
from collections import Counter
from mathutils import Vector,Quaternion
R=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'exports/Empyrean_CamRanh_Exterior_Drone.fbx'),use_anim=True,anim_offset=0.0)
s=bpy.context.scene
cam=bpy.data.objects.get('08_Drone_20s');assert cam is not None
manifest=json.loads((R/'qa/fbx_export_manifest.json').read_text())
missing=[n for n in manifest['objects'] if n not in bpy.data.objects]
assert not missing,missing
route=json.loads((R/'qa/drone_route.json').read_text())['samples'];errors=[]
for f in (1,92,157,229,306,375,410,438,480):
 s.frame_set(f);expected=Vector(route[f-1]['position']);errors.append({'frame':f,'location_error_m':(cam.matrix_world.translation-expected).length,'rotation_error_deg':math.degrees(cam.matrix_world.to_quaternion().rotation_difference(Quaternion(route[f-1]['rotation'])).angle)})
assert max(x['location_error_m'] for x in errors)<.01,errors
assert max(min(x['rotation_error_deg'],abs(360-x['rotation_error_deg'])) for x in errors)<.06,errors
bad=[]
for o in s.objects:
 if o.type=='MESH':
  if not all(math.isfinite(v) for p in o.bound_box for v in p):bad.append(o.name)
  if any(p.material_index>=len(o.material_slots) for p in o.data.polygons):bad.append(o.name+' material_index')
assert not bad,bad
material_mismatches=[]
for name,expected in manifest.get('material_checks',{}).items():
 o=bpy.data.objects[name];counts=Counter(p.material_index for p in o.data.polygons);actual={o.material_slots[i].material.name:int(n) for i,n in counts.items()}
 if actual!=expected:material_mismatches.append({'object':name,'expected':expected,'actual':actual})
assert not material_mismatches,material_mismatches
out={'passed':True,'objects':len(s.objects),'mesh_objects':sum(o.type=='MESH' for o in s.objects),'cameras':sum(o.type=='CAMERA' for o in s.objects),'images':len(bpy.data.images),'missing_objects':missing,'camera_positions':errors,'material_index_errors':bad,'material_layouts_verified':len(manifest.get('material_checks',{})),'embedded_texture_files':[i.filepath for i in bpy.data.images if i.source=='FILE'],'fps':s.render.fps}
(R/'qa/fbx_roundtrip_validation.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
