import bpy, json, math, struct
from pathlib import Path
from mathutils import Vector
R=Path('/Users/mrk/IronHand');EX=R/'assets/exports'
bpy.ops.wm.open_mainfile(filepath=str(R/'art/blender/IronHand_MK1_Rigged.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['IronHand_Rig'];hand=bpy.data.objects['IronHand_MK1_Armour']
results={};failures=[]
def check(name,condition,detail=None):
    results[name]={'pass':bool(condition),'detail':detail}
    if not condition:failures.append(name)

weights=[]
for v in hand.data.vertices:
    g=[g for g in v.groups if g.weight>0]
    weights.append(g)
check('all_vertices_have_one_rigid_weight',all(len(g)==1 and abs(g[0].weight-1)<1e-6 for g in weights))
check('weights_reference_existing_deform_bones',all(hand.vertex_groups[g[0].group].name in rig.data.bones and rig.data.bones[hand.vertex_groups[g[0].group].name].use_deform for g in weights))
check('no_face_spans_multiple_bones',all(len({weights[i][0].group for i in p.vertices})==1 for p in hand.data.polygons))
check('single_material',len(hand.data.materials)==1)
check('uv_exists',len(hand.data.uv_layers)>0)
check('23_bones',len(rig.data.bones)==23,len(rig.data.bones))
check('all_drivers_valid',all(fc.driver.is_valid for fc in rig.animation_data.drivers))
scene.frame_set(160);bpy.context.view_layer.update()
check('fractional_controls_preserved',abs(rig['thumb_curl']-.55)<1e-5 and abs(rig['thumb_opposition']-.8)<1e-5,{'thumb_curl':rig['thumb_curl'],'thumb_opposition':rig['thumb_opposition']})

def evaluated(frame):
    scene.frame_set(frame);bpy.context.view_layer.update();ev=hand.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    pts=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts
rest=evaluated(1);fist=evaluated(55);index=evaluated(110)
check('all_pose_vertices_finite',all(math.isfinite(x) for pts in [rest,fist,index] for p in pts for x in p))
maxrigiderror=0
for e in hand.data.edges:
    a,b=e.vertices
    d0=(rest[a]-rest[b]).length;d1=(fist[a]-fist[b]).length
    maxrigiderror=max(maxrigiderror,abs(d0-d1))
check('fist_preserves_rigid_panel_edge_lengths',maxrigiderror<1e-5,{'max_error_m':maxrigiderror})
other_error=0;index_motion=0
for i,g in enumerate(weights):
    name=hand.vertex_groups[g[0].group].name;d=(rest[i]-index[i]).length
    if name.startswith('Index.'):index_motion=max(index_motion,d)
    else:other_error=max(other_error,d)
check('index_control_moves_only_index',index_motion>.025 and other_error<1e-5,{'index_max_m':index_motion,'other_max_m':other_error})
restheight=max(p.z for p in rest)-min(p.z for p in rest)
check('metre_scale',.27<restheight<.29,{'height_m':restheight})
scene.frame_set(1);bpy.context.view_layer.update()
socket=bpy.data.objects['Palm_Muzzle'];expected=Vector((.008,-.152,.230))*.28
check('muzzle_aligned_to_palm', (socket.matrix_world.translation-expected).length<1e-5,{'position_m':list(socket.matrix_world.translation),'expected_m':list(expected)})
hand.data.calc_loop_triangles()
results['stats']={'vertices':len(hand.data.vertices),'faces':len(hand.data.polygons),'triangles':len(hand.data.loop_triangles),'bones':len(rig.data.bones),'materials':len(hand.data.materials),'height_m':restheight}

# Inspect glTF's packed structure without any external dependency.
blob=(EX/'IronHand_MK1_Rigged.glb').read_bytes();length,typ=struct.unpack_from('<II',blob,12);gl=json.loads(blob[20:20+length])
check('glb_contains_skin_and_animation',len(gl.get('skins',[]))==1 and len(gl.get('animations',[]))>=1)
check('glb_images_embedded',all('bufferView' in im for im in gl.get('images',[])) and len(gl.get('images',[]))>=2)

# Fresh import verifies the FBX includes baked motion, independent of drivers.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(EX/'IronHand_MK1_Rigged.fbx'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
check('fbx_skin_and_bones',len(arm.data.bones)==23 and len(meshes)==1 and any(m.type=='ARMATURE' for m in meshes[0].modifiers))
check('fbx_has_baked_action',bool(arm.animation_data and arm.animation_data.action))
scene=bpy.context.scene
scene.frame_set(1);bpy.context.view_layer.update();a=arm.pose.bones['Index.03.R'].matrix.copy()
scene.frame_set(55);bpy.context.view_layer.update();b=arm.pose.bones['Index.03.R'].matrix.copy()
delta=sum(abs(a[r][c]-b[r][c]) for r in range(4) for c in range(4))
check('fbx_baked_fist_moves_finger',delta>.2,{'matrix_delta':delta})
results['status']='pass' if not failures else 'failed';results['failures']=failures
results['limitations']=['Not validated in Unity or on iPhone.','Prototype palette UVs; no baked normal map.','Joint placement fitted visually to the generated mesh; live hand alignment remains to be calibrated.']
(R/'art/blender/rig-validation.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
if failures:raise RuntimeError('Rig validation failed: '+', '.join(failures))
