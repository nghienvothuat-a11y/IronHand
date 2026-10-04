using System;
using System.IO;
using System.Linq;
using IronHand;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEditor.XR.Management;
using UnityEditor.XR.Management.Metadata;
using UnityEditor.XR.ARKit;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.Management;

public static class PrototypeBuilder
{
    const string Root="Assets/Resources/IronHand/";
    [MenuItem("IronHand/Prepare prototype")]
    public static void Prepare()
    {
        Directory.CreateDirectory("Assets/Scenes");Directory.CreateDirectory("Assets/Settings");
        var importer=(ModelImporter)AssetImporter.GetAtPath(Root+"Hand.fbx");
        importer.animationType=ModelImporterAnimationType.Generic;importer.importAnimation=false;importer.isReadable=true;importer.optimizeGameObjects=false;importer.bakeAxisConversion=true;importer.SaveAndReimport();
        var definition=AssetDatabase.LoadAssetAtPath<GameDefinition>(Root+"Definition.asset");
        if(!definition){definition=ScriptableObject.CreateInstance<GameDefinition>();AssetDatabase.CreateAsset(definition,Root+"Definition.asset");}
        var handMat=AssetDatabase.LoadAssetAtPath<Material>(Root+"HandMaterial.mat");
        if(!handMat){handMat=new Material(Shader.Find("Universal Render Pipeline/Lit"));AssetDatabase.CreateAsset(handMat,Root+"HandMaterial.mat");}
        handMat.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"Textures/IronHand_MK1_BaseColor.png"));
        handMat.SetColor("_BaseColor",Color.white);handMat.SetFloat("_Metallic",.75f);handMat.SetFloat("_Smoothness",.65f);
        handMat.SetTexture("_EmissionMap",AssetDatabase.LoadAssetAtPath<Texture2D>(Root+"Textures/IronHand_MK1_Emission.png"));handMat.SetColor("_EmissionColor",new Color(.25f,.9f,1)*1.5f);handMat.EnableKeyword("_EMISSION");EditorUtility.SetDirty(handMat);
        var renderer=AssetDatabase.LoadAssetAtPath<UniversalRendererData>("Assets/Settings/MobileRenderer.asset");
        if(!renderer)
        {
            renderer=ScriptableObject.CreateInstance<UniversalRendererData>();AssetDatabase.CreateAsset(renderer,"Assets/Settings/MobileRenderer.asset");
            var background=ScriptableObject.CreateInstance<ARBackgroundRendererFeature>();background.name="AR Camera Background";renderer.rendererFeatures.Add(background);AssetDatabase.AddObjectToAsset(background,renderer);
        }
        var pipeline=AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/MobilePipeline.asset");
        if(!pipeline){pipeline=UniversalRenderPipelineAsset.Create(renderer);AssetDatabase.CreateAsset(pipeline,"Assets/Settings/MobilePipeline.asset");}
        pipeline.msaaSampleCount=2;pipeline.renderScale=1;pipeline.supportsHDR=false;pipeline.shadowDistance=0;pipeline.supportsCameraDepthTexture=false;pipeline.supportsCameraOpaqueTexture=false;
        GraphicsSettings.defaultRenderPipeline=pipeline;QualitySettings.renderPipeline=pipeline;QualitySettings.shadows=UnityEngine.ShadowQuality.Disable;
        // Runtime-created procedural materials must retain their shaders in player builds.
        var graphics=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/GraphicsSettings.asset")[0]);
        var shaders=graphics.FindProperty("m_AlwaysIncludedShaders");
        foreach(string name in new[]{"Universal Render Pipeline/Lit","Universal Render Pipeline/Unlit"})
        {var s=Shader.Find(name);bool found=false;for(int i=0;i<shaders.arraySize;i++)found|=shaders.GetArrayElementAtIndex(i).objectReferenceValue==s;if(!found){shaders.InsertArrayElementAtIndex(shaders.arraySize);shaders.GetArrayElementAtIndex(shaders.arraySize-1).objectReferenceValue=s;}}
        graphics.ApplyModifiedPropertiesWithoutUndo();
        PlayerSettings.companyName="IronHand";PlayerSettings.productName="IronHand";PlayerSettings.bundleVersion="0.1.0";
        PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.iOS,"com.nghienvothuat.ironhand");
        PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Standalone,"com.nghienvothuat.ironhand.simulation");
        PlayerSettings.defaultScreenWidth=1600;PlayerSettings.defaultScreenHeight=900;PlayerSettings.fullScreenMode=FullScreenMode.Windowed;
        PlayerSettings.defaultInterfaceOrientation=UIOrientation.AutoRotation;PlayerSettings.allowedAutorotateToPortrait=false;PlayerSettings.allowedAutorotateToPortraitUpsideDown=false;PlayerSettings.allowedAutorotateToLandscapeLeft=true;PlayerSettings.allowedAutorotateToLandscapeRight=true;
        PlayerSettings.iOS.targetOSVersionString="15.0";PlayerSettings.iOS.cameraUsageDescription="IronHand uses the rear camera to place enemies in your room and track your hand. Images stay on this device.";
        PlayerSettings.iOS.targetDevice=iOSTargetDevice.iPhoneAndiPad;PlayerSettings.iOS.appleEnableAutomaticSigning=true;
        PlayerSettings.SetScriptingBackend(NamedBuildTarget.iOS,ScriptingImplementation.IL2CPP);
        PlayerSettings.SetArchitecture(NamedBuildTarget.iOS,1);PlayerSettings.stripEngineCode=true;
        var settings=new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/ProjectSettings.asset")[0]);
        var input=settings.FindProperty("activeInputHandler");if(input!=null)input.intValue=2;settings.ApplyModifiedPropertiesWithoutUndo();
        ConfigureXR();
        var plugin=(PluginImporter)AssetImporter.GetAtPath("Assets/IronHand/Plugins/iOS/IronHandVision.mm");plugin.SetCompatibleWithAnyPlatform(false);plugin.SetCompatibleWithEditor(false);plugin.SetCompatibleWithPlatform(BuildTarget.iOS,true);plugin.SaveAndReimport();
        var scene=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);new GameObject("IronHand Game").AddComponent<IronHandGame>();EditorSceneManager.SaveScene(scene,"Assets/Scenes/IronHand.unity");
        EditorBuildSettings.scenes=new[]{new EditorBuildSettingsScene("Assets/Scenes/IronHand.unity",true)};
        AssetDatabase.SaveAssets();AssetDatabase.Refresh();ValidateAsset();Debug.Log("IRONHAND_PREPARED");
    }
    static void ConfigureXR()
    {
        var path="Assets/Settings/XRSettings.asset";var all=AssetDatabase.LoadAssetAtPath<XRGeneralSettingsPerBuildTarget>(path);
        if(!all){all=ScriptableObject.CreateInstance<XRGeneralSettingsPerBuildTarget>();AssetDatabase.CreateAsset(all,path);}
        EditorBuildSettings.AddConfigObject(XRGeneralSettings.k_SettingsKey,all,true);
        if(!all.HasManagerSettingsForBuildTarget(BuildTargetGroup.iOS))all.CreateDefaultManagerSettingsForBuildTarget(BuildTargetGroup.iOS);
        var general=all.SettingsForBuildTarget(BuildTargetGroup.iOS);general.InitManagerOnStart=true;
        if(!XRPackageMetadataStore.AssignLoader(general.Manager,"UnityEngine.XR.ARKit.ARKitLoader",BuildTargetGroup.iOS))throw new Exception("ARKit loader assignment failed");
        var arkit=ARKitSettings.GetOrCreateSettings();arkit.requirement=ARKitSettings.Requirement.Required;arkit.faceTracking=false;
        if(!AssetDatabase.Contains(arkit))AssetDatabase.CreateAsset(arkit,"Assets/Settings/ARKitSettings.asset");ARKitSettings.currentSettings=arkit;
        EditorUtility.SetDirty(all);EditorUtility.SetDirty(general);EditorUtility.SetDirty(general.Manager);
        // ARKit's batch preprocessor is itself guarded by this symbol. Persist it
        // before the separate iOS build process so its native plug-ins are copied.
        var defines=PlayerSettings.GetScriptingDefineSymbols(NamedBuildTarget.iOS).Split(';').Where(s=>!string.IsNullOrEmpty(s)).ToList();
        if(!defines.Contains("UNITY_XR_ARKIT_LOADER_ENABLED"))defines.Add("UNITY_XR_ARKIT_LOADER_ENABLED");
        PlayerSettings.SetScriptingDefineSymbols(NamedBuildTarget.iOS,string.Join(";",defines));
    }
    public static void ConfigureIOSBuild(){ConfigureXR();AssetDatabase.SaveAssets();}
    [MenuItem("IronHand/Validate imported hand")]
    public static void ValidateAsset()
    {
        var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(Root+"Hand.fbx");if(!prefab)throw new Exception("Hand missing");
        var skin=prefab.GetComponentsInChildren<SkinnedMeshRenderer>();
        if(skin.Length!=1||skin[0].bones.Length<16)throw new Exception("Hand skin/bones missing");
        var joints=prefab.GetComponentsInChildren<Transform>().Select(t=>t.name).ToArray();
        if(!joints.Contains("Hand.R")||!joints.Contains("Little.Tip.R"))throw new Exception("Rig mapping missing");
        Debug.Log("IRONHAND_ASSET_VALID bones="+skin[0].bones.Length+" vertices="+skin[0].sharedMesh.vertexCount+" bounds="+skin[0].sharedMesh.bounds);
    }
    [MenuItem("IronHand/Build Mac simulation")]
    public static void BuildMac()=>Build(BuildTarget.StandaloneOSX,"../Builds/Mac/IronHand.app");
    [MenuItem("IronHand/Export iOS Xcode project")]
    public static void BuildIOS()
    {
#if !UNITY_IOS || !UNITY_XR_ARKIT_LOADER_ENABLED
        throw new BuildFailedException("Run ConfigureIOSBuild, then restart Unity with -buildTarget iOS before building.");
#else
        Build(BuildTarget.iOS,"../Builds/iOS");
        string pbx=File.ReadAllText("../Builds/iOS/Unity-iPhone.xcodeproj/project.pbxproj");
        if(!pbx.Contains("libUnityARKit.a")||!pbx.Contains("UnityARKit.m"))throw new BuildFailedException("ARKit native plug-in missing from Xcode export.");
#endif
    }
    static void Build(BuildTarget target,string location)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(location));
        var r=BuildPipeline.BuildPlayer(new BuildPlayerOptions {scenes=new[]{"Assets/Scenes/IronHand.unity"},target=target,locationPathName=location,options=target==BuildTarget.iOS?BuildOptions.None:BuildOptions.Development});
        if(r.summary.result!=BuildResult.Succeeded)throw new Exception("Build failed: "+r.summary.result);
        Debug.Log("IRONHAND_BUILD_SUCCESS "+target+" "+r.summary.totalSize);
    }
}
