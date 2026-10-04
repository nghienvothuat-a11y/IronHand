#if UNITY_IOS
using System.IO;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEditor.iOS.Xcode;

public static class IOSPostBuild
{
    [PostProcessBuild(100)]
    public static void Configure(BuildTarget target,string path)
    {
        if(target!=BuildTarget.iOS)return;
        string projectPath=PBXProject.GetPBXProjectPath(path);var project=new PBXProject();project.ReadFromFile(projectPath);
        string framework=project.GetUnityFrameworkTargetGuid();
        foreach(var name in new[]{"Vision.framework","CoreGraphics.framework","QuartzCore.framework","UIKit.framework","AVFoundation.framework"})project.AddFrameworkToProject(framework,name,false);
        string file=project.FindFileGuidByProjectPath("Libraries/IronHand/Plugins/iOS/IronHandVision.mm");
        if(!string.IsNullOrEmpty(file))project.SetCompileFlagsForFile(framework,file,new System.Collections.Generic.List<string>{"-fobjc-arc"});
        project.SetBuildProperty(framework,"CLANG_CXX_LANGUAGE_STANDARD","c++17");project.WriteToFile(projectPath);
        var plist=new PlistDocument();string p=Path.Combine(path,"Info.plist");plist.ReadFromFile(p);
        plist.root.SetBoolean("ITSAppUsesNonExemptEncryption",false);plist.WriteToFile(p);
    }
}
#endif
