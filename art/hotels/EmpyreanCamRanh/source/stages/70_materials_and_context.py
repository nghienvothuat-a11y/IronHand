"""Packed CC0 PBR surfaces and detailed shared foliage for perspective rendering."""
texroot=ROOT/'source'/'textures'
for key,asset,width in [('grass','leafy_grass',2),('sand','aerial_beach_01',30)]:
    nt=M[key].node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    uv=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value=(4/width,4/width,4/width)
    nt.links.new(uv.outputs['UV'],mapping.inputs['Vector'])
    images={}
    for kind in ('diff','nor_gl','rough'):
        im=bpy.data.images.load(str(texroot/f'{asset}_{kind}_4k.jpg'),check_existing=True)
        if kind!='diff':im.colorspace_settings.name='Non-Color'
        im.pack();tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;tex.label=asset+' '+kind
        nt.links.new(mapping.outputs['Vector'],tex.inputs['Vector']);images[kind]=tex
    nt.links.new(images['diff'].outputs['Color'],bs.inputs['Base Color'])
    nt.links.new(images['rough'].outputs['Color'],bs.inputs['Roughness'])
    norm=nt.nodes.new('ShaderNodeNormalMap');norm.inputs['Strength'].default_value=.55
    nt.links.new(images['nor_gl'].outputs['Color'],norm.inputs['Color']);nt.links.new(norm.outputs['Normal'],bs.inputs['Normal'])

# Replace the broadleaf proxy spheres with thousands of individually angled leaves.
context=collection('EMP_90_Render_context')
for variant in range(3):
    old=bpy.data.objects.get('Tropical_tree_'+str(variant))
    if old is None:continue
    r=random.Random(8492+variant);mesh=Mesh()
    mesh.beam((0,0,0),(.2,0,7.3),.25,'trunk',10)
    for cluster in range(22):
        a=cluster*2.4;rad=r.uniform(.5,3.2)
        centre=Vector((rad*math.cos(a),rad*math.sin(a),r.uniform(5.1,9.1)))
        if cluster%3==0:mesh.beam((.15,0,4.2),centre,.08,'trunk',7)
        for i in range(340):
            v=Vector((r.uniform(-1,1),r.uniform(-1,1),r.uniform(-1,1)))
            if v.length>1:continue
            p=centre+Vector((v.x*1.65,v.y*1.65,v.z*1.4))
            direction=Vector((r.uniform(-1,1),r.uniform(-1,1),r.uniform(-.5,.5))).normalized()
            side=direction.cross(Vector((0,0,1))).normalized()
            length=r.uniform(.27,.5);width=r.uniform(.12,.24)
            mesh.face([p-direction*length,p-side*width+Vector((0,0,.06)),p+direction*length,p+side*width],['leaf_deep','leaf','leaf_light'][r.randrange(3)])
    temporary=mesh.object('Detailed_foliage_source',context);old_data=old.data
    for ob in S.objects:
        if ob.type=='MESH' and ob.data==old_data:ob.data=temporary.data
    bpy.data.objects.remove(temporary,do_unlink=True)

# A denser, irregular palm belt between pools and the beach.
for i in range(95):
    y=rng.uniform(-265,265);x=rng.uniform(256,279)
    if abs(y)<26:continue
    palm(x,y,rng.uniform(.85,1.3))

# Dune transition and broken wave foam: thin, irregular foam ribbons over the water.
shore=Mesh()
for line in range(5):
    for part in range(75):
        y0=-620+part*17+rng.uniform(-3,3);length=rng.uniform(6,16)
        pts=[]
        for j in range(14):
            yy=y0+length*j/13;xx=321+line*3.4+1.4*math.sin(yy*.055+line*.45)
            pts.append((xx,yy))
        shore.ribbon(pts,.18+line*.1,-.344+line*.001,'foam')
shore.object('Broken_shore_surf',context)

# An additional aerial angle looking toward the south from the northern beach.
name='06_North_sea_aerial'
if bpy.data.objects.get(name) is None:
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);collection('EMP_80_Cameras_and_lighting').objects.link(ob)
else:ob=bpy.data.objects[name]
ob.location=(610,645,455);target=Vector((12,0,22));ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
ob.data.lens=48;ob.data.clip_end=30000
for ob in S.objects:
    if ob.type=='CAMERA':ob.data.clip_end=30000
save_stage('packed_PBR_and_detail')
