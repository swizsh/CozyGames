[app]

title = Cozy Games
package.name = CozyGames
package.domain = org.cozygames
source.dir = .
source.include_exts = py,png,jpg,ttf
version = 1.0.0
requirements = python3,pygame
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.2.0
fullscreen = 1
android.api = 34
android.minapi = 21
android.ndk = 27
android.sdk = 34
android.archs = arm64-v8a
android.gradle_dependencies = androidx.appcompat:appcompat:1.6.1
android.wakelock = True
android.enable_androidx = True
android.add_src =
android.permissions = VIBRATE
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/icon.png
android.presplash_color = #F5F5DC
android.native_services = False
android.disable_aerogear = True
android.use_saucelabs = False

[buildozer]
log_level = 2
warn_on_root = 1

# ---------------------------------------------------------------------------
# BUILD INSTRUCTIONS
# ---------------------------------------------------------------------------
#
# Windows — Use WSL (Ubuntu):
#   1. Install WSL:  wsl --install -d Ubuntu
#   2. In WSL:
#      sudo apt update && sudo apt install -y python3 python3-pip git \
#        zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev \
#        libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
#      pip3 install --user buildozer cython
#   3. Copy path (inside WSL):
#      cd /mnt/c/Users/Ultra\ Dell/Desktop/TETRIS
#   4. Build:
#      buildozer android debug
#
# First build downloads SDK/NDK (~2 GB) + cross-compiles Python & pygame
# for ARM64.  Expect 30-60 minutes.
#
# APK output: bin/CozyGames-1.0.0-arm64-v8a-debug.apk
# Copy to phone and install.
#
# ---------------------------------------------------------------------------
