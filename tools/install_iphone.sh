#!/bin/bash
set -euo pipefail
project_root="$(cd "$(dirname "$0")/.." && pwd)"
: "${IRONHAND_APPLE_TEAM:?Set IRONHAND_APPLE_TEAM to your Apple development team ID}"
: "${IRONHAND_DEVICE:?Set IRONHAND_DEVICE to the iPhone UDID shown in Xcode Devices}"
export DEVELOPER_DIR="${DEVELOPER_DIR:-/Applications/Xcode.app/Contents/Developer}"
xcodebuild -project "$project_root/Builds/iOS/Unity-iPhone.xcodeproj" -scheme Unity-iPhone -configuration Debug -sdk iphoneos -destination "id=$IRONHAND_DEVICE" -derivedDataPath "$project_root/Builds/Xcode" DEVELOPMENT_TEAM="$IRONHAND_APPLE_TEAM" CODE_SIGN_STYLE=Automatic -allowProvisioningUpdates -allowProvisioningDeviceRegistration build
xcrun devicectl device install app --device "$IRONHAND_DEVICE" "$project_root/Builds/Xcode/Build/Products/Debug-iphoneos/IronHand.app"
xcrun devicectl device process launch --device "$IRONHAND_DEVICE" com.nghienvothuat.ironhand
