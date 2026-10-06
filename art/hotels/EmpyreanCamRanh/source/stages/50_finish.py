"""Final material variation, continuous terrain and exterior signage."""
# Large-scale colour breakup keeps turf and sand from reading as flat diagrams.
for key,lo,hi,scale in [
 ('grass',(.085,.145,.022),(.23,.32,.070),28),
 ('sand',(.47,.38,.25),(.74,.64,.44),45),
 ('ocean',(.014,.13,.19),(.045,.30,.35),5),
]:
    m=M[key];nt=m.node_tree
    bs=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=scale;tex.inputs['Detail'].default_value=3
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*lo,1);ramp.color_ramp.elements[1].color=(*hi,1)
    nt.links.new(tex.outputs['Fac'],ramp.inputs['Fac']);nt.links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
ctx=Mesh();ctx.box((-581,0,-1.3),(1650,3600,1.4),'grass');ctx.object('Continuous_land_substrate',collection('EMP_90_Render_context'))
# Palm leaflet shaders are double-sided opaque surfaces for both render and glTF.
for key in('leaf','leaf_light','leaf_deep','leaf_yellow'):
    bs=next(n for n in M[key].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Subsurface Weight'].default_value=.065

# Text is confined to the external entrance canopy fascia, not a fictitious logo.
signcol=collection('EMP_50_Exterior_signage')
for sp in PARAMS['towers']:
    d=bpy.data.curves.new('Exterior_nameplate','FONT');d.body='THE EMPYREAN';d.align_x='CENTER';d.size=.95;d.extrude=.024
    ob=bpy.data.objects.new(sp['id']+'_nameplate',d);signcol.objects.link(ob)
    ob.location=(sp['cx']-sp['rx']+33.6,sp['cy'],4.05)
    ob.rotation_euler=(math.pi/2,0,math.pi/2);d.materials.append(M['metal'])
save_stage('finished_exterior')
