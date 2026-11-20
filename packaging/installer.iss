; Inno Setup script - builds PersonalAssistant-Setup-<version>.exe
; iscc /DAppVersion=1.0.0 packaging\installer.iss

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6B0D4C3E-9E43-4E43-9C55-7D1D7A6F2A11}
AppName=Personal Assistant
AppVersion={#AppVersion}
AppPublisher=Personal Assistant
DefaultDirName={localappdata}\Programs\PersonalAssistant
DefaultGroupName=Personal Assistant
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=PersonalAssistant-Setup-{#AppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\PersonalAssistant.exe
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Shortcuts:"
Name: "startup"; Description: "Start automatically when I sign in to Windows (always listening)"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "..\dist\PersonalAssistant\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Personal Assistant"; Filename: "{app}\PersonalAssistant.exe"
Name: "{autodesktop}\Personal Assistant"; Filename: "{app}\PersonalAssistant.exe"; Tasks: desktopicon
Name: "{userstartup}\Personal Assistant"; Filename: "{app}\PersonalAssistant.exe"; Tasks: startup

[Run]
Filename: "{app}\PersonalAssistant.exe"; Description: "Launch Personal Assistant"; Flags: nowait postinstall skipifsilent
