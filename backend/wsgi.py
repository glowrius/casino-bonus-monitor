import sys, threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from combined import app, MEMBERSHIP_DIR, load_approved_users, save_approved_users
from combined import monitor_loop, daily_freebies_loop, claim_scheduler_loop, flood_discord_last_24h

approved = load_approved_users()
KNOWN_IDS = ["695697021868310669", "186105992252096512", "222898514789662721",
             "741378521460637773", "1389284552442253352"]
for did in KNOWN_IDS:
    if did not in approved["discord_ids"]:
        approved["discord_ids"].append(did)
save_approved_users(approved)

MEMBERSHIP_DIR.mkdir(exist_ok=True)
if not (MEMBERSHIP_DIR / "index.html").exists():
    with open(MEMBERSHIP_DIR / "index.html", "w") as f:
        f.write("")

threading.Thread(target=monitor_loop, daemon=True).start()
threading.Thread(target=daily_freebies_loop, daemon=True).start()
threading.Thread(target=claim_scheduler_loop, daemon=True).start()
threading.Thread(target=flood_discord_last_24h, daemon=True).start()
