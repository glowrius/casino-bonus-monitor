; Casino Bonus Monitor Installer
; Inno Setup 6 Script

#define MyAppName "Casino Bonus Monitor"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "glowrius"
#define MyAppURL "https://glowrius.github.io/casino-bonus-monitor/"
#define MyAppExeName "CasinoBot.exe"

[Setup]
AppId={{B8F7C3A1-2D4E-5F6A-8B9C-0D1E2F3A4B5C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt
OutputDir=..\build
OutputBaseFilename=CasinoBot-Setup-{#MyAppVersion}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
WizardImageFile=WizardImage.bmp
WizardSmallImageFile=WizardSmallImage.bmp
PrivilegesRequired=admin
DisableWelcomePage=no
CloseApplications=yes
RestartApplications=no
DisableFinishedPage=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce
Name: "installcert"; Description: "Install code signing certificate (stops Windows security warnings)"; GroupDescription: "Security:"; Flags: checkedonce

[Files]
Source: "..\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\src\data\claim_profiles.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\src\data\streamer_profiles.json"; DestDir: "{app}\data"; Flags: ignoreversion
Source: "..\CasinoBot.cer"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\src\.env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent unchecked
Filename: "certutil"; Parameters: "-addstore TrustedPublisher ""{app}\CasinoBot.cer"""; Description: "Install certificate"; Flags: runhidden postinstall skipifsilent; Tasks: installcert

[UninstallRun]
Filename: "certutil"; Parameters: "-delstore TrustedPublisher ""{app}\CasinoBot.cer"""; Flags: runhidden; Tasks: installcert

[Code]

var
  WebhookPage: TInputQueryWizardPage;
  CmdWebhook: String;
  MonitorWebhook: String;

procedure InitializeWizard;
begin
  WebhookPage := CreateInputQueryPage(
    wpSelectTasks,
    'Discord Webhook Configuration',
    'Paste your Discord webhook URLs below',
    'You can find these in your Discord server settings under Integrations → Webhooks. ' +
    'Leave blank to configure later in the .env file.'
  );

  WebhookPage.Add('CMD Webhook URL (startup flood → #cmd):', False);
  WebhookPage.Add('Monitor Webhook URL (live posts → #monitor-posts):', False);

  WebhookPage.Values[0] := GetPreviousData('CmdWebhook', '');
  WebhookPage.Values[1] := GetPreviousData('MonitorWebhook', '');
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'CmdWebhook', WebhookPage.Values[0]);
  SetPreviousData(PreviousDataKey, 'MonitorWebhook', WebhookPage.Values[1]);
end;

function ShouldWriteEnv: Boolean;
begin
  Result := (WebhookPage.Values[0] <> '') or (WebhookPage.Values[1] <> '');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: String;
  Lines: TArrayOfString;
  I: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    if ShouldWriteEnv then
    begin
      EnvFile := ExpandConstant('{app}\.env');

      SetArrayLength(Lines, 5);
      Lines[0] := '# Casino Bonus Monitor Configuration';
      Lines[1] := 'DISCORD_WEBHOOK_CMD=' + WebhookPage.Values[0];
      Lines[2] := 'DISCORD_WEBHOOK_MONITOR=' + WebhookPage.Values[1];
      Lines[3] := 'CMD_CHANNEL_ID=';
      Lines[4] := 'MONITOR_CHANNEL_ID=';

      if not SaveStringsToFile(EnvFile, Lines, False) then
      begin
        MsgBox('Failed to create .env file. You can create it manually after installation.', mbError, MB_OK);
      end;
    end;
  end;
end;
