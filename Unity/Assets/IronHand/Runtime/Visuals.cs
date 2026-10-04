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
            if(!collider)Object.Destroy(g.GetComponent<Collider>());return g;
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
        public Vector3 AimPoint => transform.position+Vector3.up*(Kind==0?0:Kind==1?.43f:.58f);
        public float Radius => spec.radius;
        public float AttackProgress => windup/.4f;
        public EnemySpec Spec=>spec;
        EnemySpec spec;
        Transform visual;
        float attackClock,windup,phase;
        public void Initialize(int kind,EnemySpec data){Kind=kind;spec=data;visual=Visuals.EnemyMesh(transform,kind);gameObject.SetActive(false);}
        public void Spawn(int id,int wave,Vector3 pos,Transform arena)
        {
            transform.SetParent(arena,true);transform.position=pos;Id=id;Health=spec.health*(1+.12f*(wave-1));Alive=true;attackClock=0;windup=0;phase=id;gameObject.SetActive(true);
        }
        public bool Hit(float damage){if(!Alive)return false;Health-=damage;if(Health>0)return false;Despawn();return true;}
        public void Despawn(){Alive=false;gameObject.SetActive(false);}
        public void Tick(float dt,Vector3 camera,System.Action<int> damage)
        {
            if(!Alive)return;
            Vector3 delta=camera-transform.position;delta.y=0;
            if(delta.sqrMagnitude>.001f)transform.rotation=Quaternion.LookRotation(-delta.normalized,Vector3.up);
            if(delta.magnitude>.75f){transform.position+=delta.normalized*(spec.speed*dt);windup=0;}
            else
            {
                attackClock-=dt;
                if(attackClock<=0){windup+=dt;if(windup>=.4f){damage(spec.damage);windup=0;attackClock=spec.attackSeconds;}}
            }
            phase+=dt*3;visual.localPosition=new Vector3(0,Kind==0?Mathf.Sin(phase)*.035f:Mathf.Sin(phase)*.012f,windup*.14f);
        }
    }
    public sealed class CombatFx : MonoBehaviour
    {
        readonly LineRenderer[] beams=new LineRenderer[12];readonly float[] life=new float[12];int cursor;
        AudioSource audioSource;AudioClip shot,hit;
        public bool Sound=true;
        public void Initialize()
        {
            for(int i=0;i<beams.Length;i++)
            {
                var g=new GameObject("Pulse beam");g.transform.SetParent(transform);var l=g.AddComponent<LineRenderer>();l.positionCount=2;l.startWidth=.012f;l.endWidth=.004f;l.material=Visuals.Material(new Color(.2f,.93f,1),true);l.enabled=false;beams[i]=l;
            }
            audioSource=gameObject.AddComponent<AudioSource>();audioSource.spatialBlend=0;audioSource.volume=.13f;shot=Tone("Pulse",480,.075f);hit=Tone("Impact",120,.11f);
        }
        static AudioClip Tone(string name,float hz,float seconds)
        {
            int count=(int)(22050*seconds);var data=new float[count];for(int i=0;i<count;i++){float t=(float)i/count;data[i]=Mathf.Sin(2*Mathf.PI*hz*i/22050*(1-t*.3f))*Mathf.Pow(1-t,3);}
            var clip=AudioClip.Create(name,count,1,22050,false);clip.SetData(data,0);return clip;
        }
        public void Shot(Vector3 start,Vector3 end,Color color,bool landed)
        {
            int i=cursor++%beams.Length;beams[i].SetPosition(0,start);beams[i].SetPosition(1,end);beams[i].startColor=color;beams[i].endColor=Color.white;beams[i].enabled=true;life[i]=.08f;
            if(Sound)audioSource.PlayOneShot(landed?hit:shot);
        }
        public void Tick(float dt){for(int i=0;i<life.Length;i++)if(life[i]>0){life[i]-=dt;if(life[i]<=0)beams[i].enabled=false;}}
    }
}
