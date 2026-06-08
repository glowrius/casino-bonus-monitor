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

[Components]
Name: "bot"; Description: "CasinoBot main program"; Types: full custom compact; Flags: fixed
Name: "dashboard"; Description: "Claim City Dashboard (Python GUI for license/cookies/claims)"; Types: full custom

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce
Name: "installcert"; Description: "Install code signing certificate (stops Windows security warnings)"; GroupDescription: "Security:"; Flags: checkedonce

[Files]
Source: "..\build\CasinoBot.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: bot
Source: "..\src\data\claim_profiles.json"; DestDir: "{app}\src\data"; Flags: ignoreversion; Components: bot
Source: "..\src\data\streamer_profiles.json"; DestDir: "{app}\src\data"; Flags: ignoreversion; Components: bot
Source: "..\src\data\license_keys.json"; DestDir: "{app}\src\data"; Flags: ignoreversion; Components: bot
Source: "..\scripts\CasinoBot.cer"; DestDir: "{app}"; Flags: ignoreversion; Components: bot
Source: "..\src\.env.example"; DestDir: "{app}"; DestName: ".env.example"; Flags: ignoreversion; Components: bot
Source: "..\build\CasinoDashboard.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: dashboard

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Components: bot
Name: "{group}\Claim City Dashboard"; Filename: "{app}\CasinoDashboard.exe"; WorkingDir: "{app}"; Components: dashboard
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; Components: bot

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: postinstall nowait skipifsilent unchecked; Components: bot
Filename: "{app}\CasinoDashboard.exe"; Description: "Launch Claim City Dashboard"; Flags: postinstall nowait skipifsilent unchecked; Components: dashboard
Filename: "certutil"; Parameters: "-addstore TrustedPublisher ""{app}\CasinoBot.cer"""; Description: "Install certificate"; Flags: runhidden postinstall skipifsilent; Tasks: installcert

[UninstallRun]
Filename: "certutil"; Parameters: "-delstore TrustedPublisher ""{app}\CasinoBot.cer"""; Flags: runhidden; Tasks: installcert

[Code]

var
  ConfigPage: TInputQueryWizardPage;
  BotToken: String;
  CmdChannelId: String;
  MonitorChannelId: String;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(
    wpSelectTasks,
    'Discord Bot Configuration',
    'Paste your Discord bot token and channel IDs below',
    'Get your bot token from https://discord.com/developers/applications. ' +
    'Channel IDs are found by right-clicking a channel → Copy ID (Developer Mode must be enabled). ' +
    'Leave blank to configure later in the .env file.'
  );

  ConfigPage.Add('Bot Token:', False);
  ConfigPage.Add('Monitor Channel ID (#monitor-posts):', False);
  ConfigPage.Add('CMD Channel ID (#cmd):', False);
  ConfigPage.Add('Streamer Channel ID (#streamer-chat):', False);
  ConfigPage.Add('Daily Claims Channel ID (#daily-claims):', False);

  ConfigPage.Values[0] := GetPreviousData('BotToken', '');
  ConfigPage.Values[1] := GetPreviousData('MonitorChannelId', '');
  ConfigPage.Values[2] := GetPreviousData('CmdChannelId', '');
  ConfigPage.Values[3] := GetPreviousData('StreamerChannelId', '');
  ConfigPage.Values[4] := GetPreviousData('DailyClaimsChannelId', '');
end;

procedure RegisterPreviousData(PreviousDataKey: Integer);
begin
  SetPreviousData(PreviousDataKey, 'BotToken', ConfigPage.Values[0]);
  SetPreviousData(PreviousDataKey, 'MonitorChannelId', ConfigPage.Values[1]);
  SetPreviousData(PreviousDataKey, 'CmdChannelId', ConfigPage.Values[2]);
  SetPreviousData(PreviousDataKey, 'StreamerChannelId', ConfigPage.Values[3]);
  SetPreviousData(PreviousDataKey, 'DailyClaimsChannelId', ConfigPage.Values[4]);
end;

function ShouldWriteEnv: Boolean;
begin
  Result := (ConfigPage.Values[0] <> '') or (ConfigPage.Values[1] <> '') or (ConfigPage.Values[2] <> '') or (ConfigPage.Values[3] <> '') or (ConfigPage.Values[4] <> '');
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  EnvFile: String;
  Lines: TArrayOfString;
begin
  if CurStep = ssPostInstall then
  begin
    if ShouldWriteEnv then
    begin
      EnvFile := ExpandConstant('{app}\.env');

      SetArrayLength(Lines, 8);
      Lines[0] := '# Casino Bonus Monitor Configuration';
      Lines[1] := 'DISCORD_BOT_TOKEN=' + ConfigPage.Values[0];
      Lines[2] := 'MONITOR_CHANNEL_ID=' + ConfigPage.Values[1];
      Lines[3] := 'CMD_CHANNEL_ID=' + ConfigPage.Values[2];
      Lines[4] := 'STREAMER_CHANNEL_ID=' + ConfigPage.Values[3];
      Lines[5] := 'DAILY_CLAIMS_CHANNEL_ID=' + ConfigPage.Values[4];
      Lines[6] := 'REDDIT_RSS_URLS=https://www.reddit.com/r/sweepstakesidehustle/.rss';
      Lines[7] := 'POLL_INTERVAL_SECONDS=10';

      if not SaveStringsToFile(EnvFile, Lines, False) then
      begin
        MsgBox('Failed to create .env file. You can create it manually after installation.', mbError, MB_OK);
      end;
    end;
  end;
end;
