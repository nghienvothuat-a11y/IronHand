using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace IronHand
{
    [Serializable]
    public sealed class SaveData
    {
        public int schemaVersion = 1, gold, xp, equipped, damageRank, healthRank, manaRank;
        public bool[] owned = {true,false,false};
        public int Level => xp >= 700 ? 5 : xp >= 450 ? 4 : xp >= 250 ? 3 : xp >= 100 ? 2 : 1;
        public bool IsValid() => schemaVersion == 1 && gold >= 0 && gold <= 100000000 && xp >= 0 && xp <= 100000000
            && owned != null && owned.Length == 3 && owned[0] && equipped >= 0 && equipped < 3 && owned[equipped]
            && damageRank >= 0 && damageRank <= 5 && healthRank >= 0 && healthRank <= 5 && manaRank >= 0 && manaRank <= 5;
        public SaveData Copy() => JsonUtility.FromJson<SaveData>(JsonUtility.ToJson(this));
    }
    public sealed class SaveStore
    {
        readonly string path;
        public string LastError {get; private set;}
        public bool Recovered {get; private set;}
        public SaveStore(string directory) {Directory.CreateDirectory(directory);path=Path.Combine(directory,"progress.json");}
        SaveData Read(string p)
        {
            try {if (!File.Exists(p)) return null; var d=JsonUtility.FromJson<SaveData>(File.ReadAllText(p));return d != null && d.IsValid() ? d : null;}
            catch {return null;}
        }
        public SaveData Load()
        {
            var d=Read(path); if(d!=null)return d;
            d=Read(path+".bak"); Recovered=d!=null;
            if(d!=null)return d;
            if(File.Exists(path))LastError="Save invalid or from a newer version. Originals preserved.";
            return new SaveData();
        }
        public bool Write(SaveData data)
        {
            if(!data.IsValid()) {LastError="Invalid save rejected";return false;}
            try
            {
                // An invalid main file must never overwrite the last valid backup.
                if(File.Exists(path) && Read(path)==null)
                    File.Copy(path,path+".invalid-"+DateTime.UtcNow.Ticks,false);
                string temp=path+".tmp";
                using(var fs=new FileStream(temp,FileMode.Create,FileAccess.Write,FileShare.None))
                using(var sw=new StreamWriter(fs)) {sw.Write(JsonUtility.ToJson(data,true));sw.Flush();fs.Flush(true);}
                if(Read(temp)==null)throw new IOException("Save verification failed");
                if(File.Exists(path))File.Replace(temp,path,Read(path)!=null ? path+".bak" : null);
                else File.Move(temp,path);
                LastError=null;return true;
            }
            catch(Exception e) {LastError=e.Message;return false;}
        }
    }
    public sealed class Progression
    {
        public SaveData Data {get; private set;}
        readonly SaveStore store;
        readonly HashSet<int> rewards = new HashSet<int>();
        public string SaveError => store.LastError;
        public Progression(SaveStore s) {store=s;Data=s.Load();}
        public void BeginRun() => rewards.Clear();
        public void Flush() => store.Write(Data);
        public bool Reward(int uniqueId,int gold,int xp)
        {
            if(gold<0 || xp<0 || !rewards.Add(uniqueId))return false;
            Data.gold=Math.Min(100000000,Data.gold+gold);Data.xp=Math.Min(100000000,Data.xp+xp);
            Flush();return true;
        }
        public static int UpgradeCost(int rank) => Mathf.RoundToInt(50*Mathf.Pow(1.5f,rank));
        public int Rank(int kind) => kind==0?Data.damageRank:kind==1?Data.healthRank:Data.manaRank;
        public bool Upgrade(int kind)
        {
            if(kind<0||kind>2)return false;
            int rank=Rank(kind),price=UpgradeCost(rank);
            if(rank>=5||Data.gold<price)return false;
            var next=Data.Copy();next.gold-=price;
            if(kind==0)next.damageRank++;else if(kind==1)next.healthRank++;else next.manaRank++;
            if(!store.Write(next))return false;Data=next;return true;
        }
        public bool Equip(int index,ArmorSpec spec)
        {
            if(index<0||index>=3||Data.Level<spec.level||(!Data.owned[index]&&Data.gold<spec.price))return false;
            var next=Data.Copy();if(!next.owned[index]){next.gold-=spec.price;next.owned[index]=true;}next.equipped=index;
            if(!store.Write(next))return false;Data=next;return true;
        }
    }
    public sealed class GestureGate
    {
        double openedAt=-1;
        public bool IsOpen {get; private set;}
        public bool Tick(float openness,bool valid,double capture,double now)
        {
            if(!valid||now-capture>.2||now<capture||openness<.60f){Reset();return false;}
            if(!IsOpen && openness<.82f){Reset();return false;}
            if(openness>=.82f && openedAt<0)openedAt=now;
            IsOpen=openedAt>=0 && now-openedAt>=.12;
            return IsOpen;
        }
        public void Reset() {openedAt=-1;IsOpen=false;}
    }
}
