# Third-party notices

## Hushpad

Copyright (C) 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad contributors

Director: 황경진 Kyeongjin Hwang  
Contact: wind2sp@9rowpar.com

Hushpad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Everything in `hushpad_app/`, `hushpad_main.py`, `assets/`, `website/`, `marketing/` and `tests/` was written for Hushpad and is covered by the copyright above. The app icon and brand artwork are GPL-licensed works like the rest of the source; the Hushpad name and logo are additionally trademarks (see NOTICE).

## Components distributed in the release builds

The Windows build (`Hushpad-win64.zip`) and the macOS build (`Hushpad-macos-arm64.zip`) bundle the components below, unmodified. The full license texts are included in the `licenses/` folder of each build and of this repository (see [licenses/README.txt](licenses/README.txt)).

| Component | Version | License | License text | Source |
| --- | --- | --- | --- | --- |
| Qt for Python: PySide6, shiboken6 | 6.12.0 | LGPL-3.0-only | `licenses/LGPL-3.0.txt` + `LICENSE` (GPL-3.0) | https://code.qt.io/cgit/pyside/pyside-setup.git (tag v6.12.0) |
| Qt libraries: Core, Gui, Widgets, Network, OpenGL, Svg, Multimedia, MultimediaWidgets, and their platform, style, image-format, icon-engine, TLS, network-information, input-context and multimedia plugins | 6.12.0 | LGPL-3.0-only | `licenses/LGPL-3.0.txt` + `LICENSE` | https://download.qt.io/official_releases/qt/6.12/ |
| Third-party code inside Qt (e.g. zlib, libpng, libjpeg, FreeType, HarfBuzz, PCRE2, double-conversion) | as shipped in Qt 6.12.0 | various permissive licenses | https://doc.qt.io/qt-6/licenses-used-in-qt.html | Qt source above |
| FFmpeg libraries used by Qt Multimedia: libavcodec, libavformat (63.1.101), libavutil (61), libswscale (10), libswresample (7) | as shipped with PySide6 6.12.0 | LGPL-2.1-or-later | `licenses/LGPL-2.1.txt` | https://ffmpeg.org/download.html — see the written offer below |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | `licenses/cryptography-LICENSE.txt`, `licenses/Apache-2.0.txt`, `licenses/cryptography-BSD-3-Clause.txt` | https://github.com/pyca/cryptography |
| OpenSSL (inside cryptography and the Python runtime) | 3.x | Apache-2.0 | `licenses/Apache-2.0.txt` | https://www.openssl.org/source/ |
| cffi | 2.0.0 | MIT | `licenses/cffi-MIT.txt` | https://github.com/python-cffi/cffi |
| pycparser | 3.0 | BSD-3-Clause | `licenses/pycparser-BSD-3-Clause.txt` | https://github.com/eliben/pycparser |
| libffi | 3.x (bundled with Python) | MIT | `licenses/libffi-MIT.txt` | https://github.com/libffi/libffi |
| Python runtime | 3.14 | PSF-2.0 (and the licenses listed in it) | `licenses/Python-PSF-2.0.txt` | https://www.python.org/downloads/source/ |
| PyInstaller bootloader | 6.19.0 | GPL-2.0-or-later with the PyInstaller bootloader exception | `licenses/PyInstaller-COPYING.txt` | https://github.com/pyinstaller/pyinstaller |
| Microsoft Visual C++ runtime (Windows build only: VCRUNTIME140*, MSVCP140*) | 14.x | Microsoft Visual C++ Redistributable license terms | — | https://learn.microsoft.com/cpp/windows/latest-supported-vc-redist |

Not distributed: Pillow is used only at build time to draw the icons. Qt Virtual Keyboard, Qt QML/Quick and the Mesa software OpenGL renderer that PySide6 would otherwise pull in are removed from the builds by `build.py`.

### LGPL: replacing the libraries

Qt, PySide6 and the FFmpeg libraries are shipped as separate shared libraries that Hushpad links to dynamically. You may replace them with your own (modified) builds: on Windows they are the `.dll` files in `Hushpad/_internal/PySide6/` and `Hushpad/_internal/shiboken6/`; on macOS they are the frameworks and `.dylib` files inside `Hushpad.app/Contents/Frameworks/`. You can also run Hushpad from source with any PySide6 installation (`python hushpad_main.py`) or rebuild it with `python build.py`.

### Written offer for FFmpeg source

For at least three years after we distribute a Hushpad release, NINEROW partners Co., Ltd. will give anyone who asks a complete machine-readable copy of the source code of the FFmpeg libraries included in that release, for no more than the cost of providing it. Write to wind2sp@9rowpar.com and name the Hushpad version.

## Fonts

Hushpad does not bundle fonts. It uses fonts installed on your system (for example Malgun Gothic, Segoe UI, D2Coding, Consolas on Windows; Apple SD Gothic Neo, Hiragino, PingFang on macOS).

## Trademarks

Windows is a trademark of Microsoft Corporation. macOS and Mac are trademarks of Apple Inc. Qt is a trademark of The Qt Company Ltd. Hushpad is not affiliated with or endorsed by Microsoft, Apple or The Qt Company.
