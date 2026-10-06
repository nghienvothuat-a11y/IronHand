"""20-second continuous, photo-model drone route. Preserve static master."""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
R=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh')
s=bpy.data.scenes['Empyrean_Exterior'];bpy.context.window.scene=s
c=bpy.data.collections.get('EMP_81_Drone_Animation')
if not c:
 c=bpy.data.collections.new('EMP_81_Drone_Animation');s.collection.children.link(c)
for o in list(c.objects):bpy.data.objects.remove(o,do_unlink=True)
cam=bpy.data.objects.new('08_Drone_20s',bpy.data.cameras.new('Drone_FullFrame_26mm'));c.objects.link(cam)
cam.data.lens=26;cam.data.sensor_width=36;cam.data.clip_start=.2;cam.data.clip_end=6000
cam.rotation_mode='QUATERNION';s.camera=cam
spec=json.loads((R/'source/parameters.json').read_text())['towers'][1]
def plan(u):
 rx,ry=spec['rx'],spec['ry'];b=spec['curve_blend'];run=spec['wing_run']*spec['wing_negative' if u<0 else 'wing_positive']
 px=-rx+rx*run*u*u;py=ry*u
 ex=-rx*math.cos(u*math.pi/2)+rx*(run-1)*abs(u)**3;ey=ry*(.86*math.sin(u*math.pi/2)+.14*u)
 return Vector((spec['cx']+px*(1-b)+ex*b,spec['cy']+py*(1-b)+ey*b))
def inside(u,d,z):
 p=plan(u);v=(plan(u+.0001)-plan(u-.0001)).normalized();p+=Vector((v.y,-v.x))*d
 return (p.x,p.y,z)
# Each key is time, position, gaze target. Hermite tangents avoid stop-start motion.
keys=[
 (0,(475,145,68),(95,148,22)),
 (2.0,(300,153,43),(123,155,12)),
 (3.8,(174,159,28),(100,155,13)),
 (5.3,(100,164,35),(64,162,33)),
 (6.5,inside(0,28,37),inside(0,8.5,37)),
 (8.1,inside(-.36,28,36),inside(-.36,8.5,36)),
 (9.5,inside(-.67,28,28),inside(-.67,8.5,28)),
 (10.7,(210,100,26),(179,65,22)),
 (11.8,(239,40,24),(139,0,14)),
 (12.7,(197,0,21),(52,0,12)),
 (14.0,(57,0,20),(-89,25,15)),
 (15.0,(-63,0,21),(-61,108,26)),
 (15.8,(-155,0,24),(20,22,20)),
 (16.5,(-224,-18,39),(0,0,20)),
 (17.3,(-291,-100,99),(0,0,22)),
 (18.5,(-405,-248,220),(0,0,23)),
 (20,(-535,-425,365),(12,0,22)),
]
def spline(t,col):
 ix=next((j for j in range(len(keys)-1) if t<=keys[j+1][0]),len(keys)-2)
 a,b=keys[ix],keys[ix+1];dt=b[0]-a[0];u=max(0,min(1,(t-a[0])/dt));p0=Vector(a[col]);p1=Vector(b[col])
 def tangent(i):
  if i==0:return (Vector(keys[1][col])-Vector(keys[0][col]))/(keys[1][0]-keys[0][0])*.65
  if i==len(keys)-1:return (Vector(keys[-1][col])-Vector(keys[-2][col]))/(keys[-1][0]-keys[-2][0])*.50
  return (Vector(keys[i+1][col])-Vector(keys[i-1][col]))/(keys[i+1][0]-keys[i-1][0])*.78
 return (2*u**3-3*u*u+1)*p0+(u**3-2*u*u+u)*dt*tangent(ix)+(-2*u**3+3*u*u)*p1+(u**3-u*u)*dt*tangent(ix+1)
s.render.fps=24;s.render.fps_base=1;s.frame_start=1;s.frame_end=480
# Interpolate unwrapped yaw/pitch rather than a target passing close to camera.
# This keeps the final turn smooth and horizon level.
angles=[]
for t,p,target in keys:
 d=Vector(target)-Vector(p);yaw=math.atan2(d.y,d.x);pitch=math.atan2(d.z,math.hypot(d.x,d.y))
 if angles:
  while yaw-angles[-1][0]>math.pi:yaw-=2*math.pi
  while yaw-angles[-1][0]<-math.pi:yaw+=2*math.pi
 angles.append(Vector((yaw,pitch,0)))
anglekeys=[(k[0],angles[i],angles[i]) for i,k in enumerate(keys)]
samples=[];prev=None
for frame in range(0,483):
 t=(frame-1)/24;p=spline(t,1);target=spline(t,2)
 original_keys=keys;keys=anglekeys;ang=spline(t,1);keys=original_keys
 direction=Vector((math.cos(ang.x)*math.cos(ang.y),math.sin(ang.x)*math.cos(ang.y),math.sin(ang.y)))
 q=direction.to_track_quat('-Z','Y')
 if prev and prev.dot(q)<0:q.negate()
 cam.location=p;cam.rotation_quaternion=q
 cam.keyframe_insert('location',frame=frame);cam.keyframe_insert('rotation_quaternion',frame=frame)
 if 1<=frame<=480:samples.append({'frame':frame,'time':t,'position':list(p),'target':list(target),'rotation':list(q)})
 prev=q.copy()
# Blender 5 actions are layered.
a=cam.animation_data.action
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
s.timeline_markers.clear()
for name,t in [('SEA_APPROACH',0),('POOL_OVERFLIGHT',3.8),('GLASS_CLOSE_PASS',6.5),('TURN_TO_CENTRAL_ROAD',10.7),('CENTRAL_ROAD',12.7),('CLIMB_AND_REVEAL',16.5)]:
 marker=s.timeline_markers.new(name,frame=round(t*24)+1)
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=48
s.eevee.use_raytracing=True;s.eevee.ray_tracing_method='SCREEN';s.eevee.ray_tracing_options.resolution_scale='2'
s.eevee.ray_tracing_options.screen_trace_quality=.5;s.eevee.use_fast_gi=True;s.eevee.fast_gi_method='GLOBAL_ILLUMINATION';s.eevee.fast_gi_resolution='2'
s.eevee.fast_gi_ray_count=2;s.eevee.fast_gi_step_count=12;s.eevee.shadow_pool_size='1024'
s.render.use_motion_blur=True;s.render.motion_blur_shutter=.24;s.eevee.motion_blur_steps=2
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.color_depth='8';s.render.image_settings.compression=15
s.render.film_transparent=False;s.render.filepath=str(R/'renders/drone_frames/frame_')
s['drone_duration_seconds']=20;s['drone_route']='Sea > B north-sea pool > curved glass > central road sea to land > rising resort reveal'
s['drone_version']=3
s.frame_set(1)
for ar in bpy.context.screen.areas:
 if ar.type=='VIEW_3D':ar.spaces.active.region_3d.view_perspective='CAMERA'
(R/'qa/drone_route.json').write_text(json.dumps({'fps':24,'frames':480,'control_points':keys,'samples':samples},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'source/Empyrean_CamRanh_Drone_20s.blend'),compress=True)
print('DRONE_CREATED',len(samples),len(s.objects),flush=True)
