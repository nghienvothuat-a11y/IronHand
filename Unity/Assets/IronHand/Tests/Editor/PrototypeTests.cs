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
    [Test] public void RocketSweepFindsTargetBetweenFrames()
    {
        Assert.True(ProjectileGeometry.SegmentSphere(Vector3.zero,Vector3.forward*4,Vector3.forward*2,.2f,out float fraction));
        Assert.AreEqual(.45f,fraction,.0001f);
        Assert.False(ProjectileGeometry.SegmentSphere(Vector3.zero,Vector3.forward*4,new Vector3(1,0,2),.2f,out _));
        Assert.False(ProjectileGeometry.SegmentSphere(Vector3.zero,Vector3.forward,Vector3.forward*2,.2f,out _));
    }
    [Test] public void RocketSweepIncludesTheTargetsVisibleWingsAndHead()
    {
        var bounds=new Bounds(new Vector3(0,.5f,2),new Vector3(.8f,1,.3f));
        Assert.True(ProjectileGeometry.SegmentBounds(new Vector3(.35f,.9f,0),new Vector3(.35f,.9f,4),bounds,0,out float fraction));Assert.Less(fraction,.5f);
        Assert.False(ProjectileGeometry.SegmentBounds(new Vector3(.6f,.9f,0),new Vector3(.6f,.9f,4),bounds,0,out _));
    }
    [Test] public void StationaryTargetDoesNotApproachCameraAndDiesOnce()
    {
        var go=new GameObject("Test target");var arena=new GameObject("Test arena");
        try
        {
            var enemy=go.AddComponent<EnemyActor>();enemy.Initialize(1,new EnemySpec("Test",30,10,10,10,3,2,.2f));
            var spawn=new Vector3(1,0,3);enemy.Spawn(1,1,spawn,arena.transform);
            for(int i=0;i<100;i++)enemy.Tick(.1f,Vector3.zero);
            Assert.AreEqual(spawn,enemy.transform.position);Assert.AreEqual(30,enemy.Health);
            Assert.False(enemy.Hit(10));Assert.AreEqual(20,enemy.Health);Assert.True(enemy.Hit(20));Assert.False(enemy.Hit(20));
        }
        finally{UnityEngine.Object.DestroyImmediate(go);UnityEngine.Object.DestroyImmediate(arena);}
    }
    [Test] public void RocketsDealDamageOnlyAfterTravelAndCannotHitAfterReset()
    {
        var go=new GameObject("Test target");var arena=new GameObject("Test arena");var fxGo=new GameObject("Test rockets");
        try
        {
            var enemy=go.AddComponent<EnemyActor>();enemy.Initialize(0,new EnemySpec("Test",30,10,10,10,0,2,.2f));enemy.Spawn(1,1,Vector3.forward*2,arena.transform);
            var fx=fxGo.AddComponent<CombatFx>();fx.Initialize();fx.Sound=false;var enemies=new[]{enemy};
            System.Action<EnemyActor,int,Vector3> hit=(e,d,p)=>e.Hit(d);
            Assert.True(fx.Launch(Vector3.zero,enemy.AimPoint,10));Assert.AreEqual(30,enemy.Health);
            fx.TickProjectiles(.1f,enemies,hit);Assert.AreEqual(30,enemy.Health);
            fx.TickProjectiles(.4f,enemies,hit);Assert.AreEqual(20,enemy.Health);
            fx.TickProjectiles(.4f,enemies,hit);Assert.AreEqual(20,enemy.Health);
            fx.Launch(Vector3.zero,enemy.AimPoint,10);fx.Clear();fx.TickProjectiles(1,enemies,hit);Assert.AreEqual(20,enemy.Health);
        }
        finally{UnityEngine.Object.DestroyImmediate(go);UnityEngine.Object.DestroyImmediate(arena);UnityEngine.Object.DestroyImmediate(fxGo);}
    }
    [TestCase(false,1.333333f)][TestCase(true,1.777778f)] public void RetargetFitsDifferentFingerLengths(bool left,float aspect)
    {
        var cameraGo=new GameObject("Test camera");var rigGo=new GameObject("Test rig");
        try
        {
            var camera=cameraGo.AddComponent<Camera>();camera.aspect=aspect;camera.fieldOfView=58;
            var sim=new SimulatedHand{firing=true,left=left};sim.Tick();
            for(int i=5;i<21;i++)sim.Frame.points[i].y+=(i%4)*.012f;
            var rig=rigGo.AddComponent<HandRigDriver>();rig.Initialize(camera);rig.Tick(sim.Frame,camera,.033f);
            Assert.True(rig.Visible);
            var flags=System.Reflection.BindingFlags.NonPublic|System.Reflection.BindingFlags.Instance;
            var bones=(Transform[])typeof(HandRigDriver).GetField("joints",flags).GetValue(rig);
            var points=(Vector3[])typeof(HandRigDriver).GetField("worldPoints",flags).GetValue(rig);
            for(int i=0;i<21;i++)Assert.Less(Vector3.Distance(camera.WorldToScreenPoint(bones[i].position),camera.WorldToScreenPoint(points[i])),1f,$"Joint {i} {bones[i].name}, parent {bones[i].parent.name}");
        }
        finally{UnityEngine.Object.DestroyImmediate(rigGo);UnityEngine.Object.DestroyImmediate(cameraGo);}
    }
    [Test] public void CoverageBehindArmourKeepsTheSameScreenOutline()
    {
        var go=new GameObject("Test projection");
        try
        {
            var camera=go.AddComponent<Camera>();camera.aspect=4f/3;go.transform.position=new Vector3(2,1,3);go.transform.rotation=Quaternion.Euler(25,60,0);
            foreach(var uv in new[]{new Vector2(.1f,.2f),new Vector2(.8f,.85f)})
            {
                var front=camera.ViewportToWorldPoint(new Vector3(uv.x,uv.y,.38f));var back=HandCoverageShell.BehindInSamePixel(camera,front,.08f);
                var projected=camera.WorldToViewportPoint(back);Assert.AreEqual(uv.x,projected.x,.00001f);Assert.AreEqual(uv.y,projected.y,.00001f);Assert.Greater(projected.z,.38f);
            }
        }
        finally{UnityEngine.Object.DestroyImmediate(go);}
    }
}
