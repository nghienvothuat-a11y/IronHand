"""Background-only portable FBX, including the baked drone camera."""
import bpy,json,math,time
from pathlib import Path
from collections import Counter
R=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh');s=bpy.context.scene;s.frame_set(1)
# The source .blend retains full Cycles/EEVEE nodes. FBX uses portable shading.
for m in bpy.data.materials:
 if not m.use_nodes:continue
 bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not bs:continue
 if m.name=='EMP_Irrigated_lawn':
  for link in list(bs.inputs['Base Color'].links):m.node_tree.links.remove(link)
  bs.inputs['Base Color'].default_value=(.1,.18,.022,1)
 m.diffuse_color=bs.inputs['Base Color'].default_value[:]
 m.roughness=bs.inputs['Roughness'].default_value;m.metallic=bs.inputs['Metallic'].default_value
# Embedded textures remain available even if moved off this computer.
# FBX requires a consistent material layout on shared meshes. Preserve instances
# by sharing a mesh per (original mesh, effective material slots) group.
mesh_groups={}
for o in s.objects:
 if o.type!='MESH':continue
 mats=tuple(slot.material for slot in o.material_slots)
 key=(o.data.as_pointer(),tuple(m.as_pointer() if m else 0 for m in mats))
 if key not in mesh_groups:
  mesh=o.data.copy();mesh.name=o.data.name+'_FBX'
  for i,m in enumerate(mats):mesh.materials[i]=m
  mesh_groups[key]=mesh
 o.data=mesh_groups[key]
 for slot,mat in zip(o.material_slots,mats):slot.link='DATA';slot.material=mat
selected=[]
for o in s.objects:
 keep=not o.hide_render and (o.type in {'MESH','FONT'} or o.name=='08_Drone_20s')
 o.hide_set(False);o.select_set(keep)
 if keep:selected.append(o.name)
bpy.context.view_layer.objects.active=s.camera
material_checks={};seen=set()
for o in s.objects:
 if o.name not in selected or o.type!='MESH' or o.data in seen:continue
 seen.add(o.data)
 counts=Counter(p.material_index for p in o.data.polygons)
 material_checks[o.name]={o.material_slots[i].material.name:int(n) for i,n in counts.items()}
out=R/'exports/Empyrean_CamRanh_Exterior_Drone.fbx'
bpy.ops.export_scene.fbx(filepath=str(out),use_selection=True,object_types={'MESH','OTHER','CAMERA'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=True,mesh_smooth_type='FACE',use_custom_props=True,bake_anim=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=False,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='COPY',embed_textures=True,add_leaf_bones=False)
manifest={'file':str(out),'bytes':out.stat().st_size,'objects':selected,'units':'metres','camera':'08_Drone_20s','fps':24,'frame_start':1,'frame_end':480,'textures_embedded':True,'material_checks':material_checks,'material_note':'FBX carries portable materials; procedural shading, lighting and render settings remain in the Blender file.'}
(R/'qa/fbx_export_manifest.json').write_text(json.dumps(manifest,indent=2));print('FBX_EXPORTED',out.stat().st_size,len(selected),flush=True)
