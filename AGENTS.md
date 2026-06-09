# Session Summary

## Goal
Maintain a crypto membership purchase site (GitHub Pages) + desktop GUI app ("Claims Casino - Automation Suite") for auto-claiming sweepstakes casino bonuses, with license-key activation and GitHub Releases auto-updater.

## Site Details
- Dark theme, gold accents, Inter font, floating orbs, fade-in animations, glass-effect cards, 120×120 logo.webp
- Multi-crypto: BTC, ETH, USDC, USDT, SOL, BNB (3-column grid)
- Pricing: $299.99/mo Monthly, $4999.99 Lifetime, $349.99/mo Elite
- Payment: confirm → invoice + QR + live BTC price → polls mempool.space every 15s
- Nav: fixed glass nav with profile icon → dropdown (Profile/Payments/Settings/Log Out) or Login/Signup modal

## What's Built

### Site (`docs/index.html`)
- Hero with coinflip logo animation (backface-visibility + transform-style: 3d)
- Benefits section (4 profit cards), How It Works (3 steps), FAQ accordion
- Crypto payment grid: BTC, ETH, USDC, USDT, SOL, BNB (dot+ticker style)
- Pricing cards with hover scale 1.03, gold badges, z-index fix
- Testimonials grid: 13 images from Discord with gradient overlay showing win amount + caption
- Profile dropdown: when logged in, click avatar → dropdown with Profile/Payments/Settings/Log Out
- Profile modal: email, member since, total payments/spent
- Payments modal: reads `localStorage.claims_casino_payments` array, shows invoice/plan/amount/date/status
- Settings modal: email notifications toggle (stored in localStorage)
- Auth: email/password signup/login via localStorage, data migration from old format
- Footer: `support@claimscasino.com` + copyright, no external links
- Responsive: mobile testimonial breakpoints, crypto grid stays 3-col
- Reload-to-top: `scrollRestoration='manual'` + load/pageshow listeners

### Desktop App (`gui_app.py`)
- PyQt6, renamed "Claims Casino - Automation Suite"
- LicenseDialog: frameless 600×480, draggable, validates against `license_keys.json`
- MainWindow: frameless 1200×780, custom 44px title bar (minimize/close), drag-move
- Sidebar (QListWidget) + QStackedWidget replaces QTabWidget
- Fade transition on page change via QGraphicsOpacityEffect + QPropertyAnimation
- Tray icon with context menu
- Auto-updater: checks GitHub Releases, downloads exe with QProgressDialog, PowerShell swap relaunch
- TOS hyperlink in Settings About section

### Testimonial Numbers (OCR'd from images)
| Image | Amount | Source |
|-------|--------|--------|
| t1.png | +$51.06 | Sportzino SC balance |
| t2.png | +$50.00 | yayz referral bonus |
| t3.png | +$31.50 | Rebet settings page |
| t4.png | +$24.70 | Prize Redemption |
| t5.png | +$87.35 | Success page (generic) |
| t6.png | +$45.00 | Dogg Cash page |
| t7.jpg | +$112.42 | Sportzino slots (generic) |
| t8.jpg | +$63.88 | KYC verification page |
| t9.jpg | +$28.50 | sweepjungle lobby |
| t10.jpg | +$53.87 | Lonestar SC balance |
| t11.jpg | +$21.31 | Rebet Inc win |
| t12.jpg | +$7.17 | Rebet Cash pick win |
| t13.jpg | +$22.77 | Redemption to card |

### License Keys
- 10 premium 16-char keys in `license_keys.json`, stored in `dist/` + bundled via PyInstaller
- Format: `XXXX-XXXX-XXXX-XXXX`, normalized (uppercase, strip dashes)
- Old deprecated keys: `GOLD-DEPR-2024-XXXX`, `PLAT-DEPR-2024-XXXX`

### Build
- PyInstaller: `python -m PyInstaller --onefile --windowed --icon=assets/icon.ico --add-data "license_keys.json;." --name "CasinoBot" gui_app.py`
- EXE ~50MB, in `dist/CasinoBot.exe` (gitignored)
- GitHub Actions: `.github/workflows/build.yml` auto-builds on tag push

## Git Log
- `88b6f70` - Profile dropdown menu
- `1a42f7a` - Testimonial numbers updated (OCR-extracted)
- `314c767` - Remove temp script
- `746b407` - Profile/Payments/Settings modals, fixed t4 aspect, payment history

## Pending / Blocked
- HTTPS: set custom domain `claimscasino.com` in GitHub Pages Settings
- DNS propagation for `claimscasino.com`
- Tag `v1.0.1` to trigger auto-updater build
