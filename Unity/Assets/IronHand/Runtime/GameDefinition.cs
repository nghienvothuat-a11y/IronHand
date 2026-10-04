using UnityEngine;

namespace IronHand
{
    [CreateAssetMenu(menuName = "IronHand/Game Definition")]
    public sealed class GameDefinition : ScriptableObject
    {
        public float waveSeconds = 35, cleanupSeconds = 15, breakSeconds = 6;
        public int waveCount = 5, maxEnemies = 5;
        public float firstSpawnInterval = 4, finalSpawnInterval = 2.5f;
        public int seed = 731;
        public ArmorSpec[] armors = {
            new ArmorSpec("SCOUT", "MK.01", 1, 0, 0, 0, 0, new Color(.23f,.91f,.98f)),
            new ArmorSpec("PULSE", "MK.02", 3, 200, 3, 0, 20, new Color(.64f,.43f,1)),
            new ArmorSpec("AEGIS", "MK.03", 5, 500, 1, 40, 10, new Color(1,.57f,.24f))
        };
        public EnemySpec[] enemies = {
            new EnemySpec("DRONE",30,8,10,10,.32f,2,.17f),
            new EnemySpec("SENTINEL",50,12,15,15,.23f,2,.22f),
            new EnemySpec("BRUTE",100,20,30,30,.15f,2.5f,.3f)
        };
    }
    [System.Serializable]
    public sealed class ArmorSpec
    {
        public string name, code;
        public int level, price, damage, health, mana;
        public Color color;
        public ArmorSpec(string n,string c,int l,int p,int d,int h,int m,Color tint)
        {name=n;code=c;level=l;price=p;damage=d;health=h;mana=m;color=tint;}
    }
    [System.Serializable]
    public sealed class EnemySpec
    {
        public string name;
        public int health, damage, gold, xp;
        public float speed, attackSeconds, radius;
        public EnemySpec(string n,int h,int d,int g,int x,float s,float a,float r)
        {name=n;health=h;damage=d;gold=g;xp=x;speed=s;attackSeconds=a;radius=r;}
    }
}
