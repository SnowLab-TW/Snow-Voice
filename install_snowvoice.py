"""Per-user Windows installer. Startup is opt-in via --startup."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

BASE = Path(__file__).resolve().parent
INSTALL_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "SnowVoicePure" / "App"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
FILES = ("SnowVoice.pyw", "snowvoice_core.py", "snowvoice_control.py", "requirements.txt")


def main():
    if sys.platform != "win32":
        raise SystemExit("SnowVoice Ver 1.2 requires Windows.")
    if sys.version_info < (3, 11):
        raise SystemExit("Install Python 3.11 or newer first.")
    import winreg
    for name in FILES:
        if not (BASE / name).is_file():
            raise SystemExit(f"Missing package file: {name}")
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    # Refuse an active app rather than replace files underneath it.
    import socket
    try:
        with socket.create_connection(("127.0.0.1", 47854), timeout=0.5):
            raise SystemExit("Close SnowVoice Ver 1.2 from its tray menu before reinstalling.")
    except OSError:
        pass
    env_dir = INSTALL_DIR / ".venv"
    venv.EnvBuilder(with_pip=True).create(env_dir)
    python = env_dir / "Scripts" / "python.exe"
    pythonw = env_dir / "Scripts" / "pythonw.exe"
    subprocess.run([str(python), "-m", "pip", "install", "-r", str(BASE / "requirements.txt")], check=True)
    for name in FILES:
        source, dest = BASE / name, INSTALL_DIR / name
        if source.resolve() != dest.resolve():
            shutil.copy2(source, dest)
    if "--startup" in sys.argv:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            command = subprocess.list2cmdline([str(pythonw), str(INSTALL_DIR / "SnowVoice.pyw"), "--startup"])
            winreg.SetValueEx(key, "SnowVoicePure", 0, winreg.REG_SZ, command)
    subprocess.Popen([str(pythonw), str(INSTALL_DIR / "SnowVoice.pyw"), "--settings"], cwd=INSTALL_DIR)
    print("Installed SnowVoice Ver 1.2. Startup enabled only when --startup was supplied.")


if __name__ == "__main__":
    main()
