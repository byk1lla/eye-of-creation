# Eye of Creation

**English** · [Türkçe](README.tr.md)

An ASCII cinematic loop. The camera dives into the pupil of an eye, travels through the birth of the universe, and comes back to the same eye through a black hole. It renders in real time with Python + pygame, and the same loop ships as a screensaver for **macOS, Windows and Linux**.

**EYE → CREATION → BIG BANG → GALAXY → BLACK HOLE → EYE**

![preview](docs/preview.png)

## Run it

```bash
python3 -m venv eye-env
source eye-env/bin/activate          # Windows: eye-env\Scripts\activate
pip install -r requirements.txt
python eye_of_creation.py
```

| Key | Action |
| --- | --- |
| `SPACE` | pause / resume |
| `1`–`5` | jump to a scene |
| `←` / `→` | speed |
| `C` | color mode (COLOR / MATRIX / MONO) |
| `ESC` | quit |

> On Python 3.14 the original `pygame` package ships a broken font module, so `requirements.txt` installs the drop-in compatible `pygame-ce` instead.

## Screensaver

Each screensaver plays a pre-rendered, seamless 55-second loop (`assets/EyeOfCreation.mp4`, 1920×1200). Clone or download the **whole** repository first, because the installers need the video in `assets/`.

### macOS

Requires Xcode Command Line Tools (`xcode-select --install`).

```bash
./macos/install.sh
```

The script builds `EyeOfCreation.saver`, copies it to `~/Library/Screen Savers` and opens the Screen Saver settings. Pick **Eye of Creation** from the list.

### Windows

Double-click **`windows\install.bat`**.

The script copies the screensaver and the video to `%LOCALAPPDATA%\EyeOfCreation` and opens the Screen Saver settings with Eye of Creation selected. Nothing else needs installing; it runs on the .NET Framework 4.8 that comes with Windows 10/11. Every monitor gets its own copy of the loop.

> The `.scr` isn't code-signed, so SmartScreen may warn you the first time. Click **More info → Run anyway**.

### Linux

Requires [XScreenSaver](https://www.jwz.org/xscreensaver/) and [mpv](https://mpv.io/):

```bash
sudo apt install xscreensaver mpv     # Fedora: dnf, Arch: pacman -S
./linux/install.sh
```

The script registers Eye of Creation as an XScreenSaver hack. Pick it in `xscreensaver-settings`. GNOME and KDE's built-in lock screens don't support custom screensavers, so you need XScreenSaver for this (it works best on X11).

## Re-rendering the video

If you change the code, regenerate the screensaver video (requires ffmpeg):

```bash
EOC_W=1920 EOC_H=1200 EOC_SAVER=1 python tools/record.py assets/EyeOfCreation.mp4
```

## Building the screensavers yourself

- **macOS:** `macos/build.sh` (Swift, no Xcode project needed). GitHub Actions builds it on every push, and `v*` tags attach the `.saver` to a release.
- **Windows:** `dotnet build windows -c Release`, then rename `EyeOfCreation.exe` to `EyeOfCreation.scr`. This also builds on macOS and Linux.

## Credits

- The hands in the CREATION scene come from Michelangelo's *The Creation of Adam* (Sistine Chapel, public domain). The image is embedded in the script.
- Inspired by the "Eye of Creation" reel by [@erfanxasadi](https://www.instagram.com/erfanxasadi/).
