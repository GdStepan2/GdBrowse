import os
import sys
import configparser
from pathlib import Path
from typing import Optional

# =========================
# Папка данных (Документы/GdStepan2/GdBrowser/)
# =========================
def get_documents_dir() -> Path:
    home = Path.home()
    p1 = home / "Documents"
    p2 = home / "Документы"
    if p1.exists():
        return p1
    if p2.exists():
        return p2
    return home

APP_DATA_DIR = get_documents_dir() / "GdStepan2" / "GdBrowser"
USER_DATA_DIR = APP_DATA_DIR / "user_data"
CACHE_DIR = APP_DATA_DIR / "cache"
DOWNLOADS_DIR = APP_DATA_DIR / "downloads"
LOG_DIR = APP_DATA_DIR / "logs"

START_HTML_PATH = APP_DATA_DIR / "start.html"
SETTINGS_INI_PATH = APP_DATA_DIR / "settings.ini"
CAT_PATH = APP_DATA_DIR / "maxwell.jpg"
HOME_URL = START_HTML_PATH.resolve().as_uri()

SEARCH_ENGINES = {
    "Google":      "https://www.google.com/search?q={q}",
    "DuckDuckGo":  "https://duckduckgo.com/?q={q}",
    "Bing":        "https://www.bing.com/search?q={q}",
    "Яндекс":      "https://yandex.ru/search/?text={q}",
    "Startpage":   "https://www.startpage.com/do/search?q={q}",
    "Brave":       "https://search.brave.com/search?q={q}",
}

DEFAULT_ENGINE = "Google"
DEFAULT_LOG_MB = 15


START_HTML_TEMPLATE = r"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>GdBrowser</title>
  <style>
    :root{
      --bg: #f7d9b5;
      --card: rgba(255,255,255,.55);
      --card2: rgba(255,255,255,.35);
      --border: rgba(0,0,0,.08);
      --shadow: 0 18px 50px rgba(0,0,0,.10);
      --text: #2b2b2b;
      --muted: rgba(0,0,0,.55);
      --accent: #f2992e;
    }
    *{ box-sizing:border-box; }
    html,body{ height:100%; margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; color:var(--text); }
    body{
      background:
        radial-gradient(1200px 600px at 50% 40%, #ffe9cf 0%, rgba(255,233,207,0) 60%),
        radial-gradient(900px 500px at 30% 70%, rgba(255,255,255,.35) 0%, rgba(255,255,255,0) 60%),
        var(--bg);
      display:flex; align-items:center; justify-content:center;
      padding: 28px 18px;
    }
    .wrap{ width:min(920px, 96vw); text-align:center; }
    .logo{
      font-size: clamp(48px, 7vw, 86px);
      font-weight: 800;
      letter-spacing: -1px;
      color: var(--accent);
      margin: 0 0 18px 0;
      user-select:none;
    }
    .logo span{ color:#ffb463; }

    .search{
      margin: 0 auto;
      width: min(760px, 96vw);
      background: linear-gradient(180deg, var(--card), var(--card2));
      border: 1px solid var(--border);
      border-radius: 999px;
      box-shadow: var(--shadow);
      padding: 10px 14px;
      display:flex; align-items:center; gap: 10px;
      backdrop-filter: blur(10px);
    }
    .icon{ width: 22px; height: 22px; opacity: .65; flex: 0 0 auto; }
    input{
      border:0; outline:0; background: transparent;
      width: 100%;
      font-size: 18px;
      padding: 10px 6px;
      color: var(--text);
    }
    .btn{
      border:0; outline:0;
      background: rgba(0,0,0,.06);
      color: rgba(0,0,0,.65);
      border-radius: 999px;
      padding: 10px 12px;
      cursor:pointer;
      transition: transform .05s ease, background .15s ease;
      user-select:none;
      font-size: 14px;
      font-weight: 700;
      white-space: nowrap;
    }
    .btn:hover{ background: rgba(0,0,0,.09); }
    .btn:active{ transform: scale(.98); }
    .hint{ margin-top: 12px; font-size: 13px; color: var(--muted); }

    .links{
      margin-top: 18px;
      display:flex; flex-wrap:wrap; gap:10px;
      justify-content:center;
      align-items:center;
    }
    .chip{
      text-decoration:none;
      color: rgba(0,0,0,.76);
      background: rgba(255,255,255,.38);
      border: 1px solid rgba(0,0,0,.07);
      border-radius: 999px;
      padding: 10px 14px;
      box-shadow: 0 10px 30px rgba(0,0,0,.08);
      backdrop-filter: blur(8px);
      font-weight: 700;
      font-size: 14px;
      display:inline-flex; gap:8px; align-items:center;
      max-width: 280px;
    }
    .chip:hover{ background: rgba(255,255,255,.52); }
    .chip .url{
      opacity: .6;
      font-weight: 600;
      max-width: 150px;
      overflow:hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .x{
      border:0; outline:0;
      background: rgba(0,0,0,.08);
      color: rgba(0,0,0,.65);
      width: 22px; height: 22px;
      border-radius: 999px;
      cursor:pointer;
      display:inline-flex; align-items:center; justify-content:center;
      font-weight: 900;
      flex: 0 0 auto;
      margin-left: 4px;
    }
    .x:hover{ background: rgba(0,0,0,.12); }
  </style>
</head>
<body>
  <main class="wrap">
    <h1 class="logo">Gd<span>Browser</span></h1>

    <form class="search" id="form" autocomplete="off">
      <svg class="icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z" stroke="currentColor" stroke-width="2"/>
        <path d="M16.5 16.5 21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
      <input id="q" placeholder="Введите запрос или URL" autofocus />
      <button class="btn" id="btnSearch" type="submit">Найти</button>
    </form>

    <div class="hint">Enter — поиск • Ctrl+L — фокус на адресной строке</div>

    <div class="links" id="links"></div>
  </main>

  <script>
    const linksEl = document.getElementById("links");
    const form = document.getElementById("form");
    const input = document.getElementById("q");

    const DEFAULT_TEMPLATE = "https://www.google.com/search?q={q}";
    const DEFAULT_LINKS = [
      {"title":"YouTube","url":"https://www.youtube.com/"},
      {"title":"VK","url":"https://vk.com/"},
      {"title":"GitHub","url":"https://github.com/"}
    ];

    function tooltipsEnabled(){
      // "1" / "0"
      const v = localStorage.getItem("ui_tooltips");
      if (v === null || v === undefined) return true;
      return v !== "0";
    }

    function getTemplate(){
      return localStorage.getItem("search_template") || DEFAULT_TEMPLATE;
    }

    function looksLikeUrl(s){
      return s.includes(".") && !s.includes(" ") && !s.startsWith("?");
    }

    function loadLinks(){
      try{
        const raw = localStorage.getItem("quick_links");
        if(!raw) return DEFAULT_LINKS.slice();
        const arr = JSON.parse(raw);
        if(Array.isArray(arr)) return arr;
      }catch(e){}
      return DEFAULT_LINKS.slice();
    }

    function saveLinks(arr){
      localStorage.setItem("quick_links", JSON.stringify(arr));
    }

    function shortHost(url){
      try{
        const u = new URL(url);
        return u.host.replace(/^www\./,'');
      }catch(e){
        return url;
      }
    }

    function renderLinks(){
      linksEl.innerHTML = "";
      const links = loadLinks();
      const tips = tooltipsEnabled();

      // кнопка "+"
      const addBtn = document.createElement("button");
      addBtn.className = "btn";
      addBtn.type = "button";
      addBtn.textContent = "+ Добавить ссылку";
      addBtn.title = tips ? "Добавить новую быструю ссылку" : "";
      addBtn.onclick = () => {
        const title = (prompt("Название ссылки (например: YouTube):") || "").trim();
        if(!title) return;

        let url = (prompt("URL (например: https://youtube.com):") || "").trim();
        if(!url) return;

        if(!url.includes("://")) url = "https://" + url;

        const arr = loadLinks();
        arr.push({title, url});
        saveLinks(arr);
        renderLinks();
      };
      linksEl.appendChild(addBtn);

      for(let i=0;i<links.length;i++){
        const it = links[i];
        const a = document.createElement("a");
        a.className = "chip";
        a.href = it.url || "#";
        a.innerHTML = `<span>${it.title || "Link"}</span><span class="url">${shortHost(it.url || "")}</span>`;
        a.title = tips ? (it.url || "") : "";

        // кнопка удаления
        const x = document.createElement("button");
        x.className = "x";
        x.type = "button";
        x.textContent = "×";
        x.title = tips ? "Удалить ссылку" : "";
        x.onclick = (ev) => {
          ev.preventDefault();
          ev.stopPropagation();
          if(!confirm(`Удалить ссылку "${it.title}"?`)) return;
          const arr = loadLinks();
          arr.splice(i, 1);
          saveLinks(arr);
          renderLinks();
        };

        a.appendChild(x);
        linksEl.appendChild(a);
      }

      // подсказки на кнопке поиска
      const btnSearch = document.getElementById("btnSearch");
      if (btnSearch) btnSearch.title = tips ? "Выполнить поиск" : "";
    }

    // сделаем доступным извне (для обновления из Python)
    window.renderLinks = renderLinks;

    renderLinks();

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const raw = (input.value || "").trim();
      if(!raw) return;

      if (raw.includes("://")) { location.href = raw; return; }
      if (looksLikeUrl(raw)) { location.href = "https://" + raw; return; }

      const q = encodeURIComponent(raw);
      const tpl = getTemplate();
      location.href = tpl.replace("{q}", q);
    });
  </script>
</body>
</html>
"""


def ensure_app_files():
    for p in (APP_DATA_DIR, USER_DATA_DIR, CACHE_DIR, DOWNLOADS_DIR, LOG_DIR):
        p.mkdir(parents=True, exist_ok=True)

    if not START_HTML_PATH.exists():
        START_HTML_PATH.write_text(START_HTML_TEMPLATE, encoding="utf-8")

    if not SETTINGS_INI_PATH.exists():
        cfg = configparser.ConfigParser()
        cfg["search"] = {"engine": DEFAULT_ENGINE}
        cfg["logs"] = {"enabled": "true", "max_mb": str(DEFAULT_LOG_MB)}
        cfg["ui"] = {"tooltips": "true"}
        with SETTINGS_INI_PATH.open("w", encoding="utf-8") as f:
            cfg.write(f)


def clamp_int(v: str, d: int, lo: int, hi: int) -> int:
    try:
        x = int(float(v))
    except Exception:
        return d
    return max(lo, min(hi, x))


def load_cfg() -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()
    cfg.read(SETTINGS_INI_PATH, encoding="utf-8")

    if "search" not in cfg:
        cfg["search"] = {"engine": DEFAULT_ENGINE}
    if "logs" not in cfg:
        cfg["logs"] = {"enabled": "true", "max_mb": str(DEFAULT_LOG_MB)}
    if "ui" not in cfg:
        cfg["ui"] = {"tooltips": "true"}

    if "engine" not in cfg["search"]:
        cfg["search"]["engine"] = DEFAULT_ENGINE
    if "enabled" not in cfg["logs"]:
        cfg["logs"]["enabled"] = "true"
    if "max_mb" not in cfg["logs"]:
        cfg["logs"]["max_mb"] = str(DEFAULT_LOG_MB)
    if "tooltips" not in cfg["ui"]:
        cfg["ui"]["tooltips"] = "true"

    return cfg


def save_cfg(cfg: configparser.ConfigParser):
    with SETTINGS_INI_PATH.open("w", encoding="utf-8") as f:
        cfg.write(f)


# =========================
# Логи: если достигли лимита — очищаем файл
# =========================
class TruncatingFileLogger:
    def __init__(self, enabled: bool, max_bytes: int, log_path: Path):
        self.enabled = enabled
        self.max_bytes = max_bytes
        self.log_path = log_path
        self._logger = None

        if not enabled:
            return

        import logging
        self._logger = logging.getLogger("gdbrowser")
        self._logger.setLevel(logging.DEBUG)
        self._logger.handlers.clear()

        handler = logging.FileHandler(str(log_path), encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(fmt)
        self._logger.addHandler(handler)

    def _truncate_if_needed(self):
        if not self.enabled:
            return
        try:
            if self.log_path.exists() and self.log_path.stat().st_size > self.max_bytes:
                self.log_path.write_text("", encoding="utf-8")
        except Exception:
            pass

    def info(self, msg: str):
        if not self.enabled:
            return
        self._truncate_if_needed()
        self._logger.info(msg)

    def warning(self, msg: str):
        if not self.enabled:
            return
        self._truncate_if_needed()
        self._logger.warning(msg)

    def error(self, msg: str):
        if not self.enabled:
            return
        self._truncate_if_needed()
        self._logger.error(msg)


def truncate_if_big(path: Path, max_bytes: int):
    try:
        if path.exists() and path.stat().st_size > max_bytes:
            path.write_text("", encoding="utf-8")
    except Exception:
        pass


# =========================
# До импортов PyQt6 читаем настройки логов
# =========================
ensure_app_files()
CFG = load_cfg()

LOG_ENABLED = (CFG.get("logs", "enabled", fallback="true").strip().lower() == "true")
LOG_MAX_MB = clamp_int(CFG.get("logs", "max_mb", fallback=str(DEFAULT_LOG_MB)), DEFAULT_LOG_MB, 1, 500)
LOG_MAX_BYTES = LOG_MAX_MB * 1024 * 1024

LOG_FILE = LOG_DIR / "gdbrowser.log"
CHROMIUM_LOG = LOG_DIR / "chromium.log"

truncate_if_big(LOG_FILE, LOG_MAX_BYTES)
truncate_if_big(CHROMIUM_LOG, LOG_MAX_BYTES)

LOGGER = TruncatingFileLogger(LOG_ENABLED, LOG_MAX_BYTES, LOG_FILE)
LOGGER.info("=== start ===")
LOGGER.info(f"Data dir: {APP_DATA_DIR}")
LOGGER.info(f"Logs enabled: {LOG_ENABLED}, max_mb: {LOG_MAX_MB}")

# Chromium log — только если логи включены (иначе не пишем вообще)
if LOG_ENABLED:
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = " ".join([
        "--enable-logging=stderr",
        "--v=1",
        "--log-file=" + str(CHROMIUM_LOG),
    ])


# =========================
# PyQt6 imports
# =========================
from PyQt6.QtCore import QUrl, QSize, Qt
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QMessageBox, QFileDialog,
    QDialog, QFormLayout, QComboBox, QDialogButtonBox,
    QCheckBox, QSpinBox, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings


DARK_QSS = """
QMainWindow { background: #0f111a; }
QToolBar { background: #151a26; border: 0px; spacing: 8px; padding: 8px; }
QLineEdit {
    background: #0f1420; color: #e7eaf0;
    border: 1px solid #2a3142; border-radius: 10px;
    padding: 8px 12px; selection-background-color: #2b6cff;
    font-size: 13px;
}
QLineEdit:focus { border: 1px solid #3a74ff; }
QTabWidget::pane { border: 0px; background: #0f111a; }
QTabBar::tab {
    background: #151a26; color: #cdd3df;
    border: 1px solid #232a3a; border-bottom: 0px;
    padding: 8px 12px; margin-right: 6px;
    border-top-left-radius: 10px; border-top-right-radius: 10px;
}
QTabBar::tab:selected {
    background: #1b2233; color: #ffffff;
    border: 1px solid #2a3550; border-bottom: 0px;
}
QTabBar::tab:hover { background: #182033; }
"""


def looks_like_url(text: str) -> bool:
    return ("." in text) and (" " not in text)


def encode_query(text: str) -> str:
    return QUrl.toPercentEncoding(text).data().decode("utf-8")


class SettingsDialog(QDialog):
    def __init__(self, cfg: configparser.ConfigParser, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # поисковик
        self.combo_engine = QComboBox()
        for n in SEARCH_ENGINES.keys():
            self.combo_engine.addItem(n)
        self.combo_engine.setCurrentText(self.cfg.get("search", "engine", fallback=DEFAULT_ENGINE))
        form.addRow("Поисковик:", self.combo_engine)

        # подсказки (tooltips)
        self.chk_tooltips = QCheckBox("Показывать подсказки при наведении")
        self.chk_tooltips.setChecked(self.cfg.get("ui", "tooltips", fallback="true").strip().lower() == "true")
        form.addRow("Подсказки:", self.chk_tooltips)

        # логи вкл/выкл
        self.chk_logs = QCheckBox("Включить логи")
        self.chk_logs.setChecked(self.cfg.get("logs", "enabled", fallback="true").strip().lower() == "true")
        form.addRow("Логи:", self.chk_logs)

        # размер логов
        self.spin_mb = QSpinBox()
        self.spin_mb.setRange(1, 500)
        self.spin_mb.setValue(clamp_int(self.cfg.get("logs", "max_mb", fallback=str(DEFAULT_LOG_MB)),
                                        DEFAULT_LOG_MB, 1, 500))
        self.spin_mb.setSuffix(" MB")
        form.addRow("Макс размер логов:", self.spin_mb)

        layout.addLayout(form)

        # пути
        row = QHBoxLayout()
        lab = QLabel(f"Папка данных:\n{APP_DATA_DIR}")
        lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(lab, 1)
        btn_data = QPushButton("Открыть")
        btn_data.clicked.connect(lambda: os.startfile(str(APP_DATA_DIR)))
        row.addWidget(btn_data)
        layout.addLayout(row)

        row2 = QHBoxLayout()
        lab2 = QLabel(f"Папка логов:\n{LOG_DIR}")
        lab2.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row2.addWidget(lab2, 1)
        btn_logs = QPushButton("Открыть")
        btn_logs.clicked.connect(lambda: os.startfile(str(LOG_DIR)))
        row2.addWidget(btn_logs)
        layout.addLayout(row2)

        note = QLabel("⚠ Для включения/выключения chromium.log нужен перезапуск.")
        note.setStyleSheet("color: rgba(255,255,255,.7);")
        layout.addWidget(note)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_engine(self) -> str:
        return self.combo_engine.currentText()

    def get_tooltips_enabled(self) -> bool:
        return self.chk_tooltips.isChecked()

    def get_logs_enabled(self) -> bool:
        return self.chk_logs.isChecked()

    def get_logs_max_mb(self) -> int:
        return int(self.spin_mb.value())


class BrowserPage(QWebEnginePage):
    def __init__(self, profile: QWebEngineProfile, new_tab_page_callback):
        super().__init__(profile)
        self._new_tab_page_callback = new_tab_page_callback

    def createWindow(self, window_type):
        # middle-click / target=_blank / window.open -> вкладка в фоне
        return self._new_tab_page_callback(switch_to_new_tab=False)


class BrowserTab(QWidget):
    def __init__(self, profile: QWebEngineProfile, new_tab_page_callback, url: str):
        super().__init__()
        self.view = QWebEngineView()
        self.page = BrowserPage(profile, new_tab_page_callback)
        self.view.setPage(self.page)

        # FullScreen отключаем полностью (чтобы не было крашей)
        self.view.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, False)
        try:
            self.page.fullScreenRequested.connect(lambda req: req.reject())
        except Exception:
            pass

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        self.view.setUrl(QUrl(url))


class MiniBrowser(QMainWindow):
    def __init__(self, cfg: configparser.ConfigParser):
        super().__init__()
        self.cfg = cfg

        self.setWindowTitle("GdBrowser")
        self.resize(1200, 780)

        # UI settings
        self.tooltips_enabled = (self.cfg.get("ui", "tooltips", fallback="true").strip().lower() == "true")

        # WebEngine profile: постоянные файлы
        self.profile = QWebEngineProfile("GdBrowserProfile", self)
        self.profile.setPersistentStoragePath(str(USER_DATA_DIR))
        self.profile.setCachePath(str(CACHE_DIR))
        self.profile.downloadRequested.connect(self.on_download_requested)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        self.statusBar().showMessage(f"Данные: {APP_DATA_DIR}")

        self.tb = QToolBar("Навигация")
        self.tb.setMovable(False)
        self.tb.setIconSize(QSize(18, 18))
        self.addToolBar(self.tb)

        self.act_back = QAction("←", self)
        self.act_forward = QAction("→", self)
        self.act_reload = QAction("⟳", self)
        self.act_home = QAction("⌂", self)
        self.act_new_tab = QAction("+", self)
        self.act_settings = QAction("⚙", self)

        self.act_back.triggered.connect(lambda: self.current_view().back())
        self.act_forward.triggered.connect(lambda: self.current_view().forward())
        self.act_reload.triggered.connect(lambda: self.current_view().reload())
        self.act_home.triggered.connect(lambda: self.current_view().setUrl(QUrl(HOME_URL)))
        self.act_new_tab.triggered.connect(lambda: self.add_tab(HOME_URL, switch=True))
        self.act_settings.triggered.connect(self.open_settings)

        self.tb.addAction(self.act_back)
        self.tb.addAction(self.act_forward)
        self.tb.addAction(self.act_reload)
        self.tb.addAction(self.act_home)
        self.tb.addSeparator()
        self.tb.addAction(self.act_settings)

        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Введите адрес или запрос и нажмите Enter…")
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        self.tb.addWidget(self.urlbar)

        self.tb.addSeparator()
        self.tb.addAction(self.act_new_tab)

        self.addAction(self._shortcut("Ctrl+L", lambda: (self.urlbar.setFocus(), self.urlbar.selectAll())))
        self.addAction(self._shortcut("Ctrl+T", lambda: self.add_tab(HOME_URL, switch=True)))
        self.addAction(self._shortcut("Ctrl+W", lambda: self.close_tab(self.tabs.currentIndex())))

        # применяем подсказки
        self.apply_tooltips(self.tooltips_enabled)

        self.add_tab(HOME_URL, switch=True)

    def _shortcut(self, key: str, fn):
        a = QAction(self)
        a.setShortcut(QKeySequence(key))
        a.triggered.connect(fn)
        return a

    def apply_tooltips(self, enabled: bool):
        self.tooltips_enabled = enabled

        tips = {
            self.act_back: "Назад",
            self.act_forward: "Вперёд",
            self.act_reload: "Обновить",
            self.act_home: "Домой (стартовая)",
            self.act_settings: "Настройки",
            self.act_new_tab: "Новая вкладка",
        }

        for act, tip in tips.items():
            act.setToolTip(tip if enabled else "")

        self.urlbar.setToolTip("Введите URL или запрос и нажмите Enter" if enabled else "")
        self.tb.setToolTip("Панель навигации" if enabled else "")

        # Прокинем на стартовую страницу (для HTML tooltips)
        self.push_ui_tooltips_to_home()

    def push_ui_tooltips_to_home(self):
        # обновить localStorage ui_tooltips на всех домашних вкладках
        val = "1" if self.tooltips_enabled else "0"
        js = (
            f"localStorage.setItem('ui_tooltips','{val}');"
            "if (window.renderLinks) window.renderLinks();"
        )
        for i in range(self.tabs.count()):
            t = self.tabs.widget(i)
            if t and t.view.url().toString().startswith(HOME_URL):
                t.view.page().runJavaScript(js)

    def new_tab_page(self, switch_to_new_tab: bool) -> QWebEnginePage:
        tab = self.add_tab("about:blank", switch=switch_to_new_tab, return_tab=True)
        return tab.page

    def add_tab(self, url: str, switch: bool = False, return_tab: bool = False):
        tab = BrowserTab(self.profile, self.new_tab_page, url)
        idx = self.tabs.addTab(tab, "Загрузка…")

        tab.view.titleChanged.connect(lambda t, tab=tab: self.tabs.setTabText(
            self.tabs.indexOf(tab), (t[:28] + "…") if len(t) > 28 else t
        ))
        tab.view.urlChanged.connect(lambda q, tab=tab: self.on_url_changed(q, tab))
        tab.view.loadFinished.connect(lambda ok, tab=tab: self.on_load_finished(ok, tab))

        if switch:
            self.tabs.setCurrentIndex(idx)

        return tab if return_tab else None

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            return
        self.tabs.removeTab(index)

    def current_tab(self):
        return self.tabs.currentWidget()

    def current_view(self):
        t = self.current_tab()
        return t.view if t else None

    def on_tab_changed(self, _):
        v = self.current_view()
        if v:
            self.urlbar.setText(v.url().toString())

    def on_url_changed(self, qurl: QUrl, tab: BrowserTab):
        if tab == self.current_tab():
            self.urlbar.setText(qurl.toString())
            self.urlbar.setCursorPosition(0)

    def on_load_finished(self, ok: bool, tab: BrowserTab):
        if not ok:
            return
        if tab.view.url().toString().startswith(HOME_URL):
            engine = self.cfg.get("search", "engine", fallback=DEFAULT_ENGINE)
            tpl = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE]).replace("\\", "\\\\").replace("'", "\\'")
            js = (
                f"localStorage.setItem('search_template','{tpl}');"
                f"localStorage.setItem('ui_tooltips','{'1' if self.tooltips_enabled else '0'}');"
                "if (window.renderLinks) window.renderLinks();"
            )
            tab.view.page().runJavaScript(js)

    def open_settings(self):
        dlg = SettingsDialog(self.cfg, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        old_logs_enabled = (self.cfg.get("logs", "enabled", fallback="true").strip().lower() == "true")
        old_logs_mb = clamp_int(self.cfg.get("logs", "max_mb", fallback=str(DEFAULT_LOG_MB)), DEFAULT_LOG_MB, 1, 500)

        self.cfg["search"]["engine"] = dlg.get_engine()
        self.cfg["ui"]["tooltips"] = "true" if dlg.get_tooltips_enabled() else "false"
        self.cfg["logs"]["enabled"] = "true" if dlg.get_logs_enabled() else "false"
        self.cfg["logs"]["max_mb"] = str(dlg.get_logs_max_mb())
        save_cfg(self.cfg)

        # применить подсказки сразу
        self.apply_tooltips(dlg.get_tooltips_enabled())

        # обновить search_template на домашней странице
        for i in range(self.tabs.count()):
            t = self.tabs.widget(i)
            if t and t.view.url().toString().startswith(HOME_URL):
                engine = self.cfg.get("search", "engine", fallback=DEFAULT_ENGINE)
                tpl = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE]).replace("\\", "\\\\").replace("'", "\\'")
                t.view.page().runJavaScript(
                    f"localStorage.setItem('search_template','{tpl}');"
                    "if (window.renderLinks) window.renderLinks();"
                )

        new_logs_enabled = dlg.get_logs_enabled()
        new_logs_mb = dlg.get_logs_max_mb()
        if (new_logs_enabled != old_logs_enabled) or (new_logs_mb != old_logs_mb):
            QMessageBox.information(
                self,
                "Логи",
                "Настройки логов сохранены.\n"
                "Очистка будет при достижении лимита.\n"
                "Для включения/выключения chromium.log нужен перезапуск."
            )

    def build_url(self, text: str) -> QUrl:
        text = text.strip()
        if not text:
            return QUrl(HOME_URL)

        if text == "!cat_secret":
            if CAT_PATH.exists():
                return QUrl(CAT_PATH.resolve().as_uri())
            QMessageBox.warning(self, "Секретка", f"Нет файла:\n{CAT_PATH}")
            return QUrl(HOME_URL)

        if "://" in text:
            return QUrl(text)

        if looks_like_url(text):
            return QUrl("https://" + text)

        engine = self.cfg.get("search", "engine", fallback=DEFAULT_ENGINE)
        tpl = SEARCH_ENGINES.get(engine, SEARCH_ENGINES[DEFAULT_ENGINE])
        return QUrl(tpl.replace("{q}", encode_query(text)))

    def navigate_to_url(self):
        self.current_view().setUrl(self.build_url(self.urlbar.text()))

    def on_download_requested(self, download):
        try:
            filename = download.downloadFileName() or "download"
        except Exception:
            filename = "download"

        reply = QMessageBox.question(
            self,
            "Загрузка файла",
            f"Сайт хочет скачать:\n\n{filename}\n\nРазрешить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            try:
                download.cancel()
            except Exception:
                pass
            return

        default_path = str((DOWNLOADS_DIR / filename).resolve())
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить как…", default_path)
        if not path:
            try:
                download.cancel()
            except Exception:
                pass
            return

        if hasattr(download, "setPath"):
            download.setPath(path)
        download.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("GdBrowser")
    app.setStyleSheet(DARK_QSS)

    win = MiniBrowser(CFG)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    ensure_app_files()
    CFG = load_cfg()
    main()
