
import os
import sys
import json
import time
import wave
import socket
import tempfile
import threading
import ctypes
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

import keyring
import numpy as np
import pyperclip
import sounddevice as sd
from openai import OpenAI
from pynput import keyboard
from opencc import OpenCC
import pystray
from PIL import Image, ImageTk, ImageDraw
from snowvoice_core import valid_key_shape, format_transcript, error_message

APP_NAME = "SnowVoice"
APP_VERSION = "1.2"
KEYRING_SERVICE = "SnowVoicePure_OpenAI"
KEYRING_USER = "default"

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "int16"
IPC_HOST = "127.0.0.1"
IPC_PORT = 47854

APPDATA = Path(os.getenv("APPDATA", Path.home()))
DATA_DIR = APPDATA / "SnowVoicePure"
DATA_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = DATA_DIR / "config.json"
LOG_PATH = DATA_DIR / "SnowVoice.log"

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "SnowVoice_logo.png"
ICON_PATH = BASE_DIR / "SnowVoice.ico"

CC = OpenCC("s2twp")

DEFAULT_KEYWORDS = ""

DEFAULT_CONFIG = {
    "model": "gpt-transcribe",
    "language": "zh",
    "auto_paste": False,
    "force_zh_tw": True,
    "keywords": DEFAULT_KEYWORDS,
}


def log(message):
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + " | " + str(message) + "\n")
    except Exception:
        pass


def install_exception_hook():
    def handler(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        log("Unhandled exception: " + exc_type.__name__)
    sys.excepthook = handler


install_exception_hook()


def load_config():
    for path in (CONFIG_PATH,):
        if path.exists():
            try:
                saved = json.loads(path.read_text(encoding="utf-8"))
                cfg = DEFAULT_CONFIG.copy()
                cfg.update({k: v for k, v in saved.items() if k in DEFAULT_CONFIG})
                return cfg
            except Exception as exc:
                log(f"Could not read config {path}: {type(exc).__name__}")
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    CONFIG_PATH.write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_brand_image(size):
    if LOGO_PATH.is_file():
        with Image.open(LOGO_PATH) as logo:
            return logo.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
    # Code-drawn neutral icon; no personal photos or image metadata.
    img = Image.new("RGBA", (128, 128), "#102238")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((48, 18, 80, 77), radius=16, fill="#75d4ee")
    draw.arc((33, 43, 95, 96), 0, 180, fill="white", width=7)
    draw.line((64, 95, 64, 111), fill="white", width=7)
    draw.line((44, 111, 84, 111), fill="white", width=7)
    return img.resize((size, size), Image.Resampling.LANCZOS)


class SnowVoice:
    def __init__(self, ipc_socket, show_settings_on_start=False):
        self.cfg = load_config()
        self.ipc_socket = ipc_socket

        self.frames = []
        self.stream = None
        self.recording = False
        self.transcribing = False
        self.hotkey_down = False
        self.keys_down = set()

        self.root = tk.Tk()
        self.root.withdraw()
        self.root.protocol("WM_DELETE_WINDOW", self.hide_settings)

        # Proper small app icon; never insert the full-size logo into layout.
        try:
            self.root.iconbitmap(default=str(ICON_PATH))
        except Exception:
            try:
                title_img = load_brand_image(64)
                self._title_icon = ImageTk.PhotoImage(title_img)
                self.root.iconphoto(True, self._title_icon)
            except Exception:
                pass

        self.tray = pystray.Icon(
            APP_NAME,
            load_brand_image(64),
            APP_NAME,
            menu=pystray.Menu(
                pystray.MenuItem("開啟設定", self._tray_open_settings),
                pystray.MenuItem("設定 / 更新 API Key", self._tray_api_key),
                pystray.MenuItem("測試錄音", self._tray_test_recording),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("結束 SnowVoice", self._tray_quit),
            )
        )

        self.keyboard_listener = None
        self._start_keyboard_listener()

        threading.Thread(target=self._ipc_loop, daemon=True).start()

        api_exists = bool(self.get_api_key())
        if show_settings_on_start or not api_exists:
            self.root.after(250, self.show_settings)

        if not api_exists:
            # First run should never hide the API entry point.
            self.root.after(700, self.set_api_key)

    # ---------------- API Key ----------------
    def get_api_key(self):
        key = keyring.get_password(KEYRING_SERVICE, KEYRING_USER)
        if key:
            return key

        return None

    def set_api_key(self):
        win = tk.Toplevel(self.root)
        win.title("SnowVoice — OpenAI API Key")
        win.geometry("560x205")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()

        ttk.Label(
            win,
            text="OpenAI API Key",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=18, pady=(16, 4))

        ttk.Label(
            win,
            text="貼上 sk-... / sk-proj-... API Key。Key 會存入 Windows Credential Manager。",
            wraplength=520
        ).pack(anchor="w", padx=18, pady=(0, 10))

        key_var = tk.StringVar()
        entry = ttk.Entry(win, textvariable=key_var, show="•", width=68)
        entry.pack(fill="x", padx=18)
        entry.focus_set()

        button_row = ttk.Frame(win)
        button_row.pack(fill="x", padx=18, pady=16)

        def save():
            key = key_var.get().strip()
            if not valid_key_shape(key):
                messagebox.showwarning(
                    "SnowVoice", "請貼上完整 sk- 開頭的 Secret Key，不能使用 key_ Tracking ID。", parent=win
                )
                return
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USER, key)
                messagebox.showinfo(
                    "SnowVoice", "API Key 已儲存；格式檢查通過，尚未連線驗證。", parent=win
                )
                win.destroy()
                self.show_settings()
            except Exception as exc:
                messagebox.showerror(
                    "SnowVoice",
                    f"API Key 儲存失敗：\n{type(exc).__name__}",
                    parent=win
                )

        ttk.Button(button_row, text="儲存 API Key", command=save).pack(side="left")
        ttk.Button(button_row, text="取消", command=win.destroy).pack(side="right")

    # ---------------- Push-to-talk ----------------
    def _start_keyboard_listener(self):
        ctrl_variants = {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r}
        alt_variants = {
            keyboard.Key.alt, keyboard.Key.alt_l,
            keyboard.Key.alt_r, keyboard.Key.alt_gr
        }
        target = keyboard.Key.f12

        def combo_active():
            return (
                any(k in self.keys_down for k in ctrl_variants)
                and any(k in self.keys_down for k in alt_variants)
                and target in self.keys_down
            )

        def on_press(key):
            self.keys_down.add(key)
            if combo_active() and not self.hotkey_down:
                self.hotkey_down = True
                self.root.after(0, self.start_recording)

        def on_release(key):
            self.keys_down.discard(key)
            if self.hotkey_down and not combo_active():
                self.hotkey_down = False
                self.root.after(0, self.stop_recording)

        self.keyboard_listener = keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )
        self.keyboard_listener.start()

    # ---------------- Audio ----------------
    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            log(f"Audio status: {status}")
        if self.recording:
            if self.recorded_frames < SAMPLE_RATE * 120:
                self.frames.append(indata.copy())
                self.recorded_frames += frames
            elif not self.limit_queued:
                self.limit_queued = True
                self.root.after(0, self.stop_recording)

    def start_recording(self):
        if self.recording or self.transcribing:
            return

        if not self.get_api_key():
            self.show_settings()
            self.set_api_key()
            return

        self.paste_target = ctypes.windll.user32.GetForegroundWindow()
        self.frames = []
        self.recorded_frames = 0
        self.limit_queued = False
        try:
            self.stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=self._audio_callback,
            )
            self.stream.start()
            self.recording = True
            self.tray.title = "SnowVoice — 錄音中"
        except Exception as exc:
            if self.stream is not None:
                self.stream.close()
                self.stream = None
            log(f"Microphone error: {type(exc).__name__}")
            messagebox.showerror(
                "SnowVoice",
                f"無法啟動麥克風：\n{type(exc).__name__}"
            )

    def stop_recording(self):
        if not self.recording:
            return

        self.recording = False

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        except Exception as exc:
            log(f"Closing stream: {type(exc).__name__}")
        finally:
            self.stream = None

        self.tray.title = APP_NAME

        if not self.frames:
            return

        self.transcribing = True
        self.tray.title = "SnowVoice Ver 1.2 — 轉錄中"
        threading.Thread(
            target=self._transcribe_worker,
            daemon=True
        ).start()

    def _write_wav(self):
        audio = np.concatenate(self.frames, axis=0)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp.close()

        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(np.dtype(DTYPE).itemsize)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())

        return tmp.name

    def _transcribe_worker(self):
        wav_path = None

        try:
            key = self.get_api_key()
            if not key:
                return

            client = OpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=60.0, max_retries=0)
            wav_path = self._write_wav()

            prompt = (
                "請將語音逐字轉錄成繁體中文（台灣），不要使用簡體中文。"
                "不要摘要，不要自行改寫原意。"
                "英文技術名詞、縮寫、品牌名請保留英文原文與正確大小寫。"
                "使用台灣常用標點與用字。"
                "如果整段語音明顯是問句，句尾使用問號；"
                "保留正常的句尾標點。"
            )

            keywords = self.cfg.get("keywords", "").strip()
            if keywords:
                prompt += " 重要詞彙：" + keywords

            with open(wav_path, "rb") as audio_file:
                result = client.audio.transcriptions.create(
                    model=self.cfg.get("model", "gpt-transcribe"),
                    file=audio_file,
                    language=self.cfg.get("language", "zh") or "zh",
                    prompt=prompt,
                )

            text = (getattr(result, "text", None) or "").strip()
            if not text:
                return

            if self.cfg.get("force_zh_tw", True):
                text = CC.convert(text)

            text = format_transcript(text)
            pyperclip.copy(text)
            self.tray.title = "SnowVoice Ver 1.2 — 已複製，請貼上"

            if self.cfg.get("auto_paste", False):
                time.sleep(0.10)
                if ctypes.windll.user32.GetForegroundWindow() != self.paste_target:
                    self.tray.title = "SnowVoice Ver 1.2 — 已複製，請手動貼上"
                    return
                kb = keyboard.Controller()
                with kb.pressed(keyboard.Key.ctrl):
                    kb.press("v")
                    kb.release("v")

        except Exception as exc:
            log("Transcription failed: " + type(exc).__name__)
            msg = error_message(exc)
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "SnowVoice 轉錄失敗", msg
                )
            )
        finally:
            if wav_path:
                try:
                    os.remove(wav_path)
                except OSError:
                    pass
            self.transcribing = False
            self.frames = []

    # ---------------- Settings window ----------------
    def show_settings(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.title(f"SnowVoice Ver {APP_VERSION}")
        self.root.geometry("700x620")
        self.root.minsize(650, 570)

        for child in self.root.winfo_children():
            child.destroy()

        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=18, pady=(16, 6))

        try:
            brand = load_brand_image(86)
            self._settings_logo = ImageTk.PhotoImage(brand)
            ttk.Label(header, image=self._settings_logo).pack(
                side="left", padx=(0, 12)
            )
        except Exception as exc:
            log(f"Settings logo error: {type(exc).__name__}")

        title_box = ttk.Frame(header)
        title_box.pack(side="left", fill="y")

        ttk.Label(
            title_box,
            text=f"SnowVoice Ver {APP_VERSION}",
            font=("Segoe UI", 19, "bold")
        ).pack(anchor="w", pady=(8, 1))

        ttk.Label(
            title_box,
            text="按住 Ctrl + Alt + F12 說話，放開後複製文字；預設手動貼上。",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        # API section is always visible near the top.
        api_frame = ttk.LabelFrame(self.root, text="OpenAI API")
        api_frame.pack(fill="x", padx=18, pady=8)

        api_status = "已儲存（尚未驗證）" if self.get_api_key() else "⚠ 尚未設定"
        ttk.Label(
            api_frame,
            text=f"API Key：{api_status}",
            font=("Segoe UI", 10, "bold")
        ).pack(side="left", padx=12, pady=11)

        ttk.Button(
            api_frame,
            text="設定 / 更新 API Key",
            command=self.set_api_key
        ).pack(side="right", padx=12, pady=8)

        settings = ttk.LabelFrame(self.root, text="語音設定")
        settings.pack(fill="x", padx=18, pady=8)

        model_var = tk.StringVar(
            value=self.cfg.get("model", "gpt-transcribe")
        )
        language_var = tk.StringVar(
            value=self.cfg.get("language", "zh")
        )
        auto_paste_var = tk.BooleanVar(
            value=self.cfg.get("auto_paste", False)
        )
        force_tw_var = tk.BooleanVar(
            value=self.cfg.get("force_zh_tw", True)
        )

        row = ttk.Frame(settings)
        row.pack(fill="x", padx=12, pady=7)
        ttk.Label(row, text="模型", width=14).pack(side="left")
        ttk.Combobox(
            row,
            textvariable=model_var,
            state="normal",
            width=28,
            values=[
                "gpt-transcribe",
            ]
        ).pack(side="left")

        row = ttk.Frame(settings)
        row.pack(fill="x", padx=12, pady=7)
        ttk.Label(row, text="語言", width=14).pack(side="left")
        ttk.Entry(row, textvariable=language_var, width=12).pack(side="left")
        ttk.Label(
            row, text="繁體中文請維持 zh"
        ).pack(side="left", padx=8)

        row = ttk.Frame(settings)
        row.pack(fill="x", padx=12, pady=7)
        ttk.Label(row, text="Push-to-talk", width=14).pack(side="left")
        ttk.Label(
            row,
            text="Ctrl + Alt + F12　（按住錄音 / 放開送出）"
        ).pack(side="left")

        row = ttk.Frame(settings)
        row.pack(fill="x", padx=12, pady=5)
        ttk.Checkbutton(
            row,
            text="自動貼上（選用：等待時請勿切換游標或視窗）",
            variable=auto_paste_var
        ).pack(side="left")

        row = ttk.Frame(settings)
        row.pack(fill="x", padx=12, pady=5)
        ttk.Checkbutton(
            row,
            text="強制轉換成台灣繁體中文",
            variable=force_tw_var
        ).pack(side="left")

        keywords_frame = ttk.LabelFrame(
            self.root, text="關鍵詞 / 專有名詞"
        )
        keywords_frame.pack(
            fill="both", expand=True, padx=18, pady=8
        )

        keywords_text = tk.Text(
            keywords_frame, height=7, wrap="word"
        )
        keywords_text.pack(
            fill="both", expand=True, padx=10, pady=10
        )
        keywords_text.insert(
            "1.0",
            self.cfg.get("keywords", DEFAULT_KEYWORDS)
        )

        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=18, pady=(4, 14))

        def save():
            self.cfg["model"] = model_var.get()
            self.cfg["language"] = language_var.get().strip() or "zh"
            self.cfg["auto_paste"] = bool(auto_paste_var.get())
            self.cfg["force_zh_tw"] = bool(force_tw_var.get())
            self.cfg["keywords"] = keywords_text.get(
                "1.0", "end"
            ).strip()
            save_config(self.cfg)
            messagebox.showinfo(
                "SnowVoice", "設定已儲存。", parent=self.root
            )

        ttk.Button(
            bottom, text="儲存設定", command=save
        ).pack(side="left")

        ttk.Button(
            bottom,
            text="隱藏到系統匣",
            command=self.hide_settings
        ).pack(side="right")

    def hide_settings(self):
        self.root.withdraw()

    # ---------------- Local IPC ----------------
    def _ipc_loop(self):
        while True:
            try:
                conn, _ = self.ipc_socket.accept()
                conn.settimeout(1.0)
                data = conn.recv(128).decode(
                    "utf-8", errors="ignore"
                ).strip().upper()
                conn.close()

                if data == "SHOW":
                    self.root.after(0, self.show_settings)
                elif data == "API":
                    self.root.after(0, self.set_api_key)
                elif data == "QUIT":
                    self.root.after(0, self.quit_app)
                    return
            except OSError:
                return
            except Exception as exc:
                log(f"IPC error: {type(exc).__name__}")

    # ---------------- Tray actions ----------------
    def _tray_open_settings(self, icon, item):
        self.root.after(0, self.show_settings)

    def _tray_api_key(self, icon, item):
        self.root.after(0, self.set_api_key)

    def _tray_test_recording(self, icon, item):
        if self.recording:
            self.root.after(0, self.stop_recording)
        else:
            self.root.after(0, self.start_recording)

    def _tray_quit(self, icon, item):
        self.root.after(0, self.quit_app)

    def quit_app(self):
        if self.transcribing:
            messagebox.showinfo("SnowVoice Ver 1.2", "正在轉錄，請稍候完成後再結束。")
            return
        try:
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        except Exception:
            pass

        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass

        try:
            self.ipc_socket.close()
        except Exception:
            pass

        try:
            self.tray.stop()
        except Exception:
            pass

        self.root.quit()
        self.root.destroy()

    def run(self):
        threading.Thread(
            target=self.tray.run, daemon=True
        ).start()
        self.root.mainloop()


def send_existing_instance(command):
    try:
        with socket.create_connection(
            (IPC_HOST, IPC_PORT), timeout=0.7
        ) as s:
            s.sendall(command.encode("utf-8"))
        return True
    except OSError:
        return False


def main():
    # Offline packaging check: no credentials, microphone capture or API requests.
    if "--self-test" in sys.argv:
        from snowvoice_selftest import run_self_test
        index = sys.argv.index("--self-test")
        raise SystemExit(run_self_test(Path(sys.argv[index + 1])))

    show_settings = "--settings" in sys.argv
    startup_mode = "--startup" in sys.argv

    # Give Windows a moment to finish login/session initialization.
    if startup_mode:
        time.sleep(6)

    ipc_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM
    )
    try:
        ipc_socket.bind((IPC_HOST, IPC_PORT))
        ipc_socket.listen(4)
    except OSError:
        # SnowVoice is already running.
        send_existing_instance("SHOW" if show_settings else "SHOW")
        return

    # Inno Setup checks this mutex before replacing/removing a running app.
    ctypes.windll.kernel32.CreateMutexW.restype = ctypes.c_void_p
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "SnowVoice_Ver12")
    log(f"SnowVoice Ver {APP_VERSION} starting")
    try:
        SnowVoice(
            ipc_socket=ipc_socket,
            show_settings_on_start=show_settings
        ).run()
    except Exception:
        log("Fatal application error")
        raise
    finally:
        if mutex:
            ctypes.windll.kernel32.CloseHandle(ctypes.c_void_p(mutex))


if __name__ == "__main__":
    main()
