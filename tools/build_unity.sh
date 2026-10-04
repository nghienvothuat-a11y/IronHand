#!/bin/bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
unity_bin="${IRONHAND_UNITY_EDITOR:-/Applications/Unity/Hub/Editor/6000.3.19f1/Unity.app/Contents/MacOS/Unity}"
mkdir -p "$project_root/tmp"
common=(-batchmode -nographics -projectPath "$project_root/Unity")
case "${1:-prepare}" in
  prepare) "$unity_bin" "${common[@]}" -executeMethod PrototypeBuilder.Prepare -quit -logFile "$project_root/tmp/unity-prepare.log" ;;
  test) "$unity_bin" "${common[@]}" -runTests -testPlatform EditMode -testResults "$project_root/tmp/editmode-results.xml" -logFile "$project_root/tmp/unity-tests.log" ;;
  mac) "$unity_bin" "${common[@]}" -executeMethod PrototypeBuilder.BuildMac -quit -logFile "$project_root/tmp/unity-build-mac.log" ;;
  ios)
    "$unity_bin" "${common[@]}" -buildTarget iOS -executeMethod PrototypeBuilder.ConfigureIOSBuild -quit -logFile "$project_root/tmp/unity-configure-ios.log"
    "$unity_bin" "${common[@]}" -buildTarget iOS -executeMethod PrototypeBuilder.BuildIOS -quit -logFile "$project_root/tmp/unity-build-ios.log" ;;
  *) echo 'Usage: tools/build_unity.sh prepare|test|mac|ios' >&2; exit 2 ;;
esac
