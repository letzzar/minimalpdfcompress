; Inno Setup script for MinimalPDF Compress.
;
; Two install modes, chosen by the user before anything is elevated:
;
;   Install for me only   -> %LOCALAPPDATA%\Programs\MinimalPDF Compress, no UAC
;   Install for all users -> C:\Program Files\MinimalPDF Compress, UAC at that point
;
; PrivilegesRequired=lowest starts Setup unelevated, and
; PrivilegesRequiredOverridesAllowed=dialog makes Inno ask which one up front.
; Only the all-users answer triggers the elevation prompt, so the installer
; never asks for admin before the user has decided it needs it. The {auto*}
; constants then resolve to the per-user or the machine-wide location to match.
;
; Built by tools/package.py, which passes AppVersion, SourceDir and OutputDir.

#define AppName "MinimalPDF Compress"
#define AppExeName "MinimalPDF_Compress.exe"
#define AppPublisher "MinimalPDF Compress contributors"
#define AppURL "https://github.com/letzzar/minimalpdfcompress"

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef SourceDir
  #define SourceDir "..\..\dist\MinimalPDF_Compress"
#endif
#ifndef OutputDir
  #define OutputDir "..\..\dist"
#endif
#ifndef OutputBaseFilename
  #define OutputBaseFilename "MinimalPDF_Compress-setup"
#endif

[Setup]
AppId={{4CEF6330-548B-42BE-8482-18AF8E338CEF}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
VersionInfoVersion=1.10.0.0
VersionInfoDescription={#AppName} installer

PrivilegesRequired=lowest
; "dialog" is what asks the user; "commandline" additionally honours
; /CURRENTUSER and /ALLUSERS so the installer can be scripted and tested
; unattended. Neither changes the default, which stays unelevated.
PrivilegesRequiredOverridesAllowed=commandline dialog

DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=auto
AllowNoIcons=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

OutputDir={#OutputDir}
OutputBaseFilename={#OutputBaseFilename}
SetupIconFile=..\..\src\pdf.ico
LicenseFile=..\..\LICENSE.md
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
; The app is a folder build on purpose; see FORK.md. Nothing is unpacked at
; runtime, only at install time, which is what an installer is for.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Ghostscript and the optimisers write scratch files next to themselves; the
; user's own settings live in %APPDATA% and are deliberately left alone.
Type: filesandordirs; Name: "{app}\__pycache__"
