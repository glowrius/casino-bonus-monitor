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
    QSystemTrayIcon, QMenu, QFrame, QListWidget, QStackedWidget, QProgressDialog, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QAction, QPixmap, QPainter, QFontDatabase, QIcon

# ═══════════════════════════════════════════════════════════════
# STYLESHEET (Website Theme)
# ═══════════════════════════════════════════════════════════════

DARK_SS = """
QMainWindow, QDialog { background: #111114; color: #e0e0e8; }
QWidget { background: #111114; color: #e0e0e8; }
QListWidget {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #1a1a1e, stop:1 #141418);
    border: none; border-right: 1px solid rgba(255,255,255,0.04); border-bottom-left-radius: 12px;
    color: #888; font-size: 14px; font-weight: 600; outline: none;
    padding: 8px 0; min-width: 200px; max-width: 200px;
}
QListWidget::item { padding: 14px 20px; border-left: 3px solid transparent; }
QListWidget::item:selected {
    background: rgba(255,215,0,0.08); color: #FFD700; border-left: 3px solid #FFD700;
}
QListWidget::item:hover:!selected {
    background: rgba(255,255,255,0.03); color: #ccc; border-left: 3px solid rgba(255,215,0,0.3);
}
QPushButton {
    background: rgba(42,42,46,0.6); color: #f0efed; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px; padding: 10px 24px; font-size: 13px; font-weight: 600;
}
QPushButton:hover { background: rgba(255,255,255,0.1); border-color: #FFD700; }
QPushButton:pressed { background: rgba(0,0,0,0.3); }
QPushButton#gold {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFD700, stop:1 #FFB300);
    color: #111114; border: none; font-weight: 700;
}
QPushButton#gold:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffe44d, stop:1 #FFC107); }
QPushButton#danger { background: #ef4444; color: #fff; border-color: #ef4444; }
QPushButton#danger:hover { background: #dc2626; }
QPushButton#success { background: #22c55e; color: #fff; border-color: #22c55e; }
QPushButton#success:hover { background: #16a34a; }
QPushButton:disabled { background: rgba(255,255,255,0.03); color: #555; border-color: rgba(255,255,255,0.04); }
QLineEdit {
    background: rgba(28,28,33,0.8); color: #f0efed; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px; padding: 10px 14px; font-size: 14px;
}
QLineEdit:focus { border-color: #FFD700; }
QTableWidget {
    background: rgba(28,28,33,0.6); color: #e0e0e8; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; gridline-color: rgba(255,255,255,0.04); font-size: 13px;
}
QTableWidget::item { padding: 8px; }
QTableWidget::item:selected { background: rgba(255,215,0,0.1); color: #FFD700; }
QHeaderView::section {
    background: rgba(34,34,38,0.8); color: #FFD700; padding: 10px; border: none;
    border-bottom: 2px solid #FFD700; font-weight: 700; font-size: 12px;
}
QLabel#title { font-size: 24px; font-weight: 800; }
QLabel#subtitle { font-size: 14px; color: #888; }
QLabel#statv { font-size: 28px; font-weight: 800; }
QLabel#statl { font-size: 12px; color: #888; letter-spacing: 1px; }
QCheckBox { color: #e0e0e8; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.1); border-radius: 4px; background: rgba(28,28,33,0.6); }
QCheckBox::indicator:checked { background: #FFD700; border-color: #FFD700; }
QSpinBox { background: rgba(28,28,33,0.8); color: #f0efed; border: 1px solid rgba(255,255,255,0.08); border-radius: 8px; padding: 8px; font-size: 13px; }
QSpinBox:focus { border-color: #FFD700; }
QGroupBox {
    border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; margin-top: 16px;
    padding: 20px 16px 16px; font-weight: 700; font-size: 13px; color: #FFD700;
    background: rgba(28,28,33,0.4);
}
QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 8px; }
QTextEdit { background: rgba(10,10,14,0.8); color: #b0b0b8; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 12px; font-family: Consolas,Courier New,monospace; font-size: 12px; }
QStatusBar { background: rgba(28,28,33,0.85); color: #888; border-top: 1px solid rgba(255,255,255,0.04); font-size: 12px; }
QStatusBar::item { border: none; }
QScrollBar:vertical { background: rgba(28,28,33,0.4); width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.25); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QSplitter::handle { background: rgba(255,255,255,0.06); width: 1px; }
"""

# ═══════════════════════════════════════════════════════════════
# WIDGETS
# ═══════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, label, initial="0", color="#22c55e"):
        super().__init__()
        self.setObjectName("sc")
        self.setStyleSheet(f"#sc{{background:rgba(28,28,33,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:20px;}}"
                           f"#sc:hover{{border-color:#FFD700;}}")
        lo = QVBoxLayout()
        lo.setContentsMargins(16, 12, 16, 12)
        lo.setSpacing(4)
        self.v = QLabel(initial)
        self.v.setObjectName("statv")
        g = f"background:linear-gradient(135deg,{color},{color});-webkit-background-clip:text;" if color == "#FFD700" else ""
        if g:
            self.v.setStyleSheet(f"font-size:34px;font-weight:800;color:{color};")
        else:
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
        lo.setContentsMargins(40, 44, 40, 40)
        lo.setSpacing(16)

        logo_path = Path(getattr(sys, "_MEIPASS", BASE_DIR)) / "assets" / "logo.png"
        if logo_path.exists():
            lp = QLabel()
            px = QPixmap(str(logo_path)).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lp.setPixmap(px)
            lp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lo.addWidget(lp)

        t = QLabel("CLAIMS CASINO")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size:36px;font-weight:800;background:linear-gradient(135deg,#FFD700,#FFB300);-webkit-background-clip:text;background-clip:text;color:transparent;letter-spacing:3px;")
        lo.addWidget(t)

        s = QLabel("License Activation Required")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setStyleSheet("font-size:14px;color:#888;")
        lo.addWidget(s)
        lo.addSpacing(12)

        self.k = QLineEdit()
        self.k.setPlaceholderText("Enter license key (XXXX-XXXX-XXXX-XXXX)")
        self.k.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.k.setStyleSheet("font-size:20px;font-weight:700;letter-spacing:2px;padding:16px;border-radius:12px;")
        lo.addWidget(self.k)

        self.st = QLabel("")
        self.st.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.st.setStyleSheet("font-size:13px;")
        lo.addWidget(self.st)

        b = QPushButton("ACTIVATE LICENSE")
        b.setObjectName("gold")
        b.setStyleSheet("font-size:17px;font-weight:700;padding:16px;border-radius:12px;letter-spacing:2px;")
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
    def __init__(self):
        super().__init__()
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
        lo.addLayout(c)

        mg = QGroupBox("Monitoring Status")
        ml = QVBoxLayout()
        self.mi = QLabel("Scans: 0 | Found: 0 | Last: N/A")
        self.mi.setStyleSheet("font-size:13px;color:#b0b0b8;")
        ml.addWidget(self.mi)
        mg.setLayout(ml)
        lo.addWidget(mg)

        lg = QGroupBox("Activity Log")
        ll = QVBoxLayout()
        self.logv = QTextEdit()
        self.logv.setReadOnly(True)
        self.logv.setMaximumHeight(160)
        ll.addWidget(self.logv)
        lg.setLayout(ll)
        lo.addWidget(lg)
        lo.addStretch()
        self.setLayout(lo)

        self.running = False
        self.threads = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh)
        self.timer.start(2000)

    def log(self, msg):
        self.logv.append(msg)
        sb = self.logv.verticalScrollBar(); sb.setValue(sb.maximum())

    def toggle(self):
        if self.running: self.stop()
        else: self.start()

    def start(self):
        self.log("[SYSTEM] Starting monitoring...")
        self.running = True
        self.tgl.setText("STOP MONITORING")
        self.tgl.setObjectName("danger"); self.tgl.style().unpolish(self.tgl); self.tgl.style().polish(self.tgl)
        for fn in [combined.monitor_loop, combined.claim_scheduler_loop, combined.daily_freebies_loop]:
            t = threading.Thread(target=fn, daemon=True); t.start(); self.threads.append(t)
        with combined.state_lock:
            combined.state["bot_status"] = "online"; combined.state["status"] = "online"
        self.log("[SYSTEM] ✅ Monitoring active — scanning Reddit every 60s")
        self.stlbl.setText("● ONLINE")
        self.stlbl.setStyleSheet("color:#22c55e;font-size:16px;font-weight:700;")

    def stop(self):
        self.log("[SYSTEM] Stopping monitoring...")
        self.running = False
        self.tgl.setText("START MONITORING")
        self.tgl.setObjectName("success"); self.tgl.style().unpolish(self.tgl); self.tgl.style().polish(self.tgl)
        with combined.state_lock:
            combined.state["bot_status"] = "offline"; combined.state["status"] = "offline"
        self.stlbl.setText("● OFFLINE")
        self.stlbl.setStyleSheet("color:#ef4444;font-size:16px;font-weight:700;")
        self.log("[SYSTEM] ❌ Monitoring stopped")

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
# DAILY SC TAB (Accounts + Schedule + Log merged)
# ═══════════════════════════════════════════════════════════════

class DailySCTab(QWidget):
    def __init__(self):
        super().__init__()
        self.workers = []
        lo = QVBoxLayout()
        lo.setContentsMargins(24, 24, 24, 24)
        lo.setSpacing(14)

        t = QLabel("Daily SC")
        t.setObjectName("title")
        lo.addWidget(t)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(8)
        a = QPushButton("+ ADD ACCOUNT"); a.setObjectName("gold"); a.clicked.connect(self.add); tb.addWidget(a)
        ca = QPushButton("CLAIM ALL"); ca.setObjectName("success"); ca.clicked.connect(self.claim_all); tb.addWidget(ca)
        r = QPushButton("REFRESH"); r.clicked.connect(self.load); tb.addWidget(r); tb.addStretch(); lo.addLayout(tb)

        # Splitter: Account table top, Schedule + Log bottom
        sp = QSplitter(Qt.Orientation.Vertical)

        # --- Account Table ---
        aw = QWidget()
        al = QVBoxLayout(aw); al.setContentsMargins(0,0,0,0); al.setSpacing(6)
        al.addWidget(QLabel("Accounts"))
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
        al.addWidget(self.tbl)
        sp.addWidget(aw)

        # --- Schedule + Log ---
        bw = QWidget()
        bl = QVBoxLayout(bw); bl.setContentsMargins(0,0,0,0); bl.setSpacing(6)
        bl.addWidget(QLabel("Claim Schedule"))
        self.schtbl = QTableWidget()
        self.schtbl.setColumnCount(5)
        self.schtbl.setHorizontalHeaderLabels(["Casino","Last Claim","Next Claim","Status","Cooldown"])
        self.schtbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.schtbl.verticalHeader().setVisible(False)
        self.schtbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.schtbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        bl.addWidget(self.schtbl)
        bl.addWidget(QLabel("Activity Log"))
        self.logv = QTextEdit()
        self.logv.setReadOnly(True)
        self.logv.setMaximumHeight(140)
        bl.addWidget(self.logv)
        sp.addWidget(bw)

        sp.setSizes([300, 300])
        lo.addWidget(sp)
        self.setLayout(lo)

        self.load()
        self.timer = QTimer()
        self.timer.timeout.connect(self.load)
        self.timer.start(5000)

    def log(self, msg):
        self.logv.append(msg)
        sb = self.logv.verticalScrollBar(); sb.setValue(sb.maximum())

    def load(self):
        accts = combined.load_accounts()
        sched = combined.load_claim_schedule()
        sites = combined.load_sites()
        sm = {s["domain"]: s["name"] for s in sites}

        # Account table
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
            b.setObjectName("success")
            b.setStyleSheet("QPushButton{background:#22c55e;color:#fff;border-radius:8px;padding:6px 14px;font-size:11px;font-weight:700;}QPushButton:hover{background:#16a34a;}")
            b.clicked.connect(lambda checked,d=dom: self.claim(d))
            self.tbl.setCellWidget(i,5,b)

        # Schedule table
        now = time.time()
        doms = set(sm.keys()); doms.update(sched.keys())
        self.schtbl.setRowCount(len(doms))
        for i,dom in enumerate(sorted(doms)):
            self.schtbl.setItem(i,0,QTableWidgetItem(sm.get(dom,dom)))
            s = sched.get(dom,{})
            lc = s.get("last_claim",0)
            self.schtbl.setItem(i,1,QTableWidgetItem(datetime.fromtimestamp(lc).strftime("%m/%d %H:%M") if lc else "Never"))
            if lc:
                nc = lc+86400
                if now>=nc: ns = "Ready Now"
                else: r=int(nc-now); h,m=divmod(r,3600); m//=60; ns=f"{h}h {m}m"
            else: ns = "Ready Now"
            ni = QTableWidgetItem(ns)
            ni.setForeground(QColor("#22c55e" if ns=="Ready Now" else "#eab308"))
            self.schtbl.setItem(i,2,ni)
            st = s.get("status","never")
            si = QTableWidgetItem(st.upper())
            si.setForeground(QColor("#22c55e" if st in ("done","never") else "#eab308" if st=="claiming" else "#ef4444"))
            self.schtbl.setItem(i,3,si)
            if lc:
                pct = min(100,int(((now-lc)/86400)*100))
                bar = "█"*(pct//5)+"░"*(20-pct//5)
                self.schtbl.setItem(i,4,QTableWidgetItem(f"{pct}% {bar}"))
            else: self.schtbl.setItem(i,4,QTableWidgetItem("—"))

    def claim(self, dom):
        accts = combined.load_accounts()
        if dom not in accts: return
        info = accts[dom]
        self.log(f"[USER] Manual claim: {dom}")
        sched = combined.load_claim_schedule()
        sched[dom] = sched.get(dom,{"last_claim":0,"status":"claiming"})
        sched[dom]["status"] = "claiming"
        combined.save_claim_schedule(sched)
        w = ClaimWorker(dom,info["username"],info["password"])
        w.log.connect(self.log)
        w.done.connect(self.fin)
        self.workers.append(w); w.start()

    def claim_all(self):
        accts = combined.load_accounts()
        for dom in accts:
            self.claim(dom)

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
                self.log(f"[USER] Added: {dom}")

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
# STREAMER SNIPER TAB
# ═══════════════════════════════════════════════════════════════

class StreamerSniperTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout()
        lo.setContentsMargins(24,24,24,24); lo.setSpacing(14)

        t = QLabel("Streamer Sniper")
        t.setObjectName("title"); lo.addWidget(t)

        tb = QHBoxLayout(); tb.setSpacing(8)
        self.sniper_tgl = QPushButton("START SNIPER")
        self.sniper_tgl.setObjectName("success")
        self.sniper_tgl.clicked.connect(self.toggle_sniper)
        tb.addWidget(self.sniper_tgl)
        tb.addStretch()
        lo.addLayout(tb)

        # Streamer list
        sg = QGroupBox("Monitored Streamers")
        sl = QVBoxLayout()
        self.streamer_list = QTableWidget()
        self.streamer_list.setColumnCount(4)
        self.streamer_list.setHorizontalHeaderLabels(["Platform","Username","Status","Last Seen"])
        self.streamer_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.streamer_list.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.streamer_list.verticalHeader().setVisible(False)
        self.streamer_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.streamer_list.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        sl.addWidget(self.streamer_list)
        ab = QHBoxLayout()
        self.sadd = QPushButton("+ ADD STREAMER"); self.sadd.setObjectName("gold"); self.sadd.clicked.connect(self.add_streamer)
        self.srm = QPushButton("REMOVE"); self.srm.clicked.connect(self.remove_streamer)
        ab.addWidget(self.sadd); ab.addWidget(self.srm); ab.addStretch()
        sl.addLayout(ab)
        sg.setLayout(sl); lo.addWidget(sg)

        lg = QGroupBox("Sniper Log")
        ll = QVBoxLayout()
        self.sniper_log = QTextEdit()
        self.sniper_log.setReadOnly(True)
        ll.addWidget(self.sniper_log)
        lg.setLayout(ll); lo.addWidget(lg)

        lo.addStretch()
        self.setLayout(lo)
        self.sniper_running = False
        self.sniper_threads = []
        self.refresh_streamers()

    def log(self, msg):
        self.sniper_log.append(msg)
        sb = self.sniper_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def refresh_streamers(self):
        streamers = combined.load_streamers() if hasattr(combined, 'load_streamers') else []
        self.streamer_list.setRowCount(len(streamers))
        for i, s in enumerate(streamers):
            self.streamer_list.setItem(i,0,QTableWidgetItem(s.get("platform","Kick")))
            self.streamer_list.setItem(i,1,QTableWidgetItem(s.get("username","")))
            self.streamer_list.setItem(i,2,QTableWidgetItem(s.get("status","idle")))
            self.streamer_list.setItem(i,3,QTableWidgetItem(s.get("last_seen","Never")))

    def add_streamer(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Streamer"); dlg.setFixedSize(360,200)
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        lo.addWidget(QLabel("Streamer Username:"))
        un = QLineEdit(); un.setPlaceholderText("streamer_name"); lo.addWidget(un)
        lo.addWidget(QLabel("Platform:"))
        plat = QLineEdit("Kick"); lo.addWidget(plat)
        bl = QHBoxLayout()
        ok = QPushButton("ADD"); ok.setObjectName("gold"); ok.clicked.connect(dlg.accept)
        no = QPushButton("CANCEL"); no.clicked.connect(dlg.reject)
        bl.addWidget(ok); bl.addWidget(no); lo.addLayout(bl)
        if dlg.exec():
            u = un.text().strip()
            p = plat.text().strip() or "Kick"
            if u:
                streamers = combined.load_streamers() if hasattr(combined, 'load_streamers') else []
                streamers.append({"platform": p, "username": u, "status": "idle", "last_seen": "Never"})
                if hasattr(combined, 'save_streamers'):
                    combined.save_streamers(streamers)
                self.refresh_streamers()
                self.log(f"[SNIPER] Added streamer: {u} ({p})")

    def remove_streamer(self):
        r = self.streamer_list.currentRow()
        if r < 0: return
        streamers = combined.load_streamers() if hasattr(combined, 'load_streamers') else []
        if r < len(streamers):
            u = streamers[r].get("username","")
            del streamers[r]
            if hasattr(combined, 'save_streamers'):
                combined.save_streamers(streamers)
            self.refresh_streamers()
            self.log(f"[SNIPER] Removed streamer: {u}")

    def toggle_sniper(self):
        if self.sniper_running:
            self.sniper_running = False
            self.sniper_tgl.setText("START SNIPER")
            self.sniper_tgl.setObjectName("success"); self.sniper_tgl.style().unpolish(self.sniper_tgl); self.sniper_tgl.style().polish(self.sniper_tgl)
            self.log("[SNIPER] Stopped")
        else:
            self.sniper_running = True
            self.sniper_tgl.setText("STOP SNIPER")
            self.sniper_tgl.setObjectName("danger"); self.sniper_tgl.style().unpolish(self.sniper_tgl); self.sniper_tgl.style().polish(self.sniper_tgl)
            self.log("[SNIPER] Starting streamer monitoring...")
            if hasattr(combined, 'monitor_streamer_loop'):
                t = threading.Thread(target=combined.monitor_streamer_loop, daemon=True)
                t.start(); self.sniper_threads.append(t)
            self.log("[SNIPER] ✅ Streamer sniper active")

# ═══════════════════════════════════════════════════════════════
# LINK AUTOMATION TAB
# ═══════════════════════════════════════════════════════════════

class LinkAutomationTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout()
        lo.setContentsMargins(24,24,24,24); lo.setSpacing(14)

        t = QLabel("Link Automation")
        t.setObjectName("title"); lo.addWidget(t)

        # Add URL
        ab = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste sweepstakes link to auto-process...")
        ab.addWidget(self.url_input)
        self.add_btn = QPushButton("ADD LINK")
        self.add_btn.setObjectName("gold")
        self.add_btn.clicked.connect(self.add_link)
        ab.addWidget(self.add_btn)
        lo.addLayout(ab)

        # Queue table
        self.queue_tbl = QTableWidget()
        self.queue_tbl.setColumnCount(5)
        self.queue_tbl.setHorizontalHeaderLabels(["URL","Added","Status","Result",""])
        self.queue_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.queue_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_tbl.verticalHeader().setVisible(False)
        self.queue_tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.queue_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lo.addWidget(self.queue_tbl)

        tb = QHBoxLayout()
        self.process_btn = QPushButton("PROCESS QUEUE")
        self.process_btn.setObjectName("success")
        self.process_btn.clicked.connect(self.process_queue)
        tb.addWidget(self.process_btn)
        self.clear_btn = QPushButton("CLEAR ALL")
        self.clear_btn.clicked.connect(self.clear_queue)
        tb.addWidget(self.clear_btn)
        tb.addStretch()
        lo.addLayout(tb)

        lg = QGroupBox("Automation Log")
        ll = QVBoxLayout()
        self.link_log = QTextEdit()
        self.link_log.setReadOnly(True)
        ll.addWidget(self.link_log)
        lg.setLayout(ll); lo.addWidget(lg)

        lo.addStretch()
        self.setLayout(lo)
        self.refresh_queue()

    def log(self, msg):
        self.link_log.append(msg)
        sb = self.link_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def refresh_queue(self):
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        self.queue_tbl.setRowCount(len(queue))
        for i, item in enumerate(queue):
            self.queue_tbl.setItem(i,0,QTableWidgetItem(item.get("url","")[:60]))
            self.queue_tbl.setItem(i,1,QTableWidgetItem(item.get("added","")))
            self.queue_tbl.setItem(i,2,QTableWidgetItem(item.get("status","pending")))
            self.queue_tbl.setItem(i,3,QTableWidgetItem(item.get("result","")))
            rb = QPushButton("REMOVE")
            rb.setStyleSheet("QPushButton{color:#ef4444;font-size:11px;padding:4px 10px;border-radius:6px;}")
            rb.clicked.connect(lambda checked, idx=i: self.remove_link(idx))
            self.queue_tbl.setCellWidget(i,4,rb)

    def add_link(self):
        url = self.url_input.text().strip()
        if not url: return
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        queue.append({"url": url, "added": datetime.now().strftime("%m/%d %H:%M"), "status": "pending", "result": ""})
        if hasattr(combined, 'save_link_queue'):
            combined.save_link_queue(queue)
        self.url_input.clear()
        self.refresh_queue()
        self.log(f"[LINK] Added: {url[:50]}...")

    def remove_link(self, idx):
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        if idx < len(queue):
            del queue[idx]
            if hasattr(combined, 'save_link_queue'):
                combined.save_link_queue(queue)
            self.refresh_queue()

    def clear_queue(self):
        if hasattr(combined, 'save_link_queue'):
            combined.save_link_queue([])
        self.refresh_queue()
        self.log("[LINK] Queue cleared")

    def process_queue(self):
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        if not queue: return
        self.log(f"[LINK] Processing {len(queue)} links...")
        for i, item in enumerate(queue):
            if item.get("status") == "done": continue
            item["status"] = "processing"
            if hasattr(combined, 'save_link_queue'):
                combined.save_link_queue(queue)
            self.refresh_queue()
            try:
                result = combined.process_link(item["url"]) if hasattr(combined, 'process_link') else {"success": True, "message": "Stub - link processed"}
                item["status"] = "done" if result.get("success") else "failed"
                item["result"] = result.get("message", result.get("error", "Unknown"))
            except Exception as e:
                item["status"] = "failed"
                item["result"] = str(e)
            if hasattr(combined, 'save_link_queue'):
                combined.save_link_queue(queue)
            self.refresh_queue()
            self.log(f"[LINK] {item['status'].upper()}: {item['url'][:40]} -> {item['result'][:60]}")
        self.log("[LINK] Queue processing complete")

# ═══════════════════════════════════════════════════════════════
# SETTINGS TAB
# ═══════════════════════════════════════════════════════════════

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(20)
        t = QLabel("Settings"); t.setObjectName("title"); lo.addWidget(t)

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
        l = QLabel('<a href="https://claimscasino.com/terms" style="color:#FFD700;text-decoration:none;">Terms of Service</a>')
        l.setOpenExternalLinks(True)
        al.addWidget(l)
        al.addWidget(QLabel("© 2026 Claims Casino Automation"))
        ag.setLayout(al); lo.addWidget(ag)
        lo.addStretch(); self.setLayout(lo)

    def save(self):
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
        for item in ["\U0001f4ca  Dashboard", "\U0001f3b0  Daily SC", "\U0001f3ac  Streamer Sniper", "\U0001f517  Link Automation", "\u2699  Settings"]:
            self.sidebar.addItem(item)
        ml.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.dt = DashboardTab()
        self.dst = DailySCTab()
        self.sst = StreamerSniperTab()
        self.lat = LinkAutomationTab()
        self.ste = SettingsTab()
        self.stack.addWidget(self.dt)
        self.stack.addWidget(self.dst)
        self.stack.addWidget(self.sst)
        self.stack.addWidget(self.lat)
        self.stack.addWidget(self.ste)
        ml.addWidget(self.stack)
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.on_page_change)

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
        vl = QLabel("v1.0.1")
        vl.setStyleSheet("color:#555;padding:0 12px;")
        sb.addPermanentWidget(vl)

        # Tray
        ico = BASE_DIR / "assets/icon.ico"
        self.tray = QSystemTrayIcon(self)
        if ico.exists():
            self.tray.setIcon(QIcon(str(ico)))
        else:
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

    def on_page_change(self, idx):
        if idx < 0: return
        self.stack.setCurrentIndex(idx)
        w = self.stack.currentWidget()
        if w:
            ef = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(ef)
            an = QPropertyAnimation(ef, b"opacity")
            an.setDuration(200)
            an.setStartValue(0.0)
            an.setEndValue(1.0)
            an.setEasingCurve(QEasingCurve.Type.OutCubic)
            an.start()

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
            if tag <= "v1.0.1": return
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
