import bpy, sys, argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--camera',default='01_Aerial_from_land');p.add_argument('--out',required=True);p.add_argument('--width',type=int,default=1600);p.add_argument('--samples',type=int,default=48);p.add_argument('--cpu',action='store_true')
args=p.parse_args(sys.argv[sys.argv.index('--')+1:])
s=bpy.data.scenes['Empyrean_Exterior'];bpy.context.window.scene=s
s.camera=bpy.data.objects[args.camera]
s.render.resolution_x=args.width;s.render.resolution_y=round(args.width*2/3);s.render.resolution_percentage=100
s.cycles.samples=args.samples;s.cycles.use_denoising=True
prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.get_devices()
metal=[d for d in prefs.devices if d.type=='METAL'] if not args.cpu else []
for d in prefs.devices:d.use=d.type=='METAL' if metal else d.type=='CPU'
s.cycles.device='GPU' if metal else 'CPU'
s.render.filepath=args.out
print('RENDER_DEVICE',prefs.compute_device_type,[(d.name,d.use) for d in prefs.devices],flush=True)
bpy.ops.render.render(write_still=True,scene=s.name)
print('RENDER_COMPLETE',args.out,flush=True)
