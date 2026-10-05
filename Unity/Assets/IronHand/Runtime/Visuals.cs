using System.Collections.Generic;
using UnityEngine;

namespace IronHand
{
    public static class Visuals
    {
        static readonly Dictionary<string,Material> materials=new Dictionary<string,Material>();
        public static Material Material(Color color,bool glow=false)
        {
            string key=color.ToString()+glow;if(materials.TryGetValue(key,out var cached)&&cached)return cached;
            var shader=Shader.Find(glow?"Universal Render Pipeline/Unlit":"Universal Render Pipeline/Lit");
            var m=new Material(shader);m.color=color;m.SetColor("_BaseColor",color);
            if(!glow){m.SetFloat("_Metallic",.65f);m.SetFloat("_Smoothness",.6f);}materials[key]=m;return m;
        }
        public static GameObject Part(Transform parent,PrimitiveType type,Vector3 pos,Vector3 size,Material material,bool collider=false)
        {
            var g=GameObject.CreatePrimitive(type);g.transform.SetParent(parent,false);g.transform.localPosition=pos;g.transform.localScale=size;g.GetComponent<Renderer>().sharedMaterial=material;
            if(!collider){if(Application.isPlaying)Object.Destroy(g.GetComponent<Collider>());else Object.DestroyImmediate(g.GetComponent<Collider>());}return g;
        }
        public static Transform EnemyMesh(Transform parent,int kind)
        {
            var root=new GameObject("Armour").transform;root.SetParent(parent,false);
            var steel=Material(kind==2?new Color(.22f,.13f,.11f):new Color(.10f,.17f,.23f));
            var core=Material(kind==0?new Color(1,.36f,.2f):kind==1?new Color(1,.7f,.24f):new Color(1,.2f,.28f),true);
            if(kind==0)
            {
                Part(root,PrimitiveType.Sphere,Vector3.zero,new Vector3(.34f,.18f,.23f),steel);
                Part(root,PrimitiveType.Cube,new Vector3(0,0,-.11f),new Vector3(.18f,.035f,.035f),core);
                for(int s=-1;s<=1;s+=2){Part(root,PrimitiveType.Cube,new Vector3(s*.25f,0,0),new Vector3(.22f,.035f,.15f),steel);Part(root,PrimitiveType.Cylinder,new Vector3(s*.3f,.02f,0),new Vector3(.2f,.014f,.2f),core);}
            }
            else
            {
                float scale=kind==2?1.35f:1;root.localScale=Vector3.one*scale;
                Part(root,PrimitiveType.Cube,new Vector3(0,.42f,0),new Vector3(.34f,.35f,.22f),steel);
                Part(root,PrimitiveType.Cube,new Vector3(0,.71f,0),new Vector3(.22f,.18f,.20f),steel);
                Part(root,PrimitiveType.Cube,new Vector3(0,.71f,-.105f),new Vector3(.17f,.035f,.016f),core);
                Part(root,PrimitiveType.Sphere,new Vector3(0,.45f,-.12f),Vector3.one*.09f,core);
                for(int s=-1;s<=1;s+=2){Part(root,PrimitiveType.Cube,new Vector3(s*.25f,.4f,0),new Vector3(.13f,.38f,.17f),steel);Part(root,PrimitiveType.Cube,new Vector3(s*.10f,.13f,0),new Vector3(.13f,.28f,.17f),steel);}
            }
            return root;
        }
    }
    public sealed class EnemyActor : MonoBehaviour
    {
        public int Kind {get;private set;}
        public int Id {get;private set;}
        public bool Alive {get;private set;}
        public float Health {get;private set;}
        public float MaxHealth {get;private set;}
        public Vector3 AimPoint => transform.position+Vector3.up*(Kind==0?0:Kind==1?.43f:.58f);
        public float Radius => spec.radius;
        public EnemySpec Spec=>spec;
        public Bounds HitBounds {get {var bounds=bodyRenderers[0].bounds;for(int i=1;i<bodyRenderers.Length;i++)bounds.Encapsulate(bodyRenderers[i].bounds);return bounds;}}
        EnemySpec spec;
        Renderer[] bodyRenderers;
        Transform visual,healthRoot,healthFill;
        float phase;
        public void Initialize(int kind,EnemySpec data)
        {
            Kind=kind;spec=data;visual=Visuals.EnemyMesh(transform,kind);bodyRenderers=visual.GetComponentsInChildren<Renderer>();
            healthRoot=new GameObject("Target health").transform;healthRoot.SetParent(transform,false);
            Visuals.Part(healthRoot,PrimitiveType.Cube,Vector3.zero,new Vector3(.42f,.035f,.008f),Visuals.Material(new Color(.025f,.04f,.06f),true));
            healthFill=Visuals.Part(healthRoot,PrimitiveType.Cube,new Vector3(0,0,-.006f),new Vector3(.4f,.022f,.008f),Visuals.Material(new Color(1,.3f,.1f),true)).transform;
            gameObject.SetActive(false);
        }
        public void Spawn(int id,int wave,Vector3 pos,Transform arena)
        {
            transform.SetParent(arena,true);transform.position=pos;Id=id;Health=MaxHealth=spec.health*(1+.12f*(wave-1));Alive=true;phase=id;gameObject.SetActive(true);UpdateHealth();
        }
        public bool Hit(float damage)
        {
            if(!Alive||damage<=0)return false;
            Health=Mathf.Max(0,Health-damage);UpdateHealth();if(Health>0)return false;Despawn();return true;
        }
        void UpdateHealth(){float ratio=Health/Mathf.Max(1,MaxHealth);healthFill.localScale=new Vector3(.4f*ratio,.022f,.008f);healthFill.localPosition=new Vector3(-.2f*(1-ratio),0,-.006f);}
        public void Despawn(){Alive=false;gameObject.SetActive(false);}
        public void Tick(float dt,Vector3 camera)
        {
            if(!Alive)return;
            Vector3 delta=camera-transform.position;delta.y=0;
            if(delta.sqrMagnitude>.001f)transform.rotation=Quaternion.LookRotation(-delta.normalized,Vector3.up);
            // Target practice: the world-space spawn position stays fixed. No attacks.
            phase+=dt*2;visual.localPosition=new Vector3(0,Kind==0?Mathf.Sin(phase)*.018f:0,0);
            healthRoot.position=AimPoint+Vector3.up*(Kind==0?.27f:Kind==1?.49f:.65f);
            healthRoot.rotation=Quaternion.LookRotation(healthRoot.position-camera,Vector3.up);
        }
    }
}
