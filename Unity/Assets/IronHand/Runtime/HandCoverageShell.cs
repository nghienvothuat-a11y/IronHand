using System.Collections.Generic;
using UnityEngine;

namespace IronHand
{
    // Opaque armour beneath the detailed Tripo plates. This is a geometric
    // coverage envelope around landmarks, not a segmentation mask of real skin.
    public sealed class HandCoverageShell
    {
        readonly Transform root,palm,cuff;
        readonly Transform[] fingers=new Transform[15];
        readonly Mesh palmMesh;
        readonly List<Vector2> samples=new List<Vector2>(80),hull=new List<Vector2>(80);
        readonly List<Vector3> vertices=new List<Vector3>(160);
        readonly List<int> triangles=new List<int>(480);
        readonly Vector3[] liningPoints=new Vector3[21];
        public HandCoverageShell(Transform parent)
        {
            root=new GameObject("Opaque articulated armour lining").transform;root.SetParent(parent,false);
            var metal=Visuals.Material(new Color(.19f,.24f,.29f));
            palm=new GameObject("Palm coverage").transform;palm.SetParent(root,false);
            palmMesh=new Mesh{name="Dynamic palm envelope"};palmMesh.MarkDynamic();palm.gameObject.AddComponent<MeshFilter>().sharedMesh=palmMesh;palm.gameObject.AddComponent<MeshRenderer>().sharedMaterial=metal;
            for(int i=0;i<15;i++)fingers[i]=Visuals.Part(root,PrimitiveType.Capsule,Vector3.zero,Vector3.one,metal).transform;
            cuff=Visuals.Part(root,PrimitiveType.Capsule,Vector3.zero,Vector3.one,metal).transform;
            root.gameObject.SetActive(false);
        }
        public void SetVisible(bool value)=>root.gameObject.SetActive(value);
        static float Cross(Vector2 a,Vector2 b,Vector2 c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
        void Circle(Vector2 p,float radius){for(int i=0;i<8;i++){float a=i*Mathf.PI/4;samples.Add(p+new Vector2(Mathf.Cos(a),Mathf.Sin(a))*radius);}}
        public static Vector3 BehindInSamePixel(Camera camera,Vector3 point,float extraDepth)
        {
            var relative=point-camera.transform.position;float depth=Vector3.Dot(relative,camera.transform.forward);
            return camera.transform.position+relative*((depth+extraDepth)/Mathf.Max(.01f,depth));
        }
        public void Tick(Vector3[] points,Camera camera,float coverage)
        {
            SetVisible(true);float width=Vector3.Distance(points[5],points[17]);
            // Moving only along camera.forward shrinks the projected lining.
            // Move along each camera ray so it stays directly behind the same pixel.
            for(int i=0;i<21;i++)liningPoints[i]=BehindInSamePixel(camera,points[i],width*.22f);
            points=liningPoints;width=Vector3.Distance(points[5],points[17]);Vector3 behind=Vector3.zero;
            var origin=points[0]+behind;var right=camera.transform.right;var up=camera.transform.up;
            Vector2 Local(int i){var d=points[i]-points[0];return new Vector2(Vector3.Dot(d,right),Vector3.Dot(d,up));}
            samples.Clear();Circle(Vector2.zero,width*.43f*coverage);
            Circle(Local(1),width*.17f*coverage);
            for(int i=5;i<=17;i+=4)Circle(Local(i),width*.16f*coverage);
            samples.Sort((a,b)=>a.x==b.x?a.y.CompareTo(b.y):a.x.CompareTo(b.x));hull.Clear();
            foreach(var p in samples){while(hull.Count>=2&&Cross(hull[hull.Count-2],hull[hull.Count-1],p)<=0)hull.RemoveAt(hull.Count-1);hull.Add(p);}
            int lower=hull.Count;
            for(int i=samples.Count-2;i>=0;i--){var p=samples[i];while(hull.Count>lower&&Cross(hull[hull.Count-2],hull[hull.Count-1],p)<=0)hull.RemoveAt(hull.Count-1);hull.Add(p);}
            if(hull.Count>1)hull.RemoveAt(hull.Count-1);
            vertices.Clear();triangles.Clear();int count=hull.Count;float thickness=width*.07f;
            foreach(var p in hull)vertices.Add(new Vector3(p.x,p.y,-thickness));
            foreach(var p in hull)vertices.Add(new Vector3(p.x,p.y,thickness));
            for(int i=1;i<count-1;i++){triangles.Add(0);triangles.Add(i+1);triangles.Add(i);triangles.Add(count);triangles.Add(count+i);triangles.Add(count+i+1);}
            for(int i=0;i<count;i++){int j=(i+1)%count;triangles.Add(i);triangles.Add(j);triangles.Add(count+i);triangles.Add(j);triangles.Add(count+j);triangles.Add(count+i);}
            // A concave thumb web joins the palm to the thumb's MCP joint without
            // filling the whole open space between the thumb and index finger.
            Vector2 web=Vector2.Lerp((Local(5)+Local(2))*.5f,Vector2.zero,.22f);
            AddWebTriangle(Local(5),web,Local(1),thickness);
            AddWebTriangle(web,Local(2),Local(1),thickness);
            palmMesh.Clear();palmMesh.SetVertices(vertices);palmMesh.SetTriangles(triangles,0);palmMesh.RecalculateNormals();palmMesh.RecalculateBounds();
            palm.position=origin;palm.rotation=camera.transform.rotation;
            for(int d=0;d<5;d++)for(int k=0;k<3;k++)
            {
                int i=1+d*4+k;float radius=width*(d==0?.16f:d==4?.12f:.135f)*coverage;
                Segment(fingers[d*3+k],points[i]+behind,points[i+1]+behind,radius,camera);
            }
            var palmUp=(points[9]-points[0]).normalized;
            Segment(cuff,points[0]+behind,points[0]-palmUp*width*1.25f+behind,width*.42f*coverage,camera);
        }
        void AddWebTriangle(Vector2 a,Vector2 b,Vector2 c,float thickness)
        {
            if(Cross(a,b,c)>0){var swap=b;b=c;c=swap;}
            int i=vertices.Count;
            vertices.Add(new Vector3(a.x,a.y,-thickness));vertices.Add(new Vector3(b.x,b.y,-thickness));vertices.Add(new Vector3(c.x,c.y,-thickness));
            vertices.Add(new Vector3(a.x,a.y,thickness));vertices.Add(new Vector3(b.x,b.y,thickness));vertices.Add(new Vector3(c.x,c.y,thickness));
            triangles.Add(i);triangles.Add(i+1);triangles.Add(i+2);triangles.Add(i+3);triangles.Add(i+5);triangles.Add(i+4);
        }
        static void Segment(Transform segment,Vector3 a,Vector3 b,float radius,Camera camera)
        {
            var direction=b-a;segment.position=(a+b)*.5f;
            segment.rotation=Quaternion.LookRotation(camera.transform.forward,direction.sqrMagnitude>.000001f?direction:camera.transform.up);
            segment.localScale=new Vector3(radius*2,(direction.magnitude+radius*2)*.5f,radius*.45f);
        }
        public void Dispose(){if(Application.isPlaying){Object.Destroy(palmMesh);if(root)Object.Destroy(root.gameObject);}else {Object.DestroyImmediate(palmMesh);if(root)Object.DestroyImmediate(root.gameObject);}}
    }
}
