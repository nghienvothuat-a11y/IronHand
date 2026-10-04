import bpy,json
bpy.ops.wm.open_mainfile(filepath='/Users/mrk/IronHand/art/blender/IronHand_MK1_Rigged.blend')
r=bpy.data.objects['IronHand_Rig'];r.animation_data.action=None
for prop in ['thumb_curl','index_curl','middle_curl','ring_curl','little_curl','thumb_opposition','wrist_pitch','wrist_yaw']:r[prop]=0
best=[]
for index in [.3,.45,.6,.75,.9,1]:
 for thumb in [.1,.25,.4,.55,.7,.85,1]:
  for opp in [-1,-.75,-.5,-.25,0,.25,.5,.75,1]:
   r['thumb_curl']=thumb;r['index_curl']=index;r['thumb_opposition']=opp;r.update_tag();bpy.context.view_layer.update()
   a=r.pose.bones['Thumb.Tip.R'].head;b=r.pose.bones['Index.Tip.R'].head
   best.append(((a-b).length,thumb,index,opp,list(a),list(b)))
print('BEST',json.dumps(sorted(best)[:5]))
