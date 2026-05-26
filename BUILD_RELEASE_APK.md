# Build a signed release APK - Survey Office Manager

Use this after the debug APK works correctly on your phone.

## 1) Activate your Buildozer environment

```bash
source ~/buildozer_env/bin/activate
cd ~/projects/survey_equipment_apk_ready
```

## 2) Create a keystore once

Keep this file and password safe. You need the same keystore for future updates.

```bash
keytool -genkey -v \
  -keystore survey_office_release.keystore \
  -alias surveyoffice \
  -keyalg RSA -keysize 2048 -validity 10000
```

## 3) Build release APK

```bash
buildozer -v android release
```

## 4) Sign the APK manually if Buildozer outputs an unsigned APK

Find the unsigned APK:

```bash
ls bin/*release*.apk
```

Then sign it:

```bash
export ANDROID_HOME=$HOME/.buildozer/android/platform/android-sdk
$ANDROID_HOME/build-tools/*/zipalign -p 4 bin/*release*.apk surveyoffice-aligned.apk
$ANDROID_HOME/build-tools/*/apksigner sign \
  --ks survey_office_release.keystore \
  --ks-key-alias surveyoffice \
  --out surveyoffice-release-signed.apk \
  surveyoffice-aligned.apk
```

Check signature:

```bash
$ANDROID_HOME/build-tools/*/apksigner verify --verbose surveyoffice-release-signed.apk
```

Copy to Windows Downloads:

```bash
cp surveyoffice-release-signed.apk /mnt/c/Users/nocha/Downloads/
```
