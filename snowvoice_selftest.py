"""Windows frozen-app smoke check; never access stored credentials or the API."""
import json
from pathlib import Path
import sys
import traceback


def run_self_test(report_path):
    report = {"ok": False, "frozen": bool(getattr(sys, "frozen", False)), "checks": []}
    root = None
    try:
        import tkinter as tk
        import sounddevice as sd
        import keyring.backends.Windows
        from opencc import OpenCC
        from PIL import Image
        import pystray._win32
        import pynput.keyboard._win32
        from openai import OpenAI

        assert sys.platform == "win32", "Windows only"
        assert OpenCC("s2twp").convert("软件") == "軟體"
        report["checks"].append("OpenCC dictionaries")
        assert sd.get_portaudio_version()[0] > 0
        report["checks"].append("PortAudio DLL (no recording)")
        assert keyring.backends.Windows.WinVaultKeyring.priority > 0
        report["checks"].append("Windows Credential Manager backend (no key access)")
        assert OpenAI is not None
        report["checks"].append("OpenAI, pynput and pystray imports (no network)")
        base = Path(__file__).resolve().parent
        with Image.open(base / "SnowVoice_logo.png") as logo:
            logo.load()
        report["checks"].append("Bundled branding")
        root = tk.Tk()
        from __main__ import SnowVoice, DEFAULT_CONFIG
        app = SnowVoice.__new__(SnowVoice)
        app.root = root
        app.cfg = DEFAULT_CONFIG.copy()
        app.get_api_key = lambda: None
        app.show_settings()
        root.update()
        from PIL import ImageGrab
        x, y = root.winfo_rootx(), root.winfo_rooty()
        ImageGrab.grab(bbox=(x, y, x + root.winfo_width(), y + root.winfo_height())).save(
            Path(report_path).with_suffix(".png"))
        report["checks"].append("Actual settings window (empty config, no saved key access)")
        report["ok"] = True
    except Exception:
        report["error"] = traceback.format_exc()
    finally:
        if root is not None:
            root.destroy()
        Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["ok"] else 1
