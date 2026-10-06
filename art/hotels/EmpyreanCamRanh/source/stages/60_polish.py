"""Lighting/material corrections after inspecting the first actual render."""
S.view_settings.exposure=-.8
next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.10
bpy.data.lights['Tropical_afternoon_sun'].energy=1.9
for key,col,rough,metal in [('glass',(.035,.085,.105),.23,.30),('glass_light',(.12,.205,.225),.28,.25),('rail',(.12,.22,.245),.24,.2)]:
    bs=next(n for n in M[key].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal

for key in ('grass','sand','ocean'):
    nt=M[key].node_tree;coord=nt.nodes.new('ShaderNodeTexCoord')
    for tex in [n for n in nt.nodes if n.type=='TEX_NOISE']:
        # Object coordinates are metres for these world-space meshes.
        nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
        is_color=any(link.to_node.type=='VALTORGB' for link in tex.outputs['Fac'].links)
        tex.inputs['Scale'].default_value=({'grass':.09,'sand':.09,'ocean':.009}[key] if is_color else {'grass':8,'sand':14,'ocean':.7}[key])
nt=M['water'].node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
coord=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.1
bn=nt.nodes.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.24;bn.inputs['Distance'].default_value=.08
nt.links.new(coord.outputs['Object'],noise.inputs['Vector']);nt.links.new(noise.outputs['Fac'],bn.inputs['Height']);nt.links.new(bn.outputs['Normal'],bs.inputs['Normal'])
bs.inputs['Base Color'].default_value=(.017,.27,.32,1)

# Broader foliage for the surrounding tropical shelter belt. Shared mesh instances.
context=collection('EMP_90_Render_context');tree_templates=[]
for variant in range(3):
    tm=Mesh();r=random.Random(929+variant)
    tm.beam((0,0,0),(.25,0,7),.25,'trunk',9)
    for i in range(30):
        a=i*2.4;rad=r.uniform(.4,3.2);z=r.uniform(5,9)
        c=(rad*math.cos(a),rad*math.sin(a),z)
        ellipsoid(tm,c,(r.uniform(1.1,1.9),r.uniform(1.2,2),r.uniform(1.2,2.1)),['leaf_deep','leaf','leaf_light'][i%3],10,7)
        if i%7==0:tm.beam((.15,0,4),c,.095,'trunk',6)
    ob=tm.object('Tropical_tree_'+str(variant),context);ob.location=(-285-variant*15,310,0);tree_templates.append(ob)
for i in range(480):
    if i<300:x=rng.uniform(-394,-263);y=rng.uniform(-460,460)
    else:x=rng.uniform(-205,250);y=rng.choice((-1,1))*rng.uniform(315,455)
    base=rng.choice(tree_templates);ob=bpy.data.objects.new('Tropical_shelter_belt',base.data);context.objects.link(ob)
    ob.location=(x,y,-.55);sc=rng.uniform(.75,1.2);ob.scale=(sc,sc,sc);ob.rotation_euler.z=rng.random()*math.tau
# A few shade trees in the parking courts; keep the central view corridors open.
for yy in(-249,249):
    for xx in(-184,-153,-115,-73,-28,12,54,97,139,180):
        base=rng.choice(tree_templates);ob=bpy.data.objects.new('Parking_shade_tree',base.data);collection('EMP_40_Palms_and_planting').objects.link(ob)
        ob.location=(xx,yy+8,.1);ob.scale=(.55,.55,.55)
S.cycles.samples=96
save_stage('render_polish')
