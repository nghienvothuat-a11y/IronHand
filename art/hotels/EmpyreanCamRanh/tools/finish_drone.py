"""Validate the rendered sequence, encode H.264, create delivery proof."""
import json,subprocess,hashlib,os
from pathlib import Path
from PIL import Image,ImageDraw
R=Path('/Users/mrk/3D-Assets/EmpyreanCamRanh');frames=R/'renders/drone_frames'
expected=[frames/f'frame_{f:04d}.png' for f in range(1,481)]
assert all(p.exists() for p in expected), 'The 480-frame render is incomplete'
for p in expected:
 with Image.open(p) as im:
  assert im.size==(1920,1080),(p,im.size)
  im.verify()
output=R/'renders/Empyrean_CamRanh_Drone_20s.mp4';temp=output.with_name(output.stem+'.encoding.mp4')
cmd=['/opt/homebrew/bin/ffmpeg','-y','-framerate','24','-start_number','1','-i',str(frames/'frame_%04d.png'),'-frames:v','480','-vf','scale=in_range=full:out_range=tv:out_color_matrix=bt709','-c:v','libx264','-preset','slow','-crf','17','-pix_fmt','yuv420p','-r','24','-color_primaries','bt709','-color_trc','iec61966-2-1','-colorspace','bt709','-movflags','+faststart','-an','-metadata','title=The Empyrean Cam Ranh - 20s Drone Tour',str(temp)]
subprocess.run(cmd,check=True)
info=json.loads(subprocess.check_output(['/opt/homebrew/bin/ffprobe','-v','error','-show_streams','-show_format','-of','json',str(temp)]))
v=next(s for s in info['streams'] if s['codec_type']=='video')
assert (v['width'],v['height'],v['nb_frames'],v['r_frame_rate'])==(1920,1080,'480','24/1'),v
assert abs(float(info['format']['duration'])-20)<.001,info
# Full decode catches corrupt or truncated output beyond metadata-only checks.
subprocess.run(['/opt/homebrew/bin/ffmpeg','-v','error','-i',str(temp),'-f','null','-'],check=True)
os.replace(temp,output)
contactframes=[1,49,92,133,157,195,229,260,306,337,361,385,409,438,480]
contact=Image.new('RGB',(1440,5*297),(22,25,29));draw=ImageDraw.Draw(contact)
for i,f in enumerate(contactframes):
 with Image.open(expected[f-1]) as im:
  im=im.resize((480,270),Image.Resampling.LANCZOS);x=i%3*480;y=i//3*297;contact.paste(im,(x,y));draw.text((x+12,y+278),f'{(f-1)/24:05.2f} s',fill=(225,230,233))
contact.save(R/'renders/Empyrean_Drone_Storyboard.jpg',quality=93)
files=[output,R/'exports/Empyrean_CamRanh_Exterior_Drone.fbx',R/'source/Empyrean_CamRanh_Drone_20s.blend',R/'renders/Empyrean_Drone_Storyboard.jpg']
manifest={'video':info,'checks':{'png_frames_valid':480,'full_video_decode':True,'fbx_roundtrip':json.loads((R/'qa/fbx_roundtrip_validation.json').read_text()),'camera_route':json.loads((R/'qa/drone_collision_audit.json').read_text())},'files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]}
(R/'qa/drone_delivery_manifest.json').write_text(json.dumps(manifest,indent=2));print('DELIVERY_READY',output,flush=True)
