"""Flask API'sini ve PyQt arayüzünü birlikte başlatır.

Proje kökünden çalıştırılır:  python app.py
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def api_baslat():
    """Flask sunucusunu ayrı bir süreçte başlatır."""
    ortam = dict(os.environ, PYTHONPATH=str(PROJECT_ROOT))
    return subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "api" / "main.py")],
        cwd=str(PROJECT_ROOT),
        env=ortam,
    )


def main():
    api = api_baslat()
    try:
        from gui.gui_pyqt import main as arayuz_baslat

        arayuz_baslat()
    finally:
        api.terminate()


if __name__ == "__main__":
    main()
