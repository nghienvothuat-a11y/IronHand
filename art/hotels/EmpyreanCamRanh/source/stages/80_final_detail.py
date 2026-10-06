"""Final appearance and reference-specific public-realm details."""
nt=M['grass'].node_tree;bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
diff=next(n for n in nt.nodes if n.type=='TEX_IMAGE' and n.image and 'leafy_grass_diff' in n.image.name)
gray=nt.nodes.new('ShaderNodeRGBToBW');nt.links.new(diff.outputs['Color'],gray.inputs['Color'])
ramp=nt.nodes.new('ShaderNodeValToRGB')
ramp.color_ramp.elements[0].position=.035;ramp.color_ramp.elements[0].color=(.026,.063,.009,1)
ramp.color_ramp.elements[1].position=.52;ramp.color_ramp.elements[1].color=(.18,.255,.042,1)
nt.links.new(gray.outputs['Val'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
M['grass'].diffuse_color=(.10,.18,.022,1)
ground=Mesh();ground.face([(-12000,-12000,-.65),(244,-12000,-.65),(244,12000,-.65),(-12000,12000,-.65)],'grass')
ground.object('Continuous_terrain_under_all_context',collection('EMP_90_Render_context'))

# Wavy paving motif on the sea-facing public axis, observed in the overhead photo.
paving=Mesh()
for row in range(18):
    points=[]
    for j in range(100):
        x=59+j*1.81;y=-23+row*2.55+1.8*math.sin(x*.13)
        points.append((x,y))
    paving.ribbon(points,.65,.257,'dark_paving')
paving.object('Wave_pattern_seafront_plaza',collection('EMP_20_Site_and_landscape'))

# Garden beds, low hedges, and white stepping stones near the north lazy river.
hedge=Mesh()
for sp in PARAMS['towers']:
    cx,cy=sp['cx'],sp['cy']
    for side in(-1,1):
        points=[(cx-19+j*1.65,cy+side*(43+4*math.sin(j*.11))) for j in range(48)]
        hedge.ribbon(points,1.9,.3,'leaf_deep')
        for j,p in enumerate(points):
            if j%2==0:bush(*p,.72)
    # A walkway axis from lobby toward the pool.
    for j in range(11):
        hedge.box((cx-40+j*2.0,cy,.31),(1.45,3.2,.14),'pale')
hedge.object('Garden_edges_and_stepping_stones',collection('EMP_20_Site_and_landscape'))

# Additional shallow shophouse rows on the land-side courtyard, kept as distinct shells.
col=collection('EMP_30_Arena_Town_Exterior');extra=Mesh()
for yy in(-63,):
    for xx in(-171,-142,-113,-84):
        for dx in(-8,0,8):
            x=xx+dx
            extra.box((x,yy,5.8),(7.5,16,11.2),'ivory')
            for side in(-1,1):
                for z in(2.3,5.9,9.4):
                    extra.box((x,yy+side*8.03,z),(5.7,.12,2.6),'glass')
                    extra.box((x,yy+side*8.8,z-1.45),(7.4,1.7,.19),'ivory')
                    if z>3:extra.box((x,yy+side*9.5,z-.86),(6.9,.09,.87),'rail')
            extra.box((x,yy,11.6),(7.8,16.3,.25),'ivory')
            extra.box((x,yy,12.5),(6,6,1.8),'ivory')
            for sg in(-1,1):
                for off in(-3,3):extra.beam((x+off,yy+sg*6,11.6),(x+off,yy+sg*6,14),.09,'ivory',4)
                for j in range(7):extra.box((x,yy+sg*(4+j*.5),14),(6.3,.15,.17),'ivory')
extra.object('Arena_Town_southern_terrace_row',col)

# Daylight balance: avoid a second solar disc giving competing shadows.
sky=next(n for n in S.world.node_tree.nodes if n.type=='TEX_SKY');sky.sun_disc=False
next(n for n in S.world.node_tree.nodes if n.type=='BACKGROUND').inputs['Strength'].default_value=.24
bpy.data.lights['Tropical_afternoon_sun'].energy=3.0
bpy.data.objects['Tropical_afternoon_sun'].rotation_euler=Vector((1,.65,-1.7)).to_track_quat('-Z','Y').to_euler()
S.view_settings.exposure=-.1
# Pool ceramic makes the shallow water read clear turquoise.
bs=next(n for n in M['water'].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
bs.inputs['Base Color'].default_value=(.012,.33,.42,1);bs.inputs['Roughness'].default_value=.16
bs.inputs['Metallic'].default_value=.08;bs.inputs['Transmission Weight'].default_value=.12

S.camera=bpy.data.objects['02_Sea_facing_aerial']
save_stage('individual_wings_render_ready')
