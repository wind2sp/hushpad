# Third-party notices

## Hushpad

Copyright (C) 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad contributors

Director: 황경진 Kyeongjin Hwang  
Contact: wind2sp@9rowpar.com

Hushpad is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

Everything in `hushpad_app/`, `hushpad_main.py`, `assets/`, `website/` and `marketing/` was written for Hushpad and is covered by the copyright above (the app icon and brand artwork are also trademarks, see NOTICE).

## Components distributed with the Windows and macOS builds

The released app bundles the following software. Each keeps its own license; none of them is modified by Hushpad. The Qt and PySide6 libraries are shipped as separate, replaceable shared libraries (dynamic linking), as the LGPL requires.

| Component | Version | License | Source |
| --- | --- | --- | --- |
| Qt for Python (PySide6, shiboken6) | 6.12.0 | LGPL-3.0-only | https://code.qt.io/cgit/pyside/pyside-setup.git |
| Qt (Core, Gui, Widgets, Svg, Network, Multimedia, MultimediaWidgets) | 6.12.0 | LGPL-3.0-only | https://download.qt.io/official_releases/qt/ |
| FFmpeg libraries used by Qt Multimedia (avcodec, avformat, avutil, swscale, swresample) | as shipped with PySide6 6.12.0 | LGPL-2.1-or-later | https://ffmpeg.org/download.html |
| cryptography | 48.0.0 | Apache-2.0 OR BSD-3-Clause | https://github.com/pyca/cryptography |
| OpenSSL (inside cryptography / Python) | 3.x | Apache-2.0 | https://www.openssl.org/source/ |
| cffi | 2.0.0 | MIT | https://github.com/python-cffi/cffi |
| pycparser | 3.0 | BSD-3-Clause | https://github.com/eliben/pycparser |
| Pillow (build-time icon generation only) | 12.1.1 | MIT-CMU | https://github.com/python-pillow/Pillow |
| Python runtime | 3.14 | PSF-2.0 | https://www.python.org/downloads/source/ |
| PyInstaller bootloader | 6.19 | GPL-2.0-or-later with the PyInstaller bootloader exception | https://github.com/pyinstaller/pyinstaller |

The full text of the LGPL-3.0 is available at https://www.gnu.org/licenses/lgpl-3.0.html (it builds on the GPL-3.0 text in [LICENSE](LICENSE)). The Apache-2.0, BSD-3-Clause, MIT, MIT-CMU and PSF-2.0 texts are included in the respective packages' distribution metadata inside the app bundle (`_internal/*.dist-info/`) and at the source links above.

To use a different build of Qt or PySide6 with Hushpad, install it in a Python environment and run Hushpad from source (`python hushpad_main.py`), or rebuild with `python build.py`.

## Fonts

Hushpad does not bundle fonts. It uses fonts installed on your system (for example Malgun Gothic, Segoe UI, D2Coding, Consolas on Windows; Apple SD Gothic Neo, Hiragino, PingFang on macOS).

## Trademarks

Windows is a trademark of Microsoft Corporation. macOS and Mac are trademarks of Apple Inc. Hushpad is not affiliated with or endorsed by Microsoft or Apple.
