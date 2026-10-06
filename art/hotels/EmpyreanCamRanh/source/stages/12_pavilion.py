"""Low sea-side pavilion: curve AWAY from the pool, toward the south boundary.
Direction checked against user_maps_reverse_overview.png and resort_map.jpg.
Shares the tower's existing attachment; not a mirror of the whole building.
"""
sp=PARAMS['towers'][3];c=collection('EMP_10_'+sp['id'])
for name in ('D_distinct_curved_pavilion_roof_and_colonnade','D_curved_pavilion_glazed_shell','South_east_pavilion_corner_ground'):
    if bpy.data.objects.get(name):bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
p0=Vector(arcpt(sp['cx'],sp['cy'],sp['rx'],sp['ry'],-math.radians(119)))
controls=[(p0.x+8,p0.y),(211,-252),(220,-269),(223,-284),(222,-296)]
path=[]
for i in range(len(controls)-1):
    a=Vector(controls[max(0,i-1)]);b=Vector(controls[i]);cc=Vector(controls[i+1]);d=Vector(controls[min(len(controls)-1,i+2)])
    for j in range(20):
        t=j/20
        path.append(.5*((2*b)+(-a+cc)*t+(2*a-5*b+4*cc-d)*t*t+(-a+3*b-3*cc+d)*t*t*t))
path.append(Vector(controls[-1]))
can=Mesh();glass=Mesh();sections=[]
for i,p in enumerate(path):
    tangent=(path[min(i+1,len(path)-1)]-path[max(i-1,0)]).normalized()
    normal=Vector((-tangent.y,tangent.x));z=8.6+.9*math.sin(i/(len(path)-1)*math.pi)
    sections.append((p+normal*8,p-normal*8,z))
for i in range(len(sections)-1):
    left,right,z=sections[i];nl,nr,nz=sections[i+1]
    can.face([(*left,z),(*right,z),(*nr,nz),(*nl,nz)],'pale')
    can.face([(*nl,nz-.5),(*nr,nz-.5),(*right,z-.5),(*left,z-.5)],'ivory')
    can.face([(*left,.7),(*right,.7),(*nr,.7),(*nl,.7)],'stone')
    for sg,a,b in [(1,left,nl),(-1,right,nr)]:
        edge=[(*a,z-.5),(*b,nz-.5),(*b,nz),(*a,z)]
        pane=[(*a,1),(*b,1),(*b,nz-.5),(*a,z-.5)]
        can.face(list(reversed(edge)) if sg==1 else edge,'ivory')
        glass.face(list(reversed(pane)) if sg==1 else pane,'glass_light')
        if i%4==0:can.beam((*a,.7),(*a,z-.05),.17,'ivory',8)
    if i%4==0:can.beam((*left,z+.04),(*right,z+.04),.10,'ivory',6)
left,right,z=sections[-1]
can.face([(*left,z-.5),(*right,z-.5),(*right,z),(*left,z)],'ivory')
glass.face([(*left,1),(*right,1),(*right,z-.5),(*left,z-.5)],'glass_light')
can.object('D_distinct_curved_pavilion_roof_and_colonnade',c)
glass.object('D_curved_pavilion_glazed_shell',c)
# Small corner infill supports the corrected outer pavilion and the road around it.
ground=Mesh();ground.box((207,-294.5,-.48),(88,57, .9),'grass')
ground.object('South_east_pavilion_corner_ground',collection('EMP_20_Site_and_landscape'))
PARAMS['pavilion_direction']={'status':'outward, away from pool','control_points_xy':[list(p) for p in controls],'reference':'User Google Maps screenshots and resort_map.jpg; estimated dimensions'}
(ROOT/'source'/'parameters.json').write_text(json.dumps(PARAMS,indent=2))
S['pavilion_curve_revision']=2
print('PAVILION_OUTWARD',controls)
