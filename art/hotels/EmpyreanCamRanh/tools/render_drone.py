import bpy,sys,argparse,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--frames',default='');p.add_argument('--width',type=int,default=1920);p.add_argument('--samples',type=int,default=32);p.add_argument('--out',required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);s=bpy.context.scene
s.render.resolution_x=a.width;s.render.resolution_y=round(a.width*9/16);s.eevee.taa_render_samples=a.samples
out=Path(a.out);out.mkdir(exist_ok=True,parents=True)
frames=[int(f) for f in a.frames.split(',')] if a.frames else range(1,481)
t0=time.time()
for frame in frames:
 f=out/f'frame_{frame:04d}.png'
 if f.exists():continue
 s.frame_set(frame);s.render.filepath=str(f);t=time.time();bpy.ops.render.render(write_still=True)
 print('DRONE_FRAME',frame,'SECONDS',round(time.time()-t,2),'ELAPSED',round(time.time()-t0,1),flush=True)
print('RENDER_DONE',flush=True)
