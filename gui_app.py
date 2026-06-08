#!/usr/bin/env python3
"""
Casino Automation Suite Desktop App
License-activated GUI for auto-claiming daily free SC from 80+ casinos,
Reddit sweepstakes monitoring, and Discord alert integration.
"""

import sys, os, json, time, threading, hashlib, webbrowser, subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ── Data directory (alongside exe/script) ──
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

sys.path.insert(0, str(BASE_DIR))

import combined

# Override combined paths to live next to exe
combined.SCRIPT_DIR = BASE_DIR
combined.SITES_FILE = BASE_DIR / "sites.json"
combined.ACCOUNTS_FILE = BASE_DIR / "accounts.json"
combined.LICENSE_KEYS_FILE = BASE_DIR / "license_keys.json"
meipass_keys = Path(getattr(sys, "_MEIPASS", ".")) / "license_keys.json"
if meipass_keys.exists() and not combined.LICENSE_KEYS_FILE.exists():
    combined.LICENSE_KEYS_FILE = meipass_keys
combined.CLAIM_SCHEDULE_FILE = BASE_DIR / "claim_schedule.json"
combined.APPROVED_USERS_FILE = BASE_DIR / "approved_users.json"
combined.ADMIN_USERS_FILE = BASE_DIR / "admin_users.json"

if not combined.SITES_FILE.exists():
    combined.save_sites(combined.DEFAULT_SITES)

# ── PyQt6 ──
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QTextEdit,
    QCheckBox, QSpinBox, QGroupBox, QFormLayout, QStatusBar,
    QSystemTrayIcon, QMenu, QFrame, QListWidget, QStackedWidget, QProgressDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction, QPixmap, QPainter, QFontDatabase

# ═══════════════════════════════════════════════════════════════
# STYLESHEET
# ═══════════════════════════════════════════════════════════════

DARK_SS = """
QListWidget {
    background: #1a1a1e; border: none; border-right: 1px solid #2a2a2e;
    color: #888; font-size: 14px; font-weight: 600; outline: none;
    padding: 8px 0; min-width: 200px; max-width: 200px;
    border-bottom-left-radius: 12px;
}
QListWidget::item {
    padding: 14px 20px; border-left: 3px solid transparent;
}
QListWidget::item:selected {
    background: #1f1f24; color: #FFD700; border-left: 3px solid #FFD700;
}
QListWidget::item:hover:!selected {
    background: #222228; color: #ccc; border-left: 3px solid #3a3a3e;
}
QMainWindow, QDialog { background: #111114; color: #e0e0e8; border: 1px solid #3a3a3e; border-radius: 12px; }
QWidget { background: #111114; color: #e0e0e8; }
QTabWidget::pane { border: 1px solid #2a2a2e; background: #111114; }
QTabBar::tab {
    background: #1c1c21; color: #888; padding: 10px 24px;
    border: 1px solid #2a2a2e; border-bottom: none;
    border-top-left-radius: 6px; border-top-right-radius: 6px;
    font-weight: 600; font-size: 13px;
}
QTabBar::tab:selected { background: #111114; color: #FFD700; border-bottom: 2px solid #FFD700; }
QTabBar::tab:hover:!selected { color: #ccc; }
QPushButton {
    background: #2a2a2e; color: #e0e0e8; border: 1px solid #3a3a3e;
    border-radius: 10px; padding: 10px 24px; font-size: 13px; font-weight: 600;
}
QPushButton:hover { background: #3a3a3e; border-color: #FFD700; }
QPushButton:pressed { background: #222; }
QPushButton#gold { background: #FFD700; color: #111; border-color: #FFD700; font-weight: 700; }
QPushButton#gold:hover { background: #ffe44d; }
QPushButton#danger { background: #ef4444; color: #fff; border-color: #ef4444; }
QPushButton#danger:hover { background: #dc2626; }
QPushButton#success { background: #22c55e; color: #fff; border-color: #22c55e; }
QPushButton:disabled { background: #1a1a1e; color: #555; border-color: #2a2a2e; }
QLineEdit {
    background: #1c1c21; color: #e0e0e8; border: 1px solid #2a2a2e;
    border-radius: 10px; padding: 10px 14px; font-size: 14px;
}
QLineEdit:focus { border-color: #FFD700; }
QTableWidget {
    background: #1c1c21; color: #e0e0e8; border: 1px solid #2a2a2e;
    border-radius: 10px; gridline-color: #2a2a2e; font-size: 13px;
}
QTableWidget::item { padding: 8px; }
QTableWidget::item:selected { background: #2a2a2e; color: #FFD700; }
QHeaderView::section {
    background: #222226; color: #FFD700; padding: 10px; border: none;
    border-bottom: 2px solid #FFD700; font-weight: 700; font-size: 12px;
}
QLabel#title { font-size: 24px; font-weight: 800; color: #FFD700; }
QLabel#subtitle { font-size: 14px; color: #888; }
QLabel#statv { font-size: 28px; font-weight: 800; color: #FFD700; }
QLabel#statl { font-size: 12px; color: #888; letter-spacing: 1px; }
QCheckBox { color: #e0e0e8; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #2a2a2e; border-radius: 4px; background: #1c1c21; }
QCheckBox::indicator:checked { background: #FFD700; border-color: #FFD700; }
QSpinBox { background: #1c1c21; color: #e0e0e8; border: 1px solid #2a2a2e; border-radius: 8px; padding: 8px; font-size: 13px; }
QGroupBox { border: 1px solid #2a2a2e; border-radius: 10px; margin-top: 16px; padding: 20px 16px 16px; font-weight: 700; font-size: 13px; color: #FFD700; }
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 8px; }
QTextEdit { background: #0a0a0e; color: #b0b0b8; border: 1px solid #2a2a2e; border-radius: 8px; padding: 12px; font-family: Consolas,Courier New,monospace; font-size: 12px; }
QStatusBar { background: #1c1c21; color: #888; border-top: 1px solid #2a2a2e; font-size: 12px; }
QStatusBar::item { border: none; }
QScrollBar:vertical { background: #1c1c21; width: 10px; border-radius: 5px; }
QScrollBar::handle:vertical { background: #3a3a3e; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
"""

# ═══════════════════════════════════════════════════════════════
# WIDGETS
# ═══════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, label, initial="0", color="#FFD700"):
        super().__init__()
        self.setObjectName("sc")
        self.setStyleSheet(f"#sc{{background:#1c1c21;border:1px solid #2a2a2e;border-radius:12px;padding:20px;}}")
        lo = QVBoxLayout()
        lo.setContentsMargins(16, 12, 16, 12)
        lo.setSpacing(4)
        self.v = QLabel(initial)
        self.v.setObjectName("statv")
        self.v.setStyleSheet(f"font-size:34px;font-weight:800;color:{color};")
        lo.addWidget(self.v)
        l = QLabel(label)
        l.setObjectName("statl")
        lo.addWidget(l)
        self.setLayout(lo)
    def set_val(self, x): self.v.setText(str(x))

# ═══════════════════════════════════════════════════════════════
# LICENSE DIALOG
# ═══════════════════════════════════════════════════════════════

class LicenseDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claims Casino - Automation Suite")
        self.setFixedSize(600, 480)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        lo = QVBoxLayout()
        lo.setContentsMargins(40, 40, 40, 40)
        lo.setSpacing(16)

        t = QLabel("CLAIMS CASINO")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size:42px;font-weight:800;color:#FFD700;letter-spacing:4px;")
        lo.addWidget(t)

        s = QLabel("License Activation Required")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setObjectName("subtitle")
        lo.addWidget(s)
        lo.addSpacing(16)

        self.k = QLineEdit()
        self.k.setPlaceholderText("Enter license key (XXXX-XXXX-XXXX-XXXX)")
        self.k.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.k.setStyleSheet("font-size:22px;font-weight:700;letter-spacing:2px;padding:16px;border-radius:10px;")
        lo.addWidget(self.k)

        self.st = QLabel("")
        self.st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.st.setStyleSheet("font-size:13px;")
        lo.addWidget(self.st)

        b = QPushButton("ACTIVATE LICENSE")
        b.setObjectName("gold")
        b.setStyleSheet("font-size:18px;font-weight:700;padding:16px;border-radius:10px;letter-spacing:2px;")
        b.clicked.connect(self.go)
        lo.addWidget(b)
        lo.addStretch()

        i = QLabel("Don't have a license? Contact support on Discord.")
        i.setAlignment(Qt.AlignmentFlag.AlignCenter)
        i.setStyleSheet("color:#555;font-size:11px;")
        lo.addWidget(i)
        self.setLayout(lo)
        self.k.returnPressed.connect(self.go)
        self.dragPos = None

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.dragPos = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self.dragPos is not None:
            self.move(self.pos() + e.globalPosition().toPoint() - self.dragPos)
            self.dragPos = e.globalPosition().toPoint()
            e.accept()

    def mouseReleaseEvent(self, e):
        self.dragPos = None

    def go(self):
        key = self.k.text().strip()
        if not key:
            self.st.setText("Enter a license key.")
            self.st.setStyleSheet("color:#ef4444;font-size:13px;")
            return
        result = combined.validate_license_key(key)
        if result.get("valid"):
            with open(BASE_DIR / "license.dat", "w") as f:
                json.dump({"key": key, "tier": result.get("tier"), "at": time.time()}, f)
            self.accept()
        else:
            r = result.get("reason", "Invalid key")
            self.st.setText(f"Failed: {r}")
            self.st.setStyleSheet("color:#ef4444;font-size:13px;font-weight:600;")

# ═══════════════════════════════════════════════════════════════
# CLAIM WORKER THREAD
# ═══════════════════════════════════════════════════════════════

class ClaimWorker(QThread):
    log = pyqtSignal(str)
    done = pyqtSignal(str, bool, float)

    def __init__(self, domain, username, password):
        super().__init__()
        self.domain = domain
        self.username = username
        self.password = password

    def run(self):
        self.log.emit(f"[{datetime.now():%H:%M:%S}] Starting claim for {self.domain}...")
        try:
            auto = combined.CasinoAutomation(headless=combined.HEADLESS_MODE)
            if not auto.start():
                self.log.emit(f"[{datetime.now():%H:%M:%S}] ❌ Browser failed for {self.domain}")
                self.done.emit(self.domain, False, 0); return
            self.log.emit(f"[{datetime.now():%H:%M:%S}] Logging into {self.domain}...")
            if auto.login(self.domain, self.username, self.password):
                self.log.emit(f"[{datetime.now():%H:%M:%S}] ✅ Logged in. Claiming...")
                sc = auto.claim_daily_bonus(self.domain)
                auto.close()
                if sc > 0:
                    sched = combined.load_claim_schedule()
                    sched[self.domain] = {"last_claim": time.time(), "status": "done"}
                    combined.save_claim_schedule(sched)
                    self.log.emit(f"[{datetime.now():%H:%M:%S}] ✅ Claimed {sc} SC at {self.domain}")
                    self.done.emit(self.domain, True, sc)
                else:
                    self.log.emit(f"[{datetime.now():%H:%M:%S}] ⚠ No SC at {self.domain}")
                    self.done.emit(self.domain, False, 0)
            else:
                auto.close()
                self.log.emit(f"[{datetime.now():%H:%M:%S}] ❌ Login failed for {self.domain}")
                self.done.emit(self.domain, False, 0)
        except Exception as e:
            self.log.emit(f"[{datetime.now():%H:%M:%S}] ❌ Error: {e}")
            self.done.emit(self.domain, False, 0)

# ═══════════════════════════════════════════════════════════════
# DASHBOARD TAB
# ═══════════════════════════════════════════════════════════════

class DashboardTab(QWidget):
    def __init__(self, logfn):
        super().__init__()
        self.logfn = logfn
        lo = QVBoxLayout()
        lo.setContentsMargins(24, 24, 24, 24)
        lo.setSpacing(20)

        t = QLabel("Dashboard")
        t.setObjectName("title")
        lo.addWidget(t)

        g = QHBoxLayout()
        g.setSpacing(16)
        self.c1 = StatCard("Total SC Claimed", "$0.00", "#22c55e")
        self.c2 = StatCard("Claims Today", "0")
        self.c3 = StatCard("Alerts Sent", "0")
        self.c4 = StatCard("Uptime", "0h 0m")
        g.addWidget(self.c1); g.addWidget(self.c2); g.addWidget(self.c3); g.addWidget(self.c4)
        lo.addLayout(g)

        c = QHBoxLayout(); c.setSpacing(12)
        self.stlbl = QLabel("● OFFLINE")
        self.stlbl.setStyleSheet("color:#ef4444;font-size:16px;font-weight:700;")
        c.addWidget(self.stlbl); c.addStretch()
        self.tgl = QPushButton("START MONITORING")
        self.tgl.setObjectName("success")
        self.tgl.clicked.connect(self.toggle)
        c.addWidget(self.tgl)
        self.fld = QPushButton("FLOOD DISCORD")
        self.fld.setObjectName("gold")
        self.fld.clicked.connect(self.flood)
        c.addWidget(self.fld)
        lo.addLayout(c)

        mg = QGroupBox("Monitoring Status")
        ml = QVBoxLayout()
        self.mi = QLabel("Scans: 0 | Found: 0 | Last: N/A")
        self.mi.setStyleSheet("font-size:13px;color:#b0b0b8;")
        ml.addWidget(self.mi)
        mg.setLayout(ml)
        lo.addWidget(mg)
        lo.addStretch()
        self.setLayout(lo)

        self.running = False
        self.threads = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

    def toggle(self):
        if self.running:
            self.stop()
        else:
            self.start()

    def start(self):
        self.logfn("[SYSTEM] Starting monitoring...")
        self.running = True
        self.tgl.setText("STOP MONITORING")
        self.tgl.setObjectName("danger"); self.tgl.style().unpolish(self.tgl); self.tgl.style().polish(self.tgl)
        for fn in [combined.monitor_loop, combined.claim_scheduler_loop, combined.daily_freebies_loop]:
            t = threading.Thread(target=fn, daemon=True); t.start(); self.threads.append(t)
        with combined.state_lock:
            combined.state["bot_status"] = "online"; combined.state["status"] = "online"
        self.logfn("[SYSTEM] ✅ Monitoring active — scanning Reddit every 60s")
        self.stlbl.setText("● ONLINE")
        self.stlbl.setStyleSheet("color:#22c55e;font-size:16px;font-weight:700;")

    def stop(self):
        self.logfn("[SYSTEM] Stopping monitoring...")
        self.running = False
        self.tgl.setText("START MONITORING")
        self.tgl.setObjectName("success"); self.tgl.style().unpolish(self.tgl); self.tgl.style().polish(self.tgl)
        with combined.state_lock:
            combined.state["bot_status"] = "offline"; combined.state["status"] = "offline"
        self.stlbl.setText("● OFFLINE")
        self.stlbl.setStyleSheet("color:#ef4444;font-size:16px;font-weight:700;")
        self.logfn("[SYSTEM] ❌ Monitoring stopped")

    def flood(self):
        self.logfn("[SYSTEM] Flooding Discord...")
        threading.Thread(target=self._flood, daemon=True).start()
    def _flood(self):
        p = combined.flood_discord_last_24h()
        self.logfn(f"[SYSTEM] ✅ Flood done — {p} alerts posted")

    def refresh(self):
        with combined.state_lock:
            s = dict(combined.state)
        self.c1.set_val(f"${s.get('sc_total',0):.2f}")
        self.c2.set_val(str(s.get('claimed',0)))
        self.c3.set_val(str(s.get('found',0)))
        u = s.get('runtime',0); h,m = divmod(u,3600); m//=60
        self.c4.set_val(f"{int(h)}h {int(m)}m")
        la = s.get('last_alert')
        self.mi.setText(f"Scans: {s.get('scanned',0)} | Found: {s.get('found',0)} | Last: {(la.get('title','N/A')[:40] if la else 'N/A')}")
        st = s.get("bot_status","offline")
        if st=="online":
            self.stlbl.setText("● ONLINE")
            self.stlbl.setStyleSheet("color:#22c55e;font-size:16px;font-weight:700;")
        else:
            self.stlbl.setText("● OFFLINE")
            self.stlbl.setStyleSheet("color:#ef4444;font-size:16px;font-weight:700;")

# ═══════════════════════════════════════════════════════════════
# ACCOUNTS TAB
# ═══════════════════════════════════════════════════════════════

class AccountsTab(QWidget):
    def __init__(self, logfn):
        super().__init__()
        self.logfn = logfn; self.workers = []
        lo = QVBoxLayout()
        lo.setContentsMargins(24, 24, 24, 24)
        lo.setSpacing(16)
        t = QLabel("Casino Accounts"); t.setObjectName("title"); lo.addWidget(t)
        tb = QHBoxLayout(); tb.setSpacing(8)
        a = QPushButton("+ ADD ACCOUNT"); a.setObjectName("gold"); a.clicked.connect(self.add); tb.addWidget(a)
        r = QPushButton("REFRESH"); r.clicked.connect(self.load); tb.addWidget(r); tb.addStretch(); lo.addLayout(tb)

        self.tbl = QTableWidget()
        self.tbl.setColumnCount(6)
        self.tbl.setHorizontalHeaderLabels(["Domain","Username","Last Claim","Status","SC Total",""])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lo.addWidget(self.tbl)
        self.setLayout(lo)
        self.load()
        self.timer = QTimer()
        self.timer.timeout.connect(self.load)
        self.timer.start(5000)

    def load(self):
        accts = combined.load_accounts()
        sched = combined.load_claim_schedule()
        sites = combined.load_sites()
        sm = {s["domain"]: s["name"] for s in sites}
        self.tbl.setRowCount(len(accts))
        for i,(dom,info) in enumerate(sorted(accts.items())):
            self.tbl.setItem(i,0,QTableWidgetItem(sm.get(dom,dom)))
            self.tbl.setItem(i,1,QTableWidgetItem(info.get("username","")))
            sc = sched.get(dom,{})
            lc = sc.get("last_claim",0)
            self.tbl.setItem(i,2,QTableWidgetItem(datetime.fromtimestamp(lc).strftime("%m/%d %H:%M") if lc else "Never"))
            st = sc.get("status","never")
            si = QTableWidgetItem(st.upper())
            si.setForeground(QColor("#22c55e" if st in ("done","never") else "#eab308" if st=="claiming" else "#ef4444"))
            self.tbl.setItem(i,3,si)
            sct = info.get("sc_total",0)
            sci = QTableWidgetItem(f"${sct:.2f}")
            sci.setForeground(QColor("#FFD700"))
            self.tbl.setItem(i,4,sci)
            b = QPushButton("CLAIM NOW")
            b.setStyleSheet("QPushButton{background:#22c55e;color:#fff;border-radius:6px;padding:6px 14px;font-size:11px;font-weight:700;}QPushButton:hover{background:#16a34a;}")
            b.clicked.connect(lambda checked,d=dom: self.claim(d))
            self.tbl.setCellWidget(i,5,b)

    def claim(self, dom):
        accts = combined.load_accounts()
        if dom not in accts: return
        info = accts[dom]
        self.logfn(f"[USER] Manual claim: {dom}")
        sched = combined.load_claim_schedule()
        sched[dom] = sched.get(dom,{"last_claim":0,"status":"claiming"})
        sched[dom]["status"] = "claiming"
        combined.save_claim_schedule(sched)
        w = ClaimWorker(dom,info["username"],info["password"])
        w.log.connect(self.logfn)
        w.done.connect(self.fin)
        self.workers.append(w); w.start()

    def fin(self, dom, ok, sc):
        if ok:
            with combined.state_lock:
                combined.state["claimed"] += 1
                combined.state["sc_total"] = round(combined.state["sc_total"]+sc,2)
            accts = combined.load_accounts()
            if dom in accts:
                accts[dom]["sc_total"] = round(accts[dom].get("sc_total",0)+sc,2)
                combined.save_accounts(accts)
        self.load()

    def add(self):
        d = AddAccountDlg(self)
        if d.exec():
            dom,un,pw = d.vals()
            if dom and un and pw:
                accts = combined.load_accounts()
                accts[dom] = {"username":un,"password":pw,"sc_total":0}
                combined.save_accounts(accts)
                self.load()
                self.logfn(f"[USER] Added: {dom}")

class AddAccountDlg(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account"); self.setFixedSize(400,260)
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(12)
        t = QLabel("Add Account"); t.setObjectName("title"); t.setStyleSheet("font-size:20px;"); lo.addWidget(t)
        fm = QFormLayout(); fm.setSpacing(10)
        self.d = QLineEdit(); self.d.setPlaceholderText("chumbacasino.com"); fm.addRow("Domain:",self.d)
        self.u = QLineEdit(); self.u.setPlaceholderText("Account email"); fm.addRow("Username:",self.u)
        self.p = QLineEdit(); self.p.setPlaceholderText("Password"); self.p.setEchoMode(QLineEdit.EchoMode.Password); fm.addRow("Password:",self.p)
        lo.addLayout(fm); lo.addSpacing(12)
        bl = QHBoxLayout()
        s = QPushButton("SAVE"); s.setObjectName("gold"); s.clicked.connect(self.accept)
        c = QPushButton("CANCEL"); c.clicked.connect(self.reject)
        bl.addWidget(s); bl.addWidget(c); lo.addLayout(bl)
        self.setLayout(lo)
    def vals(self): return self.d.text().strip(),self.u.text().strip(),self.p.text().strip()

# ═══════════════════════════════════════════════════════════════
# MONITOR TAB
# ═══════════════════════════════════════════════════════════════

class MonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(16)
        t = QLabel("Live Monitor Feed"); t.setObjectName("title"); lo.addWidget(t)
        self.v = QTextEdit(); self.v.setReadOnly(True); lo.addWidget(self.v)
        cl = QPushButton("CLEAR"); cl.clicked.connect(self.v.clear)
        hl = QHBoxLayout(); hl.addWidget(cl); hl.addStretch(); lo.addLayout(hl)
        self.setLayout(lo)
    def log(self, msg):
        self.v.append(msg)
        sb = self.v.verticalScrollBar(); sb.setValue(sb.maximum())

# ═══════════════════════════════════════════════════════════════
# SCHEDULE TAB
# ═══════════════════════════════════════════════════════════════

class ScheduleTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(16)
        t = QLabel("Claim Schedule"); t.setObjectName("title"); lo.addWidget(t)
        d = QLabel("24h cooldown. Green=ready  Yellow=cooling  Red=error")
        d.setObjectName("subtitle"); lo.addWidget(d)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(5)
        self.tbl.setHorizontalHeaderLabels(["Casino","Last Claim","Next Claim","Status","Cooldown"])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lo.addWidget(self.tbl); self.setLayout(lo)
        self.timer = QTimer(); self.timer.timeout.connect(self.refresh); self.timer.start(5000)

    def refresh(self):
        sched = combined.load_claim_schedule()
        sites = combined.load_sites()
        sm = {s["domain"]:s["name"] for s in sites}
        now = time.time()
        doms = set(sm.keys()); doms.update(sched.keys())
        self.tbl.setRowCount(len(doms))
        for i,dom in enumerate(sorted(doms)):
            self.tbl.setItem(i,0,QTableWidgetItem(sm.get(dom,dom)))
            s = sched.get(dom,{})
            lc = s.get("last_claim",0)
            self.tbl.setItem(i,1,QTableWidgetItem(datetime.fromtimestamp(lc).strftime("%m/%d %H:%M") if lc else "Never"))
            if lc:
                nc = lc+86400
                if now>=nc: ns = "Ready Now"
                else: r=int(nc-now); h,m=divmod(r,3600); m//=60; ns=f"{h}h {m}m"
            else: ns = "Ready Now"
            ni = QTableWidgetItem(ns)
            ni.setForeground(QColor("#22c55e" if ns=="Ready Now" else "#eab308"))
            self.tbl.setItem(i,2,ni)
            st = s.get("status","never")
            si = QTableWidgetItem(st.upper())
            si.setForeground(QColor("#22c55e" if st in ("done","never") else "#eab308" if st=="claiming" else "#ef4444"))
            self.tbl.setItem(i,3,si)
            if lc:
                pct = min(100,int(((now-lc)/86400)*100))
                bar = "█"*(pct//5)+"░"*(20-pct//5)
                self.tbl.setItem(i,4,QTableWidgetItem(f"{pct}% {bar}"))
            else: self.tbl.setItem(i,4,QTableWidgetItem("—"))

# ═══════════════════════════════════════════════════════════════
# SETTINGS TAB
# ═══════════════════════════════════════════════════════════════

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(20)
        t = QLabel("Settings"); t.setObjectName("title"); lo.addWidget(t)

        wg = QGroupBox("Discord Webhooks")
        wl = QFormLayout(); wl.setSpacing(8)
        self.lw = QLineEdit(combined.LIVE_WEBHOOK); wl.addRow("Live:",self.lw)
        self.fw = QLineEdit(combined.FREECASH_WEBHOOK); wl.addRow("Free SC:",self.fw)
        self.cw = QLineEdit(combined.CLAIMS_WEBHOOK); wl.addRow("Claims:",self.cw)
        wg.setLayout(wl); lo.addWidget(wg)

        bg = QGroupBox("Bot Behavior")
        bl = QFormLayout(); bl.setSpacing(8)
        self.hc = QCheckBox("Headless mode (invisible browser)")
        self.hc.setChecked(combined.HEADLESS_MODE); bl.addRow(self.hc)
        self.sp = QSpinBox(); self.sp.setRange(10,600); self.sp.setValue(combined.CHECK_INTERVAL); self.sp.setSuffix(" sec")
        bl.addRow("Check interval:",self.sp)
        bg.setLayout(bl); lo.addWidget(bg)

        lg = QGroupBox("License")
        ll = QVBoxLayout()
        lf = BASE_DIR / "license.dat"
        if lf.exists():
            try:
                with open(lf) as f: ld = json.load(f)
                ll.addWidget(QLabel(f"Key: {ld.get('key','N/A')}\nTier: {ld.get('tier','N/A')}"))
            except: ll.addWidget(QLabel("Corrupted license file."))
        else: ll.addWidget(QLabel("No license."))
        lg.setLayout(ll); lo.addWidget(lg)

        s = QPushButton("SAVE SETTINGS"); s.setObjectName("gold"); s.clicked.connect(self.save); lo.addWidget(s)

        ag = QGroupBox("About")
        al = QVBoxLayout()
        al.addWidget(QLabel("Casino - Automation Suite v1.0.0"))
        al.addWidget(QLabel("© 2026 Claims Casino"))
        ag.setLayout(al); lo.addWidget(ag)
        lo.addStretch(); self.setLayout(lo)

    def save(self):
        combined.LIVE_WEBHOOK = self.lw.text().strip()
        combined.FREECASH_WEBHOOK = self.fw.text().strip()
        combined.CLAIMS_WEBHOOK = self.cw.text().strip()
        combined.HEADLESS_MODE = self.hc.isChecked()
        combined.CHECK_INTERVAL = self.sp.value()
        QMessageBox.information(self,"Saved","Settings saved.")

# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claims Casino - Automation Suite")
        self.setFixedSize(1200, 780)

        c = QWidget(); self.setCentralWidget(c)
        ml = QHBoxLayout(c); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        self.sidebar = QListWidget()
        self.sidebar.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        for item in ["\U0001f4ca  Dashboard", "\U0001f464  Accounts", "\U0001f50d  Monitor", "\U0001f4c5  Schedule", "\u2699  Settings"]:
            self.sidebar.addItem(item)
        ml.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.mt = MonitorTab()
        self.dt = DashboardTab(self.mt.log)
        self.at = AccountsTab(self.mt.log)
        self.st = ScheduleTab()
        self.ste = SettingsTab()
        self.stack.addWidget(self.dt)
        self.stack.addWidget(self.at)
        self.stack.addWidget(self.mt)
        self.stack.addWidget(self.st)
        self.stack.addWidget(self.ste)
        ml.addWidget(self.stack)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)

        sb = QStatusBar(); self.setStatusBar(sb)
        self.sl = QLabel("● OFFLINE")
        self.sl.setStyleSheet("color:#ef4444;font-weight:700;padding:0 12px;")
        sb.addWidget(self.sl)
        self.cl = QLabel("Claims: 0")
        self.cl.setStyleSheet("color:#888;padding:0 12px;")
        sb.addWidget(self.cl)
        self.stl = QLabel("SC: $0.00")
        self.stl.setStyleSheet("color:#FFD700;font-weight:600;padding:0 12px;")
        sb.addWidget(self.stl)
        vl = QLabel("v1.0.0")
        vl.setStyleSheet("color:#555;padding:0 12px;")
        sb.addPermanentWidget(vl)

        # Tray
        self.tray = QSystemTrayIcon(self)
        # Create a simple gold pixmap as icon
        px = QPixmap(32,32); px.fill(QColor("#111114"))
        p = QPainter(px); p.setBrush(QColor("#FFD700")); p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(2,2,28,28); p.setFont(QFont("Arial",16,700)); p.setPen(QColor("#111"))
        p.drawText(px.rect(),Qt.AlignmentFlag.AlignCenter,"CC"); p.end()
        self.tray.setIcon(QIcon(px))

        tm = QMenu()
        tm.addAction("Show", self.show)
        tm.addAction("Hide", self.hide_to_tray)
        tm.addSeparator()
        tm.addAction("Exit", QApplication.quit)
        self.tray.setContextMenu(tm)
        self.tray.setToolTip("Claims Casino")
        self.tray.activated.connect(lambda r: self.show() if r==QSystemTrayIcon.ActivationReason.DoubleClick else None)

        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.refresh_st)
        self.status_timer.start(2000)

        QTimer.singleShot(3000, self.check_up)

    def refresh_st(self):
        with combined.state_lock: s = dict(combined.state)
        st = s.get("bot_status","offline")
        if st=="online":
            self.sl.setText("● ONLINE")
            self.sl.setStyleSheet("color:#22c55e;font-weight:700;padding:0 12px;")
        else:
            self.sl.setText("● OFFLINE")
            self.sl.setStyleSheet("color:#ef4444;font-weight:700;padding:0 12px;")
        self.cl.setText(f"Claims: {s.get('claimed',0)}")
        self.stl.setText(f"SC: ${s.get('sc_total',0):.2f}")

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() <= 44:
            self.dragPos = e.globalPosition().toPoint()
            e.accept()

    def mouseMoveEvent(self, e):
        if e.buttons() == Qt.MouseButton.LeftButton and self.dragPos is not None:
            self.move(self.pos() + e.globalPosition().toPoint() - self.dragPos)
            self.dragPos = e.globalPosition().toPoint()
            e.accept()

    def mouseReleaseEvent(self, e):
        self.dragPos = None

    def hide_to_tray(self):
        self.hide(); self.tray.show()
        self.tray.showMessage("Claims Casino","Minimized to tray.",QSystemTrayIcon.MessageIcon.Information,2000)

    def closeEvent(self, e):
        if self.tray.isVisible(): self.hide_to_tray(); e.ignore()
        else: e.accept()

    def check_up(self):
        try:
            r = combined.requests.get(
                "https://api.github.com/repos/glowrius/casino-bonus-monitor/releases/latest", timeout=5)
            if r.status_code != 200: return
            data = r.json()
            tag = data.get("tag_name", "v0.0.0")
            if tag <= "v1.0.0": return
            assets = data.get("assets", [])
            exe_asset = None
            for a in assets:
                if a.get("name", "").endswith(".exe"):
                    exe_asset = a
                    break
            if not exe_asset: return
            mb = exe_asset.get("size", 0) / 1048576
            if QMessageBox.question(self, "Update Available",
                f"Claims Casino {tag} available ({mb:.1f} MB).\nDownload and install now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            self.download_update(exe_asset["browser_download_url"], tag)
        except: pass

    def download_update(self, url, tag):
        pd = QProgressDialog(f"Downloading {tag}...", "Cancel", 0, 0, self)
        pd.setWindowTitle("Update"); pd.setCancelButton(None)
        pd.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        pd.setFixedSize(360, 100); pd.show()
        tmp = BASE_DIR / f"CasinoBot_{tag}.exe"
        try:
            r = combined.requests.get(url, stream=True, timeout=60)
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            chunk_size = 65536
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pd.setValue(int(downloaded / total * 100))
                            pd.setLabelText(f"Downloading {tag}... {downloaded*100//total}%")
            pd.close()
            exe = sys.executable
            ps = (
                f'Start-Sleep -Seconds 2; '
                f'Copy-Item -Path "{tmp}" -Destination "{exe}" -Force; '
                f'Start-Process -FilePath "{exe}"; '
                f'Remove-Item -Path "{tmp}" -Force'
            )
            subprocess.Popen(["powershell", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW)
            QApplication.quit()
        except Exception as e:
            pd.close()
            if tmp.exists(): tmp.unlink()
            QMessageBox.warning(self, "Update Failed", f"Download failed:\n{e}")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_SS)

    # Check license
    lf = BASE_DIR / "license.dat"
    ok = False
    if lf.exists():
        try:
            with open(lf) as f: ld = json.load(f)
            if combined.validate_license_key(ld.get("key","")).get("valid"): ok = True
        except: pass

    if not ok:
        dlg = LicenseDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted: sys.exit(0)

    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
