"""Empyrean exterior reconstruction. Metres; +X = sea, +Y = north.
Photo-based approximation, NOT survey/CAD. All geometry is original and editable.
Run stages inside the scene Empyrean_Exterior. No destructive global reset.
"""
import bpy, math, random, json, os
from mathutils import Vector
from collections import defaultdict
from pathlib import Path
ROOT=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
S=bpy.data.scenes['Empyrean_Exterior']
rng=random.Random(1026)

def collection(name):
    c=bpy.data.collections.get(name)
    if c is None:
        c=bpy.data.collections.new(name); S.collection.children.link(c)
    return c

def mat(name, color, rough=.5, metal=0, bump=0, scale=6, transmission=0):
    if bpy.data.materials.get('EMP_'+name):return bpy.data.materials['EMP_'+name]
    m=bpy.data.materials.new('EMP_'+name); m.diffuse_color=(*color,1)
    m.use_nodes=True
    n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Roughness'].default_value=rough
    n.inputs['Metallic'].default_value=metal
    n.inputs['Transmission Weight'].default_value=transmission
    if bump:
        tex=m.node_tree.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=scale
        tex.inputs['Detail'].default_value=3
        b=m.node_tree.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value=.23
        b.inputs['Distance'].default_value=bump
        m.node_tree.links.new(tex.outputs['Fac'],b.inputs['Height'])
        m.node_tree.links.new(b.outputs['Normal'],n.inputs['Normal'])
    return m

M={
 'ivory':mat('Warm_white_precast',(.79,.80,.76),.62,bump=.028,scale=65),
 'soffit':mat('Slab_soffit',(.60,.64,.61),.7),
 'stone':mat('Limestone_paving',(.61,.57,.46),.8,bump=.035,scale=35),
 'pale':mat('Pale_terrazzo',(.77,.75,.65),.78,bump=.03,scale=45),
 'dark_paving':mat('Basalt_paving',(.22,.255,.26),.75,bump=.035,scale=45),
 'asphalt':mat('Asphalt',(.055,.069,.073),.93,bump=.025,scale=160),
 'glass':mat('Blue_green_glazing',(.09,.20,.24),.17,.46,transmission=.12),
 'glass_light':mat('Glazing_sky_reflection',(.23,.34,.36),.24,.35),
 'curtain':mat('Opaque_warm_window_blinds',(.39,.38,.30),.55),
 'rail':mat('Balcony_glass',(.27,.40,.42),.2,.35,transmission=.22),
 'metal':mat('Champagne_aluminium',(.34,.34,.27),.28,.72),
 'black':mat('Recesses_charcoal',(.025,.037,.037),.65),
 'water':mat('Pool_water',(.025,.42,.52),.12,.25,transmission=.26),
 'tile':mat('Pool_mosaic',(.06,.36,.40),.4,bump=.008,scale=90),
 'grass':mat('Irrigated_lawn',(.19,.29,.065),.92,bump=.06,scale=50),
 'roof':mat('Roof_membrane',(.35,.36,.32),.8,bump=.035,scale=20),
 'wood':mat('Teak_decking',(.32,.21,.105),.65,bump=.025,scale=22),
 'sand':mat('Beach_sand',(.63,.54,.37),.91,bump=.11,scale=16),
 'trunk':mat('Palm_trunk',(.25,.20,.12),.93,bump=.055,scale=60),
 'leaf':mat('Palm_frond_dark',(.065,.17,.038),.74),
 'leaf_light':mat('Palm_frond_sunlit',(.18,.30,.06),.73),
 'fabric':mat('Ivory_canvas',(.86,.81,.67),.92,bump=.015,scale=70),
 'paint':mat('Traffic_paint',(.84,.83,.68),.7),
 'ocean':mat('Cam_Ranh_sea',(.025,.22,.285),.17,.30,bump=.21,scale=1.3),
 'foam':mat('Shoreline_foam',(.65,.79,.76),.48),
}

class Mesh:
    def __init__(self): self.v=[]; self.f=[]; self.mi=[]; self.sm=[]; self.keys=[]
    def face(self, pts, material='ivory', smooth=False):
        start=len(self.v); self.v.extend(tuple(p) for p in pts)
        self.f.append(tuple(range(start,start+len(pts))))
        if material not in self.keys:self.keys.append(material)
        self.mi.append(self.keys.index(material)); self.sm.append(smooth)
    def box(self, center, size, material='ivory', angle=0):
        x,y,z=center; a,b,c=[s/2 for s in size]; co=math.cos(angle); si=math.sin(angle)
        p=[(x+u*co-v*si,y+u*si+v*co,z+w) for u,v,w in
           [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]]
        for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:
            self.face([p[i] for i in ids],material)
    def beam(self,a,b,r=.07,material='metal',n=6):
        a,b=Vector(a),Vector(b); d=b-a
        if d.length<1e-6:return
        d.normalize(); aux=Vector((0,0,1)) if abs(d.z)<.95 else Vector((1,0,0))
        u=d.cross(aux).normalized(); v=d.cross(u).normalized()
        ra=[a+r*(u*math.cos(i*2*math.pi/n)+v*math.sin(i*2*math.pi/n)) for i in range(n)]
        rb=[p+(b-a) for p in ra]
        self.face(list(reversed(ra)),material); self.face(rb,material)
        for i in range(n):j=(i+1)%n;self.face([ra[i],ra[j],rb[j],rb[i]],material,True)
    def disk(self,c,r,z,material='stone',n=96):
        pts=[(c[0]+r*math.cos(i*2*math.pi/n),c[1]+r*math.sin(i*2*math.pi/n),z) for i in range(n)]
        self.face(pts,material)
    def ribbon(self,points,width,z,material='stone',closed=False):
        count=len(points)
        for i in range(count if closed else count-1):
            j=(i+1)%count; a=Vector(points[i]);b=Vector(points[j]);d=(b-a).normalized();q=Vector((-d.y,d.x))*width/2
            self.face([(a.x+q.x,a.y+q.y,z),(a.x-q.x,a.y-q.y,z),(b.x-q.x,b.y-q.y,z),(b.x+q.x,b.y+q.y,z)],material)
    def joined_ribbon(self,points,width,z,material='stone'):
        """Closed continuous strip with mitred joins, for the perimeter road."""
        points=[Vector(p) for p in points];edges=[]
        for i,p in enumerate(points):
            prev=(p-points[i-1]).normalized();nxt=(points[(i+1)%len(points)]-p).normalized()
            n0=Vector((-prev.y,prev.x));n1=Vector((-nxt.y,nxt.x));bis=(n0+n1).normalized()
            off=bis*(width/2/max(.25,bis.dot(n0)));edges.append((p+off,p-off))
        for i,(left,right) in enumerate(edges):
            nl,nr=edges[(i+1)%len(edges)]
            self.face([(*left,z),(*right,z),(*nr,z),(*nl,z)],material)
    def object(self,name,c,uv=True):
        me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(self.v,[],self.f);me.update()
        for key in self.keys:me.materials.append(M[key])
        for p,mi,sm in zip(me.polygons,self.mi,self.sm):p.material_index=mi;p.use_smooth=sm
        if uv:
            layer=me.uv_layers.new(name='UV_Metre_Tiling')
            for p in me.polygons:
                axis=max(range(3),key=lambda i:abs(p.normal[i]))
                ij=[i for i in range(3) if i!=axis]
                for li in p.loop_indices:
                    co=me.vertices[me.loops[li].vertex_index].co
                    layer.data[li].uv=(co[ij[0]]/4,co[ij[1]]/4)
        ob=bpy.data.objects.new(name,me);c.objects.link(ob);return ob

def planpoint(spec,u):
    rx,ry=spec['rx'],spec['ry'];blend=spec.get('curve_blend',0)
    run=spec.get('wing_run',1.85)*spec.get('wing_negative' if u<0 else 'wing_positive',1)
    px=-rx+rx*run*u*u;py=ry*u
    ex=-rx*math.cos(u*math.pi/2)+rx*(run-1)*abs(u)**3
    ey=ry*(.86*math.sin(u*math.pi/2)+.14*u)
    return(spec['cx']+px*(1-blend)+ex*blend,spec['cy']+py*(1-blend)+ey*blend)

def arcpt(cx,cy,rx,ry,t,z=0):
    spec=next(p for p in PARAMS['towers'] if p['cx']==cx and p['cy']==cy)
    u=t/math.radians(119);off=rx-spec['rx'];px,py=planpoint(spec,u)
    p=planpoint(spec,u-.0001);q=planpoint(spec,u+.0001);dx=q[0]-p[0];dy=q[1]-p[1];length=math.hypot(dx,dy)
    return(px-off*dy/length,py+off*dx/length,z)

def facade_angle(rx,ry,t,cx,cy):
    spec=next(p for p in PARAMS['towers'] if p['cx']==cx and p['cy']==cy);u=t/math.radians(119)
    p=planpoint(spec,u-.0001);q=planpoint(spec,u+.0001)
    return -math.atan2(q[0]-p[0],q[1]-p[1])

def arc_strip(mesh,cx,cy,rx,ry,half,a,b,z,thick,material='ivory',n=100):
    for i in range(n):
        t=a+(b-a)*i/n;u=a+(b-a)*(i+1)/n
        p=[arcpt(cx,cy,rx-half,ry-half,t,z),arcpt(cx,cy,rx+half,ry+half,t,z),
           arcpt(cx,cy,rx+half,ry+half,u,z),arcpt(cx,cy,rx-half,ry-half,u,z)]
        mesh.face(list(reversed(p)),material)
        if thick>0:
            low=[(v[0],v[1],v[2]-thick) for v in p]
            mesh.face(low,'soffit')
            for j in [0,1,2,3]:
                k=(j+1)%4
                if j in (1,3) or (j==0 and i==0) or (j==2 and i==n-1):mesh.face([p[k],low[k],low[j],p[j]],material, j in(1,3))

def save_stage(label):
    dest=ROOT/'source'/'Empyrean_CamRanh_Exterior.blend'
    bpy.data.libraries.write(str(dest),{S},fake_user=True,compress=True)
    print('STAGE',label,'objects',len(S.objects),'saved',dest)

PARAMS={
 'units':'metres','scale_status':'photo-estimated, not surveyed',
 'site_bounds':[-218,248,-300,300],
 'towers':[
  {'id':'A_Land_North','cx':-70,'cy':155,'rx':72,'ry':87,'floors':25,'curve_blend':.10,'wing_run':1.75,'wing_negative':1.01,'wing_positive':.97,'crown_negative':12,'crown_positive':10},
  {'id':'B_Sea_North','cx':125,'cy':155,'rx':69,'ry':85,'floors':21,'curve_blend':.22,'wing_run':1.83,'wing_negative':.96,'wing_positive':1.06,'crown_negative':10,'crown_positive':13},
  {'id':'C_Land_South','cx':-70,'cy':-155,'rx':73,'ry':86,'floors':12,'curve_blend':.72,'wing_run':1.66,'wing_negative':1.10,'wing_positive':.94,'crown_negative':20,'crown_positive':27},
  {'id':'D_Sea_South','cx':125,'cy':-155,'rx':70,'ry':87,'floors':10,'curve_blend':.86,'wing_run':1.72,'wing_negative':1.12,'wing_positive':.95,'crown_negative':23,'crown_positive':29},
 ],'floor_height':3.05,'podium_height':5.2,
 'note':'Spatial tower IDs. South heights follow the actual 2026 official photos, differing from older marketing renders. Counts are modelling estimates; exact dimensions require drawings.'}
(ROOT/'source'/'parameters.json').write_text(json.dumps(PARAMS,indent=2))
print('COMMON_READY')
