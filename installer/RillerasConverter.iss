; Inno Setup script — builds RillerasConverterSetup.exe.
;
; Payload is the one-folder PyInstaller build in dist\RillerasConverter\, so the
; installed app starts immediately instead of unpacking itself on every launch.
; The user still only ever handles a single Setup.exe.
;
; Built automatically by build.bat. Inno Setup: https://jrsoftware.org/isdl.php

#define AppName        "Rilleras Converter"
#define AppVersion     "2.0.0"
#define AppPublisher   "ErdoganAlper"
#define AppExeName     "RillerasConverter.exe"

[Setup]
AppId={{9C1B4E2A-7F3D-4B6E-9A21-5D8C0F1E4A73}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=RillerasConverterSetup
SetupIconFile=..\convert.ico
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ArchitecturesAllowed=x64compatible
; Installs per-user by default, so no admin prompt is needed. The user can
; still choose an all-users install, which is why settings.json lives in
; %APPDATA% rather than next to the executable.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
DisableDirPage=no
DisableReadyPage=no
; Refuse to run on top of a copy that is currently open.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; The whole one-folder build, including the nested _internal directory.
Source: "..\dist\RillerasConverter\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#AppName}";       Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Saved preferences — the app writes these at runtime, so Inno does not track them.
Type: filesandordirs; Name: "{userappdata}\RillerasConverter"
