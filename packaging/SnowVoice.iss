#define AppVersion "1.2"
[Setup]
AppId={{78C6C899-6A8A-46A3-989D-E6F908501A12}
AppName=Snow Voice
AppVersion={#AppVersion}
AppPublisher=Snow Lab
AppPublisherURL=https://github.com/eericni/Snow-Voice
AppSupportURL=https://github.com/eericni/Snow-Voice/issues
DefaultDirName={localappdata}\Programs\SnowVoice
DefaultGroupName=Snow Voice
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\release
OutputBaseFilename=SnowVoice-Setup-v1.2-x64
SetupIconFile=SnowVoice.ico
UninstallDisplayIcon={app}\SnowVoice.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
AppMutex=SnowVoice_Ver12
CloseApplications=no
RestartApplications=no
InfoBeforeFile=INSTALL_NOTES.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
Name: "startup"; Description: "Start Snow Voice when I sign in to Windows"; Flags: unchecked

[Files]
Source: "..\dist\SnowVoice\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Snow Voice"; Filename: "{app}\SnowVoice.exe"; Parameters: "--settings"
Name: "{group}\Uninstall Snow Voice"; Filename: "{uninstallexe}"
Name: "{userdesktop}\Snow Voice"; Filename: "{app}\SnowVoice.exe"; Parameters: "--settings"; Tasks: desktopicon
Name: "{userstartup}\Snow Voice"; Filename: "{app}\SnowVoice.exe"; Parameters: "--startup"; Tasks: startup

[Run]
Filename: "{app}\SnowVoice.exe"; Parameters: "--settings"; Description: "Launch Snow Voice"; Flags: nowait postinstall skipifsilent
