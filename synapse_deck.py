import os
import sys
import subprocess
import threading
import json
import time 
from evdev import InputDevice, ecodes
from functools import partial 

# PyQt5 Deluxe Imports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QGridLayout, QTextEdit, QMessageBox, 
    QFileDialog, QTabWidget, QScrollArea, QFrame, QDialog, QStackedWidget,
    QGraphicsDropShadowEffect, QSystemTrayIcon, QMenu, QAction, QStyle,
    QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QIcon

# === 🛡️ TERMINAL CLEANUP ===
os.environ["QT_LOGGING_RULES"] = "*.debug=false;qt.qpa.input=false"
if os.geteuid() == 0:
    os.environ["XDG_RUNTIME_DIR"] = f"/run/user/{os.getuid()}"

# === ⚙️ CONFIG & PATHS ===
REAL_USER = os.getenv("SUDO_USER") or os.getenv("USER") or os.getlogin() or "USER"
USER_HOME = os.path.expanduser(f"~{REAL_USER}")

# Map voor data
SCRIPT_DIR = os.path.join(USER_HOME, ".synapse_macros")
CONFIG_FILE = os.path.join(SCRIPT_DIR, "macros.json")
GUI_MAP_FILE = os.path.join(SCRIPT_DIR, "gui_map.json") 
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")
os.makedirs(SCRIPT_DIR, exist_ok=True)

# Standaard instellingen (Jouw device staat hier als default)
DEFAULT_SETTINGS = {
    "device_path": "/dev/input/by-id/usb-1189_USB_Composite_Device_CD70134330383838-if01-event-kbd",
    "ignored_keys": [29, 42, 56, 100, 125]
}

# === 🔄 DATA LOADING ===
macros = {}
gui_map = {}
settings = DEFAULT_SETTINGS.copy()

def load_all():
    global macros, gui_map, settings
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f: macros = json.load(f)
        if os.path.exists(GUI_MAP_FILE):
            with open(GUI_MAP_FILE, "r") as f: gui_map = json.load(f)
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f: settings.update(json.load(f))
    except: pass

def save_all():
    with open(CONFIG_FILE, "w") as f: json.dump(macros, f, indent=4)
    with open(GUI_MAP_FILE, "w") as f: json.dump(gui_map, f, indent=4)
    with open(SETTINGS_FILE, "w") as f: json.dump(settings, f, indent=4)

load_all()

# === 🛠️ SESSION & APP LAUNCHER FIX ===
def get_session_context():
    try:
        pid = subprocess.check_output(f"pgrep -u {REAL_USER} -f 'session|shell|plasma|xfce|cinnamon' | head -n 1", shell=True).decode().strip()
        env = subprocess.check_output(f"sudo tr '\\0' '\\n' < /proc/{pid}/environ | grep -E '^(DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR|DISPLAY|XAUTHORITY)='", shell=True).decode().strip()
        return "\n".join([f"export {l}" for l in env.split('\n')]) + f"\nexport HOME={USER_HOME}\n"
    except:
        return f"export DISPLAY=:0\nexport HOME={USER_HOME}\nexport XAUTHORITY={USER_HOME}/.Xauthority\n"

SESSION_VARS = get_session_context()
ROBUST_TEMPLATE = f"#!/bin/bash\n{SESSION_VARS}\n{{}}"

# === 🎨 UI STYLING: SYNAPSE DARK ELITE ===
STYLE_SHEET = f"""
QMainWindow, QDialog {{ background-color: #050506; }}
QWidget {{ color: #ffffff; font-family: 'Inter', 'Segoe UI', sans-serif; }}

QScrollBar:vertical {{ background: #050506; width: 8px; }}
QScrollBar::handle:vertical {{ background: #1c1c21; border-radius: 4px; }}
QScrollBar::handle:vertical:hover {{ background: #00e5ff; }}

QFrame#MainDeck, QFrame#SettingsBox {{ background-color: #0d0d10; border: 1px solid #1c1c21; border-radius: 20px; }}

QTabWidget::pane {{ border: 1px solid #1c1c21; background: #08080a; border-radius: 12px; top: -1px; }}
QTabBar::tab {{ background: #0d0d10; padding: 12px 35px; margin-right: 5px; border-top-left-radius: 10px; border-top-right-radius: 10px; font-size: 11px; font-weight: bold; color: #555; border: 1px solid #1c1c21; }}
QTabBar::tab:selected {{ background: #141418; color: #00e5ff; border-top: 2px solid #00e5ff; }}

QPushButton {{ background-color: #121217; border: 1px solid #25252b; border-bottom: 3px solid #000; border-radius: 10px; font-weight: 700; font-size: 11px; color: #a0a0ab; padding: 10px; }}
QPushButton:hover {{ background-color: #1a1a21; border-color: #00e5ff; color: #ffffff; border-bottom: 3px solid #008ba3; }}

QPushButton#AppCard {{ background-color: #0d0d12; border: 1px solid #1c1c21; border-bottom: 4px solid #050507; border-radius: 12px; font-size: 10px; color: #d1d1d1; padding: 15px; }}
QPushButton#AppCard:hover {{ background-color: #14141a; border-color: #00e5ff; color: #ffffff; border-bottom: 4px solid #008ba3; }}

QPushButton#CategoryCard {{ background-color: #0d0d12; border-left: 5px solid #00e5ff; border-bottom: 3px solid #050507; text-align: left; padding-left: 20px; font-size: 13px; font-weight: 900; color: #ffffff; }}
QPushButton#BackButton {{ background-color: #1c1c21; border: 1px solid #333; color: #00e5ff; font-weight: 800; margin-bottom: 15px; border-radius: 8px; }}

QTextEdit {{ background-color: #050506; border: 1px solid #1c1c21; color: #00ff41; border-radius: 10px; font-family: 'Consolas', monospace; }}

QLineEdit {{
    background-color: #0d0d12;
    border: 1px solid #1c1c21;
    border-radius: 10px;
    padding: 12px;
    color: #00e5ff;
    font-weight: bold;
}}
"""

# === 🎧 LISTENER ===
class KeyListener(QThread):
    key_signal = pyqtSignal(str)
    def run(self):
        try:
            dev_path = settings.get("device_path")
            if os.path.exists(dev_path):
                dev = InputDevice(dev_path)
                for event in dev.read_loop():
                    if event.type == ecodes.EV_KEY and event.value == 1:
                        if event.code not in settings.get("ignored_keys", []):
                            self.key_signal.emit(str(event.code))
        except: pass

# === 📱 MAIN UI ===
class SynapseDeck(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SYNAPSE COMMAND DECK")
        self.setFixedSize(1000, 800)
        self.setStyleSheet(STYLE_SHEET)
        
        self.learning_id = None 
        self.btns = {}
        self.init_ui()
        self.setup_tray()
        
        self.listener = KeyListener()
        self.listener.key_signal.connect(self.handle_input)
        self.listener.start()

    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        tray_menu = QMenu()
        open_action = QAction("Open Deck", self)
        quit_action = QAction("Exit Fully", self)
        open_action.triggered.connect(self.showNormal)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(open_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            if self.isVisible(): self.hide()
            else: self.showNormal(); self.activateWindow()

    def closeEvent(self, event):
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def quit_application(self):
        self.tray_icon.hide()
        QApplication.quit()

    def init_ui(self):
        central = QWidget(); self.setCentralWidget(central)
        main_layout = QVBoxLayout(central); main_layout.setContentsMargins(40, 40, 40, 40)

        # Header
        top = QHBoxLayout(); v = QVBoxLayout()
        l1 = QLabel("SYNAPSE"); l1.setStyleSheet("font-size: 34px; font-weight: 900; letter-spacing: 5px;")
        l2 = QLabel("COMMAND DECK"); l2.setStyleSheet("font-size: 12px; color: #00e5ff; letter-spacing: 3px;")
        v.addWidget(l1); v.addWidget(l2); top.addLayout(v); top.addStretch()
        
        set_btn = QPushButton("⚙ SETUP / INFO")
        set_btn.setFixedSize(160, 40)
        set_btn.setStyleSheet("background: #141418; border: 1px solid #00e5ff; color: #00e5ff; border-radius: 8px;")
        set_btn.clicked.connect(self.open_settings)
        top.addWidget(set_btn, Qt.AlignTop)
        main_layout.addLayout(top)

        # Deck Frame
        deck = QFrame(); deck.setObjectName("MainDeck")
        dl = QHBoxLayout(deck); dl.setContentsMargins(30, 40, 30, 40)

        # Grid
        grid_w = QWidget(); grid = QGridLayout(grid_w); grid.setSpacing(15)
        for i in range(3):
            for j in range(4):
                idx = i * 4 + j + 1
                kid = f"K{idx}"
                b = QPushButton(kid); b.setFixedSize(110, 100)
                b.clicked.connect(partial(self.trigger_learning, kid))
                shadow = QGraphicsDropShadowEffect(); shadow.setBlurRadius(25); shadow.setColor(Qt.transparent); b.setGraphicsEffect(shadow)
                grid.addWidget(b, i, j); self.btns[kid] = b
        dl.addWidget(grid_w)

        # Rotary
        rl = QVBoxLayout(); rl.setSpacing(35)
        for r in ["R1", "R2"]:
            rf = QFrame(); rv = QVBoxLayout(rf)
            dial = QPushButton("DIAL"); dial.setFixedSize(90, 90)
            dial.setStyleSheet("border-radius: 45px; border: 3px solid #1c1c21; background: #0d0d10; border-bottom: 4px solid #000;")
            dial.clicked.connect(partial(self.trigger_learning, f"{r}_DRUK"))
            rv.addWidget(dial, Qt.AlignCenter); self.btns[f"{r}_DRUK"] = dial
            rl.addWidget(rf)
        dl.addLayout(rl); main_layout.addWidget(deck)

        self.status = QLabel("SYSTEM OPERATIONAL")
        self.status.setStyleSheet("color: #444; font-size: 10px; font-weight: bold; letter-spacing: 3px;")
        main_layout.addWidget(self.status, Qt.AlignCenter)
        self.update_ui()

    def update_ui(self):
        for gid, btn in self.btns.items():
            code = gui_map.get(gid); sh = btn.graphicsEffect()
            if code and code in macros:
                name = os.path.basename(macros[code]).replace('.sh','').replace('_',' ').upper()
                btn.setText(f"{gid}\n\n{name}"); btn.setProperty("linked", "true")
                if sh: sh.setColor(Qt.cyan if gid.startswith('K') else Qt.white)
            else:
                btn.setText(f"{gid}\n\nEMPTY"); btn.setProperty("linked", "false")
                if sh: sh.setColor(Qt.transparent)
            btn.style().polish(btn)

    def trigger_learning(self, gid):
        self.learning_id = gid
        self.status.setText(f"WAITING FOR INPUT: {gid}")
        self.status.setStyleSheet("color: #ff2e63; font-weight: bold;")

    def handle_input(self, code):
        if self.learning_id:
            target = self.learning_id; self.learning_id = None 
            gui_map[target] = code; save_all()
            self.status.setText("COMMAND ASSIGNED"); self.status.setStyleSheet("color: #00e5ff; font-weight: bold;")
            self.open_menu(code, target)
        else:
            if code in macros:
                path = macros[code]
                if os.path.exists(path):
                    subprocess.Popen(["sudo", "-u", REAL_USER, "bash", path], start_new_session=True)

    def open_settings(self):
        dlg = QDialog(self); dlg.setWindowTitle("SYNAPSE SETUP CENTER"); dlg.setMinimumSize(850, 700)
        dlg.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(dlg); tabs = QTabWidget()

        # TAB 1: DEVICE CONFIG
        t1 = QWidget(); tl1 = QVBoxLayout(t1); tl1.setContentsMargins(20,20,20,20)
        tl1.addWidget(QLabel("DEVICE PATH (Must start with /dev/input/by-id/):"))
        inp = QLineEdit(settings.get("device_path"))
        tl1.addWidget(inp); sb = QPushButton("SAVE & RESTART LISTENER")
        sb.setStyleSheet("background: #00e5ff; color: #000; font-weight: bold;")
        def save():
            settings["device_path"] = inp.text(); save_all()
            self.listener.terminate(); self.listener = KeyListener()
            self.listener.key_signal.connect(self.handle_input); self.listener.start()
            QMessageBox.information(dlg, "Saved", "Device path updated!")
        sb.clicked.connect(save); tl1.addWidget(sb); tl1.addStretch()
        tabs.addTab(t1, "DEVICE CONFIG")

        # TAB 2: GUIDE
        t2 = QScrollArea(); f2 = QFrame(); tl2 = QVBoxLayout(f2); f2.setObjectName("SettingsBox")
        guide = [
            ("1. FIND YOUR DEVICE", "Run this in terminal to find your ID. Copy the name and put '/dev/input/by-id/' in front of it:", "ls /dev/input/by-id/"),
            ("2. ENABLE NO-PASSWORD SUDO", "Run 'sudo visudo' and add this line at the very bottom:", f"{REAL_USER} ALL=(root) SETENV: NOPASSWD: /usr/bin/python3 {os.path.abspath(__file__)}"),
            ("3. START SCRIPT", f"Create a file 'start_synapse.sh' in {USER_HOME}:", f"sudo DISPLAY=:0 XAUTHORITY={USER_HOME}/.Xauthority /usr/bin/python3 {os.path.abspath(__file__)}"),
            ("4. DESKTOP ICON", "Create a Launcher on your desktop with this Exec path:", f"{USER_HOME}/start_synapse.sh")
        ]
        for title, desc, code in guide:
            tl2.addWidget(QLabel(f"<b>{title}</b>")); tl2.addWidget(QLabel(desc))
            if code: 
                ed = QTextEdit(code); ed.setFixedHeight(50); ed.setReadOnly(True)
                tl2.addWidget(ed)
        tl2.addStretch(); t2.setWidget(f2); t2.setWidgetResizable(True); tabs.addTab(t2, "SETUP GUIDE")

        l.addWidget(tabs); dlg.exec_()

    def open_menu(self, code, gid):
        dialog = QDialog(self); dialog.setWindowTitle(f"CONFIG // {gid}")
        dialog.setMinimumSize(850, 750); dialog.setStyleSheet(STYLE_SHEET)
        l = QVBoxLayout(dialog); tabs = QTabWidget()

        prog_widget = QWidget(); prog_layout = QVBoxLayout(prog_widget)
        search_bar = QLineEdit(); search_bar.setPlaceholderText("SEARCH APPLICATIONS...")
        prog_layout.addWidget(search_bar)

        self.stack = QStackedWidget()
        self.cat_v = QScrollArea(); f_cat = QFrame(); self.cat_l = QVBoxLayout(f_cat)
        self.app_data = self.get_categorized_apps()
        for cat, apps in sorted(self.app_data.items()):
            if not apps: continue
            b = QPushButton(f"{cat.upper()}   ▸"); b.setObjectName("CategoryCard"); b.setMinimumHeight(60)
            b.clicked.connect(partial(self.show_apps, code, cat, apps, dialog))
            self.cat_l.addWidget(b)
        self.cat_l.addStretch(); self.cat_v.setWidget(f_cat); self.cat_v.setWidgetResizable(True)
        self.stack.addWidget(self.cat_v); prog_layout.addWidget(self.stack); tabs.addTab(prog_widget, "PROGRAMS")
        search_bar.textChanged.connect(lambda text: self.filter_apps(text, code, dialog))

        t3 = QWidget(); l3 = QVBoxLayout(t3); l3.setContentsMargins(25, 25, 25, 25)
        l3.addWidget(QLabel("SCRIPT ENGINE:")); ed = QTextEdit(); ed.setPlainText("#!/bin/bash\n")
        l3.addWidget(ed); sb = QPushButton("DEPLOY MODULE")
        sb.setStyleSheet("background: #00e5ff; color: #000; font-size: 13px; font-weight: 900;"); sb.clicked.connect(lambda: self.finalize(code, f"Custom_{code}", ed.toPlainText(), dialog))
        l3.addWidget(sb); tabs.addTab(t3, "ADVANCED")

        l.addWidget(tabs); dialog.exec_()

    def filter_apps(self, text, code, dialog):
        if not text.strip(): self.stack.setCurrentIndex(0); return
        matches = {}
        for cat, apps in self.app_data.items():
            for name, cmd in apps.items():
                if text.lower() in name.lower(): matches[name] = cmd
        self.show_apps(code, f"RESULTS", matches, dialog, is_search=True)

    def show_apps(self, code, cat, apps, dialog, is_search=False):
        v = QScrollArea(); f = QFrame(); l = QVBoxLayout(f); l.setContentsMargins(20, 20, 20, 20)
        if not is_search:
            back = QPushButton("« BACK TO CATEGORIES"); back.setObjectName("BackButton"); back.setFixedSize(220, 45)
            back.clicked.connect(lambda: self.stack.setCurrentIndex(0)); l.addWidget(back)
        grid_container = QWidget(); grid = QGridLayout(grid_container); grid.setSpacing(15)
        for i, (name, cmd) in enumerate(sorted(apps.items())):
            b = QPushButton(name); b.setObjectName("AppCard"); b.setMinimumHeight(70)
            b.clicked.connect(lambda ch, n=name, c=cmd: self.finalize(code, f"Open_{n}", f"exec {c}", dialog))
            grid.addWidget(b, i // 3, i % 3)
        l.addWidget(grid_container); l.addStretch(); v.setWidget(f); v.setWidgetResizable(True)
        if self.stack.count() > 1: self.stack.removeWidget(self.stack.widget(1))
        self.stack.addWidget(v); self.stack.setCurrentIndex(1)

    def get_categorized_apps(self):
        cm = {'AudioVideo': 'Multimedia', 'Development': 'Dev Tools', 'Game': 'Gaming', 'Graphics': 'Creative', 'Network': 'Internet', 'Office': 'Productivity', 'System': 'System', 'Utility': 'Utilities'}
        res = {n: {} for n in cm.values()}; res['Uncategorized'] = {}
        for d in ['/usr/share/applications', f'{USER_HOME}/.local/share/applications']:
            if not os.path.exists(d): continue
            for f in os.listdir(d):
                if f.endswith('.desktop'):
                    try:
                        with open(os.path.join(d, f), 'r') as c:
                            lines = c.readlines()
                            name = next(l.split('=')[1].strip() for l in lines if l.startswith('Name='))
                            exe = next(l.split('=')[1].strip() for l in lines if l.startswith('Exec='))
                            cl = next((l.split('=')[1].strip() for l in lines if l.startswith('Categories=')), "Uncategorized")
                            fc = "Uncategorized"
                            for t, h in cm.items():
                                if t in cl: fc = h; break
                            res[fc][name] = exe.split()[0].replace('%U','').replace('%u','')
                    except: continue
        return res

    def finalize(self, code, name, content, dialog):
        if not content.startswith("#!"): content = ROBUST_TEMPLATE.format(content)
        path = os.path.join(SCRIPT_DIR, f"{name.replace(' ','_')}.sh")
        with open(path, "w") as f: f.write(content)
        os.chmod(path, 0o755)
        macros[code] = path; save_all(); self.update_ui(); dialog.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    win = SynapseDeck(); win.show(); sys.exit(app.exec_())
