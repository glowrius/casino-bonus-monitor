<div align="center">
  <img src="https://glowrius.github.io/casino-bonus-monitor/" alt="Casino Bonus Monitor" width="80">
  <h1>Casino Bonus Monitor</h1>
  <p><strong>One program. Every free SC opportunity. Real-time Discord delivery.</strong></p>
  <p>
    <a href="https://glowrius.github.io/casino-bonus-monitor/">Website</a> ·
    <a href="https://github.com/glowrius/casino-bonus-monitor/releases">Download</a> ·
    <a href="#quick-start">Quick Start</a>
  </p>
  <p>
    <a href="https://github.com/glowrius/casino-bonus-monitor/releases/latest"><img src="https://img.shields.io/github/v/release/glowrius/casino-bonus-monitor?label=Download&color=FFD700&style=for-the-badge" alt="Download"></a>
  </p>
  <br>
</div>

## Features

- **🎰 Auto-Claim Daily SC** — Automatically collects 24h free Sweepscash from social casinos
- **🔗 Free Spins & SC Monitors** — Real-time Reddit scanning for no-deposit bonuses and promo codes
- **🎯 Streamer Link Sniping** — Watches Kick.com chats for dropped giveaways and bonus links
- **🚀 Startup Flood** — Replays last 24h of posts on every launch
- **⚡ Real-time Delivery** — New posts land within 10 seconds with role pings

## Quick Start

1. [Download the latest installer](https://github.com/glowrius/casino-bonus-monitor/releases)
2. Run `CasinoBot-Setup-v2.0.0.exe`
3. Paste your Discord webhook URLs during setup
4. Done — posts start flowing immediately

## Discord Setup

1. Create two webhooks in your Discord server:
   - **#cmd** channel → receives startup flood (last 24h)
   - **#monitor-posts** channel → receives real-time alerts
2. Create the `@Monitor Pings` role for notifications
3. Paste webhook URLs during installation

## Pushing Updates

Tag a commit and push — GitHub Actions builds + releases automatically:

```powershell
git add .
git commit -m "Add new feature"
git tag v2.1.0
git push origin v2.1.0
```

All running instances auto-update within 24 hours.

## Manual Build

```powershell
.\scripts\build.ps1           # Builds CasinoBot.exe
.\scripts\build-installer.ps1  # Builds CasinoBot-Setup.exe
.\scripts\release.ps1          # Creates GitHub Release
```

## License

MIT
