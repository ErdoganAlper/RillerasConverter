; Inno Setup script — wraps dist\RillerasConverter.exe in a Windows installer.
; Build with:  build.bat   (it calls ISCC automatically when Inno Setup is present)
; Get Inno Setup from https://jrsoftware.org/isdl.php

#define AppName        "Rilleras Converter"
#define AppVersion     "2.0.0"
#define AppPublisher   "ErdoganAlper"
#define AppExeName     "RillerasConverter.exe"

[Setup]
AppId={{9C1B4E2A-7F3D-4B6E-9A21-5D8C0F1E4A73}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=Output
OutputBaseFilename=RillerasConverterSetup
SetupIconFile=..\convert.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
; Per-user install needs no admin rights.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Files]
Source: "..\dist\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.md";          DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#AppName}";        Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}";  Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; settings.json is written next to the executable at runtime.
Type: files; Name: "{app}\settings.json"
