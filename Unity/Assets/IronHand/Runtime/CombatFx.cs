using System;
using System.Collections.Generic;
using UnityEngine;

namespace IronHand
{
    public static class ProjectileGeometry
    {
        public static bool SegmentBounds(Vector3 start,Vector3 end,Bounds bounds,float padding,out float fraction)
        {
            fraction=0;bounds.Expand(padding*2);if(bounds.Contains(start))return true;
            var delta=end-start;float distance=delta.magnitude;if(distance<.00001f)return false;
            if(!bounds.IntersectRay(new Ray(start,delta/distance),out float hit)||hit>distance)return false;
            fraction=hit/distance;return true;
        }
        // Swept collision prevents a fast rocket tunnelling through a small target.
        public static bool SegmentSphere(Vector3 start,Vector3 end,Vector3 center,float radius,out float fraction)
        {
            fraction=0;var offset=start-center;float c=offset.sqrMagnitude-radius*radius;if(c<=0)return true;
            var delta=end-start;float a=delta.sqrMagnitude;if(a<1e-8f)return false;
            float b=Vector3.Dot(offset,delta),disc=b*b-a*c;if(disc<0)return false;
            float t=(-b-Mathf.Sqrt(disc))/a;if(t<0||t>1)return false;fraction=t;return true;
        }
    }
    public sealed class CombatFx : MonoBehaviour
    {
        sealed class Rocket
        {
            public Transform root,flame;
            public Vector3 position,velocity;
            public float life;
            public int damage;
        }
        sealed class Burst {public Transform flash,ring;public float life,duration,size;}
        sealed class Fragment
        {
            public Transform root;public Vector3 velocity,spin;public float life,floor,size;
        }
        readonly Rocket[] rockets=new Rocket[20];readonly Burst[] bursts=new Burst[16];readonly Fragment[] fragments=new Fragment[80];
        int burstCursor,fragmentCursor;
        AudioSource audioSource;AudioClip shot,impact,death;
        public bool Sound=true;
        public int RocketsLaunched {get;private set;}
        public int Impacts {get;private set;}
        public int Destructions {get;private set;}
        public void Initialize()
        {
            var steel=Visuals.Material(new Color(.25f,.32f,.39f));var glow=Visuals.Material(new Color(1,.46f,.09f),true);
            for(int i=0;i<rockets.Length;i++)
            {
                var root=new GameObject("Palm rocket").transform;root.SetParent(transform);
                Visuals.Part(root,PrimitiveType.Capsule,Vector3.zero,new Vector3(.032f,.068f,.032f),steel).transform.localRotation=Quaternion.Euler(90,0,0);
                Visuals.Part(root,PrimitiveType.Sphere,new Vector3(0,0,.07f),new Vector3(.033f,.033f,.045f),glow);
                for(int wing=0;wing<2;wing++)Visuals.Part(root,PrimitiveType.Cube,new Vector3(0,0,-.038f),wing==0?new Vector3(.065f,.009f,.035f):new Vector3(.009f,.065f,.035f),steel);
                var flame=Visuals.Part(root,PrimitiveType.Sphere,new Vector3(0,0,-.12f),new Vector3(.03f,.03f,.13f),glow).transform;
                rockets[i]=new Rocket{root=root,flame=flame};root.gameObject.SetActive(false);
            }
            for(int i=0;i<bursts.Length;i++)
            {
                var flash=Visuals.Part(transform,PrimitiveType.Sphere,Vector3.zero,Vector3.one,glow).transform;
                var ring=Visuals.Part(transform,PrimitiveType.Sphere,Vector3.zero,Vector3.one,Visuals.Material(new Color(1,.83f,.3f),true)).transform;
                bursts[i]=new Burst{flash=flash,ring=ring};flash.gameObject.SetActive(false);ring.gameObject.SetActive(false);
            }
            for(int i=0;i<fragments.Length;i++)
            {
                var root=Visuals.Part(transform,PrimitiveType.Cube,Vector3.zero,Vector3.one,i%4==0?glow:steel).transform;
                fragments[i]=new Fragment{root=root};root.gameObject.SetActive(false);
            }
            audioSource=gameObject.AddComponent<AudioSource>();audioSource.spatialBlend=0;audioSource.volume=.16f;
            shot=Tone("Rocket launch",170,.12f,false);impact=Tone("Rocket impact",90,.2f,true);death=Tone("Armour destruction",55,.38f,true);
        }
        static AudioClip Tone(string name,float hz,float seconds,bool noise)
        {
            int count=(int)(22050*seconds);var data=new float[count];var random=new System.Random(73);
            for(int i=0;i<count;i++){float t=(float)i/count;float tone=Mathf.Sin(2*Mathf.PI*hz*i/22050*(1-t*.4f));data[i]=(noise?tone*.3f+((float)random.NextDouble()*2-1)*.7f:tone)*Mathf.Pow(1-t,3);}
            var clip=AudioClip.Create(name,count,1,22050,false);clip.SetData(data,0);return clip;
        }
        public bool Launch(Vector3 start,Vector3 destination,int damage)
        {
            foreach(var r in rockets)if(r.life<=0)
            {
                var direction=(destination-start).normalized;if(direction.sqrMagnitude<.5f)return false;
                r.position=start;r.velocity=direction*5f;r.life=2;r.damage=damage;r.root.position=start;r.root.rotation=Quaternion.LookRotation(direction);r.root.gameObject.SetActive(true);
                RocketsLaunched++;if(Sound)audioSource.PlayOneShot(shot);return true;
            }
            return false;
        }
        public void TickProjectiles(float dt,IReadOnlyList<EnemyActor> enemies,Action<EnemyActor,int,Vector3> impactCallback)
        {
            foreach(var r in rockets)if(r.life>0)
            {
                var end=r.position+r.velocity*dt;EnemyActor target=null;float nearest=2;
                foreach(var e in enemies)if(e.Alive&&ProjectileGeometry.SegmentBounds(r.position,end,e.HitBounds,.025f,out float t)&&t<nearest){target=e;nearest=t;}
                if(target){var point=Vector3.Lerp(r.position,end,nearest);r.life=0;r.root.gameObject.SetActive(false);Impacts++;impactCallback(target,r.damage,point);continue;}
                r.position=end;r.root.position=end;r.life-=dt;r.flame.localScale=new Vector3(.026f,.026f,.12f+Mathf.Sin(r.life*95)*.025f);
                if(r.life<=0)r.root.gameObject.SetActive(false);
            }
        }
        public void Explosion(Vector3 point,bool destroyed,float floor)
        {
            var b=bursts[burstCursor++%bursts.Length];b.duration=destroyed?.38f:.18f;b.life=b.duration;b.size=destroyed?.42f:.15f;
            b.flash.position=b.ring.position=point;b.flash.gameObject.SetActive(true);b.ring.gameObject.SetActive(true);
            b.flash.localScale=b.ring.localScale=Vector3.one*.015f;
            int count=destroyed?12:4;if(destroyed)Destructions++;
            for(int i=0;i<count;i++)
            {
                var f=fragments[fragmentCursor++%fragments.Length];f.life=destroyed?2.1f:.45f;f.floor=floor;
                f.size=destroyed?UnityEngine.Random.Range(.025f,.07f):.012f;
                f.root.position=point+UnityEngine.Random.insideUnitSphere*.055f;f.root.rotation=UnityEngine.Random.rotation;
                f.velocity=UnityEngine.Random.onUnitSphere*UnityEngine.Random.Range(.7f,1.7f)+Vector3.up*1.4f;
                f.spin=UnityEngine.Random.insideUnitSphere*560;f.root.localScale=new Vector3(f.size,f.size*.45f,f.size*1.6f);f.root.gameObject.SetActive(true);
            }
            if(Sound)audioSource.PlayOneShot(destroyed?death:impact);
        }
        public void Tick(float dt)
        {
            foreach(var b in bursts)if(b.life>0)
            {
                b.life-=dt;float t=1-Mathf.Max(0,b.life)/b.duration;
                b.flash.localScale=Vector3.one*b.size*Mathf.Sin(t*Mathf.PI);
                b.ring.localScale=Vector3.one*b.size*.5f*(1-t);
                if(b.life<=0){b.flash.gameObject.SetActive(false);b.ring.gameObject.SetActive(false);}
            }
            foreach(var f in fragments)if(f.life>0)
            {
                f.life-=dt;f.velocity+=Vector3.down*9.81f*dt;var p=f.root.position+f.velocity*dt;
                if(p.y<f.floor+f.size*.5f){p.y=f.floor+f.size*.5f;if(f.velocity.y<0)f.velocity=new Vector3(f.velocity.x*.65f,-f.velocity.y*.28f,f.velocity.z*.65f);f.spin*=.85f;}
                f.root.position=p;f.root.Rotate(f.spin*dt,Space.World);
                float fade=Mathf.Clamp01(f.life/.35f);f.root.localScale=new Vector3(f.size,f.size*.45f,f.size*1.6f)*fade;
                if(f.life<=0)f.root.gameObject.SetActive(false);
            }
        }
        public void ClearProjectiles(){foreach(var r in rockets){r.life=0;r.root.gameObject.SetActive(false);}}
        public void Clear()
        {
            ClearProjectiles();
            foreach(var b in bursts){b.life=0;b.flash.gameObject.SetActive(false);b.ring.gameObject.SetActive(false);}
            foreach(var f in fragments){f.life=0;f.root.gameObject.SetActive(false);}
        }
    }
}
