"""Keep planting clear of the corrected outward pavilion and local access road."""
import bpy,json
from mathutils import Vector
from pathlib import Path
_root=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
_s=bpy.data.scenes['Empyrean_Exterior']
_moves=[]
for ob in _s.objects:
    if not ob.name.startswith(('Coconut_palm','Tropical_shelter_belt','Tropical_tree','Parking_shade_tree','Landscape_shrub')):continue
    x,y=ob.location.x,ob.location.y
    if 202<x<237 and -304<y<-250:
        ob.location.x=191+(x%4);_moves.append(ob.name)
    elif 234<x<253 and -307<y<-207:
        ob.location.x=258+(x%5);_moves.append(ob.name)
    elif 172<x<243 and -327<y<-301:
        ob.location.y=-337-(abs(y)%7);_moves.append(ob.name)
(_root/'qa'/'pavilion_planting_clearance.json').write_text(json.dumps({'moved_objects':_moves,'count':len(_moves)},indent=2))
print('PAVILION_PLANTING_CLEARANCE',len(_moves))
