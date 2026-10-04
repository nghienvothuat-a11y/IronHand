using System.Collections;
using System.Collections.Generic;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

namespace IronHand
{
    public sealed class ArenaController : MonoBehaviour
    {
        public bool IsDevice {get;private set;}
        public bool IsPlaced => Root;
        public bool Tracking => !IsDevice || (ARSession.state==ARSessionState.SessionTracking && (!anchor || anchor.trackingState==TrackingState.Tracking));
        public bool CanPlace {get;private set;}
        public string Status {get;private set;}="INITIALIZING";
        public Camera Camera {get;private set;}
        public Transform Root {get;private set;}
        public IHandTrackingProvider Hands {get;private set;}
        public SimulatedHand Simulation => Hands as SimulatedHand;
        ARSession session;
        ARPlaneManager planes;
        ARRaycastManager rays;
        ARAnchorManager anchors;
        ARAnchor anchor;
        ARRaycastHit hit;
        readonly List<ARRaycastHit> hits=new List<ARRaycastHit>();
        GameObject marker;
        public void Initialize()
        {
            IsDevice=Application.platform==RuntimePlatform.IPhonePlayer;
            var originGO=new GameObject("XR Origin");originGO.SetActive(false);var origin=originGO.AddComponent<XROrigin>();
            var offset=new GameObject("Camera Offset");offset.transform.SetParent(originGO.transform,false);origin.CameraFloorOffsetObject=offset;
            var cameraGO=new GameObject("AR Camera");cameraGO.transform.SetParent(offset.transform,false);
            Camera=cameraGO.AddComponent<Camera>();Camera.tag="MainCamera";Camera.nearClipPlane=.03f;Camera.farClipPlane=30;Camera.fieldOfView=58;
            Camera.backgroundColor=new Color(.018f,.03f,.048f);Camera.clearFlags=CameraClearFlags.SolidColor;origin.Camera=Camera;
            cameraGO.AddComponent<AudioListener>();originGO.SetActive(true);
            if(IsDevice)
            {
                var sessionGO=new GameObject("AR Session");sessionGO.SetActive(false);
                session=sessionGO.AddComponent<ARSession>();session.enabled=false;session.matchFrameRateRequested=false;
                sessionGO.AddComponent<ARInputManager>();sessionGO.SetActive(true);
                ARSession.stateChanged+=OnSessionState;
                cameraGO.AddComponent<ARPoseDriver>();
                var cm=cameraGO.AddComponent<ARCameraManager>();cm.requestedFacingDirection=CameraFacingDirection.World;
                cameraGO.AddComponent<ARCameraBackground>();
                planes=originGO.AddComponent<ARPlaneManager>();planes.requestedDetectionMode=PlaneDetectionMode.Horizontal;
                rays=originGO.AddComponent<ARRaycastManager>();anchors=originGO.AddComponent<ARAnchorManager>();
                var vision=cameraGO.AddComponent<VisionHandProvider>();vision.enabled=false;vision.cameraManager=cm;vision.enabled=true;Hands=vision;
                StartCoroutine(StartAR());
            }
            else {Camera.transform.position=new Vector3(0,1.25f,0);Hands=new SimulatedHand();Status="DESKTOP SIMULATION";CanPlace=true;CreateHangar();}
        }
        IEnumerator StartAR()
        {
            Status="REQUESTING CAMERA PERMISSION";
            yield return Application.RequestUserAuthorization(UserAuthorization.WebCam);
            bool authorized=Application.HasUserAuthorization(UserAuthorization.WebCam);
            Debug.Log("IRONHAND_AR camera_authorized="+authorized);
            if(!authorized){Status="CAMERA DENIED — enable in iOS Settings";yield break;}
            Status="CHECKING AR AVAILABILITY";
            yield return ARSession.CheckAvailability();
            Debug.Log("IRONHAND_AR availability="+ARSession.state);
            if(ARSession.state==ARSessionState.Unsupported){Status="AR NOT SUPPORTED";yield break;}
            session.enabled=true;Status="Move phone slowly to find a floor";
        }
        void OnSessionState(ARSessionStateChangedEventArgs args){Debug.Log("IRONHAND_AR state="+args.state+" reason="+ARSession.notTrackingReason);}
        void OnDestroy(){if(IsDevice)ARSession.stateChanged-=OnSessionState;}
        public void Tick()
        {
            Hands?.Tick();
            if(!IsDevice)return;
            if(IsPlaced){Status=Tracking?"WORLD TRACKING":"TRACKING INTERRUPTED";return;}
            CanPlace=false;
            if(!Tracking)return;
            if(rays.Raycast(new Vector2(Screen.width*.5f,Screen.height*.38f),hits,TrackableType.PlaneWithinPolygon))
            {
                hit=hits[0];CanPlace=hit.distance>=1.0f && hit.distance<=3.5f;
                Status=CanPlace?"Floor found · confirm a clear play area":"Aim at a clear floor 1–3 m away";
                if(!marker){marker=GameObject.CreatePrimitive(PrimitiveType.Cylinder);Destroy(marker.GetComponent<Collider>());marker.name="Arena placement marker";marker.GetComponent<Renderer>().material=Visuals.Material(new Color(.05f,.8f,.9f),true);}
                marker.SetActive(CanPlace);marker.transform.position=hit.pose.position;marker.transform.localScale=new Vector3(.6f,.002f,.6f);
            }
            else {Status="Move phone slowly · find a textured floor";if(marker)marker.SetActive(false);}
        }
        public bool Place()
        {
            if(!CanPlace)return false;
            if(IsPlaced)return true;
            if(IsDevice)
            {
                anchor=anchors.AttachAnchor(planes.GetPlane(hit.trackableId),hit.pose);
                if(!anchor){Status="Could not anchor area · try again";return false;}
                Root=new GameObject("World Arena").transform;Root.SetParent(anchor.transform,false);
            }
            else {Root=new GameObject("Simulation Arena").transform;Root.position=new Vector3(0,0,2.2f);}
            Root.rotation=Quaternion.Euler(0,Camera.transform.eulerAngles.y,0);
            if(marker)marker.SetActive(false);return true;
        }
        public void ResetArena()
        {
            if(Root)Destroy(Root.gameObject);if(anchor)Destroy(anchor.gameObject);Root=null;anchor=null;
            if(IsDevice)session.Reset();
        }
        public bool TrySpawnPosition(System.Random random,bool flying,out Vector3 position)
        {
            position=Vector3.zero;if(!Root)return false;
            for(int i=0;i<30;i++)
            {
                var candidate=Root.TransformPoint(new Vector3((float)(random.NextDouble()*2-1)*1.25f,flying?.85f:0,(float)(random.NextDouble()*.8)));
                if(Vector3.Distance(candidate,Camera.transform.position)<1.5f)continue;
                position=candidate;return true;
            }
            return false;
        }
        void CreateHangar()
        {
            var mat=Visuals.Material(new Color(.025f,.055f,.075f),true);
            var floor=GameObject.CreatePrimitive(PrimitiveType.Plane);floor.name="Simulation floor";floor.transform.localScale=Vector3.one*2;floor.GetComponent<Renderer>().material=mat;
            var line=Visuals.Material(new Color(.04f,.23f,.27f),true);
            for(int i=-8;i<=8;i++)
            {
                Visuals.Part(floor.transform,PrimitiveType.Cube,new Vector3(i,.006f,0),new Vector3(.006f,.005f,16),line,false);
                Visuals.Part(floor.transform,PrimitiveType.Cube,new Vector3(0,.006f,i),new Vector3(16,.005f,.006f),line,false);
            }
            RenderSettings.fog=true;RenderSettings.fogColor=Camera.backgroundColor;RenderSettings.fogMode=FogMode.ExponentialSquared;RenderSettings.fogDensity=.06f;
        }
    }
}
