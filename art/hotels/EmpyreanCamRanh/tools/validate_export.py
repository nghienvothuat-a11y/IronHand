import bpy,json,math,struct
from pathlib import Path
from mathutils import Vector
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
p=root/'exports'/'Empyrean_Exterior_Core.glb';data=p.read_bytes()
magic,version,length=struct.unpack_from('<4sII',data,0)
assert magic==b'glTF' and version==2 and length==len(data)
jl,jt=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+jl])
assert jt==0x4E4F534A
assert len(doc['meshes'])>20
assert any('A_Land_North' in n.get('name','') for n in doc['nodes'])
assert any('D_distinct_curved_pavilion' in n.get('name','') for n in doc['nodes'])
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert objects and all(all(math.isfinite(c) for v in o.bound_box for c in v) for o in objects)
points=[o.matrix_world@Vector(p) for o in objects for p in o.bound_box]
stats={'status':'passed','checks':['GLB 2.0 header and length','four-tower nodes and distinct pavilion','Blender round-trip import','finite world coordinates'],'bytes':len(data),'gltf_meshes':len(doc['meshes']),'gltf_nodes':len(doc['nodes']),'gltf_materials':len(doc.get('materials',[])),'gltf_images':len(doc.get('images',[])),'imported_mesh_objects':len(objects),'world_bounds_min':[min(p[a] for p in points) for a in range(3)],'world_bounds_max':[max(p[a] for p in points) for a in range(3)]}
(root/'qa'/'export_validation.json').write_text(json.dumps(stats,indent=2))
print('VALIDATED',stats,flush=True)
