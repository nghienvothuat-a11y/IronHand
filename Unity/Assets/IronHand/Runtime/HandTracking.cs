using System;
using System.Runtime.InteropServices;
using UnityEngine;
using Unity.Collections.LowLevel.Unsafe;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace IronHand
{
    public sealed class HandFrame
    {
        public readonly Vector2[] points=new Vector2[21];
        public readonly float[] confidence=new float[21];
        public double capturedAt, inferenceMs;
        public long sequence;
        public bool valid, left;
        public float openness;
        public float Width => Vector2.Distance(points[5],points[17]);
        public bool Fresh(double now) => valid && now-capturedAt<=.2 && now>=capturedAt;
    }
    public interface IHandTrackingProvider {HandFrame Frame {get;} string Status {get;} void Tick();}
    public static class HandGeometry
    {
        // Invert the affine transform used by ARKitBackground.shader: row-vector UV * display matrix.
        public static Vector2 SensorToViewport(Vector2 sensor,Matrix4x4 display)
        {
            float a=display.m00,b=display.m10,c=display.m01,d=display.m11;
            float x=sensor.x-display.m20-display.m30,y=sensor.y-display.m21-display.m31;
            float det=a*d-b*c;
            return Mathf.Abs(det)<1e-5f ? new Vector2(-1,-1) : new Vector2((d*x-b*y)/det,(-c*x+a*y)/det);
        }
        public static float Openness(HandFrame f)
        {
            float score=0;int[] starts={5,9,13,17};
            foreach(int j in starts)
            {
                if(f.confidence[j]<.35f||f.confidence[j+1]<.35f||f.confidence[j+2]<.35f||f.confidence[j+3]<.35f)return 0;
                float straight=Vector2.Distance(f.points[j],f.points[j+3]);
                float length=Vector2.Distance(f.points[j],f.points[j+1])+Vector2.Distance(f.points[j+1],f.points[j+2])+Vector2.Distance(f.points[j+2],f.points[j+3]);
                float reach=Vector2.Distance(f.points[0],f.points[j+3])/Mathf.Max(.001f,Vector2.Distance(f.points[0],f.points[j+1]));
                score+=Mathf.Clamp01((straight/Mathf.Max(.001f,length)-.55f)/.4f)*Mathf.Clamp01((reach-.95f)/.4f);
            }
            return score/4;
        }
    }
    public sealed class SimulatedHand : IHandTrackingProvider
    {
        public HandFrame Frame {get;}=new HandFrame();
        public string Status => "SIMULATED HAND";
        public bool firing, lost, left;
        public void Tick()
        {
            var f=Frame;f.valid=!lost;f.left=left;f.capturedAt=Time.realtimeSinceStartupAsDouble;f.sequence++;
            f.points[0]=new Vector2(.78f,.19f);
            for(int finger=0;finger<5;finger++)for(int k=0;k<4;k++)
            {
                int i=1+finger*4+k;
                float x=finger==0?-.04f-k*.018f:(finger-2)*.033f;
                float y=finger==0?.025f+k*.025f:.105f+k*(firing?.038f:.009f);
                f.points[i]=f.points[0]+new Vector2(left?-x:x,y);
                f.confidence[i]=lost?0:1;
            }
            f.confidence[0]=lost?0:1;f.openness=firing?1:0;
        }
    }
    public sealed class VisionHandProvider : MonoBehaviour,IHandTrackingProvider
    {
        public HandFrame Frame {get;}=new HandFrame();
        public string Status {get;private set;}="WAITING FOR CAMERA";
        public ARCameraManager cameraManager;
        readonly float[] nativePoints=new float[63];
        Matrix4x4 pendingDisplay;
        double pendingCapture, nextCapture;
        XRCpuImage.AsyncConversion conversion;
        bool converting, pending;
        long serial;
#if UNITY_IOS && !UNITY_EDITOR
        [DllImport("__Internal")] static extern int IH_Submit(IntPtr rgba,int width,int height,double capture);
        [DllImport("__Internal")] static extern int IH_Poll([Out]float[] xyz,out double capture,out double elapsed,out int handedness);
        [DllImport("__Internal")] static extern void IH_Reset();
#endif
        void OnEnable(){Status="WAITING FOR HAND";if(cameraManager)cameraManager.frameReceived+=OnFrame;}
        void OnDisable()
        {
            if(cameraManager)cameraManager.frameReceived-=OnFrame;
            if(converting)conversion.Dispose();converting=false;pending=false;Frame.valid=false;Status="HAND SCAN STARTS AFTER AREA CONFIRMATION";
#if UNITY_IOS && !UNITY_EDITOR
            IH_Reset();
#endif
        }
        void OnFrame(ARCameraFrameEventArgs args)
        {
#if UNITY_IOS && !UNITY_EDITOR
            double now=Time.realtimeSinceStartupAsDouble;
            if(pending||converting||now<nextCapture||!args.displayMatrix.HasValue)return;
            if(!cameraManager.TryAcquireLatestCpuImage(out var image))return;
            using(image)
            {
                int w=Mathf.Min(640,image.width),h=Mathf.RoundToInt(w*(float)image.height/image.width);
                var p=new XRCpuImage.ConversionParams {inputRect=new RectInt(0,0,image.width,image.height),outputDimensions=new Vector2Int(w,h),outputFormat=TextureFormat.RGBA32,transformation=XRCpuImage.Transformation.None};
                conversion=image.ConvertAsync(p);converting=true;pendingDisplay=args.displayMatrix.Value;pendingCapture=now;nextCapture=now+1.0/20;
            }
#endif
        }
        public unsafe void Tick()
        {
#if UNITY_IOS && !UNITY_EDITOR
            if(converting && conversion.status.IsDone())
            {
                if(conversion.status==XRCpuImage.AsyncConversionStatus.Ready)
                {
                    var data=conversion.GetData<byte>();var size=conversion.conversionParams.outputDimensions;
                    pending=IH_Submit((IntPtr)NativeArrayUnsafeUtility.GetUnsafeReadOnlyPtr(data),size.x,size.y,pendingCapture)==1;
                    Status=pending?"VISION TRACKING":"VISION BUSY";
                }
                conversion.Dispose();converting=false;
            }
            if(!pending)return;
            int result=IH_Poll(nativePoints,out double capture,out double elapsed,out int handedness);
            if(result==0)return;pending=false;
            var f=Frame;f.valid=result==1;f.capturedAt=capture;f.inferenceMs=elapsed;f.sequence=++serial;f.left=handedness==1;
            for(int i=0;i<21;i++)
            {
                // Vision points have bottom-left origin; the raw camera buffer has top-left origin.
                f.points[i]=HandGeometry.SensorToViewport(new Vector2(nativePoints[i*3],1-nativePoints[i*3+1]),pendingDisplay);
                f.confidence[i]=nativePoints[i*3+2];
            }
            f.valid &= f.confidence[0]>.4f && f.confidence[5]>.4f && f.confidence[9]>.4f && f.confidence[17]>.4f && f.Width>.03f;
            f.openness=f.valid?HandGeometry.Openness(f):0;
            Status=result<0?"VISION ERROR":f.valid?"HAND DETECTED":"SHOW FULL HAND";
#endif
        }
    }
}
