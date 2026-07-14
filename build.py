#!/usr/bin/env python3
"""Build script — creates a single-file executable via PyInstaller.

Usage:
    python build.py            # build for current OS
    python build.py --onedir   # build as a directory (faster startup)

On Windows the result is  dist/SIMH_Panel.exe
On macOS  the result is  dist/SIMH_Panel
On Linux  the result is  dist/SIMH_Panel
"""
import subprocess
import sys
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SPEC = os.path.join(ROOT, "simh_panel.spec")


def main():
    onedir = "--onedir" in sys.argv

    if shutil.which("pyinstaller") is None:
        print("PyInstaller не найден. Установите: pip install pyinstaller")
        sys.exit(1)

    cmd = ["pyinstaller", "--clean", "--noconfirm"]

    if onedir:
        cmd += [
            "--name", "SIMH_Panel",
            "--noconsole",
            "--add-data", f"config{os.pathsep}config",
            "main.py",
        ]
    else:
        cmd += [SPEC]

    print(f">>> {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)

    if result.returncode == 0:
        print("\n=== Сборка завершена ===")
        dist = os.path.join(ROOT, "dist")
        for name in os.listdir(dist):
            full = os.path.join(dist, name)
            size = os.path.getsize(full) if os.path.isfile(full) else "dir"
            print(f"  {name}  ({size})")
        print(f"\nИсполняемый файл: {dist}")
    else:
        print("\n!!! Ошибка сборки", file=sys.stderr)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
