import bpy,time
from pathlib import Path
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.use_adaptive_sampling=True;s.cycles.adaptive_threshold=.08;s.cycles.max_bounces=5;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=3;s.cycles.transmission_bounces=3
p=bpy.context.preferences.addons['cycles'].preferences;p.get_devices()
for d in p.devices:d.use=d.type=='METAL'
s.cycles.device='GPU';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.use_persistent_data=True
for f in (157,1,438):
 s.frame_set(f);s.render.filepath=f'/Users/mrk/3D-Assets/EmpyreanCamRanh/qa/cycles_drone_{f:04d}.png';t=time.time();bpy.ops.render.render(write_still=True);print('BENCH',f,time.time()-t,flush=True)
