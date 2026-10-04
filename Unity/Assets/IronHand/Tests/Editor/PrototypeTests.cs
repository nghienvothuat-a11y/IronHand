using System;
using System.IO;
using IronHand;
using NUnit.Framework;
using UnityEngine;

public class PrototypeTests
{
    string dir;SaveStore store;
    [SetUp] public void Setup(){dir=Path.Combine(Path.GetTempPath(),"IronHandTests-"+Guid.NewGuid());store=new SaveStore(dir);}
    [TearDown] public void Cleanup(){Directory.Delete(dir,true);}
    [Test] public void RewardsAreExactlyOncePerRun(){var p=new Progression(store);Assert.True(p.Reward(1,10,15));Assert.False(p.Reward(1,10,15));Assert.AreEqual(10,new Progression(store).Data.gold);Assert.AreEqual(15,p.Data.xp);p.BeginRun();Assert.True(p.Reward(1,10,15));}
    [Test] public void NegativeRewardsRejected(){var p=new Progression(store);Assert.False(p.Reward(1,-10,10));Assert.AreEqual(0,p.Data.gold);}
    [Test] public void PurchaseChecksLevelAndFunds(){var p=new Progression(store);var a=new ArmorSpec("PULSE","02",3,200,0,0,0,Color.white);p.Reward(1,500,100);Assert.False(p.Equip(1,a));p.Reward(2,0,150);Assert.True(p.Equip(1,a));Assert.AreEqual(300,p.Data.gold);Assert.True(p.Equip(1,a));Assert.AreEqual(300,p.Data.gold);}
    [Test] public void UpgradeCapAndPriceSurviveReload(){var p=new Progression(store);p.Reward(1,10000,0);for(int i=0;i<5;i++)Assert.True(p.Upgrade(0));int gold=p.Data.gold;Assert.False(p.Upgrade(0));var q=new Progression(store);Assert.AreEqual(5,q.Data.damageRank);Assert.AreEqual(gold,q.Data.gold);Assert.AreEqual(75,Progression.UpgradeCost(1));}
    [Test] public void CannotOverspend(){var p=new Progression(store);Assert.False(p.Upgrade(2));Assert.AreEqual(0,p.Data.gold);Assert.False(p.Upgrade(-1));}
    [Test] public void CorruptMainRecoversBackupAndPreservesIt(){store.Write(new SaveData{gold=10});store.Write(new SaveData{gold=20});File.WriteAllText(Path.Combine(dir,"progress.json"),"broken");Assert.AreEqual(10,store.Load().gold);Assert.True(store.Recovered);Assert.True(store.Write(new SaveData{gold=30}));Assert.AreEqual(10,JsonUtility.FromJson<SaveData>(File.ReadAllText(Path.Combine(dir,"progress.json.bak"))).gold);}
    [Test] public void InvalidVersionAndRanksRejected(){Assert.False(store.Write(new SaveData{schemaVersion=100}));Assert.False(store.Write(new SaveData{damageRank=6}));Assert.False(store.Write(new SaveData{owned=new[]{true,false},equipped=0}));}
    [TestCase(0,1)][TestCase(100,2)][TestCase(250,3)][TestCase(450,4)][TestCase(700,5)] public void XPThreshold(int xp,int expected){Assert.AreEqual(expected,new SaveData{xp=xp}.Level);}
    [Test] public void GestureDebouncesAndStopsOnOldPose(){var g=new GestureGate();Assert.False(g.Tick(1,true,0,0));Assert.False(g.Tick(1,true,.1,.1));Assert.True(g.Tick(1,true,.13,.13));Assert.True(g.Tick(.7f,true,.14,.14));Assert.False(g.Tick(1,true,.14,.35));}
    [Test] public void ClosedAndInvalidStopImmediately(){var g=new GestureGate();g.Tick(1,true,1,1);Assert.True(g.Tick(1,true,1.13,1.13));Assert.False(g.Tick(.2f,true,1.14,1.14));g.Tick(1,true,2,2);Assert.True(g.Tick(1,true,2.13,2.13));Assert.False(g.Tick(1,false,2.14,2.14));}
    [Test] public void InverseDisplayHandlesRotationCropAndTranslation(){var m=Matrix4x4.identity;m.m00=0;m.m10=.8f;m.m01=-1;m.m11=0;m.m20=.1f;m.m21=1;var p=new Vector2(.3f,.7f);var tex=new Vector2(p.x*m.m00+p.y*m.m10+m.m20,p.x*m.m01+p.y*m.m11+m.m21);Assert.Less(Vector2.Distance(p,HandGeometry.SensorToViewport(tex,m)),.0001f);}
    [Test] public void MissingFingertipCannotFire(){var s=new SimulatedHand{firing=true};s.Tick();Assert.Greater(HandGeometry.Openness(s.Frame),.8f);s.Frame.confidence[8]=0;Assert.AreEqual(0,HandGeometry.Openness(s.Frame));}
}
