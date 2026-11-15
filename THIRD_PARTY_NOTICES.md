# Third-party notices

## Hushpad

Copyright (C) 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad contributors

Director: 황경진 Kyeongjin Hwang  
Contact: wind2sp@9rowpar.com

Hushpad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Everything in `hushpad_app/`, `hushpad_main.py`, `assets/`, `website/`, `marketing/` and `tests/` was written for Hushpad and is covered by the copyright above. This includes the app icon, the UI icons (`hushpad_app/icons.py`, drawn for Hushpad), the website, the promotional images and videos, and the background music (synthesized by `marketing/video/make_music.py`, no samples). The Hushpad name and logo are additionally trademarks (see NOTICE).

The source code for each release is the Git tag of the same name (for example `v1.0.0`) at https://github.com/wind2sp/hushpad, also attached to each GitHub release as "Source code".

## Components distributed in the release builds

The Windows build (`Hushpad-win64.zip`) and the macOS build (`Hushpad-macos-arm64.zip`) bundle the components below, unmodified. The full license texts are in the `licenses/` folder of each build and of this repository (see [licenses/README.txt](licenses/README.txt)).

| Component | Version | License | License text | Source |
| --- | --- | --- | --- | --- |
| Qt for Python: PySide6, shiboken6 | 6.12.0 | LGPL-3.0-only | `licenses/LGPL-3.0.txt` + `LICENSE` (GPL-3.0) | https://code.qt.io/cgit/pyside/pyside-setup.git (tag v6.12.0) |
| Qt libraries: Core, Gui, Widgets, Network, OpenGL, Svg, Multimedia, MultimediaWidgets (macOS also: Concurrent, DBus) | 6.12.0 | LGPL-3.0-only | `licenses/LGPL-3.0.txt` + `LICENSE` | https://download.qt.io/official_releases/qt/6.12/6.12.0/ |
| Qt plugins: platforms (windows / cocoa, offscreen), styles, image formats (gif, ico, jpeg, svg), icon engines (svg), multimedia (FFmpeg backend; Windows Media backend on Windows; Darwin backend on macOS) | 6.12.0 | LGPL-3.0-only | as above | as above |
| Third-party code inside Qt: FreeType, libjpeg-turbo (Independent JPEG Group), libpng, zlib, PCRE2, HarfBuzz, double-conversion, md4c and others | as shipped in Qt 6.12.0 | FreeType License, IJG, libpng, zlib, BSD-3-Clause, MIT and similar | `licenses/Qt-third-party.txt` | Qt source above; full list: https://doc.qt.io/qt-6/licenses-used-in-qt.html |
| FFmpeg 9.0.1 libraries used by Qt Multimedia: libavcodec 63, libavformat 63, libavutil 61, libswscale 10, libswresample 7 (built without GPL or non-free components) | 9.0.1 | LGPL-2.1-or-later | `licenses/LGPL-2.1.txt` | https://ffmpeg.org/releases/ — see the written offer below |
| cryptography (includes a statically linked OpenSSL 3) | 48.0.0 | Apache-2.0 OR BSD-3-Clause; OpenSSL: Apache-2.0 | `licenses/cryptography-LICENSE.txt`, `licenses/Apache-2.0.txt`, `licenses/cryptography-BSD-3-Clause.txt` | https://github.com/pyca/cryptography |
| cffi | 2.0.0 | MIT | `licenses/cffi-MIT.txt` | https://github.com/python-cffi/cffi |
| Python runtime | 3.14 | PSF-2.0 | `licenses/Python-PSF-2.0.txt` | https://www.python.org/downloads/source/ |
| Code included in the Python runtime: OpenSSL 3 (`libssl`/`libcrypto`), libffi, expat, mpdecimal, mimalloc, HACL*, zstd and others | as shipped with Python 3.14 | Apache-2.0, MIT, BSD-style (see file) | `licenses/Python-incorporated-software.txt`, `licenses/Apache-2.0.txt`, `licenses/libffi-MIT.txt`, `licenses/zstd-BSD-3-Clause.txt` | Python source above |
| PyInstaller bootloader | 6.19.0 | GPL-2.0-or-later with the PyInstaller bootloader exception | `licenses/PyInstaller-COPYING.txt` | https://github.com/pyinstaller/pyinstaller |
| Microsoft Visual C++ runtime and Universal C Runtime (Windows build only: `VCRUNTIME140*`, `MSVCP140*`, `ucrtbase.dll`, `api-ms-win-*.dll`) | 14.x / 10.0 | Microsoft Visual C++ Redistributable and Windows SDK redistribution terms | — | https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist |

Not distributed: Pillow (used only at build time to draw the icons) and pycparser (build-time dependency of cffi; its license is kept in `licenses/` for reference). Qt Virtual Keyboard, Qt QML/Quick, the Mesa software OpenGL renderer, unused image-format/platform/touch/TLS/network-information plugins and Qt's own OpenSSL copy are removed from the builds by `build.py`.

Acknowledgements: This software is based in part on the work of the Independent JPEG Group. Portions of this software are copyright © The FreeType Project (www.freetype.org). All rights reserved.

### LGPL: replacing the libraries

Qt, PySide6/shiboken6 and the FFmpeg libraries are shipped as separate shared libraries that Hushpad links to dynamically. You may replace them with your own (modified) builds:

- Windows: the `.dll` files in `Hushpad/_internal/PySide6/` and `Hushpad/_internal/shiboken6/`.
- macOS: the frameworks and `.dylib` files inside `Hushpad.app/Contents/Frameworks/`. The app is ad-hoc signed, so after replacing a library re-sign it with `codesign --force --deep --sign - Hushpad.app`.

You can also run Hushpad from source with any PySide6 installation (`pip install -r requirements.txt`, then `python hushpad_main.py`) or rebuild it with `python build.py`.

### Written offer for LGPL source code

For at least three years after we distribute a Hushpad release, NINEROW partners Co., Ltd. will give anyone who asks a complete machine-readable copy of the corresponding source code of the LGPL components included in that release (Qt 6.12.0, PySide6/shiboken6 6.12.0 and FFmpeg 9.0.1), for no more than the cost of providing it. Write to wind2sp@9rowpar.com and name the Hushpad version.

## Fonts

Hushpad does not bundle fonts. It uses fonts installed on your system (for example Malgun Gothic, Segoe UI, D2Coding, Consolas on Windows; Apple SD Gothic Neo, Hiragino, PingFang on macOS). The website also uses system fonts only.

## Trademarks

Windows, Notepad and OneDrive are trademarks of Microsoft Corporation. macOS and Mac are trademarks of Apple Inc. Qt is a trademark of The Qt Company Ltd. Dropbox is a trademark of Dropbox, Inc. Other names are trademarks of their respective owners and are used only to describe compatibility. Hushpad is not affiliated with or endorsed by Microsoft, Apple, The Qt Company or Dropbox.
