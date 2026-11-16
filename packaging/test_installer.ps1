$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force test-results | Out-Null
function Test-FrozenApp([string]$exe, [string]$reportName) {
    $report = Join-Path (Resolve-Path test-results) $reportName
    $p = Start-Process -FilePath $exe -ArgumentList "--self-test `"$report`"" -PassThru
    if (!$p.WaitForExit(60000)) { $p.Kill(); throw 'Frozen app smoke test timed out' }
    if ($p.ExitCode -ne 0) {
        if (Test-Path $report) { Get-Content $report }
        throw "Frozen app smoke test failed: $($p.ExitCode)"
    }
    $result = Get-Content $report -Raw | ConvertFrom-Json
    if (!$result.ok -or !$result.frozen) { throw 'Expected successful frozen application check' }
    Get-Content $report
}
Test-FrozenApp (Resolve-Path dist/SnowVoice/SnowVoice.exe) 'before-install.json'
$installer = (Resolve-Path release/SnowVoice-Setup-v1.2-x64.exe).Path
$installLog = Join-Path (Resolve-Path test-results) 'install.log'
$p = Start-Process $installer -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /TASKS=`"`" /LOG=`"$installLog`"" -PassThru
if (!$p.WaitForExit(120000)) { $p.Kill(); throw 'Install timed out' }
if ($p.ExitCode -ne 0) { throw "Installation failed: $($p.ExitCode)" }
$installDir = Join-Path $env:LOCALAPPDATA 'Programs\SnowVoice'
Test-FrozenApp (Join-Path $installDir 'SnowVoice.exe') 'after-install.json'
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Snow Voice\Snow Voice.lnk'
if (!(Test-Path $startMenu)) { throw 'Missing Start menu shortcut' }
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\Snow Voice.lnk'
if (Test-Path $startup) { throw 'Startup must be opt-in' }
$uninstallLog = Join-Path (Resolve-Path test-results) 'uninstall.log'
$p = Start-Process (Join-Path $installDir 'unins000.exe') -ArgumentList "/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /LOG=`"$uninstallLog`"" -PassThru
if (!$p.WaitForExit(120000)) { $p.Kill(); throw 'Uninstall timed out' }
if ($p.ExitCode -ne 0) { throw "Uninstall failed: $($p.ExitCode)" }
if ((Test-Path (Join-Path $installDir 'SnowVoice.exe')) -or (Test-Path $startMenu)) { throw 'Uninstall left application files or shortcut' }
@{ok=$true; checks=@('silent install', 'installed application settings window', 'Start menu shortcut', 'startup disabled by default', 'silent uninstall')} |
    ConvertTo-Json | Set-Content -Encoding utf8 test-results/installer.json
Copy-Item dist/SnowVoice/THIRD_PARTY/manifest.json release/dependency-manifest.json
$hash = (Get-FileHash $installer -Algorithm SHA256).Hash.ToLower()
"$hash  SnowVoice-Setup-v1.2-x64.exe" | Set-Content -Encoding ascii release/SHA256SUMS.txt
