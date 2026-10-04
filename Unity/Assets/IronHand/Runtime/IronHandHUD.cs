using UnityEngine;
using UnityEngine.UI;
using UnityEngine.EventSystems;

namespace IronHand
{
    public sealed class IronHandHUD : MonoBehaviour
    {
        static readonly Color Cyan=new Color(.28f,.92f,.96f),Ink=new Color(.027f,.058f,.083f,.96f),Muted=new Color(.51f,.64f,.69f),White=new Color(.9f,.95f,.96f);
        IronHandGame game;Font font;Sprite barSprite;RectTransform root,panel;Text status,wallet,hint,health,mana,wave,debug,calibration,centerMessage;Image healthFill,manaFill,damage,scanFill;
        GamePhase drawn=(GamePhase)(-1);bool dirty;float damageAlpha;
        Button placementButton;Text placementButtonLabel;
        public void Initialize(IronHandGame value)
        {
            game=value;font=Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            var white=Texture2D.whiteTexture;barSprite=Sprite.Create(white,new Rect(0,0,white.width,white.height),Vector2.one*.5f);
            if(!FindFirstObjectByType<EventSystem>()){var es=new GameObject("Event System");es.AddComponent<EventSystem>();es.AddComponent<StandaloneInputModule>();}
            var canvas=new GameObject("IronHand HUD").AddComponent<Canvas>();canvas.renderMode=RenderMode.ScreenSpaceOverlay;canvas.sortingOrder=20;
            var scaler=canvas.gameObject.AddComponent<CanvasScaler>();scaler.uiScaleMode=CanvasScaler.ScaleMode.ScaleWithScreenSize;scaler.referenceResolution=new Vector2(1920,1080);scaler.matchWidthOrHeight=.5f;canvas.gameObject.AddComponent<GraphicRaycaster>();
            root=Rect("Safe Area",canvas.transform,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero);
            var safe=Screen.safeArea;root.anchorMin=new Vector2(safe.x/Screen.width,safe.y/Screen.height);root.anchorMax=new Vector2(safe.xMax/Screen.width,safe.yMax/Screen.height);
            Box(root,new Vector2(0,1),new Vector2(0,1),new Vector2(0,0),new Vector2(1920,115),Ink,new Vector2(0,1));
            Label(root,"IRONHAND",32,new Vector2(48,-34),new Vector2(300,48),White);
            Label(root,"AUGMENTED COMBAT   /   PROTOTYPE 01",14,new Vector2(50,-78),new Vector2(450,25),Muted);
            status=Label(root,"",17,new Vector2(610,-45),new Vector2(560,45),Cyan);
            wallet=Label(root,"",21,new Vector2(-550,-35),new Vector2(350,55),White,new Vector2(1,1));
            Button(root,"II",new Vector2(-130,-30),new Vector2(80,58),()=>game.PauseOrResume(),false,new Vector2(1,1));
            health=Label(root,"",17,new Vector2(50,-137),new Vector2(300,26),White);
            healthFill=Bar(root,new Vector2(50,-178),new Vector2(260,8),new Color(1,.42f,.28f));
            mana=Label(root,"",17,new Vector2(50,-207),new Vector2(300,26),White);
            manaFill=Bar(root,new Vector2(50,-248),new Vector2(260,8),Cyan);
            wave=Label(root,"",22,new Vector2(-390,-140),new Vector2(330,75),White,new Vector2(1,1));
            hint=Label(root,"",19,new Vector2(50,75),new Vector2(1380,52),Muted,new Vector2(0,0));
            Button(root,"D",new Vector2(-118,98),new Vector2(65,50),()=>{game.Diagnostics=!game.Diagnostics;},false,new Vector2(1,0));
            debug=Label(root,"",16,new Vector2(-580,250),new Vector2(525,138),Cyan,new Vector2(1,0));
            var cross=Rect("Reticle",canvas.transform,new Vector2(.5f,.5f),new Vector2(.5f,.5f),Vector2.zero,new Vector2(30,30));
            Box(cross,Vector2.one*.5f,Vector2.one*.5f,Vector2.zero,new Vector2(3,24),Cyan);
            Box(cross,Vector2.one*.5f,Vector2.one*.5f,Vector2.zero,new Vector2(24,3),Cyan);
            panel=Rect("Panels",root,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero);
            damage=Box(root,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,new Color(1,0,0,0));damage.raycastTarget=false;
            game.Changed+=()=>dirty=true;
        }
        void Update()
        {
            if(drawn!=game.Phase || (dirty&&(game.Phase==GamePhase.Workshop||game.Phase==GamePhase.Ready||game.Phase==GamePhase.Results))){drawn=game.Phase;DrawPanel();}dirty=false;
            var d=game.Progress.Data;
            wallet.text=$"LV {d.Level:00}     {d.gold:N0} GOLD\n<size=14><color=#839FA8>{d.xp} TOTAL XP</color></size>";
            status.text=(game.Arena.IsDevice?"●  LIVE AR":"●  SIMULATOR")+"  /  "+(game.TrackingOK?"SYSTEM ONLINE":"TRACKING LOST");
            health.text=$"INTEGRITY    {game.HP:0} / {game.MaxHP}";healthFill.fillAmount=game.HP/game.MaxHP;
            mana.text=$"ENERGY        {game.Mana:0} / {game.MaxMana}";manaFill.fillAmount=game.Mana/game.MaxMana;
            wave.text=game.Wave>0?$"WAVE  {game.Wave:00} / 05\n<size=16>{Mathf.CeilToInt(Mathf.Max(0,game.Clock))}s   ·   {game.AliveCount} HOSTILES</size>":"";
            hint.text=game.Arena.IsDevice?"OPEN PALM TO FIRE   ·   CLOSE HAND TO RECHARGE   ·   AIM WITH YOUR PHONE":"SIMULATION   /   ENTER: CONTINUE   ·   HOLD SPACE: FIRE   ·   RIGHT DRAG: AIM   ·   H: LOSE HAND   ·   T: LOSE AR   ·   L: SWITCH HAND";
            if(game.Phase==GamePhase.Placement)hint.text="";
            var f=game.Arena.Hands.Frame;
            debug.text=game.Diagnostics?$"{game.FPS:0} FPS  /  {Time.unscaledDeltaTime*1000:0.0} ms frame\nPOSE AGE {(Time.realtimeSinceStartupAsDouble-f.capturedAt)*1000:0} ms  /  VISION {f.inferenceMs:0} ms\n{game.Arena.Hands.Status}  ·  OPEN {f.openness:P0}\n{game.Progress.SaveError ?? "SAVE OK"}":"";
            if(calibration){calibration.text=$"{game.Calibration*100:00}%   /   "+game.Arena.Hands.Status;scanFill.fillAmount=game.Calibration;}
            if(centerMessage&&game.Phase==GamePhase.Placement)
            {
                centerMessage.text=game.Arena.Status;
                placementButton.interactable=game.Arena.CanPlace;
                placementButtonLabel.text=game.Arena.CanPlace?"CONFIRM CLEAR AREA  →":"FINDING FLOOR…";
            }
            if(centerMessage&&game.Phase==GamePhase.Paused)centerMessage.text=game.TrackingOK?$"Ready · recovering {game.ResumeCountdown:0.0}s\nTap RESUME for a manual pause.":"Tracking interrupted. Hold the phone steady.\nCombat and damage are paused.";
            if(centerMessage&&game.Phase==GamePhase.Intermission)centerMessage.text=$"NEXT WAVE IN {Mathf.CeilToInt(game.Clock)}\nLower your hand and rest.";
            damageAlpha=Mathf.MoveTowards(damageAlpha,0,Time.unscaledDeltaTime*1.4f);damage.color=new Color(.9f,.08f,.03f,damageAlpha);
        }
        public void FlashDamage(){damageAlpha=.24f;}
        void DrawPanel()
        {
            foreach(Transform child in panel)Destroy(child.gameObject);calibration=null;scanFill=null;centerMessage=null;placementButton=null;placementButtonLabel=null;
            switch(game.Phase)
            {
                case GamePhase.Home:
                    Label(panel,"FIELD SYSTEM / 01",19,new Vector2(60,-345),new Vector2(650,40),Cyan);
                    Label(panel,"YOUR HAND.\nYOUR FIREPOWER.",66,new Vector2(55,-405),new Vector2(990,185),White);
                    Label(panel,"Equip living steel. Defend your space.\nFive waves. One hand. No second chances.",26,new Vector2(62,-632),new Vector2(780,90),Muted);
                    Button(panel,"DEPLOY  →",new Vector2(60,-768),new Vector2(460,80),game.StartSetup,true);
                    Button(panel,"WORKSHOP",new Vector2(550,-768),new Vector2(260,80),game.Workshop,false);
                    Label(panel,game.Armor.code+"   /   "+game.Armor.name,26,new Vector2(-530,-795),new Vector2(430,60),Cyan,new Vector2(1,1));break;
                case GamePhase.Placement:
                    var sheet=Box(panel,Vector2.zero,Vector2.right,Vector2.zero,new Vector2(0,265),Ink,new Vector2(.5f,0)).rectTransform;
                    Label(sheet,"STEP 1 / 2  ·  PLACE YOUR ARENA",28,new Vector2(48,-24),new Vector2(1000,45),White);
                    centerMessage=Label(sheet,game.Arena.Status,24,new Vector2(48,-82),new Vector2(1030,62),Cyan);
                    Label(sheet,"Point the center + at a clear floor 1–3 m ahead.\nConfirm the cyan marker first. Hand scanning comes next.",21,new Vector2(48,-164),new Vector2(1030,74),Muted);
                    placementButton=Button(sheet,"FINDING FLOOR…",new Vector2(-490,-40),new Vector2(440,78),game.ConfirmArea,true,new Vector2(1,1));
                    placementButtonLabel=placementButton.GetComponentInChildren<Text>();placementButton.interactable=game.Arena.CanPlace;
                    Button(sheet,"BACK",new Vector2(-490,-152),new Vector2(180,65),game.BackHome,false,new Vector2(1,1));
                    if(game.Arena.IsDevice)Button(sheet,"SETTINGS",new Vector2(-280,-152),new Vector2(230,65),game.Arena.OpenCameraSettings,false,new Vector2(1,1));break;
                case GamePhase.Calibration:
                    Label(panel,"STEP 2 / 2  ·  SYNC YOUR HAND",36,new Vector2(430,-295),new Vector2(1100,80),White);
                    Label(panel,"Show your entire OPEN hand. Hold it steady for 3 seconds.\nKeep your wrist and all fingertips inside the camera view.",23,new Vector2(430,-395),new Vector2(1080,100),Muted);
                    calibration=Label(panel,"",25,new Vector2(430,-555),new Vector2(900,70),Cyan);scanFill=Bar(panel,new Vector2(430,-635),new Vector2(650,12),Cyan);
                    Button(panel,"SWITCH LEFT / RIGHT",new Vector2(430,-710),new Vector2(390,66),game.ToggleHand,false);
                    Button(panel,"RESET AREA",new Vector2(850,-710),new Vector2(270,66),game.ResetArea,false);break;
                case GamePhase.Ready:
                    Modal("SYSTEM SYNCHRONIZED","Aim with the camera. Open your palm to fire.\nClose your hand to recover energy. Keep the area clear.");
                    Label(panel,game.Notice,21,new Vector2(480,-550),new Vector2(900,60),Cyan);
                    Button(panel,"BEGIN DEFENSE  →",new Vector2(480,-665),new Vector2(580,80),game.StartRun,true);break;
                case GamePhase.Intermission:
                    centerMessage=Label(panel,"",38,new Vector2(500,-390),new Vector2(950,150),White);break;
                case GamePhase.Paused:
                    Modal("SYSTEM PAUSED","");centerMessage=Label(panel,"",24,new Vector2(480,-455),new Vector2(1000,110),Muted);
                    Button(panel,"RESUME",new Vector2(480,-610),new Vector2(350,75),game.PauseOrResume,true);
                    Button(panel,"RESET AREA",new Vector2(855,-610),new Vector2(330,75),game.ResetArea,false);
                    Button(panel,"SOUND ON / OFF",new Vector2(480,-710),new Vector2(350,65),game.ToggleSound,false);
                    Button(panel,"WORKSHOP / END RUN",new Vector2(855,-710),new Vector2(400,65),game.Workshop,false);break;
                case GamePhase.Results:
                    Label(panel,game.Won?"AREA SECURED":"SYSTEM OFFLINE",54,new Vector2(60,-370),new Vector2(1040,100),White);
                    Label(panel,$"{game.Kills:00} HOSTILES NEUTRALIZED\n+{game.RunGold} GOLD     +{game.RunXP} XP",32,new Vector2(65,-510),new Vector2(970,130),Cyan);
                    Label(panel,"Your rewards are saved. Upgrade and deploy again.",23,new Vector2(65,-680),new Vector2(1050,60),Muted);
                    Button(panel,"WORKSHOP  →",new Vector2(60,-790),new Vector2(465,80),game.Workshop,true);
                    Button(panel,"REDEPLOY",new Vector2(550,-790),new Vector2(300,80),game.StartSetup,false);break;
                case GamePhase.Workshop: DrawWorkshop();break;
            }
        }
        void Modal(string title,string desc)
        {
            Box(panel,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,new Color(.01f,.025f,.045f,.83f));
            Label(panel,title,48,new Vector2(480,-295),new Vector2(1110,90),White);
            Label(panel,desc,25,new Vector2(480,-415),new Vector2(1050,130),Muted);
        }
        void DrawWorkshop()
        {
            var d=game.Progress.Data;
            Label(panel,"THE WORKSHOP",46,new Vector2(60,-310),new Vector2(1020,80),White);
            Label(panel,"BUILD YOUR NEXT ADVANTAGE",18,new Vector2(63,-386),new Vector2(800,35),Muted);
            for(int i=0;i<3;i++)
            {
                int index=i;var a=game.Config.armors[i];float x=60+i*348;
                var card=Box(panel,Vector2.up,Vector2.up,new Vector2(x,-455),new Vector2(324,245),Ink,new Vector2(0,1)).rectTransform;
                Box(card,Vector2.up,Vector2.up,Vector2.zero,new Vector2(324,4),a.color,new Vector2(0,1));
                Label(card,a.code+"  /  LV "+a.level,16,new Vector2(24,-22),new Vector2(290,30),a.color);
                Label(card,a.name,30,new Vector2(22,-65),new Vector2(290,50),White);
                Label(card,$"DMG +{a.damage}  /  HP +{a.health}  /  EN +{a.mana}",16,new Vector2(24,-122),new Vector2(290,40),Muted);
                string label=d.equipped==i?"EQUIPPED":d.Level<a.level?"LOCKED · LV "+a.level:d.owned[i]?"EQUIP":a.price+" GOLD";
                var b=Button(card,label,new Vector2(22,-177),new Vector2(280,47),()=>game.Equip(index),d.equipped==i);
                b.interactable=d.equipped!=i && d.Level>=a.level&&(d.owned[i]||d.gold>=a.price);
            }
            string[] labels={"FIREPOWER +2","INTEGRITY +10","ENERGY +10"};
            for(int i=0;i<3;i++)
            {
                int k=i,rank=game.Progress.Rank(i),cost=Progression.UpgradeCost(rank);
                Label(panel,labels[i]+$"  [{rank}/5]",18,new Vector2(64+i*348,-735),new Vector2(330,36),Muted);
                var b=Button(panel,rank==5?"MAX RANK":"UPGRADE · "+cost,new Vector2(60+i*348,-785),new Vector2(324,65),()=>game.Upgrade(k),false);b.interactable=rank<5&&d.gold>=cost;
            }
            Button(panel,"DEPLOY  →",new Vector2(-485,-770),new Vector2(410,82),game.StartSetup,true,new Vector2(1,1));
            Label(panel,game.Notice,19,new Vector2(60,-882),new Vector2(1200,45),Cyan);
        }
        RectTransform Rect(string name,Transform parent,Vector2 min,Vector2 max,Vector2 pos,Vector2 size,Vector2? pivot=null)
        {
            var r=new GameObject(name,typeof(RectTransform)).GetComponent<RectTransform>();r.SetParent(parent,false);r.anchorMin=min;r.anchorMax=max;r.pivot=pivot??new Vector2(.5f,.5f);r.sizeDelta=size;r.anchoredPosition=pos;return r;
        }
        Image Box(Transform parent,Vector2 min,Vector2 max,Vector2 pos,Vector2 size,Color color,Vector2? pivot=null)
        {var r=Rect("Panel",parent,min,max,pos,size,pivot);var i=r.gameObject.AddComponent<Image>();i.color=color;i.raycastTarget=false;return i;}
        Text Label(Transform parent,string value,int size,Vector2 pos,Vector2 dims,Color color,Vector2? anchor=null)
        {
            Vector2 a=anchor??Vector2.up;var r=Rect(value,parent,a,a,pos,dims,new Vector2(0,1));var t=r.gameObject.AddComponent<Text>();t.font=font;t.text=value;t.fontSize=size;t.color=color;t.supportRichText=true;t.raycastTarget=false;t.verticalOverflow=VerticalWrapMode.Overflow;return t;
        }
        Button Button(Transform parent,string value,Vector2 pos,Vector2 size,UnityEngine.Events.UnityAction click,bool filled,Vector2? anchor=null)
        {
            Vector2 a=anchor??Vector2.up;var bg=Box(parent,a,a,pos,size,filled?Cyan:new Color(.07f,.14f,.18f,.95f),new Vector2(0,1));bg.raycastTarget=true;
            var b=bg.gameObject.AddComponent<Button>();b.targetGraphic=bg;b.onClick.AddListener(click);var colors=b.colors;colors.highlightedColor=new Color(.75f,1,1);colors.pressedColor=new Color(.5f,.7f,.75f);colors.disabledColor=new Color(.35f,.4f,.43f,.7f);b.colors=colors;
            var t=Label(bg.transform,value,22,new Vector2(12,-4),size-new Vector2(24,8),filled?Ink:White);t.alignment=TextAnchor.MiddleCenter;return b;
        }
        Image Bar(Transform parent,Vector2 pos,Vector2 size,Color color)
        {
            var bg=Box(parent,Vector2.up,Vector2.up,pos,size,new Color(.09f,.16f,.19f),new Vector2(0,1));
            var fill=Box(bg.transform,Vector2.zero,Vector2.one,Vector2.zero,Vector2.zero,color);fill.sprite=barSprite;fill.type=Image.Type.Filled;fill.fillMethod=Image.FillMethod.Horizontal;return fill;
        }
    }
}
