$ErrorActionPreference = 'Stop'
python -m pip install --upgrade pip
if ($LASTEXITCODE) { throw 'pip upgrade failed' }
python -m pip install -r requirements.txt 'pyinstaller>=6.16,<7'
if ($LASTEXITCODE) { throw 'Dependency installation failed' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE) { throw 'Offline tests failed' }
python -m compileall -q SnowVoice.pyw snowvoice_core.py snowvoice_selftest.py
if ($LASTEXITCODE) { throw 'Compilation failed' }
python packaging/prepare_assets.py
if ($LASTEXITCODE) { throw 'Asset preparation failed' }
python -m PyInstaller --clean --noconfirm packaging/SnowVoice.spec
if ($LASTEXITCODE) { throw 'PyInstaller failed' }
Copy-Item packaging/INSTALL_NOTES.txt dist/SnowVoice/INSTALL_NOTES.txt
Copy-Item packaging/RELEASE_NOTES.md dist/SnowVoice/RELEASE_NOTES.md
python packaging/dependency_notices.py
if ($LASTEXITCODE) { throw 'Dependency notices failed' }
$compiler = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (!(Test-Path $compiler)) { throw 'Inno Setup 6 is required' }
& $compiler packaging/SnowVoice.iss
if ($LASTEXITCODE) { throw 'Inno Setup failed' }
