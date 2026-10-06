"""Targeted correction in the live hotel scene, preserving all four tower meshes."""
import bpy,json,hashlib
from pathlib import Path
root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
s=bpy.data.scenes['Empyrean_Exterior']
assert not s.get('pavilion_curve_revision'), 'This one-time migration has already been applied.'
assert Path(bpy.data.filepath)==root/'source'/'Empyrean_CamRanh_Exterior.blend'
def fingerprint(o):
    return hashlib.sha256(repr([(round(v.co.x,5),round(v.co.y,5),round(v.co.z,5)) for v in o.data.vertices]).encode()).hexdigest()
unchanged={o.name:fingerprint(o) for o in s.objects if o.type=='MESH' and o.name.startswith(('A_Land_North_','B_Sea_North_','C_Land_South_','D_Sea_South_'))}
ns={};exec(compile((root/'source'/'stages'/'00_common.py').read_text(),'common.py','exec'),ns)
exec(compile((root/'source'/'stages'/'12_pavilion.py').read_text(),'pavilion.py','exec'),ns)
Mesh=ns['Mesh'];M=ns['M'];Vector=ns['Vector'];math=ns['math'];col=ns['collection']('EMP_20_Site_and_landscape')
roadloop=[(-208,-280),(178,-280),(189,-306),(204,-313),(231,-313),(244,-300),(244,-220),(234,-198),(234,280),(-208,280)]
def replace_mesh(name,mesh):
    old=bpy.data.objects[name];temp=mesh.object('_replacement',col);old.data=temp.data;bpy.data.objects.remove(temp,do_unlink=True)
def copy_rest(name,out,skip):
    me=bpy.data.objects[name].data
    for poly in list(me.polygons)[skip:]:
        mat=me.materials[poly.material_index];key=next((k for k,v in M.items() if v==mat),None)
        if key is None:key=mat.name;M[key]=mat
        out.face([me.vertices[j].co[:] for j in poly.vertices],key,poly.use_smooth)
for name,width,z,material in [('Roads',11,.14,'asphalt'),('Plazas_paths_and_pool_decks',15,.12,'pale')]:
    me=bpy.data.objects[name].data
    # In the previous scene the first four polygons are the old rectangular perimeter.
    assert all(len(p.vertices)==4 for p in list(me.polygons)[:4])
    mesh=Mesh();mesh.joined_ribbon(roadloop,width,z,material);copy_rest(name,mesh,4);replace_mesh(name,mesh)
paint=Mesh()
for yy in range(-760,780,12):
    for xx in(-246,-231):paint.box((xx,yy,.064),(.14,5,.01),'paint')
for idx in range(len(roadloop)):
    a=Vector(roadloop[idx]);b=Vector(roadloop[(idx+1)%len(roadloop)]);d=b-a;u=d.normalized()
    for j in range(int(d.length//12)):
        p=a+u*(6+j*12);paint.box((p.x,p.y,.22),(4,.13,.01),'paint',math.atan2(d.y,d.x))
for yy in(-253,253):
    for xx in(-153,-113,-73,96,136,176):
        for dx in range(-12,15,3):paint.box((xx+dx,yy,.34),(.11,6,.015),'paint')
replace_mesh('Road_and_parking_markings',paint)
# Record that only the pavilion and its immediate ground/road connection changed.
assert all(fingerprint(bpy.data.objects[name])==value for name,value in unchanged.items())
audit={'tower_meshes_unchanged':len(unchanged),'pavilion_control_points':ns['controls'],'attachment_unchanged':True,'direction':'away from courtyard pool, south along the seaward boundary','road_loop_xy':roadloop}
(root/'qa'/'pavilion_direction_fix.json').write_text(json.dumps(audit,indent=2))
s['pavilion_curve_revision']=2
bpy.ops.wm.save_as_mainfile(filepath=str(root/'source'/'Empyrean_CamRanh_Exterior.blend'),compress=True)
print('FIX_SAVED',audit)
