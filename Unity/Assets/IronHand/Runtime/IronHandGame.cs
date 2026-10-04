using System;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace IronHand
{
    public enum GamePhase { Home, Placement, Calibration, Ready, Combat, Intermission, Paused, Results, Workshop }
    public sealed class IronHandGame : MonoBehaviour
    {
        public GameDefinition Config {get;private set;}
        public Progression Progress {get;private set;}
        public ArenaController Arena {get;private set;}
        public HandRigDriver Rig {get;private set;}
        public GamePhase Phase {get;private set;}=GamePhase.Home;
        public float HP {get;private set;}
        public float Mana {get;private set;}
        public int Wave {get;private set;}
        public float Clock {get;private set;}
        public int Kills {get;private set;}
        public int RunGold {get;private set;}
        public int RunXP {get;private set;}
        public float Calibration {get;private set;}
        public bool Won {get;private set;}
        public string Notice {get;private set;}="";
        public bool Diagnostics, SimulateTrackingLoss;
        public bool HandLeftOverride;
        public bool UseHandOverride;
        public bool Firing {get;private set;}
        public float ResumeCountdown {get;private set;}
        public IReadOnlyList<EnemyActor> Enemies=>enemies;
        public int AliveCount {get {int n=0;foreach(var e in enemies)if(e.Alive)n++;return n;}}
        public ArmorSpec Armor=>Config.armors[Progress.Data.equipped];
        public int MaxHP=>100+Progress.Data.healthRank*10+Armor.health;
        public int MaxMana=>100+Progress.Data.manaRank*10+Armor.mana;
        public int Damage=>10+Progress.Data.damageRank*2+Armor.damage;
        public bool TrackingOK=>Arena.Tracking&&!SimulateTrackingLoss&&!backgrounded;
        public float FPS {get;private set;}
        public bool AutoTest {get;private set;}
        public event Action Changed;
        readonly List<EnemyActor> enemies=new List<EnemyActor>();
        readonly List<float> calibrationWidths=new List<float>();
        readonly GestureGate gesture=new GestureGate();
        readonly SimulatedHand showroom=new SimulatedHand {firing=true};
        GamePhase beforePause;
        CombatFx fx;IronHandHUD hud;DiagnosticsRecorder recorder;
        System.Random random;
        float spawnClock,weaponClock,regenDelay,calibrationSeconds,autoClock;
        long lastSample;
        double stableStart=-1;
        int nextId, smokeRuns;
        bool smokeResetPassed, smokeUIPassed;
        bool pausedByTracking,backgrounded;
        Vector2 lastWrist;
        float lastWidth;
        void Awake()
        {
            Application.runInBackground=true;Application.targetFrameRate=30;QualitySettings.vSyncCount=0;Screen.sleepTimeout=SleepTimeout.NeverSleep;
            Config=Resources.Load<GameDefinition>("IronHand/Definition");
            AutoTest=Array.IndexOf(Environment.GetCommandLineArgs(),"--ironhand-smoke")>=0;
            string saveDir=Path.Combine(Application.persistentDataPath,Application.platform==RuntimePlatform.IPhonePlayer?"device":"simulation");
            if(AutoTest)saveDir=Path.Combine(Application.temporaryCachePath,"ironhand-smoke-"+DateTime.UtcNow.Ticks);
            Progress=new Progression(new SaveStore(saveDir));
            Arena=gameObject.AddComponent<ArenaController>();Arena.Initialize();
            Rig=new GameObject("Hand presentation").AddComponent<HandRigDriver>();Rig.Initialize(Arena.Camera);
            fx=gameObject.AddComponent<CombatFx>();fx.Initialize();
            var light=new GameObject("Key light").AddComponent<Light>();light.type=LightType.Directional;light.intensity=1.6f;light.transform.rotation=Quaternion.Euler(45,-35,0);
            RenderSettings.ambientLight=new Color(.45f,.55f,.63f);
            for(int k=0;k<3;k++)for(int i=0;i<Config.maxEnemies;i++){var e=new GameObject(Config.enemies[k].name).AddComponent<EnemyActor>();e.Initialize(k,Config.enemies[k]);enemies.Add(e);}
            hud=gameObject.AddComponent<IronHandHUD>();hud.Initialize(this);
            recorder=new DiagnosticsRecorder(Application.persistentDataPath);
            HP=MaxHP;Mana=MaxMana;ResumeCountdown=3;
            if(AutoTest){Config=Instantiate(Config);Config.waveSeconds=4;Config.cleanupSeconds=3;Config.breakSeconds=.5f;Config.firstSpawnInterval=.7f;Config.finalSpawnInterval=.5f;}
        }
        void Update()
        {
            float realDt=Mathf.Min(Time.unscaledDeltaTime,.1f),dt=realDt;
            FPS=Mathf.Lerp(FPS,1/Mathf.Max(.0001f,Time.unscaledDeltaTime),.04f);
            if(Arena.Simulation!=null)
            {
                var s=Arena.Simulation;s.firing=Phase==GamePhase.Calibration||Phase==GamePhase.Ready||Input.GetKey(KeyCode.Space)||AutoTest;
                if(Input.GetKeyDown(KeyCode.H))s.lost=!s.lost;
                if(Input.GetKeyDown(KeyCode.L))s.left=!s.left;
                if(Input.GetKeyDown(KeyCode.T))SimulateTrackingLoss=!SimulateTrackingLoss;
                if(Input.GetMouseButton(1)&&Phase==GamePhase.Combat)
                {var e=Arena.Camera.transform.eulerAngles;e.y+=Input.GetAxis("Mouse X")*2;e.x-=Input.GetAxis("Mouse Y")*2;Arena.Camera.transform.eulerAngles=e;}
            }
            if(Input.GetKeyDown(KeyCode.Return)){if(Phase==GamePhase.Home)StartSetup();else if(Phase==GamePhase.Placement)ConfirmArea();else if(Phase==GamePhase.Ready)StartRun();}
            if(Input.GetKeyDown(KeyCode.Escape))PauseOrResume();
            Arena.SetHandTracking(Phase==GamePhase.Calibration||Phase==GamePhase.Ready||Phase==GamePhase.Combat||Phase==GamePhase.Intermission);
            Arena.Tick();var frame=Arena.Hands.Frame;
            if(UseHandOverride)frame.left=HandLeftOverride;
            bool showcase=Phase==GamePhase.Home||Phase==GamePhase.Workshop||Phase==GamePhase.Results;
            if(showcase){showroom.Tick();Rig.Tick(showroom.Frame,Arena.Camera,realDt,true);}else Rig.Tick(frame,Arena.Camera,realDt);
            Rig.SetTier(Progress.Data.equipped,Armor.color);fx.Tick(realDt);
            bool active=Phase==GamePhase.Combat||Phase==GamePhase.Intermission||Phase==GamePhase.Calibration||Phase==GamePhase.Ready;
            if(active&&!TrackingOK){beforePause=Phase;pausedByTracking=true;Phase=GamePhase.Paused;ResumeCountdown=3;gesture.Reset();Firing=false;stableStart=-1;calibrationWidths.Clear();Calibration=0;Changed?.Invoke();}
            if(Phase==GamePhase.Paused&&pausedByTracking)
            {
                if(TrackingOK){ResumeCountdown-=realDt;if(ResumeCountdown<=0){Phase=beforePause;pausedByTracking=false;ResumeCountdown=3;gesture.Reset();Changed?.Invoke();}}
                else ResumeCountdown=3;
            }
            Firing=false;
            if(Phase==GamePhase.Calibration)Calibrate(frame,realDt);
            if(Phase==GamePhase.Combat)Combat(frame,dt);
            else if(Phase==GamePhase.Intermission){Clock-=dt;if(Clock<=0)BeginWave();}
            recorder.Tick(realDt,this,frame);
            if(AutoTest)SmokeTick(realDt);
        }
        public void StartSetup()
        {
            Notice="";
            if(Arena.IsPlaced)StartCalibration();else SetPhase(GamePhase.Placement);
        }
        public void ConfirmArea(){if(Arena.Place())StartCalibration();}
        void StartCalibration(){stableStart=-1;calibrationSeconds=0;Calibration=0;calibrationWidths.Clear();lastSample=-1;SetPhase(GamePhase.Calibration);}
        void Calibrate(HandFrame frame,float dt)
        {
            if(!frame.Fresh(Time.realtimeSinceStartupAsDouble)||frame.openness<.82f){stableStart=-1;calibrationSeconds=0;Calibration=0;calibrationWidths.Clear();return;}
            if(frame.sequence==lastSample)return;lastSample=frame.sequence;
            bool inside=true;for(int i=0;i<21;i++)inside &= frame.confidence[i]>.35f&&frame.points[i].x>.02f&&frame.points[i].x<.98f&&frame.points[i].y>.02f&&frame.points[i].y<.98f;
            bool stable=calibrationWidths.Count==0||(Mathf.Abs(frame.Width-lastWidth)<.025f&&Vector2.Distance(frame.points[0],lastWrist)<.05f);
            lastWidth=frame.Width;lastWrist=frame.points[0];
            if(!inside||!stable){stableStart=-1;calibrationWidths.Clear();calibrationSeconds=0;Calibration=0;return;}
            calibrationWidths.Add(frame.Width);
            // Accumulate capture intervals, not render frames or a cosmetic countdown.
            if(stableStart<0)stableStart=frame.capturedAt;
            calibrationSeconds=(float)(frame.capturedAt-stableStart);
            Calibration=Mathf.Min(1,calibrationSeconds/3);
            if(calibrationSeconds>=3&&calibrationWidths.Count>=30)
            {
                calibrationWidths.Sort();float median=calibrationWidths[calibrationWidths.Count/2];
                Notice=$"Hand calibrated · palm width {median*100:F1}% of screen";SetPhase(GamePhase.Ready);
            }
        }
        public void StartRun()
        {
            if(Phase!=GamePhase.Ready||!TrackingOK)return;
            ClearEnemies();Progress.BeginRun();random=new System.Random(Config.seed);nextId=0;Kills=RunGold=RunXP=0;HP=MaxHP;Mana=MaxMana;Wave=0;Won=false;weaponClock=0;regenDelay=0;gesture.Reset();BeginWave();
        }
        void BeginWave(){Wave++;Clock=Config.waveSeconds+Config.cleanupSeconds;spawnClock=.7f;SetPhase(GamePhase.Combat);}
        void Combat(HandFrame frame,float dt)
        {
            Clock-=dt;spawnClock-=dt;weaponClock-=dt;regenDelay-=dt;
            if(Clock>Config.cleanupSeconds&&spawnClock<=0&&AliveCount<Config.maxEnemies)
            {
                int kind=Wave==1?0:Wave<3?random.Next(2):random.Next(3);
                if(Arena.TrySpawnPosition(random,kind==0,out var pos))foreach(var e in enemies)if(!e.Alive&&e.Kind==kind){e.Spawn(++nextId,Wave,pos,Arena.Root);break;}
                spawnClock=Mathf.Lerp(Config.firstSpawnInterval,Config.finalSpawnInterval,(Wave-1f)/Mathf.Max(1,Config.waveCount-1));
            }
            bool fire=gesture.Tick(frame.openness,frame.valid,frame.capturedAt,Time.realtimeSinceStartupAsDouble);
            Firing=fire&&Mana>=4;
            if(Firing&&weaponClock<=0){Fire();weaponClock=1f/3;regenDelay=.35f;}
            if(!fire&&regenDelay<=0)Mana=Mathf.Min(MaxMana,Mana+12*dt);
            foreach(var e in enemies)if(e.Alive){e.Tick(dt,Arena.Camera.transform.position,Hurt);if(Phase!=GamePhase.Combat)break;}
            if(Phase!=GamePhase.Combat)return;
            if(Clock<=0||(Clock<=Config.cleanupSeconds&&AliveCount==0))
            {
                ClearEnemies();gesture.Reset();
                if(Wave>=Config.waveCount){Won=true;Reward(-1,50,50);SetPhase(GamePhase.Results);Progress.Flush();}
                else {Clock=Config.breakSeconds;SetPhase(GamePhase.Intermission);}
            }
        }
        void Fire()
        {
            Mana-=4;var ray=new Ray(Arena.Camera.transform.position,Arena.Camera.transform.forward);
            EnemyActor target=null;float nearest=10;
            foreach(var e in enemies)
            {
                if(!e.Alive)continue;var v=e.AimPoint-ray.origin;float d=Vector3.Dot(v,ray.direction);
                if(d<=0||d>=nearest)continue;
                float assist=Mathf.Tan(2*Mathf.Deg2Rad)*d;
                if((v-ray.direction*d).magnitude<=e.Radius+assist){nearest=d;target=e;}
            }
            var end=target?target.AimPoint:ray.GetPoint(6);
            fx.Shot(Rig.Muzzle.position,end,Armor.color,target);
            if(target&&target.Hit(Damage)){Kills++;Reward(target.Id,target.Spec.gold,target.Spec.xp);}
        }
        void Reward(int id,int gold,int xp){if(Progress.Reward(id,gold,xp)){RunGold+=gold;RunXP+=xp;Changed?.Invoke();}}
        void Hurt(int damage){HP=Mathf.Max(0,HP-damage);hud.FlashDamage();if(HP<=0){Won=false;SetPhase(GamePhase.Results);ClearEnemies();Progress.Flush();}}
        public void PauseOrResume()
        {
            if(Phase==GamePhase.Combat||Phase==GamePhase.Intermission){beforePause=Phase;pausedByTracking=false;SetPhase(GamePhase.Paused);gesture.Reset();}
            else if(Phase==GamePhase.Paused&&!pausedByTracking&&TrackingOK){SetPhase(beforePause);gesture.Reset();}
        }
        public void Workshop(){Progress.Flush();ClearEnemies();SetPhase(GamePhase.Workshop);}
        public void BackHome(){SetPhase(GamePhase.Home);}
        public void Equip(int i){Notice=Progress.Equip(i,Config.armors[i])?"Armour equipped":"Level or gold requirement not met";Changed?.Invoke();}
        public void Upgrade(int i){Notice=Progress.Upgrade(i)?"Upgrade saved":"Insufficient gold or maximum rank";Changed?.Invoke();}
        public void ResetArea(){ClearEnemies();Progress.Flush();Arena.ResetArena();gesture.Reset();SetPhase(GamePhase.Placement);}
        public void ToggleSound(){fx.Sound=!fx.Sound;Notice=fx.Sound?"Sound on":"Sound off";Changed?.Invoke();}
        public void ToggleHand(){UseHandOverride=true;HandLeftOverride=!HandLeftOverride;Notice=HandLeftOverride?"Left hand selected":"Right hand selected";Changed?.Invoke();}
        void ClearEnemies(){foreach(var e in enemies)if(e){e.Despawn();e.transform.SetParent(transform,true);}}
        void SetPhase(GamePhase value){Phase=value;Firing=false;Changed?.Invoke();}
        void OnApplicationPause(bool paused){backgrounded=paused;if(paused){gesture.Reset();Progress?.Flush();}}
        void OnApplicationFocus(bool focus){backgrounded=Application.platform==RuntimePlatform.IPhonePlayer&&!focus;if(!focus)gesture.Reset();}
        void OnDestroy(){Progress?.Flush();recorder?.Dispose();}
        void SmokeTick(float dt)
        {
            autoClock+=dt;
            if(Phase==GamePhase.Home)
            {
                // Exercise the real HUD hit target and callback, not just StartSetup.
                foreach(var button in FindObjectsByType<Button>(FindObjectsSortMode.None))
                {
                    var label=button.GetComponentInChildren<Text>();
                    if(!label||!label.text.StartsWith("DEPLOY"))continue;
                    var rect=(RectTransform)button.transform;
                    var pointer=new PointerEventData(EventSystem.current){position=RectTransformUtility.WorldToScreenPoint(null,rect.TransformPoint(rect.rect.center))};
                    var hits=new List<RaycastResult>();EventSystem.current.RaycastAll(pointer,hits);
                    smokeUIPassed=hits.Exists(hit=>hit.gameObject.GetComponentInParent<Button>()==button);
                    if(smokeUIPassed)ExecuteEvents.Execute(button.gameObject,pointer,ExecuteEvents.pointerClickHandler);
                    break;
                }
            }
            if(Phase==GamePhase.Placement)ConfirmArea();
            if(Phase==GamePhase.Ready)StartRun();
            if(Phase==GamePhase.Combat)foreach(var e in enemies)if(e.Alive){Arena.Camera.transform.LookAt(e.AimPoint);break;}
            if(Phase==GamePhase.Results&&Won&&smokeRuns==0)
            {
                smokeRuns++;
                // Exercise the destructive AR reset path after a populated run.
                ResetArea();return;
            }
            if(smokeRuns==1&&Phase==GamePhase.Calibration)
            {
                smokeResetPassed=true;
                foreach(var enemy in enemies)smokeResetPassed &= enemy!=null;
            }
            if(Phase==GamePhase.Results || autoClock>140)
            {
                bool success=Phase==GamePhase.Results&&Won&&smokeResetPassed&&smokeUIPassed;
                var result=$"{{\"completed\":{(Phase==GamePhase.Results).ToString().ToLower()},\"won\":{Won.ToString().ToLower()},\"wave\":{Wave},\"kills\":{Kills},\"gold\":{RunGold},\"xp\":{RunXP},\"runs\":{smokeRuns+1},\"arena_reset_passed\":{smokeResetPassed.ToString().ToLower()},\"ui_raycast_passed\":{smokeUIPassed.ToString().ToLower()}}}";
                File.WriteAllText(Path.Combine(Application.persistentDataPath,"smoke-result.json"),result);
                Debug.Log("IRONHAND_SMOKE "+result);AutoTest=false;Application.Quit(success?0:1);
            }
        }
    }
    public sealed class DiagnosticsRecorder : IDisposable
    {
        readonly StreamWriter writer;float elapsed;
        public DiagnosticsRecorder(string directory)
        {
            string folder=Path.Combine(directory,"diagnostics");Directory.CreateDirectory(folder);
            writer=new StreamWriter(Path.Combine(folder,DateTime.UtcNow.ToString("yyyyMMdd-HHmmss")+".csv"));
            writer.WriteLine("# Unity="+Application.unityVersion+";OS="+SystemInfo.operatingSystem+";device="+SystemInfo.deviceModel+";provider=AppleVision2D-or-simulation");
            writer.WriteLine("seconds,fps,frame_ms,pose_age_ms,inference_ms,hand_valid,world_tracking,phase,wave,enemies,hp,mana,gold,arena_status,hand_status,planes,plane_mode,camera_x,camera_y,camera_z,camera_pitch,can_place,calibration");
        }
        public void Tick(float dt,IronHandGame g,HandFrame f)
        {
            elapsed+=dt;if(elapsed<.25f)return;elapsed=0;
            var camera=g.Arena.Camera.transform;
            writer.WriteLine(string.Format(System.Globalization.CultureInfo.InvariantCulture,"{0:F3},{1:F1},{2:F1},{3:F1},{4:F1},{5},{6},{7},{8},{9},{10:F0},{11:F0},{12},{13},{14},{15},{16},{17:F3},{18:F3},{19:F3},{20:F1},{21},{22:F2}",Time.realtimeSinceStartupAsDouble,g.FPS,Time.unscaledDeltaTime*1000,(Time.realtimeSinceStartupAsDouble-f.capturedAt)*1000,f.inferenceMs,f.Fresh(Time.realtimeSinceStartupAsDouble),g.TrackingOK,g.Phase,g.Wave,g.AliveCount,g.HP,g.Mana,g.Progress.Data.gold,g.Arena.Status.Replace(',',';'),g.Arena.Hands.Status.Replace(',',';'),g.Arena.PlaneCount,g.Arena.PlaneMode.Replace(',',';'),camera.position.x,camera.position.y,camera.position.z,camera.eulerAngles.x,g.Arena.CanPlace,g.Calibration));writer.Flush();
        }
        public void Dispose()=>writer?.Dispose();
    }
}
