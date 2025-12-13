import sys
from pathlib import Path

from PyQt6.QtCore import QUrl, QSize
from PyQt6.QtGui import QKeySequence, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QWidget, QVBoxLayout, QMessageBox, QFileDialog
)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage


HOME_URL = Path(__file__).with_name("start.html").as_uri()

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


def normalize_url(text: str) -> QUrl:
    text = text.strip()
    if not text:
        return QUrl(HOME_URL)

    if "://" in text:
        return QUrl(text)

    if "." in text and " " not in text:
        return QUrl("https://" + text)

    query = QUrl.toPercentEncoding(text).data().decode("utf-8")
    return QUrl(f"https://www.google.com/search?q={query}")


class BrowserPage(QWebEnginePage):
    """
    Если сертификат плохой — блокируем загрузку.
    """
    def __init__(self, profile: QWebEngineProfile, on_bad_cert_callback):
        super().__init__(profile)
        self._bad_cert = False
        self._on_bad_cert_callback = on_bad_cert_callback

    def has_bad_cert(self) -> bool:
        return self._bad_cert

    def certificateError(self, error):
        self._bad_cert = True
        try:
            self._on_bad_cert_callback()
        except Exception:
            pass

        QMessageBox.warning(
            None,
            "Ошибка сертификата",
            "У сайта проблема с сертификатом.\n"
            "По соображениям безопасности страница заблокирована."
        )
        return False 


class BrowserTab(QWidget):
    def __init__(self, profile: QWebEngineProfile, on_bad_cert_callback, url: str):
        super().__init__()
        self.view = QWebEngineView()
        self.page = BrowserPage(profile, on_bad_cert_callback)
        self.view.setPage(self.page)
        self.view.setUrl(QUrl(url))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)


class MiniBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MiniBrowser")
        self.resize(1200, 780)

        self.profile = QWebEngineProfile.defaultProfile()
        self.profile.downloadRequested.connect(self.on_download_requested)
        self._active_downloads = []

        self._warned_insecure_hosts = set()
        self._suppress_insecure_warning = False

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        self.statusBar().showMessage("Готово")

        tb = QToolBar("Навигация")
        tb.setMovable(False)
        tb.setIconSize(QSize(18, 18))
        self.addToolBar(tb)

        self.act_back = QAction("←", self)
        self.act_forward = QAction("→", self)
        self.act_reload = QAction("⟳", self)
        self.act_home = QAction("⌂", self)
        self.act_new_tab = QAction("+", self)

        self.act_back.triggered.connect(lambda: self.current_view().back())
        self.act_forward.triggered.connect(lambda: self.current_view().forward())
        self.act_reload.triggered.connect(lambda: self.current_view().reload())
        self.act_home.triggered.connect(lambda: self.current_view().setUrl(QUrl(HOME_URL)))
        self.act_new_tab.triggered.connect(lambda: self.add_tab(HOME_URL, switch=True))

        tb.addAction(self.act_back)
        tb.addAction(self.act_forward)
        tb.addAction(self.act_reload)
        tb.addAction(self.act_home)
        tb.addSeparator()

        self.act_lock = QAction("🔓", self)
        self.act_lock.triggered.connect(self.show_security_info)
        tb.addAction(self.act_lock)

        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Введите адрес или запрос и нажмите Enter…")
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        tb.addWidget(self.urlbar)

        tb.addSeparator()
        tb.addAction(self.act_new_tab)

        self.act_focus_url = QAction(self)
        self.act_focus_url.setShortcut(QKeySequence("Ctrl+L"))
        self.act_focus_url.triggered.connect(lambda: (self.urlbar.setFocus(), self.urlbar.selectAll()))
        self.addAction(self.act_focus_url)

        self.act_new_tab_sc = QAction(self)
        self.act_new_tab_sc.setShortcut(QKeySequence("Ctrl+T"))
        self.act_new_tab_sc.triggered.connect(lambda: self.add_tab(HOME_URL, switch=True))
        self.addAction(self.act_new_tab_sc)

        self.act_close_tab_sc = QAction(self)
        self.act_close_tab_sc.setShortcut(QKeySequence("Ctrl+W"))
        self.act_close_tab_sc.triggered.connect(lambda: self.close_tab(self.tabs.currentIndex()))
        self.addAction(self.act_close_tab_sc)

        self.add_tab(HOME_URL, switch=True)

    def add_tab(self, url: str, switch: bool = False):
        tab = BrowserTab(
            profile=self.profile,
            on_bad_cert_callback=self.update_security_indicator,
            url=url
        )
        i = self.tabs.addTab(tab, "Загрузка…")

        tab.view.urlChanged.connect(lambda qurl, tab=tab: self.on_url_changed(qurl, tab))
        tab.view.titleChanged.connect(
            lambda title, tab=tab: self.tabs.setTabText(
                self.tabs.indexOf(tab),
                title[:28] + ("…" if len(title) > 28 else "")
            )
        )
        tab.view.loadFinished.connect(lambda ok, tab=tab: self.on_load_finished(ok, tab))

        if switch:
            self.tabs.setCurrentIndex(i)

    def close_tab(self, index: int):
        if self.tabs.count() <= 1:
            return
        self.tabs.removeTab(index)

    def current_tab(self) -> BrowserTab:
        return self.tabs.currentWidget()

    def current_view(self) -> QWebEngineView:
        t = self.current_tab()
        return t.view if t else None

    def current_page(self) -> BrowserPage:
        t = self.current_tab()
        return t.page if t else None

    def on_tab_changed(self, index: int):
        view = self.current_view()
        if view:
            self.urlbar.setText(view.url().toString())
        self.update_security_indicator()

    def on_url_changed(self, qurl: QUrl, tab: BrowserTab):
        if tab == self.current_tab():
            self.urlbar.setText(qurl.toString())
            self.urlbar.setCursorPosition(0)

            self.maybe_warn_insecure(qurl)

            self.update_security_indicator()

    def on_load_finished(self, ok: bool, tab: BrowserTab):
        if tab == self.current_tab():
            self.update_security_indicator()
        if not ok and tab == self.current_tab():
            QMessageBox.warning(self, "Ошибка", "Страница не загрузилась.")

    def is_https_secure(self, url: QUrl) -> bool:
        page = self.current_page()
        if not page:
            return False
        return (url.scheme().lower() == "https") and (not page.has_bad_cert())

    def update_security_indicator(self):
        view = self.current_view()
        if not view:
            self.act_lock.setVisible(False)
            return

        url = view.url()
        scheme = url.scheme().lower()

        if scheme in ("file", "about", ""):
            self.act_lock.setVisible(False)
            return

        self.act_lock.setVisible(True)

        if self.is_https_secure(url):
            self.act_lock.setText("🔒")
            self.act_lock.setToolTip("Защищённое соединение (HTTPS)")
        else:
            self.act_lock.setText("🔓")
            if scheme == "http":
                self.act_lock.setToolTip("Незащищённое соединение (HTTP)")
            elif scheme == "https":
                self.act_lock.setToolTip("Проблема с сертификатом / не подтверждено")
            else:
                self.act_lock.setToolTip("Соединение не подтверждено")

    def show_security_info(self):
        view = self.current_view()
        page = self.current_page()
        if not view or not page:
            return

        url = view.url()
        scheme = url.scheme().lower()
        host = url.host() or url.toString()

        if scheme == "https" and not page.has_bad_cert():
            QMessageBox.information(
                self,
                "Безопасность соединения",
                f"Сайт: {host}\n\n"
                "✅ Соединение защищено (HTTPS).\n"
                "Данные шифруются при передаче."
            )
            return

        if scheme == "http":
            QMessageBox.warning(
                self,
                "Безопасность соединения",
                f"Сайт: {host}\n\n"
                "⚠ Соединение НЕ защищено (HTTP).\n"
                "Данные могут быть перехвачены (пароли, сообщения и т.д.).\n"
                "Если можно — используйте HTTPS."
            )
            return

        if scheme == "https" and page.has_bad_cert():
            QMessageBox.critical(
                self,
                "Безопасность соединения",
                f"Сайт: {host}\n\n"
                "⛔ Ошибка сертификата.\n"
                "Страница заблокирована ради безопасности."
            )
            return

        QMessageBox.information(
            self,
            "Безопасность соединения",
            f"Сайт: {host}\n\n"
            "Соединение не подтверждено."
        )

    def maybe_warn_insecure(self, url: QUrl):
        if self._suppress_insecure_warning:
            return

        if url.scheme().lower() != "http":
            return

        host = url.host()
        if not host:
            return

        if host in self._warned_insecure_hosts:
            return

        self._warned_insecure_hosts.add(host)

        reply = QMessageBox.warning(
            self,
            "Незащищённый сайт",
            f"⚠ Вы открываете незашифрованный сайт (HTTP):\n{host}\n\n"
            "Данные могут быть перехвачены. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.No:
            self._suppress_insecure_warning = True
            try:
                self.current_view().stop()
                self.current_view().setUrl(QUrl(HOME_URL))
            finally:
                self._suppress_insecure_warning = False

    def navigate_to_url(self):
        url = normalize_url(self.urlbar.text())

        if url.scheme().lower() == "http":
            host = url.host() or url.toString()
            reply = QMessageBox.warning(
                self,
                "Незащищённый сайт",
                f"⚠ Адрес использует HTTP:\n{host}\n\n"
                "Данные могут быть перехвачены. Открыть всё равно?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.current_view().setUrl(url)


    def on_download_requested(self, download):
        try:
            filename = download.downloadFileName() or "download"
        except Exception:
            filename = "download"

        reply = QMessageBox.question(
            self,
            "Загрузка файла",
            f"Сайт хочет скачать файл:\n\n{filename}\n\nРазрешить загрузку?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            try:
                download.cancel()
            except Exception:
                pass
            return

        path, _ = QFileDialog.getSaveFileName(self, "Сохранить файл как…", filename)
        if not path:
            try:
                download.cancel()
            except Exception:
                pass
            return

        if hasattr(download, "setPath"):
            download.setPath(path)
        else:
            p = Path(path)
            if hasattr(download, "setDownloadDirectory"):
                download.setDownloadDirectory(str(p.parent))
            if hasattr(download, "setDownloadFileName"):
                download.setDownloadFileName(p.name)

        self._active_downloads.append(download)

        if hasattr(download, "receivedBytesChanged"):
            download.receivedBytesChanged.connect(lambda: self._update_download_status(download))
        if hasattr(download, "totalBytesChanged"):
            download.totalBytesChanged.connect(lambda: self._update_download_status(download))
        if hasattr(download, "stateChanged"):
            download.stateChanged.connect(lambda: self._download_state_changed(download))

        download.accept()
        self.statusBar().showMessage(f"Скачивание начато: {Path(path).name}")

    def _update_download_status(self, download):
        try:
            rec = int(download.receivedBytes())
            tot = int(download.totalBytes())
        except Exception:
            return

        if tot > 0:
            pct = int(rec * 100 / tot)
            self.statusBar().showMessage(f"Скачивание… {pct}% ({rec//1024} KB / {tot//1024} KB)")
        else:
            self.statusBar().showMessage(f"Скачивание… {rec//1024} KB")

    def _download_state_changed(self, download):
        try:
            is_finished = hasattr(download, "isFinished") and download.isFinished()
        except Exception:
            is_finished = False

        if is_finished:
            self.statusBar().showMessage("Скачивание завершено")
            try:
                self._active_downloads.remove(download)
            except ValueError:
                pass


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MiniBrowser")
    app.setStyleSheet(DARK_QSS)

    win = MiniBrowser()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
