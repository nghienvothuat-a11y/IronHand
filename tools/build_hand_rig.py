"""Build a reviewable prototype mechanical-hand rig from the preserved Tripo FBX.
Blender 5.2, metres, +Z fingers, palm toward -Y. Not a production anatomical scan.
"""
import bpy, bmesh, math, json
from pathlib import Path
from mathutils import Vector
from collections import defaultdict

R=Path('/Users/mrk/IronHand'); OUT=R/'art/blender'; PRE=R/'art/previews'; EXPORT=R/'assets/exports'
EXPORT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'assets/source/IronHand_MK1_Tripo_Source.fbx'))
source=next(o for o in bpy.context.scene.objects if o.type=='MESH')
bpy.context.view_layer.objects.active=source
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
source.name='Tripo_Original_Reference'

# Explicitly fitted to this generated mesh, in the source's normalized coordinates.
FINGERS={
 'Thumb':[(.155,-.040,.345),(.246,-.052,.449),(.307,-.068,.528),(.382,-.071,.621)],
 'Index':[(.112,-.045,.574),(.143,-.022,.749),(.163,.026,.852),(.175,.079,.943)],
 'Middle':[(-.013,-.044,.585),(-.013,-.020,.771),(-.013,.047,.879),(-.016,.103,.985)],
 'Ring':[(-.112,-.045,.554),(-.165,-.022,.730),(-.194,.034,.828),(-.221,.073,.905)],
 'Little':[(-.207,-.045,.510),(-.283,-.029,.619),(-.344,.002,.679),(-.380,.029,.716)],
}
FINGERS={k:[Vector(p) for p in ps] for k,ps in FINGERS.items()}
WRIST=Vector((0,-.025,.235)); SCALE=.28
def conv(v): return (Vector(v)-WRIST)*SCALE

def dist_seg(p,a,b):
    d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));return (p-a-t*d).length
def region(p):
    # Evaluate in the palm plane so front/back armour stays on the same joint.
    q=Vector((p.x,0,p.z)); candidates=[]
    for name,ps in FINGERS.items():
        flat=[Vector((a.x,0,a.z)) for a in ps]
        forward=(flat[1]-flat[0]).normalized()
        if (q-flat[0]).dot(forward)<-.008: continue
        d=min(dist_seg(q,flat[i],flat[i+1]) for i in range(3))
        if d < (.088 if name=='Thumb' else .079): candidates.append((d,name))
    if candidates: return min(candidates)[1]
    return 'Forearm' if p.z<WRIST.z else 'Hand'

def bone_for(name,p):
    if name not in FINGERS: return name+'.R'
    ps=FINGERS[name]; seg=0
    for i in (1,2):
        n=((ps[i]-ps[i-1]).normalized()+(ps[i+1]-ps[i]).normalized()).normalized()
        if (p-ps[i]).dot(n)>0:seg=i
    return f'{name}.{seg+1:02d}.R'

# Group faces by digit, bisect only that digit at its two articulation planes,
# then duplicate boundary vertices between bones. Every resulting panel is rigid.
faces_by_region=defaultdict(list)
for f in source.data.polygons:
    c=sum((source.data.vertices[i].co for i in f.vertices),Vector())/len(f.vertices)
    faces_by_region[region(c)].append(list(f.vertices))

finalverts=[]; finalfaces=[]; vertex_bones=[]; face_bones=[]; source_centres=[]
cap_count=0
for name,faces in faces_by_region.items():
    ids=sorted({i for f in faces for i in f}); remap={old:i for i,old in enumerate(ids)}
    me=bpy.data.meshes.new('Region_'+name)
    me.from_pydata([source.data.vertices[i].co for i in ids],[],[[remap[i] for i in f] for f in faces]);me.update()
    bm=bmesh.new();bm.from_mesh(me)
    planes=[]
    if name in FINGERS:
        ps=FINGERS[name]
        for i in (1,2):
            normal=((ps[i]-ps[i-1]).normalized()+(ps[i+1]-ps[i]).normalized()).normalized()
            planes.append((ps[i],normal))
            bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=ps[i],plane_no=normal,clear_inner=False,clear_outer=False)
    bm.verts.index_update();bm.faces.ensure_lookup_table()
    bone_faces=defaultdict(list)
    for f in bm.faces:bone_faces[bone_for(name,f.calc_center_median())].append(f)
    for bone,ff in bone_faces.items():
        unique=set(v for f in ff for v in f.verts)
        local=bmesh.new(); mp={v:local.verts.new(v.co) for v in unique}
        for f in ff:
            try:local.faces.new([mp[v] for v in f.verts])
            except ValueError:pass
        # Cap only new joint cuts, preserving the deliberately open cuff.
        for origin,normal in planes:
            boundary=[e for e in local.edges if e.is_boundary and all(abs((v.co-origin).dot(normal))<2e-5 for v in e.verts)]
            if len(boundary)>=3:
                try:cap_count+=len(bmesh.ops.holes_fill(local,edges=boundary,sides=0).get('faces',[]))
                except RuntimeError:pass
        bmesh.ops.recalc_face_normals(local,faces=list(local.faces))
        offset=len(finalverts); local.verts.index_update()
        vv=list(local.verts)
        finalverts.extend([conv(v.co) for v in vv]);vertex_bones.extend([bone]*len(vv))
        for f in local.faces:
            finalfaces.append([offset+v.index for v in f.verts]);face_bones.append(bone);source_centres.append(f.calc_center_median().copy())
        local.free()
    bm.free();bpy.data.meshes.remove(me)

mesh=bpy.data.meshes.new('IronHand_MK1_ArmourMesh');mesh.from_pydata(finalverts,[],finalfaces);mesh.update()
hand=bpy.data.objects.new('IronHand_MK1_Armour',mesh);bpy.context.scene.collection.objects.link(hand)
for bone in set(vertex_bones):
    group=hand.vertex_groups.new(name=bone); group.add([i for i,b in enumerate(vertex_bones) if b==bone],1.0,'REPLACE')

# Small reusable colour atlas: base, metallic/roughness, and emissive maps.
# Its deliberately shared swatches suit a stylized prototype; not a unique paint UV.
swatches=[
 ('Steel',(.24,.32,.40),.82,.29,(0,0,0)),
 ('Graphite',(.026,.044,.064),.58,.42,(0,0,0)),
 ('Copper',(.68,.29,.095),.8,.3,(0,0,0)),
 ('Joint',(.012,.018,.024),.25,.58,(0,0,0)),
 ('LightSteel',(.55,.66,.73),.88,.24,(0,0,0)),
 ('Cyan',(.02,.55,.72),.35,.23,(.015,.8,1)),
 ('DarkSteel',(.095,.135,.17),.78,.38,(0,0,0)),
 ('Amber',(.8,.37,.08),.55,.31,(1,.25,.01)),
]
TEX=EXPORT/'Textures';TEX.mkdir(exist_ok=True)
def atlas_image(name,kind):
    size=256;im=bpy.data.images.new(name,width=size,height=size,alpha=False)
    im.colorspace_settings.name='Non-Color' if kind=='orm' else 'sRGB'
    pixels=[]
    for y in range(size):
        for x in range(size):
            row=y//128;col=x//64;s=swatches[row*4+col]
            rgb=s[1] if kind=='base' else ((1,s[3],s[2]) if kind=='orm' else s[4])
            pixels.extend((*rgb,1))
    im.pixels.foreach_set(pixels)
    im.update()
    im.filepath_raw=str(TEX/f'{name}.png');im.file_format='PNG';im.save();im.pack();return im
base=atlas_image('IronHand_MK1_BaseColor','base');orm=atlas_image('IronHand_MK1_ORM','orm');emission=atlas_image('IronHand_MK1_Emission','emission')
mat=bpy.data.materials.new('IronHand_MK1_Atlas');mat.use_nodes=True
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bsdf=nodes.get('Principled BSDF')
for im,label in [(base,'Base'),(orm,'ORM'),(emission,'Emission')]:
    n=nodes.new('ShaderNodeTexImage');n.image=im;n.interpolation='Closest';n.label=label
    if label=='Base': links.new(n.outputs['Color'],bsdf.inputs['Base Color'])
    elif label=='Emission':links.new(n.outputs['Color'],bsdf.inputs['Emission Color']);bsdf.inputs['Emission Strength'].default_value=2.5
    else:
        sep=nodes.new('ShaderNodeSeparateColor');links.new(n.outputs['Color'],sep.inputs['Color']);links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
mesh.materials.clear();mesh.materials.append(mat)
uv=mesh.uv_layers.new(name='PrototypePaletteUV')
def set_swatch(obj,poly,index):
    u=(index%4+.5)/4;v=(index//4+.5)/2
    for li in poly.loop_indices:obj.data.uv_layers.active.data[li].uv=(u,v)
for poly,p,bone in zip(mesh.polygons,source_centres,face_bones):
    index=0
    if bone=='Forearm.R':index=2 if p.z<.055 or .19<p.z<.223 else 1
    elif bone=='Hand.R':
        index=1 if p.y>.015 else 0
        if p.z<.30:index=6
        if .375<p.z<.50 and .08<abs(p.x)<.15:index=2
    else:
        name=bone.split('.')[0];ps=FINGERS[name]
        d=min((p-a).length for a in ps[:-1])
        index=3 if d<.037 else (4 if p.y<-.055 else 0)
        if bone.endswith('.03.R') and p.z>ps[3].z-.025:index=2
    set_swatch(hand,poly,index)
    poly.use_smooth=False

# Armature and Blender control properties. FBX export bakes these drivers.
armdata=bpy.data.armatures.new('IronHand_HandSkeleton');rig=bpy.data.objects.new('IronHand_Rig',armdata)
bpy.context.scene.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
def bone(name,a,b,parent=None,deform=True):
    e=armdata.edit_bones.new(name);e.head=conv(a);e.tail=conv(b);e.use_deform=deform
    if parent:e.parent=armdata.edit_bones[parent]
    e.align_roll(Vector((0,-1,0)));return e
bone('Root',(0,-.025,-.06),(0,-.025,-.015),deform=False)
bone('Forearm.R',(0,-.025,.025),WRIST,'Root')
bone('Hand.R',WRIST,(0,-.025,.565),'Forearm.R')
for name,ps in FINGERS.items():
    for i in range(3):bone(f'{name}.{i+1:02d}.R',ps[i],ps[i+1],'Hand.R' if i==0 else f'{name}.{i:02d}.R')
    bone(name+'.Tip.R',ps[-1],ps[-1]+(ps[-1]-ps[-2]).normalized()*.02,f'{name}.03.R',deform=False)
bpy.ops.object.mode_set(mode='OBJECT')
rig.show_in_front=True;armdata.display_type='STICK'
mod=hand.modifiers.new('MechanicalHandSkin','ARMATURE');mod.object=rig;hand.parent=rig

def driver(pb,index,prop,mult):
    pb.rotation_mode='XYZ';fc=pb.driver_add('rotation_euler',index);drv=fc.driver;drv.type='SCRIPTED'
    var=drv.variables.new();var.name='value';var.type='SINGLE_PROP';var.targets[0].id=rig;var.targets[0].data_path=f'["{prop}"]';drv.expression=f'value * {mult}'
for name in FINGERS:
    prop=name.lower()+'_curl';rig[prop]=0.0;rig.id_properties_ui(prop).update(min=0,max=1,description=f'Curl {name} finger: 0 open / 1 closed')
    angles=(.92,1.2,.85) if name=='Thumb' else (1.20,1.32,.90)
    for i,angle in enumerate(angles):driver(rig.pose.bones[f'{name}.{i+1:02d}.R'],0,prop,angle)
rig['thumb_opposition']=0.0;rig.id_properties_ui('thumb_opposition').update(min=0,max=1)
driver(rig.pose.bones['Thumb.01.R'],2,'thumb_opposition',.85)
for prop,axis in [('wrist_pitch',0),('wrist_yaw',2)]:
    rig[prop]=0.0;rig.id_properties_ui(prop).update(min=-1,max=1);driver(rig.pose.bones['Hand.R'],axis,prop,.40)

def rigid_object(obj,bone_name,swatch):
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    obj.data.materials.clear();obj.data.materials.append(mat)
    if not obj.data.uv_layers:obj.data.uv_layers.new(name='PrototypePaletteUV')
    obj.data.uv_layers.active.name='PrototypePaletteUV'
    for p in obj.data.polygons:set_swatch(obj,p,swatch)
    vg=obj.vertex_groups.new(name=bone_name);vg.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    md=obj.modifiers.new('MechanicalHandSkin','ARMATURE');md.object=rig;obj.parent=rig
    return obj

# Dark articulated bearings bridge small cut gaps without bending metal plates.
extras=[]
for name,ps in FINGERS.items():
    for i,p in enumerate(ps[:3]):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=(.030 if name!='Thumb' else .035)*SCALE,location=conv(p))
        ob=bpy.context.object;ob.name=f'{name}_Joint_{i+1:02d}'
        extras.append(rigid_object(ob,'Hand.R' if i==0 else f'{name}.{i:02d}.R',3))

def cylinder(name,centre,radius,depth,swatch,verts=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius*SCALE,depth=depth*SCALE,location=conv(centre),rotation=(math.pi/2,0,0))
    ob=bpy.context.object;ob.name=name
    extras.append(rigid_object(ob,'Hand.R',swatch));return ob
cylinder('Palm_Core_Bezel',(.008,-.145,.465),.076,.024,2,6)
cylinder('Palm_Core_Recess',(.008,-.160,.465),.062,.012,1,6)
cylinder('Palm_Energy_Core',(.008,-.170,.465),.045,.009,5,6)

# Join everything into one material / one skinned mesh for the mobile draft.
bpy.ops.object.select_all(action='DESELECT');hand.select_set(True)
for ob in extras:ob.select_set(True)
bpy.context.view_layer.objects.active=hand;bpy.ops.object.join()
hand.name='IronHand_MK1_Armour'
# Eliminate duplicate identical material slots introduced by joining.
hand.data.materials.clear();hand.data.materials.append(mat)
for p in hand.data.polygons:p.material_index=0;p.use_smooth=True
# Sharp engineering edges with smooth bevels.
bm=bmesh.new();bm.from_mesh(hand.data)
for e in bm.edges:
    e.smooth=bool(e.is_manifold and e.calc_face_angle(0)<math.radians(35))
bm.to_mesh(hand.data);bm.free()
wn=hand.modifiers.new('WeightedPlateNormals','WEIGHTED_NORMAL');wn.keep_sharp=True;wn.weight=50

socket=bpy.data.objects.new('Palm_Muzzle',None);bpy.context.scene.collection.objects.link(socket)
socket.empty_display_type='ARROWS';socket.empty_display_size=.018
socket.location=conv((.008,-.177,.465));socket.rotation_euler=(math.pi/2,0,0)
bpy.context.view_layer.update();mw=socket.matrix_world.copy();socket.parent=rig;socket.parent_type='BONE';socket.parent_bone='Hand.R';bpy.context.view_layer.update();socket.matrix_world=mw

# Keep the unmodified source in a hidden reference collection.
ref=bpy.data.collections.new('REFERENCE - Original Tripo (hidden)');bpy.context.scene.collection.children.link(ref)
for collection in list(source.users_collection):collection.objects.unlink(source)
ref.objects.link(source);source.hide_render=True;source.hide_set(True);source.hide_viewport=True

controls=[n.lower()+'_curl' for n in FINGERS]+['thumb_opposition','wrist_pitch','wrist_yaw']
poses={
 'Open':{},
 'Relaxed':dict(thumb_curl=.16,index_curl=.16,middle_curl=.19,ring_curl=.22,little_curl=.25,thumb_opposition=.12),
 'Fist':dict(thumb_curl=.5,index_curl=1,middle_curl=1,ring_curl=1,little_curl=1,thumb_opposition=.55),
 'Index_Curl':dict(index_curl=1),
 'Pinch':dict(thumb_curl=.55,index_curl=1,thumb_opposition=.8),
}
scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=180;scene.render.fps=30
timeline=[(1,'Open'),(25,'Relaxed'),(55,'Fist'),(85,'Open'),(110,'Index_Curl'),(135,'Open'),(160,'Pinch'),(180,'Open')]
for frame,pose in timeline:
    scene.frame_set(frame)
    for prop in controls:rig[prop]=float(poses[pose].get(prop,0));rig.keyframe_insert(data_path=f'["{prop}"]',frame=frame,group='Gesture Controls')
    scene.timeline_markers.new(pose,frame=frame)
rig.animation_data.action.name='IronHand_Gesture_Demo'
rig['README']='Custom Properties curl controls: 0=open, 1=closed. Disable action for manual control. Frame 1 Open, 55 Fist, 110 Index Curl, 160 Pinch. Runtime retargeting is separate.'
hand['source_task']='56f4080d-c961-4023-9d9c-b53baca28ca2'
hand['uv_note']='Prototype palette UV: overlapping swatches, one material. Unique paint/baked normal UV is future polish.'
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene.frame_set(1);bpy.context.view_layer.update()

# Studio lighting and a saved useful camera view.
world=bpy.data.worlds.new('IronHand_StudioWorld');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.045,.065,.09,1);world.node_tree.nodes['Background'].inputs[1].default_value=.5;scene.world=world
def aim(ob,target):ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,color,size in [('Key',(-.35,-.55,.50),55,(.72,.86,1),.4),('Fill',(.45,-.1,.28),35,(1,.63,.34),.3),('Rim',(.0,.45,.40),65,(.3,.8,1),.3)]:
    dat=bpy.data.lights.new(name,'AREA');dat.energy=power;dat.color=color;dat.shape='DISK';dat.size=size
    ob=bpy.data.objects.new(name,dat);scene.collection.objects.link(ob);ob.location=loc;aim(ob,(0,0,.07))
camdata=bpy.data.cameras.new('PresentationCamera');cam=bpy.data.objects.new('PresentationCamera',camdata);scene.collection.objects.link(cam);scene.camera=cam
cam.location=(.13,-.65,.27);aim(cam,(0,0,.065));camdata.type='ORTHO';camdata.ortho_scale=.36
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='AgX'

# Initial import / runtime contract.
landmarks={'0':{'bone':'Hand.R','point':'head'}}
for start,name in [(1,'Thumb'),(5,'Index'),(9,'Middle'),(13,'Ring'),(17,'Little')]:
    for j in range(3):landmarks[str(start+j)]={'bone':f'{name}.{j+1:02d}.R','point':'head'}
    landmarks[str(start+3)]={'bone':name+'.Tip.R','point':'head'}
contract={'units':'metres','handedness':'Right','source_height_m':SCALE,'rest_wrist_origin':[0,0,0],'blender_fingers_axis':'+Z','blender_palm_normal':'-Y','landmark_mapping':landmarks,'muzzle':'Palm_Muzzle','controls':controls,'poses':poses,'status':'Blender prototype; Unity and live camera tracking not tested','normal_map':False,'uv_layout':'shared palette swatches','rig_method':'Rigid per-panel skinning; cut boundaries duplicated by deform bone'}
(EXPORT/'IronHand_MK1_RigContract.json').write_text(json.dumps(contract,indent=2))

bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);hand.select_set(True);socket.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_floor=False;space.overlay.show_overlays=False
            space.region_3d.view_distance=.48;space.region_3d.view_location=(0,0,.07);space.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'IronHand_MK1_Rigged.blend'))
bpy.ops.export_scene.fbx(filepath=str(EXPORT/'IronHand_MK1_Rigged.fbx'),use_selection=True,object_types={'ARMATURE','MESH','EMPTY'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=False,bake_anim_use_nla_strips=False,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='COPY',embed_textures=True,use_armature_deform_only=False)
bpy.ops.export_scene.gltf(filepath=str(EXPORT/'IronHand_MK1_Rigged.glb'),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='SCENE',export_frame_range=True,export_force_sampling=True)
hand.data.calc_loop_triangles()
print(json.dumps({'vertices':len(hand.data.vertices),'faces':len(hand.data.polygons),'triangles':len(hand.data.loop_triangles),'bones':len(armdata.bones),'materials':len(hand.data.materials),'joint_caps':cap_count,'bounds_m':list(hand.dimensions)}))
for frame,name in [(1,'open'),(55,'fist'),(110,'index-curl'),(160,'pinch')]:
    scene.frame_set(frame);scene.render.filepath=str(PRE/f'IronHand_MK1_{name}.png');bpy.ops.render.render(write_still=True)
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'IronHand_MK1_Rigged.blend'))
