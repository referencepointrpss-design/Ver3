# Build APK Steps - Survey Office Manager

This package has been checked for the common build blockers we found earlier.

## Important build settings already included

The `buildozer.spec` file already contains:

```ini
android.minapi = 24
android.ndk_api = 24
android.debug_artifact = apk
```

This avoids the Python `remote_debugging.o / pwritev` error that happened with API 23.

## Build in Ubuntu / WSL

Open Ubuntu and run:

```bash
source ~/buildozer_env/bin/activate
cd ~/projects/survey_equipment_apk_ready
python3 prebuild_check.py
buildozer -v android debug
```

Or run the included helper script:

```bash
source ~/buildozer_env/bin/activate
cd ~/projects/survey_equipment_apk_ready
./build_apk.sh
```

## Copy APK to Windows Downloads

After the build succeeds:

```bash
cp bin/*.apk /mnt/c/Users/nocha/Downloads/
```

## If GitHub download fails again

That is an internet/WSL connection problem, not an app-code problem. Re-run the same build command after fixing the connection or using another network/VPN.

## If Buildozer uses old cached build files

Use:

```bash
rm -rf .buildozer/android/platform/build-*
rm -rf .buildozer/android/platform/dists/surveyofficemanager
buildozer -v android debug
```

Avoid deleting `~/.buildozer` unless you want to download Android SDK/NDK again.
