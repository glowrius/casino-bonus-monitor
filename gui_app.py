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

APP_VERSION = "v1.0.2"
# Obfuscated URLs to prevent trivial string-search cracking
_ob_key = bytes([0x47, 0x8B, 0x1A, 0xD4, 0x66, 0x2F, 0x93, 0x01])
def _deobs(e):
    import base64
    raw = base64.b64decode(e.encode())
    return "".join(chr(b ^ _ob_key[i % len(_ob_key)]) for i, b in enumerate(raw))

UPDATE_MANIFEST_URL = _deobs("L/9upBUVvC4k53u9C1zwYDTidLtITPxsaP5qsAdb9i8t+HW6")
LICENSE_SERVER_URL = _deobs("L/9upFwAvG0o6Hu4DkDgdX2+KuRXAPJxLqR7txJG5WAz7g==")

if not combined.SITES_FILE.exists():
    combined.save_sites(combined.DEFAULT_SITES)

# ── PyQt6 ──
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QMessageBox, QTextEdit,
    QCheckBox, QSpinBox, QGroupBox, QFormLayout, QStatusBar,
    QSystemTrayIcon, QMenu, QFrame,     QStackedWidget, QSplitter, QProgressDialog,
    QComboBox, QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QUrl, QVariantAnimation, pyqtProperty
from PyQt6.QtGui import QFont, QColor, QAction, QPixmap, QPainter, QFontDatabase, QIcon, QDesktopServices

# ═══════════════════════════════════════════════════════════════
# STYLESHEET (Website Theme)
# ═══════════════════════════════════════════════════════════════

DARK_SS = """
QMainWindow, QDialog { background: #0a0a0f; color: #e8e8ed; }
QWidget { background: transparent; color: #e8e8ed; }
QFrame, QGroupBox, QTabWidget, QStackedWidget { background: transparent; }

/* ---- Sidebar ---- */
#sidebar { background: #0d0d14; border: none; border-right: 1px solid rgba(255,255,255,0.04); min-width: 200px; max-width: 200px; }
#sidebar QPushButton {
    background: transparent; color: #888; border: none; border-radius: 0; text-align: left;
    padding: 12px 20px; font-size: 13px; font-weight: 500; border-left: 2px solid transparent;
}
#sidebar QPushButton:hover { background: rgba(255,255,255,0.02); color: #bbb; }
#sidebar QPushButton:checked {
    background: rgba(255,215,0,0.05); color: #FFD700; border-left: 2px solid #FFD700;
}
#sidebar #navsep { background: rgba(255,255,255,0.05); max-height: 1px; min-height: 1px; margin: 4px 16px; }

/* ---- Buttons ---- */
QPushButton {
    background: rgba(255,255,255,0.04); color: #ccc; border: 1px solid rgba(255,255,255,0.06);
    border-radius: 8px; padding: 8px 18px; font-size: 13px; font-weight: 500;
}
QPushButton:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,215,0,0.3); }
QPushButton:pressed { background: rgba(0,0,0,0.2); }
QPushButton:disabled { background: rgba(255,255,255,0.02); color: #555; border-color: rgba(255,255,255,0.03); }
QPushButton#gold {
    background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #FFD700, stop:1 #F59E0B);
    color: #0a0a0f; border: none; font-weight: 600;
}
QPushButton#gold:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ffe44d, stop:1 #fbbf24); }
QPushButton#danger { background: #dc2626; color: #fff; border: none; }
QPushButton#danger:hover { background: #b91c1c; }
QPushButton#success { background: #059669; color: #fff; border: none; }
QPushButton#success:hover { background: #047857; }

/* ---- Inputs ---- */
QLineEdit {
    background: rgba(255,255,255,0.03); color: #e8e8ed; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px; padding: 8px 12px; font-size: 13px;
}
QLineEdit:focus { border-color: #FFD700; }
QSpinBox { background: rgba(255,255,255,0.03); color: #e8e8ed; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; padding: 6px 10px; font-size: 13px; }
QSpinBox:focus { border-color: #FFD700; }
QCheckBox { color: #888; font-size: 13px; spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 2px solid rgba(255,255,255,0.15); border-radius: 4px; background: transparent; }
QCheckBox::indicator:checked { background: #FFD700; border-color: #FFD700; }

/* ---- Tables ---- */
QTableWidget {
    background: rgba(255,255,255,0.02); color: #e8e8ed; border: 1px solid rgba(255,255,255,0.05);
    border-radius: 8px; gridline-color: rgba(255,255,255,0.02); font-size: 13px;
}
QTableWidget::item { padding: 6px 8px; }
QTableWidget::item:selected { background: rgba(255,215,0,0.06); color: #FFD700; }
QTableWidget::item:hover { background: rgba(255,255,255,0.02); }
QHeaderView::section {
    background: rgba(0,0,0,0.3); color: #FFD700; padding: 8px 10px; border: none;
    border-bottom: 1px solid rgba(255,215,0,0.3); font-weight: 600; font-size: 11px;
}

/* ---- Labels ---- */
QLabel#title { font-size: 20px; font-weight: 700; color: #f0f0f5; }
QLabel#statv { font-size: 26px; font-weight: 700; }
QLabel#statl { font-size: 11px; color: #666; }

/* ---- Group Boxes ---- */
QGroupBox {
    border: 1px solid rgba(255,255,255,0.05); border-radius: 8px; margin-top: 10px;
    padding: 10px 10px 8px; font-weight: 500; font-size: 11px; color: #888;
    background: rgba(255,255,255,0.015);
}
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; color: #888; }

/* ---- Text (Logs) ---- */
QTextEdit {
    background: #06060a; color: #888; border: 1px solid rgba(255,255,255,0.04);
    border-radius: 6px; padding: 8px; font-family: Consolas,'Courier New',monospace; font-size: 12px;
}

/* ---- Status Bar ---- */
QStatusBar { background: rgba(0,0,0,0.4); color: #666; border-top: 1px solid rgba(255,255,255,0.03); font-size: 12px; }
QStatusBar::item { border: none; }

/* ---- Scrollbars ---- */
QScrollBar:vertical { background: transparent; width: 6px; }
QScrollBar::handle:vertical { background: rgba(255,255,255,0.08); border-radius: 3px; min-height: 24px; }
QScrollBar::handle:vertical:hover { background: rgba(255,255,255,0.15); }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* ---- Splitter ---- */
QSplitter::handle { background: rgba(255,255,255,0.05); width: 1px; }

/* ---- Combo Box ---- */
QComboBox {
    background: rgba(255,255,255,0.03); color: #e8e8ed; border: 1px solid rgba(255,255,255,0.08);
    border-radius: 6px; padding: 6px 10px; font-size: 13px; min-height: 20px;
}
QComboBox:focus { border-color: #FFD700; }
QComboBox::drop-down { border: none; width: 24px; }
QComboBox::down-arrow { image: none; border-left: 4px solid transparent; border-right: 4px solid transparent; border-top: 5px solid #888; margin-right: 6px; }
QComboBox QAbstractItemView { background: #14141e; color: #e8e8ed; border: 1px solid rgba(255,255,255,0.08); selection-background-color: rgba(255,215,0,0.1); selection-color: #FFD700; }
"""

# ═══════════════════════════════════════════════════════════════
# WIDGETS
# ═══════════════════════════════════════════════════════════════

class StatCard(QFrame):
    def __init__(self, label, initial="0", color="#10b981"):
        super().__init__()
        self.setObjectName("sc")
        self.setStyleSheet(f"#sc{{background:rgba(22,22,34,0.65);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;}}"
                           f"#sc:hover{{border-color:rgba(255,215,0,0.3);background:rgba(22,22,34,0.8);}}")
        lo = QVBoxLayout()
        lo.setContentsMargins(14, 10, 14, 10)
        lo.setSpacing(2)
        self.v = QLabel(initial)
        self.v.setObjectName("statv")
        self.v.setStyleSheet(f"font-size:30px;font-weight:800;color:{color};")
        lo.addWidget(self.v)
        l = QLabel(label)
        l.setObjectName("statl")
        lo.addWidget(l)
        self.setLayout(lo)
    def set_val(self, x): self.v.setText(str(x))

# ═══════════════════════════════════════════════════════════════
# ANIMATED BUTTON
# ═══════════════════════════════════════════════════════════════

class AnimatedButton(QPushButton):
    _bg_start = QColor(255, 255, 255, 10)
    _bg_hover = QColor(255, 255, 255, 25)
    _bg_press = QColor(0, 0, 0, 50)

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._cur = QColor(255, 255, 255, 10)
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(180)
        self._anim.valueChanged.connect(self._apply)

    def _apply(self, c):
        self._cur = c
        a = c.alpha() / 255; r, g, b = c.red(), c.green(), c.blue()
        self.setStyleSheet(
            f"QPushButton{{background:rgba({r},{g},{b},{a});border:1px solid rgba(255,255,255,{6+int(9*a)});border-radius:8px;padding:8px 18px;font-size:13px;font-weight:500;color:#ccc;}}"
            f"QPushButton:hover{{background:rgba({min(r+10,255)},{min(g+10,255)},{min(b+10,255)},{min(a+0.08,0.5)});border-color:rgba(255,215,0,0.3);}}"
            f"QPushButton:pressed{{background:rgba(0,0,0,0.2);}}"
        )

    def _anim_to(self, target):
        self._anim.stop()
        self._anim.setStartValue(self._cur)
        self._anim.setEndValue(target)
        self._anim.start()

    def enterEvent(self, e):
        self._anim_to(AnimatedButton._bg_hover)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._anim_to(AnimatedButton._bg_start)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._anim_to(AnimatedButton._bg_press)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._anim_to(self._cur if self.underMouse() else AnimatedButton._bg_start)
        super().mouseReleaseEvent(e)


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

        # Anti-debug check
        if not combined.check_anti_debug():
            self.st.setText("Debugger detected. Exiting.")
            self.st.setStyleSheet("color:#ef4444;font-size:13px;")
            QTimer.singleShot(2000, self.close)
            return

        # Try online activation first
        hwid = combined.get_hwid()
        try:
            resp = combined.requests.post(LICENSE_SERVER_URL, json={"key": key, "hwid": hwid}, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("valid"):
                    with open(BASE_DIR / "license.dat", "w") as f:
                        json.dump({"key": key, "tier": data.get("tier", "premium"), "hwid": hwid, "at": time.time()}, f)
                    self.accept()
                    return
                else:
                    self.st.setText(data.get("reason", "License rejected by server."))
                    self.st.setStyleSheet("color:#ef4444;font-size:13px;font-weight:600;")
                    return
        except:
            pass  # Server unreachable, fall through to local

        # Fallback to local validation
        result = combined.validate_license_key(key)
        if result.get("valid"):
            with open(BASE_DIR / "license.dat", "w") as f:
                json.dump({"key": key, "tier": result.get("tier"), "hwid": hwid, "at": time.time()}, f)
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

    def __init__(self, domain, username, password, login_method="email"):
        super().__init__()
        self.domain = domain
        self.username = username
        self.password = password
        self.login_method = login_method

    def run(self):
        self.log.emit(f"[{datetime.now():%H:%M:%S}] Starting claim for {self.domain}...")
        try:
            auto = combined.CasinoAutomation(headless=combined.HEADLESS_MODE)
            if not auto.start():
                self.log.emit(f"[{datetime.now():%H:%M:%S}] ❌ Browser failed for {self.domain}")
                self.done.emit(self.domain, False, 0); return
            self.log.emit(f"[{datetime.now():%H:%M:%S}] Logging into {self.domain}...")
            if auto.login(self.domain, self.username, self.password, self.login_method):
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
        lo.setContentsMargins(16, 16, 16, 16)
        lo.setSpacing(14)

        t = QLabel("Dashboard")
        t.setObjectName("title")
        lo.addWidget(t)

        g = QHBoxLayout()
        g.setSpacing(12)
        self.c1 = StatCard("Total SC Claimed", "$0.00", "#22c55e")
        self.c2 = StatCard("Claims Today", "0")
        self.c3 = StatCard("Alerts Sent", "0")
        self.c4 = StatCard("Uptime", "0h 0m", "#6366f1")
        g.addWidget(self.c1); g.addWidget(self.c2); g.addWidget(self.c3); g.addWidget(self.c4)
        lo.addLayout(g)

        # Control center
        mc = QGroupBox("Dashboard")
        mcl = QVBoxLayout()
        self.master_btn = QPushButton("Start All")
        self.master_btn.setObjectName("success")
        self.master_btn.setStyleSheet("QPushButton{background:#10b981;color:#fff;border-radius:10px;padding:14px 32px;font-size:15px;font-weight:700;}QPushButton:hover{background:#059669;}")
        self.master_btn.clicked.connect(self.toggle_master)
        mcl.addWidget(self.master_btn)
        # Service indicators
        sind = QHBoxLayout()
        sind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.inds = {}
        for name in ["Scanner","Claims","Streamer","Links"]:
            b = QLabel(f"\u25cf {name}")
            b.setStyleSheet("color:#475569;font-size:12px;padding:4px 12px;")
            self.inds[name] = b
            sind.addWidget(b)
        mcl.addLayout(sind)
        mc.setLayout(mcl); lo.addWidget(mc)

        # System & Quick Access
        row = QHBoxLayout()
        sig = QGroupBox("System")
        sil = QVBoxLayout()
        lf = BASE_DIR / "license.dat"
        self.tier = "Premium"
        if lf.exists():
            try:
                with open(lf) as f: ld = json.load(f)
                self.tier = ld.get("tier","Premium")
            except: pass
        self.sys_info = QLabel(f"{APP_VERSION}  |  {self.tier}  |  Scans: 0  |  Found: 0  |  Last: N/A")
        self.sys_info.setStyleSheet("font-size:12px;color:#94a3b8;")
        sil.addWidget(self.sys_info)
        self.last_refresh_lbl = QLabel("Last ping: —")
        self.last_refresh_lbl.setStyleSheet("font-size:11px;color:#64748b;")
        sil.addWidget(self.last_refresh_lbl)
        sig.setLayout(sil); row.addWidget(sig)
        qag = QGroupBox("Quick Access")
        qal = QHBoxLayout(); qal.setSpacing(8)
        open_btn = QPushButton("Open Data Folder")
        open_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(BASE_DIR))))
        qal.addWidget(open_btn)
        check_btn = QPushButton("Check Now")
        check_btn.clicked.connect(self.force_check)
        qal.addWidget(check_btn)
        qag.setLayout(qal); row.addWidget(qag)
        lo.addLayout(row)

        lg = QGroupBox("Activity Log")
        ll = QVBoxLayout()
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Log"))
        hl.addStretch()
        cls = QPushButton("Clear")
        cls.setFixedWidth(70)
        cls.clicked.connect(lambda: self.logv.clear())
        hl.addWidget(cls)
        ll.addLayout(hl)
        self.logv = QTextEdit()
        self.logv.setReadOnly(True)
        self.logv.setMaximumHeight(100)
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

    def set_indicator(self, name, on):
        if name in self.inds:
            self.inds[name].setStyleSheet(f"color:#{'10b981' if on else '475569'};font-size:12px;padding:4px 12px;")

    def toggle_master(self):
        if self.running: self.stop_master()
        else: self.start_master()

    def start_master(self):
        self.log("[MASTER] Starting...")
        self.running = True
        self.master_btn.setText("Stop All")
        self.master_btn.setStyleSheet("QPushButton{background:#ef4444;color:#fff;border-radius:10px;padding:14px 32px;font-size:15px;font-weight:700;}QPushButton:hover{background:#dc2626;}")
        for fn in [combined.monitor_loop, combined.daily_freebies_loop]:
            t = threading.Thread(target=fn, daemon=True); t.start(); self.threads.append(t)
        self.set_indicator("Scanner", True)
        t = threading.Thread(target=combined.claim_scheduler_loop, daemon=True); t.start(); self.threads.append(t)
        self.set_indicator("Claims", True)
        if hasattr(combined, 'monitor_streamer_loop'):
            t = threading.Thread(target=combined.monitor_streamer_loop, daemon=True); t.start(); self.threads.append(t)
        self.set_indicator("Streamer", True)
        if hasattr(combined, 'process_queue_loop'):
            t = threading.Thread(target=combined.process_queue_loop, daemon=True); t.start(); self.threads.append(t)
        self.set_indicator("Links", True)
        with combined.state_lock:
            combined.state["bot_status"] = "online"; combined.state["status"] = "online"
        self.log("[MASTER] All systems running")

    def stop_master(self):
        self.log("[MASTER] Stopping...")
        self.running = False
        self.master_btn.setText("Start All")
        self.master_btn.setStyleSheet("QPushButton{background:#10b981;color:#fff;border-radius:10px;padding:14px 32px;font-size:15px;font-weight:700;}QPushButton:hover{background:#059669;}")
        with combined.state_lock:
            combined.state["bot_status"] = "offline"; combined.state["status"] = "offline"
        for name in self.inds:
            self.set_indicator(name, False)
        self.log("[MASTER] Stopped")

    def force_check(self):
        self.log("[DASH] Manual scan triggered")
        try:
            t = threading.Thread(target=combined.monitor_loop, daemon=True)
            t.start()
            self.log("[DASH] Scan dispatched")
        except Exception as e:
            self.log(f"[DASH] Scan failed: {e}")

    def refresh(self):
        with combined.state_lock:
            s = dict(combined.state)
        self.c1.set_val(f"${s.get('sc_total',0):.2f}")
        self.c2.set_val(str(s.get('claimed',0)))
        self.c3.set_val(str(s.get('found',0)))
        u = s.get('runtime',0); h,m = divmod(u,3600); m//=60
        self.c4.set_val(f"{int(h)}h {int(m)}m")
        la = s.get('last_alert')
        last_title = la.get('title','N/A')[:40] if la else 'N/A'
        self.sys_info.setText(f"{APP_VERSION}  |  {self.tier}  |  Scans: {s.get('scanned',0)}  |  Found: {s.get('found',0)}  |  Last: {last_title}")
        self.last_refresh_lbl.setText(f"Last ping: {datetime.now():%H:%M:%S}")
        st = s.get("bot_status","offline")
        if st=="online":
            self.set_indicator("Scanner", True)
        else:
            self.set_indicator("Scanner", False)

# ═══════════════════════════════════════════════════════════════
# DAILY SC TAB (Accounts + Schedule + Log merged)
# ═══════════════════════════════════════════════════════════════

class DailySCTab(QWidget):
    def __init__(self):
        super().__init__()
        self.workers = []
        lo = QVBoxLayout()
        lo.setContentsMargins(16, 16, 16, 16)
        lo.setSpacing(12)

        t = QLabel("Daily SC")
        t.setObjectName("title")
        lo.addWidget(t)

        # Summary + Upcoming Claims row
        sum_row = QHBoxLayout()
        sg = QGroupBox("Summary")
        sl = QHBoxLayout()
        self.daily_stat_labels = []
        for label, color in [("Total","#888"),("SC","#FFD700"),("Pending","#eab308"),("Rate","#10b981"),("Coverage","#6366f1")]:
            c = QVBoxLayout()
            c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl = QLabel("0")
            lbl.setStyleSheet(f"font-size:18px;font-weight:700;color:{color};")
            c.addWidget(lbl)
            c.addWidget(QLabel(label))
            self.daily_stat_labels.append(lbl)
            sl.addLayout(c)
        sg.setLayout(sl); sum_row.addWidget(sg)

        ng = QGroupBox("Upcoming")
        nl = QVBoxLayout()
        nl.setContentsMargins(6,6,6,6)
        self.next_tbl = QTableWidget()
        self.next_tbl.setColumnCount(3)
        self.next_tbl.setHorizontalHeaderLabels(["Casino","Ready In","Status"])
        self.next_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.next_tbl.verticalHeader().setVisible(False)
        self.next_tbl.setMaximumHeight(80)
        self.next_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.next_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        nl.addWidget(self.next_tbl)
        ng.setLayout(nl); sum_row.addWidget(ng, 1)
        lo.addLayout(sum_row)

        # Toolbar
        tb = QHBoxLayout(); tb.setSpacing(8)
        a = QPushButton("+ Add"); a.setObjectName("gold"); a.clicked.connect(self.add); tb.addWidget(a)
        ca = QPushButton("Claim All"); ca.setObjectName("success"); ca.clicked.connect(self.claim_all); tb.addWidget(ca)
        stp = QPushButton("Stop All"); stp.setObjectName("danger"); stp.clicked.connect(self.stop_all); tb.addWidget(stp)
        imp = AnimatedButton("Import"); imp.clicked.connect(self.import_accts); tb.addWidget(imp)
        r = AnimatedButton("Refresh"); r.clicked.connect(self.load); tb.addWidget(r); tb.addStretch(); lo.addLayout(tb)

        # Accounts table (stretch)
        aw = QGroupBox("Accounts")
        al = QVBoxLayout(aw); al.setContentsMargins(6,6,6,6); al.setSpacing(4)
        self.tbl = QTableWidget()
        self.tbl.setColumnCount(9)
        self.tbl.setHorizontalHeaderLabels(["Domain","Username","Login","Last Claim","Status","SC Total","","",""])
        self.tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        al.addWidget(self.tbl)
        lo.addWidget(aw, 1)

        # Schedule + Log bottom
        bw = QGroupBox("Schedule & Log")
        bl = QVBoxLayout(bw); bl.setContentsMargins(6,6,6,6); bl.setSpacing(4)
        self.schtbl = QTableWidget()
        self.schtbl.setColumnCount(5)
        self.schtbl.setHorizontalHeaderLabels(["Casino","Last Claim","Next Claim","Status","Cooldown"])
        self.schtbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.schtbl.verticalHeader().setVisible(False)
        self.schtbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.schtbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.schtbl.setMaximumHeight(100)
        bl.addWidget(self.schtbl)
        self.logv = QTextEdit()
        self.logv.setReadOnly(True)
        self.logv.setMaximumHeight(50)
        bl.addWidget(self.logv)
        lo.addWidget(bw)
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

        total_sc = sum(a.get("sc_total",0) for a in accts.values())
        pending = sum(1 for d,s in sched.items() if s.get("status")=="claiming")
        success_count = sum(1 for d,s in sched.items() if s.get("status")=="done")
        total_claims = len([d for d,s in sched.items() if s.get("last_claim",0)>0])
        rate = f"{success_count/max(total_claims,1)*100:.0f}%" if total_claims else "—"
        coverage = f"{len(accts)}/{len(sites)}"

        self.daily_stat_labels[0].setText(str(len(accts)))
        self.daily_stat_labels[1].setText(f"${total_sc:.2f}")
        self.daily_stat_labels[2].setText(str(pending))
        self.daily_stat_labels[3].setText(rate)
        self.daily_stat_labels[4].setText(coverage)

        # Account table
        self.tbl.setRowCount(len(accts))
        for i,(dom,info) in enumerate(sorted(accts.items())):
            self.tbl.setItem(i,0,QTableWidgetItem(sm.get(dom,dom)))
            self.tbl.setItem(i,1,QTableWidgetItem(info.get("username","")))
            lm = info.get("login_method","email")
            lmi = QTableWidgetItem(lm.capitalize())
            lmi.setForeground(QColor("#6366f1" if lm=="google" else "#ef4444" if lm=="apple" else "#888"))
            self.tbl.setItem(i,2,lmi)
            sc = sched.get(dom,{})
            lc = sc.get("last_claim",0)
            self.tbl.setItem(i,3,QTableWidgetItem(datetime.fromtimestamp(lc).strftime("%m/%d %H:%M") if lc else "Never"))
            st = sc.get("status","never")
            si = QTableWidgetItem(st.upper())
            si.setForeground(QColor("#10b981" if st in ("done","never") else "#eab308" if st=="claiming" else "#ef4444"))
            self.tbl.setItem(i,4,si)
            sct = info.get("sc_total",0)
            sci = QTableWidgetItem(f"${sct:.2f}")
            sci.setForeground(QColor("#FFD700"))
            self.tbl.setItem(i,5,sci)
            b = QPushButton("Claim")
            b.setObjectName("success")
            b.setStyleSheet("QPushButton{background:#10b981;color:#fff;border-radius:6px;padding:4px 12px;font-size:11px;font-weight:600;}QPushButton:hover{background:#059669;}")
            b.clicked.connect(lambda checked,d=dom: self.claim(d))
            self.tbl.setCellWidget(i,6,b)
            tb = QPushButton("Test")
            tb.setStyleSheet("QPushButton{color:#eab308;font-size:11px;padding:4px 10px;border-radius:6px;}")
            tb.clicked.connect(lambda checked,d=dom: self.log(f"[TEST] Test login for {d} (stub)"))
            self.tbl.setCellWidget(i,7,tb)
            rb = QPushButton("Remove")
            rb.setStyleSheet("QPushButton{color:#ef4444;font-size:11px;padding:4px 10px;border-radius:6px;}")
            rb.clicked.connect(lambda checked,d=dom: self.remove_account(d))
            self.tbl.setCellWidget(i,8,rb)

        # Schedule table
        now = time.time()
        doms = set(sm.keys()); doms.update(sched.keys())
        self.schtbl.setRowCount(len(doms))
        ready_list = []
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
            ni.setForeground(QColor("#10b981" if ns=="Ready Now" else "#eab308"))
            self.schtbl.setItem(i,2,ni)
            st = s.get("status","never")
            si = QTableWidgetItem(st.upper())
            si.setForeground(QColor("#10b981" if st in ("done","never") else "#eab308" if st=="claiming" else "#ef4444"))
            self.schtbl.setItem(i,3,si)
            if lc:
                pct = min(100,int(((now-lc)/86400)*100))
                bar = "█"*(pct//5)+"░"*(20-pct//5)
                self.schtbl.setItem(i,4,QTableWidgetItem(f"{pct}% {bar}"))
            else: self.schtbl.setItem(i,4,QTableWidgetItem("—"))
            # Collect for upcoming claims
            if ns != "Ready Now" and st != "claiming" and dom in accts:
                ready_list.append((ns, sm.get(dom,dom), s.get("status","never")))

        # Next Claims table (top 3 soonest)
        ready_list.sort()
        self.next_tbl.setRowCount(min(len(ready_list), 3))
        for i, (time_left, casino, status) in enumerate(ready_list[:3]):
            self.next_tbl.setItem(i,0,QTableWidgetItem(casino))
            self.next_tbl.setItem(i,1,QTableWidgetItem(time_left))
            si = QTableWidgetItem(status.upper())
            si.setForeground(QColor("#eab308"))
            self.next_tbl.setItem(i,2,si)

    def remove_account(self, dom):
        if QMessageBox.question(self,"Remove Account",f"Remove {dom}?",
            QMessageBox.StandardButton.Yes|QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes: return
        accts = combined.load_accounts()
        if dom in accts:
            del accts[dom]
            combined.save_accounts(accts)
            sched = combined.load_claim_schedule()
            if dom in sched:
                del sched[dom]
                combined.save_claim_schedule(sched)
            self.load()
            self.log(f"[USER] Removed account: {dom}")

    def claim(self, dom):
        accts = combined.load_accounts()
        if dom not in accts: return
        info = accts[dom]
        self.log(f"[USER] Manual claim: {dom}")
        sched = combined.load_claim_schedule()
        sched[dom] = sched.get(dom,{"last_claim":0,"status":"claiming"})
        sched[dom]["status"] = "claiming"
        combined.save_claim_schedule(sched)
        w = ClaimWorker(dom,info["username"],info["password"],info.get("login_method","email"))
        w.log.connect(self.log)
        w.done.connect(self.fin)
        self.workers.append(w); w.start()

    def claim_all(self):
        accts = combined.load_accounts()
        for dom in accts:
            self.claim(dom)

    def stop_all(self):
        for w in self.workers:
            if w.isRunning():
                w.terminate()
                w.wait()
        self.workers.clear()
        sched = combined.load_claim_schedule()
        for dom in sched:
            if sched[dom].get("status") == "claiming":
                sched[dom]["status"] = "never"
        combined.save_claim_schedule(sched)
        self.log("[USER] Stopped all pending claims")
        self.load()

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

    def import_accts(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Import Accounts", str(BASE_DIR), "JSON Files (*.json)")
        if not fn: return
        try:
            with open(fn) as f: data = json.load(f)
            if not isinstance(data, dict): raise ValueError("Expected dict")
            accts = combined.load_accounts()
            count = 0
            for dom, info in data.items():
                if dom not in accts and "username" in info and "password" in info:
                    accts[dom] = {"username": info["username"], "password": info["password"], "sc_total": info.get("sc_total",0), "login_method": info.get("login_method","email")}
                    count += 1
            combined.save_accounts(accts)
            self.log(f"[USER] Imported {count} accounts from {Path(fn).name}")
            self.load()
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))

    def add(self):
        d = AddAccountDlg(self)
        if d.exec():
            dom,un,pw,lm = d.vals()
            if dom and un and pw:
                accts = combined.load_accounts()
                accts[dom] = {"username":un,"password":pw,"sc_total":0,"login_method":lm}
                combined.save_accounts(accts)
                self.load()
                self.log(f"[USER] Added: {dom} ({lm})")

class AddAccountDlg(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Account"); self.setFixedSize(400,320)
        lo = QVBoxLayout(); lo.setContentsMargins(24,24,24,24); lo.setSpacing(12)
        t = QLabel("Add Account"); t.setObjectName("title"); t.setStyleSheet("font-size:20px;"); lo.addWidget(t)
        fm = QFormLayout(); fm.setSpacing(10)
        self.d = QComboBox()
        sites = combined.load_sites()
        for s in sites:
            self.d.addItem(f"{s['name']} ({s['domain']})", s["domain"])
        self.d.setEditable(True)
        fm.addRow("Casino:",self.d)
        self.u = QLineEdit(); self.u.setPlaceholderText("Account email"); fm.addRow("Username:",self.u)
        self.p = QLineEdit(); self.p.setPlaceholderText("Password"); self.p.setEchoMode(QLineEdit.EchoMode.Password); fm.addRow("Password:",self.p)
        self.lm = QComboBox()
        self.lm.addItems(["Email", "Google", "Apple"])
        fm.addRow("Login Method:", self.lm)
        lo.addLayout(fm); lo.addSpacing(12)
        bl = QHBoxLayout()
        s = QPushButton("Save"); s.setObjectName("gold"); s.clicked.connect(self.accept)
        c = QPushButton("Cancel"); c.clicked.connect(self.reject)
        bl.addWidget(s); bl.addWidget(c); lo.addLayout(bl)
        self.setLayout(lo)
    def vals(self): return self.d.currentData() or self.d.currentText().strip(),self.u.text().strip(),self.p.text().strip(),self.lm.currentText().lower()

# ═══════════════════════════════════════════════════════════════
# STREAMER SNIPER TAB
# ═══════════════════════════════════════════════════════════════

class StreamerSniperTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout()
        lo.setContentsMargins(16,16,16,16); lo.setSpacing(12)

        t = QLabel("Streamer Sniper")
        t.setObjectName("title"); lo.addWidget(t)

        self.sniper_stats = QLabel("Monitored: 0  \u00b7  Online: 0  \u00b7  Checks: 0")
        self.sniper_stats.setStyleSheet("font-size:13px;color:#94a3b8;padding:4px 0;")

        tb = QHBoxLayout(); tb.setSpacing(8)
        tb.addWidget(self.sniper_stats); tb.addStretch()
        self.sniper_tgl = QPushButton("Watch")
        self.sniper_tgl.setObjectName("success")
        self.sniper_tgl.clicked.connect(self.toggle_sniper)
        tb.addWidget(self.sniper_tgl)
        refresh_btn = QPushButton("Refresh All")
        refresh_btn.clicked.connect(self.force_refresh)
        tb.addWidget(refresh_btn)
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
        self.sadd = QPushButton("+ Add"); self.sadd.setObjectName("gold"); self.sadd.clicked.connect(self.add_streamer)
        self.srm = QPushButton("Remove"); self.srm.clicked.connect(self.remove_streamer)
        exp = QPushButton("Export"); exp.clicked.connect(self.export_streamers)
        ab.addWidget(self.sadd); ab.addWidget(self.srm); ab.addWidget(exp); ab.addStretch()
        sl.addLayout(ab)
        sg.setLayout(sl); lo.addWidget(sg)

        # Detection History + Log side by side
        bot_row = QHBoxLayout()
        dg = QGroupBox("Detections")
        dl = QVBoxLayout()
        dl.setContentsMargins(6,6,6,6)
        self.detect_tbl = QTableWidget()
        self.detect_tbl.setColumnCount(3)
        self.detect_tbl.setHorizontalHeaderLabels(["Time","Platform","Username"])
        self.detect_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.detect_tbl.verticalHeader().setVisible(False)
        self.detect_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.detect_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        dl.addWidget(self.detect_tbl)
        dg.setLayout(dl); bot_row.addWidget(dg)
        lg = QGroupBox("Log")
        ll = QVBoxLayout()
        ll.setContentsMargins(6,6,6,6)
        self.sniper_log = QTextEdit()
        self.sniper_log.setReadOnly(True)
        ll.addWidget(self.sniper_log)
        lg.setLayout(ll); bot_row.addWidget(lg)
        lo.addLayout(bot_row)

        lo.addStretch()
        self.setLayout(lo)
        self.sniper_running = False
        self.sniper_threads = []
        self.check_count = 0
        self.detections = []
        self.refresh_streamers()
        self.sniper_timer = QTimer()
        self.sniper_timer.timeout.connect(self.refresh_streamers)
        self.sniper_timer.start(10000)

    def log(self, msg):
        self.sniper_log.append(msg)
        sb = self.sniper_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def refresh_streamers(self):
        streamers = combined.load_streamers() if hasattr(combined, 'load_streamers') else []
        self.streamer_list.setRowCount(len(streamers))
        online = 0
        self.check_count += 1
        for i, s in enumerate(streamers):
            self.streamer_list.setItem(i,0,QTableWidgetItem(s.get("platform","Kick")))
            self.streamer_list.setItem(i,1,QTableWidgetItem(s.get("username","")))
            status = s.get("status","idle")
            si = QTableWidgetItem(status)
            si.setForeground(QColor("#10b981" if status=="live" else "#eab308" if status=="idle" else "#475569"))
            self.streamer_list.setItem(i,2,si)
            self.streamer_list.setItem(i,3,QTableWidgetItem(s.get("last_seen","Never")))
            if status == "live":
                online += 1
                # Log new detection
                if not self.detections or self.detections[-1].get("username") != s.get("username") or self.detections[-1].get("timestamp","") < datetime.now().strftime("%Y-%m-%d %H:%M"):
                    self.detections.append({"timestamp": datetime.now().strftime("%H:%M:%S"), "platform": s.get("platform",""), "username": s.get("username","")})
                    if len(self.detections) > 20: self.detections = self.detections[-20:]
        self.sniper_stats.setText(f"Monitored: {len(streamers)}  \u00b7  Online: {online}  \u00b7  Checks: {self.check_count}")
        # Update detection history table
        self.detect_tbl.setRowCount(min(len(self.detections), 10))
        for i, d in enumerate(self.detections[-10:]):
            self.detect_tbl.setItem(i,0,QTableWidgetItem(d.get("timestamp","")))
            self.detect_tbl.setItem(i,1,QTableWidgetItem(d.get("platform","")))
            self.detect_tbl.setItem(i,2,QTableWidgetItem(d.get("username","")))

    def force_refresh(self):
        self.log("[SNIPER] Refreshing all streamers...")
        if hasattr(combined, 'monitor_streamer_loop'):
            t = threading.Thread(target=combined.monitor_streamer_loop, daemon=True)
            t.start()
        self.refresh_streamers()
        self.log("[SNIPER] Refresh complete")

    def export_streamers(self):
        streamers = combined.load_streamers() if hasattr(combined, 'load_streamers') else []
        fn, _ = QFileDialog.getSaveFileName(self, "Export Streamers", str(BASE_DIR / "streamers_export.json"), "JSON Files (*.json)")
        if not fn: return
        try:
            with open(fn, 'w') as f: json.dump(streamers, f, indent=2)
            self.log(f"[SNIPER] Exported {len(streamers)} streamers to {Path(fn).name}")
        except Exception as e:
            self.log(f"[SNIPER] Export failed: {e}")

    def add_streamer(self):
        dlg = QDialog(self); dlg.setWindowTitle("Add Streamer"); dlg.setFixedSize(360,220)
        lo = QVBoxLayout(dlg); lo.setSpacing(12)
        lo.addWidget(QLabel("Streamer Username:"))
        un = QLineEdit(); un.setPlaceholderText("streamer_name"); lo.addWidget(un)
        lo.addWidget(QLabel("Platform:"))
        plat = QComboBox(); plat.addItems(["Kick", "Twitch"]); lo.addWidget(plat)
        bl = QHBoxLayout()
        ok = QPushButton("Add"); ok.setObjectName("gold"); ok.clicked.connect(dlg.accept)
        no = QPushButton("Cancel"); no.clicked.connect(dlg.reject)
        bl.addWidget(ok); bl.addWidget(no); lo.addLayout(bl)
        if dlg.exec():
            u = un.text().strip()
            p = plat.currentText()
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
            self.sniper_tgl.setText("Watch")
            self.sniper_tgl.setObjectName("success"); self.sniper_tgl.style().unpolish(self.sniper_tgl); self.sniper_tgl.style().polish(self.sniper_tgl)
            self.log("[SNIPER] Stopped")
        else:
            self.sniper_running = True
            self.sniper_tgl.setText("Stop Watching")
            self.sniper_tgl.setObjectName("danger"); self.sniper_tgl.style().unpolish(self.sniper_tgl); self.sniper_tgl.style().polish(self.sniper_tgl)
            self.log("[SNIPER] Watching...")
            if hasattr(combined, 'monitor_streamer_loop'):
                t = threading.Thread(target=combined.monitor_streamer_loop, daemon=True)
                t.start(); self.sniper_threads.append(t)
            self.log("[SNIPER] Active")

# ═══════════════════════════════════════════════════════════════
# LINK AUTOMATION TAB
# ═══════════════════════════════════════════════════════════════

class LinkAutomationTab(QWidget):
    def __init__(self):
        super().__init__()
        lo = QVBoxLayout()
        lo.setContentsMargins(16,16,16,16); lo.setSpacing(12)

        t = QLabel("Link Automation")
        t.setObjectName("title"); lo.addWidget(t)

        # Stats frame
        sg = QGroupBox("Link Stats")
        sl = QHBoxLayout()
        self.link_stats_labels = []
        for label, color in [("Total","#888"),("Processed","#eab308"),("Success","#10b981"),("Failed","#ef4444"),("Rate","#6366f1")]:
            c = QVBoxLayout()
            c.addWidget(QLabel("0"))
            c.addWidget(QLabel(label))
            c.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.link_stats_labels.append(c.itemAt(0).widget())
            sl.addLayout(c)
        sg.setLayout(sl); lo.addWidget(sg)

        # Add URL + casino dropdown + buttons inline
        ab = QHBoxLayout()
        self.casino_combo = QComboBox()
        self.casino_combo.setEditable(True)
        self.casino_combo.setPlaceholderText("Select casino...")
        sites = combined.load_sites()
        for s in sites:
            self.casino_combo.addItem(f"{s['name']} ({s['domain']})", s["domain"])
        self.casino_combo.setMinimumWidth(200)
        ab.addWidget(self.casino_combo)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste sweepstakes link...")
        ab.addWidget(self.url_input, 1)
        val_btn = AnimatedButton("Validate"); val_btn.clicked.connect(self.validate_url); ab.addWidget(val_btn)
        self.add_btn = QPushButton("+ Add Link"); self.add_btn.setObjectName("gold"); self.add_btn.clicked.connect(self.add_link); ab.addWidget(self.add_btn)
        lo.addLayout(ab)

        # Queue table (stretches)
        self.queue_tbl = QTableWidget()
        self.queue_tbl.setColumnCount(5)
        self.queue_tbl.setHorizontalHeaderLabels(["URL","Added","Status","Result",""])
        self.queue_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.queue_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.queue_tbl.verticalHeader().setVisible(False)
        self.queue_tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.queue_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lo.addWidget(self.queue_tbl, 1)

        # Controls row
        ctrl_row = QHBoxLayout()
        self.process_btn = QPushButton("Process All")
        self.process_btn.setObjectName("success")
        self.process_btn.clicked.connect(self.process_queue)
        ctrl_row.addWidget(self.process_btn)
        self.auto_toggle = QPushButton("Auto")
        self.auto_toggle.setStyleSheet("QPushButton{background:#1e1e2a;color:#64748b;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 16px;font-size:11px;font-weight:600;}QPushButton:hover{background:#2a2a36;}")
        self.auto_toggle.clicked.connect(self.toggle_auto)
        ctrl_row.addWidget(self.auto_toggle)
        cc_btn = AnimatedButton("Clear Done"); cc_btn.clicked.connect(self.clear_completed); ctrl_row.addWidget(cc_btn)
        self.clear_btn = AnimatedButton("Clear"); self.clear_btn.clicked.connect(self.clear_queue); ctrl_row.addWidget(self.clear_btn)
        ctrl_row.addStretch()
        self.last_result_lbl = QLabel("No links processed yet")
        self.last_result_lbl.setStyleSheet("font-size:11px;color:#64748b;")
        ctrl_row.addWidget(self.last_result_lbl)
        lo.addLayout(ctrl_row)

        # Bottom panels: Monitor Feed + Log side by side
        bottom_row = QHBoxLayout()
        # Monitor Feed
        mg = QGroupBox("Monitor Feed")
        ml = QVBoxLayout(mg); ml.setContentsMargins(6,6,6,6); ml.setSpacing(4)
        self.monitor_tbl = QTableWidget()
        self.monitor_tbl.setColumnCount(3)
        self.monitor_tbl.setHorizontalHeaderLabels(["Title","SC","Source"])
        self.monitor_tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.monitor_tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.monitor_tbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.monitor_tbl.verticalHeader().setVisible(False)
        self.monitor_tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.monitor_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.monitor_tbl.setMaximumHeight(120)
        ml.addWidget(self.monitor_tbl)
        bottom_row.addWidget(mg, 1)

        # Log
        lg = QGroupBox("Log")
        ll = QVBoxLayout(lg); ll.setContentsMargins(6,6,6,6)
        self.link_log = QTextEdit()
        self.link_log.setReadOnly(True)
        self.link_log.setMaximumHeight(120)
        ll.addWidget(self.link_log)
        bottom_row.addWidget(lg, 1)
        lo.addLayout(bottom_row)

        self.setLayout(lo)
        self.auto_running = False
        self.refresh_queue()
        self.link_timer = QTimer()
        self.link_timer.timeout.connect(self.refresh_queue)
        self.link_timer.start(5000)

    def log(self, msg):
        self.link_log.append(msg)
        sb = self.link_log.verticalScrollBar(); sb.setValue(sb.maximum())

    def refresh_queue(self):
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        self.queue_tbl.setRowCount(len(queue))

        # Update Monitor Feed
        feed = list(combined.monitor_feed) if hasattr(combined, 'monitor_feed') else []
        self.monitor_tbl.setRowCount(len(feed))
        for i, entry in enumerate(feed):
            self.monitor_tbl.setItem(i,0,QTableWidgetItem(entry.get("title","")[:50]))
            sa = entry.get("sc_amount")
            self.monitor_tbl.setItem(i,1,QTableWidgetItem(f"${sa:.2f}" if sa else "—"))
            self.monitor_tbl.setItem(i,2,QTableWidgetItem(entry.get("subreddit","")))
        total = len(queue)
        processed = sum(1 for q in queue if q.get("status") in ("done","failed"))
        success = sum(1 for q in queue if q.get("status") == "done")
        failed = sum(1 for q in queue if q.get("status") == "failed")
        rate = f"{success/max(processed,1)*100:.0f}%" if processed else "—"
        self.link_stats_labels[0].setText(str(total))
        self.link_stats_labels[1].setText(str(processed))
        self.link_stats_labels[2].setText(str(success))
        self.link_stats_labels[3].setText(str(failed))
        self.link_stats_labels[4].setText(rate)
        # Last result
        done_items = [q for q in queue if q.get("status") in ("done","failed")]
        if done_items:
            last = done_items[-1]
            self.last_result_lbl.setText(f"{last.get('url','')[:50]} — {last.get('result','')}")
        for i, item in enumerate(queue):
            self.queue_tbl.setItem(i,0,QTableWidgetItem(item.get("url","")[:60]))
            self.queue_tbl.setItem(i,1,QTableWidgetItem(item.get("added","")))
            st = item.get("status","pending")
            si = QTableWidgetItem(st)
            si.setForeground(QColor("#10b981" if st=="done" else "#ef4444" if st=="failed" else "#eab308" if st=="processing" else "#64748b"))
            self.queue_tbl.setItem(i,2,si)
            self.queue_tbl.setItem(i,3,QTableWidgetItem(item.get("result","")))
            rb = QPushButton("Remove")
            rb.setStyleSheet("QPushButton{color:#ef4444;font-size:11px;padding:4px 10px;border-radius:6px;}")
            rb.clicked.connect(lambda checked, idx=i: self.remove_link(idx))
            self.queue_tbl.setCellWidget(i,4,rb)

    def add_link(self):
        url = self.url_input.text().strip()
        if not url: return
        casino = self.casino_combo.currentData() or self.casino_combo.currentText().strip() or ""
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        queue.append({"url": url, "added": datetime.now().strftime("%m/%d %H:%M"), "status": "pending", "result": "", "casino": casino})
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

    def validate_url(self):
        url = self.url_input.text().strip()
        if not url: return
        self.log(f"[LINK] Validating {url[:50]}...")
        try:
            r = combined.requests.get(url, timeout=8, headers={"User-Agent": combined.USER_AGENT})
            if r.status_code == 200:
                self.log(f"[LINK] ✅ Valid — HTTP {r.status_code}")
            else:
                self.log(f"[LINK] ⚠ HTTP {r.status_code}")
        except Exception as e:
            self.log(f"[LINK] ❌ {e}")

    def clear_completed(self):
        queue = combined.load_link_queue() if hasattr(combined, 'load_link_queue') else []
        remaining = [q for q in queue if q.get("status") not in ("done","failed")]
        if hasattr(combined, 'save_link_queue'):
            combined.save_link_queue(remaining)
        self.refresh_queue()
        self.log(f"[LINK] Cleared {len(queue)-len(remaining)} completed items")

    def clear_queue(self):
        if hasattr(combined, 'save_link_queue'):
            combined.save_link_queue([])
        self.refresh_queue()
        self.log("[LINK] Queue cleared")

    def toggle_auto(self):
        self.auto_running = not self.auto_running
        if self.auto_running:
            self.auto_toggle.setText("Auto: On")
            self.auto_toggle.setStyleSheet("QPushButton{background:#10b981;color:#fff;border:1px solid #10b981;border-radius:8px;padding:8px 16px;font-size:11px;font-weight:600;}QPushButton:hover{background:#059669;}")
            if hasattr(combined, 'process_queue_loop'):
                t = threading.Thread(target=combined.process_queue_loop, daemon=True)
                t.start()
            self.log("[LINK] Auto on")
        else:
            self.auto_toggle.setText("Auto")
            self.auto_toggle.setStyleSheet("QPushButton{background:#1e1e2a;color:#64748b;border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:8px 16px;font-size:11px;font-weight:600;}QPushButton:hover{background:#2a2a36;}")
            self.log("[LINK] Auto off")

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
    check_updates_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        lo = QVBoxLayout(); lo.setContentsMargins(16,16,16,16); lo.setSpacing(10)
        t = QLabel("Settings"); t.setObjectName("title"); lo.addWidget(t)

        # Top row: Bot + Notifications
        top_row = QHBoxLayout()
        bg = QGroupBox("Bot")
        bl = QFormLayout(); bl.setSpacing(6)
        bl.setContentsMargins(6,6,6,6)
        self.hc = QCheckBox("Headless mode")
        self.hc.setChecked(combined.HEADLESS_MODE); bl.addRow(self.hc)
        self.sp = QSpinBox(); self.sp.setRange(10,600); self.sp.setValue(combined.CHECK_INTERVAL); self.sp.setSuffix("s")
        bl.addRow("Interval:",self.sp)
        bg.setLayout(bl); top_row.addWidget(bg)

        ng = QGroupBox("Notifications")
        nl = QVBoxLayout()
        nl.setContentsMargins(6,6,6,6)
        whl = QHBoxLayout(); whl.setSpacing(6)
        self.webhook_input = QLineEdit()
        self.webhook_input.setPlaceholderText("Discord webhook URL")
        whl.addWidget(self.webhook_input)
        test_wh = QPushButton("Test"); test_wh.clicked.connect(self.test_webhook); whl.addWidget(test_wh)
        nl.addLayout(whl)
        ng.setLayout(nl); top_row.addWidget(ng)
        lo.addLayout(top_row)

        s = QPushButton("Save"); s.setObjectName("gold"); s.clicked.connect(self.save)
        lo.addWidget(s)

        # Data + Advanced row
        mid_row = QHBoxLayout()
        dg = QGroupBox("Data")
        dl = QHBoxLayout(); dl.setSpacing(6)
        dl.setContentsMargins(6,6,6,6)
        exp_btn = QPushButton("Export All"); exp_btn.clicked.connect(self.export_data); dl.addWidget(exp_btn)
        imp_btn = QPushButton("Import All"); imp_btn.clicked.connect(self.import_data); dl.addWidget(imp_btn)
        cc_btn = QPushButton("Clear Cache"); cc_btn.clicked.connect(self.clear_cache); dl.addWidget(cc_btn)
        dg.setLayout(dl); mid_row.addWidget(dg)

        ag2 = QGroupBox("Advanced")
        al2 = QHBoxLayout(); al2.setSpacing(6)
        al2.setContentsMargins(6,6,6,6)
        self.debug_cb = QCheckBox("Debug"); self.debug_cb.setChecked(False); al2.addWidget(self.debug_cb)
        self.verbose_cb = QCheckBox("Verbose"); self.verbose_cb.setChecked(False); al2.addWidget(self.verbose_cb)
        reset_btn = QPushButton("Reset All"); reset_btn.setObjectName("danger"); reset_btn.clicked.connect(self.reset_all); al2.addWidget(reset_btn)
        ag2.setLayout(al2); mid_row.addWidget(ag2)
        lo.addLayout(mid_row)

        # About + bottom buttons
        bot_row = QHBoxLayout()
        ag = QGroupBox("About")
        al = QHBoxLayout(); al.setSpacing(10)
        al.setContentsMargins(6,6,6,6)
        lf = BASE_DIR / "license.dat"
        license_info = "No license"
        if lf.exists():
            try:
                with open(lf) as f: ld = json.load(f)
                license_info = f"{ld.get('key','N/A')}  |  {ld.get('tier','Premium')}"
            except: license_info = "Corrupted"
        al.addWidget(QLabel(f"{APP_VERSION}  |  {license_info}"))
        l = QLabel('<a href="https://claimscasino.com/terms" style="color:#FFD700;text-decoration:none;">Terms</a>')
        l.setOpenExternalLinks(True); al.addWidget(l)
        al.addWidget(QLabel("© 2026 Claims Casino"))
        ag.setLayout(al); bot_row.addWidget(ag)

        bb = QHBoxLayout(); bb.setSpacing(8)
        cu = QPushButton("Check Updates"); cu.setObjectName("gold"); cu.clicked.connect(self.check_updates_requested.emit); bb.addWidget(cu)
        su = QPushButton("Community"); su.clicked.connect(lambda: webbrowser.open("https://claimscasino.com/support")); bb.addWidget(su)
        bot_row.addLayout(bb)
        lo.addLayout(bot_row)
        lo.addStretch()
        self.setLayout(lo)

    def save(self):
        combined.HEADLESS_MODE = self.hc.isChecked()
        combined.CHECK_INTERVAL = self.sp.value()
        QMessageBox.information(self,"Saved","Settings saved.")

    def export_data(self):
        fn, _ = QFileDialog.getSaveFileName(self, "Export All Data", str(BASE_DIR / "backup.json"), "JSON Files (*.json)")
        if not fn: return
        try:
            data = {
                "accounts": combined.load_accounts(),
                "schedule": combined.load_claim_schedule(),
                "streamers": combined.load_streamers() if hasattr(combined, 'load_streamers') else [],
                "queue": combined.load_link_queue() if hasattr(combined, 'load_link_queue') else [],
                "exported_at": datetime.now().isoformat()
            }
            with open(fn, 'w') as f: json.dump(data, f, indent=2)
            QMessageBox.information(self, "Exported", f"All data exported to {Path(fn).name}")
        except Exception as e:
            QMessageBox.warning(self, "Export Failed", str(e))

    def import_data(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Import All Data", str(BASE_DIR), "JSON Files (*.json)")
        if not fn: return
        try:
            with open(fn) as f: data = json.load(f)
            if "accounts" in data:
                combined.save_accounts(data["accounts"])
            if "schedule" in data:
                combined.save_claim_schedule(data["schedule"])
            if "streamers" in data and hasattr(combined, 'save_streamers'):
                combined.save_streamers(data["streamers"])
            if "queue" in data and hasattr(combined, 'save_link_queue'):
                combined.save_link_queue(data["queue"])
            QMessageBox.information(self, "Imported", f"Data restored from {Path(fn).name}")
        except Exception as e:
            QMessageBox.warning(self, "Import Failed", str(e))

    def clear_cache(self):
        count = 0
        for f in BASE_DIR.glob("*.dat"):
            try: f.unlink(); count += 1
            except: pass
        for f in BASE_DIR.glob("*.tmp"):
            try: f.unlink(); count += 1
            except: pass
        QMessageBox.information(self, "Cache Cleared", f"Removed {count} temp files")

    def test_webhook(self):
        url = self.webhook_input.text().strip()
        if not url: return
        try:
            r = combined.requests.post(url, json={"content": "Claims Casino test ping"}, timeout=8)
            if r.status_code in (200, 204):
                QMessageBox.information(self, "Webhook", "Test sent successfully")
            else:
                QMessageBox.warning(self, "Webhook", f"HTTP {r.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Webhook", str(e))

    def reset_all(self):
        if QMessageBox.question(self, "Reset",
            "Clear ALL accounts, schedule, streamers, and queue?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        if QMessageBox.question(self, "Confirm",
            "Are you absolutely sure?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
            return
        combined.save_accounts({})
        combined.save_claim_schedule({})
        if hasattr(combined, 'save_streamers'):
            combined.save_streamers([])
        if hasattr(combined, 'save_link_queue'):
            combined.save_link_queue([])
        QMessageBox.information(self, "Reset", "All data cleared")

# ═══════════════════════════════════════════════════════════════
# MAIN WINDOW
# ═══════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Claims Casino")
        self.setMinimumSize(900, 600)
        self.resize(1200, 780)

        logo_path = Path(getattr(sys, "_MEIPASS", BASE_DIR)) / "assets" / "logo.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        c = QWidget(); self.setCentralWidget(c)
        main_lo = QVBoxLayout(c); main_lo.setContentsMargins(0,0,0,0); main_lo.setSpacing(0)

        # ═══ Custom title bar (64px) ═══
        tb = QFrame()
        tb.setObjectName("titleBar")
        tb.setFixedHeight(64)
        tb.setStyleSheet("#titleBar{background:#0d0d14;}")
        tbl = QHBoxLayout(tb); tbl.setContentsMargins(12,0,8,0); tbl.setSpacing(8)

        logo_lbl = QLabel()
        if logo_path.exists():
            px = QPixmap(str(logo_path)).scaled(36,36,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(px)
        else:
            logo_lbl.setText("CC")
            logo_lbl.setStyleSheet("color:#FFD700;font-size:20px;font-weight:700;")
        logo_lbl.setFixedSize(40,40)
        tbl.addWidget(logo_lbl)

        brand_col = QVBoxLayout(); brand_col.setSpacing(0)
        brand = QLabel("CLAIMS CASINO")
        brand.setStyleSheet("color:#FFD700;font-size:18px;font-weight:700;letter-spacing:1px;")
        brand_col.addWidget(brand)
        sub = QLabel("Automation Suite  " + APP_VERSION)
        sub.setStyleSheet("color:#888;font-size:10px;font-weight:400;")
        brand_col.addWidget(sub)
        tbl.addLayout(brand_col)

        tbl.addStretch()

        min_btn = QPushButton("—")
        min_btn.setFixedSize(40,32)
        min_btn.setStyleSheet("QPushButton{background:transparent;color:#aaa;border-radius:6px;font-size:18px;font-weight:600;}QPushButton:hover{background:#333;color:#fff;}")
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(40,32)
        close_btn.setStyleSheet("QPushButton{background:transparent;color:#aaa;border-radius:6px;font-size:16px;font-weight:600;}QPushButton:hover{background:#ef4444;color:#fff;}")
        close_btn.clicked.connect(self.close)

        tbl.addWidget(min_btn); tbl.addWidget(close_btn)
        main_lo.addWidget(tb)

        # ═══ Body: sidebar + content ═══
        body = QWidget()
        bl = QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)

        # Sidebar: custom layout with nav pinned above, Settings pinned to bottom
        sidebar_w = QWidget()
        sidebar_w.setObjectName("sidebar")
        sl = QVBoxLayout(sidebar_w); sl.setContentsMargins(0,0,0,0); sl.setSpacing(0)

        nav_items = ["\U0001f4ca  Dashboard", "\U0001f3b0  Daily SC", "\U0001f3ac  Streamer Sniper", "\U0001f517  Link Automation"]
        self.nav_btns = []
        for i, text in enumerate(nav_items):
            b = QPushButton(text)
            b.setCheckable(True)
            b.clicked.connect(lambda checked, idx=i: self.on_page_change(idx))
            sl.addWidget(b)
            self.nav_btns.append(b)

        sl.addStretch()

        sep = QFrame()
        sep.setObjectName("navsep")
        sl.addWidget(sep)

        self.settings_btn = QPushButton("\u2699  Settings")
        self.settings_btn.setCheckable(True)
        self.settings_btn.clicked.connect(lambda: self.on_page_change(4))
        sl.addWidget(self.settings_btn)

        bl.addWidget(sidebar_w)

        self.stack = QStackedWidget()
        self.dt = DashboardTab()
        self.dst = DailySCTab()
        self.sst = StreamerSniperTab()
        self.lat = LinkAutomationTab()
        self.ste = SettingsTab()
        # Wire up check updates
        self.ste.check_updates_requested.connect(lambda: self.check_up(silent=False))
        self.stack.addWidget(self.dt)
        self.stack.addWidget(self.dst)
        self.stack.addWidget(self.sst)
        self.stack.addWidget(self.lat)
        self.stack.addWidget(self.ste)
        bl.addWidget(self.stack)
        self.on_page_change(0)

        main_lo.addWidget(body)

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
        vl = QLabel(APP_VERSION)
        vl.setStyleSheet("color:#555;padding:0 12px;")
        sb.addPermanentWidget(vl)

        # Tray
        self.tray = QSystemTrayIcon(self)
        if logo_path.exists():
            px = QPixmap(str(logo_path)).scaled(32,32,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
            self.tray.setIcon(QIcon(px))
        else:
            px = QPixmap(32,32); px.fill(QColor("#0d0d14"))
            p = QPainter(px); p.setBrush(QColor("#FFD700")); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(2,2,28,28); p.setFont(QFont("Arial",16,700)); p.setPen(QColor("#0d0d14"))
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

        QTimer.singleShot(3000, lambda: self.check_up(silent=True))

        # Center on screen
        self.move(QApplication.primaryScreen().geometry().center() - self.rect().center())

    def on_page_change(self, idx):
        if idx < 0 or idx >= self.stack.count(): return
        self.stack.setCurrentIndex(idx)
        for i, btn in enumerate(self.nav_btns):
            btn.setChecked(i == idx)
        self.settings_btn.setChecked(idx == 4)

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
        if e.button() == Qt.MouseButton.LeftButton and e.position().y() <= 56:
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

    def check_up(self, silent=False):
        try:
            r = combined.requests.get(UPDATE_MANIFEST_URL, timeout=8)
            if r.status_code != 200:
                if not silent: QMessageBox.information(self, "Updater", "Could not check for updates.")
                return
            manifest = r.json()
            tag = manifest.get("version", "v0.0.0")
            dl_url = manifest.get("url", "")
            size_bytes = manifest.get("size", 0)
            if tag <= APP_VERSION or not dl_url:
                if not silent: QMessageBox.information(self, "Updater", "No new updates available.")
                return
            mb = size_bytes / 1048576
            if QMessageBox.question(self, "Updater",
                f"Claims Casino {tag} available ({mb:.1f} MB).\nDownload and install now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) != QMessageBox.StandardButton.Yes:
                return
            self.download_update(dl_url, tag)
        except Exception as e:
            if not silent: QMessageBox.warning(self, "Updater", f"Update check failed:\n{e}")

    def download_update(self, url, tag):
        pd = QProgressDialog(f"Updater — Downloading {tag}...", "Cancel", 0, 0, self)
        pd.setWindowTitle("Updater"); pd.setCancelButton(None)
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
                            pd.setLabelText(f"Updater — {downloaded*100//total}%")
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
            QMessageBox.warning(self, "Updater", f"Download failed:\n{e}")

# ═══════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════

def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_SS)

    # Anti-debug check (kill switch)
    if not combined.check_anti_debug():
        mb = QMessageBox(QMessageBox.Icon.Critical, "Security", "Debug environment detected. Application cannot run.")
        mb.exec()
        sys.exit(1)

    # Check license
    lf = BASE_DIR / "license.dat"
    ok = False
    license_key = ""
    if lf.exists():
        try:
            with open(lf) as f: ld = json.load(f)
            license_key = ld.get("key", "")
            hwid = ld.get("hwid", "")
            # Online re-validation (silent, periodic)
            try:
                if hwid:
                    r = combined.requests.post(LICENSE_SERVER_URL, json={"key": license_key, "hwid": hwid}, timeout=3)
                    if r.status_code == 200 and r.json().get("valid"):
                        ok = True
                    # If server says invalid, fall through to local check
                else:
                    ok = combined.validate_license_key(license_key).get("valid")
            except:
                ok = combined.validate_license_key(license_key).get("valid")
        except:
            pass

    if not ok:
        dlg = LicenseDialog()
        if dlg.exec() != QDialog.DialogCode.Accepted: sys.exit(1)

    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
