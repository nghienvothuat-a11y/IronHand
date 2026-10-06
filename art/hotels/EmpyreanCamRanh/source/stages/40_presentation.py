"""Architectural cameras and daylight; render scene independent of IronHand."""
pc=collection('EMP_99_Presentation')
try:S.render.engine='CYCLES'
except TypeError as exc:raise RuntimeError(str(exc))
S.cycles.samples=64;S.cycles.use_denoising=True
S.cycles.max_bounces=6;S.cycles.transmission_bounces=4
S.cycles.transparent_max_bounces=4
S.cycles.device='GPU'
prefs=bpy.context.preferences.addons['cycles'].preferences
prefs.get_devices()
for d in prefs.devices:d.use=(d.type=='METAL')
S.render.resolution_x=2400;S.render.resolution_y=1600;S.render.resolution_percentage=100
S.render.image_settings.file_format='PNG';S.render.image_settings.color_mode='RGB';S.render.image_settings.color_depth='8'
S.render.film_transparent=False
S.render.image_settings.color_mode='RGB'
S.world=bpy.data.worlds.new('Empyrean_daylight');S.world.use_nodes=True
nt=S.world.node_tree
bg=next(n for n in nt.nodes if n.type=='BACKGROUND')
sky=nt.nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING'
sky.sun_elevation=math.radians(38);sky.sun_rotation=math.radians(130)
sky.sun_disc=True
bg.inputs['Strength'].default_value=.27;nt.links.new(sky.outputs['Color'],bg.inputs['Color'])
ld=bpy.data.lights.new('Tropical_afternoon_sun','SUN');lo=bpy.data.objects.new('Tropical_afternoon_sun',ld);pc.objects.link(lo)
ld.energy=2.2;ld.angle=math.radians(2.0);lo.rotation_euler=(math.radians(29),math.radians(-21),math.radians(132))
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);pc.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.type='PERSP';d.lens=lens;d.clip_end=10000
    return o
hero=camera('01_Aerial_from_land',(-650,-740,575),(22,0,12),47)
camera('02_Sea_facing_aerial',(620,-735,450),(-3,-14,20),49)
camera('03_Pool_and_terraces',(274,-249,46),(87,-158,31),35)
camera('04_Entrance_and_plaza',(-320,-85,47),(-50,22,24),29)
top=camera('05_Masterplan',(10,0,1050),(10,0,0),49);top.data.type='ORTHO';top.data.ortho_scale=720
S.camera=hero;S.render.filepath=str(ROOT/'renders'/'01_Aerial_from_land.png')
S['asset_title']='The Empyrean Cam Ranh — exterior study'
S['accuracy']='Photo-based architectural approximation; no survey dimensions or as-built drawings supplied.'
S['scope']='Four exterior hotel wings, terraces, shophouse exteriors, central plaza, pools, landscape and coastline context. No hotel room interiors.'
S['reference_lat_lon']='12.0266349,109.2169059'
S['render_priority']='Architectural perspectives. Not a mobile-ready LOD asset.'
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.clip_end=10000
save_stage('presentation')
print('DEVICES',[(d.name,d.use) for d in prefs.devices])
