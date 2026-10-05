using System.Collections.Generic;
using UnityEngine;

namespace IronHand
{
    public sealed class HandRigDriver : MonoBehaviour
    {
        public Transform Muzzle {get;private set;}
        public bool Visible {get;private set;}
        public float Coverage {get;private set;}=1.18f;
        public float JointFitErrorPixels {get;private set;}
        Transform model, wrist;
        readonly Transform[] joints=new Transform[21];
        readonly Quaternion[] rests=new Quaternion[21];
        readonly Vector3[] restPositions=new Vector3[21],restScales=new Vector3[21],worldPoints=new Vector3[21];
        readonly Vector2[] filtered=new Vector2[21];
        readonly Vector2[] velocity=new Vector2[21];
        HandCoverageShell shell;
        long sequence=-1;
        double previousCapture;
        bool initializedPose;
        Quaternion baseBasis;
        float restWidth,restPalmLength;
        int palmLengthAxis;
        Renderer[] renderers;
        readonly List<GameObject> attachments=new List<GameObject>();
        int tier=-1;
        public void Initialize(Camera camera)
        {
            var prefab=Resources.Load<GameObject>("IronHand/Hand");
            model=Instantiate(prefab,transform).transform;model.name="Tracked mechanical hand";
            foreach(var a in model.GetComponentsInChildren<Animator>())a.enabled=false;
            foreach(var a in model.GetComponentsInChildren<Animation>())a.enabled=false;
            string[] digits={"Thumb","Index","Middle","Ring","Little"};
            foreach(var t in model.GetComponentsInChildren<Transform>())
            {
                if(t.name=="Hand.R")joints[0]=wrist=t;
                if(t.name=="Palm_Muzzle")Muzzle=t;
                for(int d=0;d<5;d++)for(int j=0;j<4;j++)
                    if(t.name==digits[d]+(j==3?".Tip.R":"."+(j+1).ToString("00")+".R"))joints[1+d*4+j]=t;
            }
            for(int i=0;i<21;i++)if(joints[i]){rests[i]=joints[i].localRotation;restPositions[i]=joints[i].localPosition;restScales[i]=joints[i].localScale;}
            var up=(joints[9].position-wrist.position).normalized;
            var right=(joints[5].position-joints[17].position).normalized;
            baseBasis=Quaternion.LookRotation(model.InverseTransformDirection(Vector3.Cross(right,up).normalized),model.InverseTransformDirection(up));
            restWidth=Vector3.Distance(joints[5].position,joints[17].position);
            restPalmLength=Vector3.Distance(joints[9].position,wrist.position);
            palmLengthAxis=MainAxis(baseBasis*Vector3.up);
            if(!Muzzle){Muzzle=new GameObject("Palm muzzle").transform;Muzzle.SetParent(wrist,false);}
            renderers=model.GetComponentsInChildren<Renderer>();
            foreach(var r in renderers)r.sharedMaterial=Resources.Load<Material>("IronHand/HandMaterial");
            foreach(var skin in model.GetComponentsInChildren<SkinnedMeshRenderer>()){skin.updateWhenOffscreen=true;skin.localBounds=new Bounds(Vector3.zero,Vector3.one*2);}
            model.gameObject.SetActive(false);
            Coverage=Mathf.Clamp(PlayerPrefs.GetFloat("IronHand.Coverage",1.18f),1f,1.6f);shell=new HandCoverageShell(transform);
        }
        public void SetCoverage(float value){Coverage=Mathf.Clamp(value,1f,1.6f);PlayerPrefs.SetFloat("IronHand.Coverage",Coverage);PlayerPrefs.Save();}
        static int MainAxis(Vector3 v){v=new Vector3(Mathf.Abs(v.x),Mathf.Abs(v.y),Mathf.Abs(v.z));return v.x>v.y&&v.x>v.z?0:v.y>v.z?1:2;}
        void OnDestroy(){shell?.Dispose();}
        public void SetTier(int index,Color color)
        {
            if(index==tier)return;tier=index;
            foreach(var go in attachments)Destroy(go);attachments.Clear();
            var m=Visuals.Material(color,true);
            // Three modular variants share the same rig; attachments follow the wrist.
            for(int i=0;i<index;i++)
            {
                var p=Visuals.Part(wrist,PrimitiveType.Cube,new Vector3((i==0?-1:1)*.045f,0,-.035f),new Vector3(.022f,.07f,.018f),m,false);
                attachments.Add(p);
            }
            var block=new MaterialPropertyBlock();block.SetColor("_EmissionColor",color*1.5f);
            foreach(var r in renderers)r.SetPropertyBlock(block);
        }
        public void Tick(HandFrame frame,Camera camera,float dt,bool showcase=false)
        {
            bool valid=showcase||frame.Fresh(Time.realtimeSinceStartupAsDouble);
            Visible=valid;model.gameObject.SetActive(valid);shell.SetVisible(valid&&!showcase);if(!valid){initializedPose=false;return;}
            if(frame.sequence!=sequence || showcase)
            {
                float sampleDt=Mathf.Clamp((float)(frame.capturedAt-previousCapture),.016f,.1f);
                float alpha=initializedPose?1-Mathf.Exp(-sampleDt/.015f):1;
                for(int i=0;i<21;i++)
                {
                    if(initializedPose&&frame.confidence[i]<.25f)continue;
                    var next=Vector2.Lerp(filtered[i],frame.points[i],alpha);
                    velocity[i]=initializedPose?Vector2.Lerp(velocity[i],(next-filtered[i])/sampleDt,.55f):Vector2.zero;filtered[i]=next;
                }
                previousCapture=frame.capturedAt;sequence=frame.sequence;
            }
            // AR cameras use a custom projection matrix. Solve against that matrix
            // rather than the inspector fieldOfView or aspect-distorted UV distances.
            Vector3 AtUnitDepth(int i)=>camera.ViewportToWorldPoint(new Vector3(filtered[i].x,filtered[i].y,1));
            float projectedWidth=Vector3.Distance(AtUnitDepth(5),AtUnitDepth(17));
            float depth=showcase?Mathf.Clamp(restWidth/Mathf.Max(.001f,projectedWidth),.18f,.85f):.38f;
            // Monocular depth is an apparent-size estimate, not an AR world-space hand measurement.
            float prediction=showcase?0:Mathf.Clamp((float)(Time.realtimeSinceStartupAsDouble-frame.capturedAt),0,.075f);
            for(int i=0;i<21;i++){var p=filtered[i]+Vector2.ClampMagnitude(velocity[i]*prediction,frame.Width*.10f);worldPoints[i]=camera.ViewportToWorldPoint(new Vector3(p.x,p.y,depth));}
            Vector3 World(int i) => worldPoints[i];
            Vector3 up=(World(9)-World(0)).normalized,right=(World(5)-World(17)).normalized;
            Vector3 normal=Vector3.Cross(right,up).normalized;
            if(normal.sqrMagnitude<.01f)return;
            for(int i=0;i<21;i++)if(joints[i]){joints[i].localRotation=rests[i];joints[i].localPosition=restPositions[i];joints[i].localScale=restScales[i];}
            float scale=showcase?1:Vector3.Distance(World(5),World(17))/Mathf.Max(.001f,restWidth)*Coverage;
            var modelScale=Vector3.one*scale;
            if(!showcase)modelScale[palmLengthAxis]=Vector3.Distance(World(9),World(0))/Mathf.Max(.001f,restPalmLength)*Coverage;
            if(frame.left)modelScale.x*=-1;model.localScale=modelScale;
            // Reflected handedness is resolved by the same landmark basis rather than reversing the fire ray.
            var basis=baseBasis;if(frame.left)basis=Quaternion.LookRotation(-(baseBasis*Vector3.forward),baseBasis*Vector3.up);
            model.rotation=Quaternion.LookRotation(normal,up)*Quaternion.Inverse(basis);
            model.position+=World(0)-wrist.position;
            if(showcase)return;
            for(int d=0;d<5;d++)for(int k=0;k<3;k++)
            {
                int i=1+d*4+k;var bone=joints[i];var child=joints[i+1];
                if(!bone||!child||frame.confidence[i]<.35f||frame.confidence[i+1]<.35f)continue;
                bone.position=World(i);
                var desired=World(i+1)-World(i);if(desired.sqrMagnitude<1e-8f){child.position=World(i+1);continue;}
                var delta=Quaternion.FromToRotation(child.position-bone.position,desired);
                bone.rotation=delta*bone.rotation;
                // The source uses rigid per-panel weights. Moving a child joint
                // alone does not shorten its parent's armour plate.
                float factor=desired.magnitude/Mathf.Max(.00001f,(child.position-bone.position).magnitude);
                var boneScale=bone.localScale;int axis=MainAxis(restPositions[i+1]);boneScale[axis]*=Mathf.Clamp(factor,.12f,4);bone.localScale=boneScale;
                // Retarget joint spacing too: real finger lengths differ from the source mesh.
                child.position=World(i+1);
            }
            Muzzle.position=Vector3.Lerp(World(0),World(9),.58f)-camera.transform.forward*.035f;
            shell.Tick(worldPoints,camera,Coverage);
            JointFitErrorPixels=0;
            for(int i=0;i<21;i++)if(joints[i])JointFitErrorPixels=Mathf.Max(JointFitErrorPixels,Vector3.Distance(camera.WorldToScreenPoint(joints[i].position),camera.WorldToScreenPoint(World(i))));
            initializedPose=true;
        }
    }
}
