"""Remove only application program files/startup. Settings and credentials remain."""
import os
from pathlib import Path
import shutil
import socket
import sys
import time


def main():
    if sys.platform != "win32":
        raise SystemExit("Windows only.")
    import winreg
    install_dir = Path(os.environ["LOCALAPPDATA"]) / "SnowVoicePure" / "App"
    if Path(__file__).resolve().is_relative_to(install_dir.resolve()):
        raise SystemExit("Run uninstall from the extracted download folder, outside the installation.")
    try:
        with socket.create_connection(("127.0.0.1", 47854), timeout=1) as s:
            s.sendall(b"QUIT")
        time.sleep(2)
    except OSError:
        pass
    # Abort if app hasn't exited; never remove files beneath a running app.
    try:
        with socket.create_connection(("127.0.0.1", 47854), timeout=0.5):
            raise SystemExit("Close SnowVoice Ver 1.2 manually and retry uninstall.")
    except OSError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, "SnowVoicePure")
    except FileNotFoundError:
        pass
    if install_dir.exists():
        shutil.rmtree(install_dir)
    print("SnowVoice Ver 1.2 removed. Settings and Credential Manager key retained; see README for full removal.")


if __name__ == "__main__":
    main()
