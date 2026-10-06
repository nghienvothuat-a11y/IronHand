import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
R=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh');s=bpy.context.scene
route=json.loads((R/'qa/drone_route.json').read_text())['samples']
objs=[];trees={}
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 pts=[o.matrix_world@Vector(c) for c in o.bound_box];lo=Vector(tuple(min(p[a] for p in pts) for a in range(3)));hi=Vector(tuple(max(p[a] for p in pts) for a in range(3)))
 # Only objects sufficiently near some sampled camera position need BVH.
 if not any(all(lo[a]-8<=r['position'][a]<=hi[a]+8 for a in range(3)) for r in route):continue
 if o.data not in trees:trees[o.data]=BVHTree.FromPolygons([v.co for v in o.data.vertices],[p.vertices[:] for p in o.data.polygons],all_triangles=False)
 objs.append((o,lo,hi,o.matrix_world.inverted_safe(),min(abs(x) for x in o.scale)))
nearest=[];intersections=[]
for idx,r in enumerate(route):
 p=Vector(r['position']);near=(999,None)
 for o,lo,hi,inv,scale in objs:
  if any(p[a]<lo[a]-8 or p[a]>hi[a]+8 for a in range(3)):continue
  hit=trees[o.data].find_nearest(inv@p)
  if hit[0] is not None:
   dist=(o.matrix_world@hit[0]-p).length
   if dist<near[0]:near=(dist,o.name)
  if idx:
   pp=Vector(route[idx-1]['position']);a=inv@pp;b=inv@p;d=b-a
   if d.length>1e-7:
    hit=trees[o.data].ray_cast(a,d.normalized(),d.length)
    if hit[0] is not None:intersections.append({'frame':r['frame'],'object':o.name})
 if near[0]<8:nearest.append({'frame':r['frame'],'distance':near[0],'object':near[1]})
speeds=[(Vector(b['position'])-Vector(a['position'])).length*24 for a,b in zip(route,route[1:])]
turns=[Quaternion(a['rotation']).rotation_difference(Quaternion(b['rotation'])).angle*180/math.pi*24 for a,b in zip(route,route[1:])]
out={'samples':len(route),'segment_surface_intersections':intersections,'closest_surface':min(nearest,key=lambda n:n['distance']) if nearest else None,'max_speed_mps':max(speeds),'max_turn_degrees_per_second':max(turns),'nearby_samples_under_3m':[n for n in nearest if n['distance']<3]}
(R/'qa/drone_collision_audit.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2),flush=True)
