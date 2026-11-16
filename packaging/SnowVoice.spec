# Build on Windows x64. Do not include configs, credentials, recordings or screenshots.
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, copy_metadata

root = Path(SPECPATH).parent
datas = [(str(root / "SnowVoice_logo.png"), "."), (str(root / "packaging" / "SnowVoice.ico"), ".")]
datas += collect_data_files("opencc")
datas += collect_data_files("_sounddevice_data")
datas += copy_metadata("keyring", recursive=True)
binaries = collect_dynamic_libs("_sounddevice_data")
a = Analysis(
    [str(root / "SnowVoice.pyw")], pathex=[str(root)],
    binaries=binaries, datas=datas,
    hiddenimports=["keyring.backends.Windows", "win32timezone", "pystray._win32",
                   "pynput.keyboard._win32", "pynput.mouse._win32", "snowvoice_selftest"],
    hookspath=[], runtime_hooks=[], excludes=["pytest"], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="SnowVoice",
          debug=False, strip=False, upx=False, console=False,
          icon=str(root / "packaging" / "SnowVoice.ico"))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="SnowVoice")
