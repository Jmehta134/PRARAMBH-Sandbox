import sys
import os
import json
import zipfile
import shutil
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

MANIFEST_URL = "https://raw.githubusercontent.com/Jmehta134/PRARAMBH-Sandbox/main/version.json"

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            response = requests.get(self.url, stream=True, timeout=15)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            self.progress.emit(int((downloaded / total_size) * 100))
            self.finished.emit(True, "Download complete.")
        except Exception as e:
            self.finished.emit(False, str(e))

class AppManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("µP PRARAMBH - App Manager")
        self.setFixedSize(440, 290)
        self.setStyleSheet("""
            QWidget { background-color: #1E1E1E; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; font-weight: bold; padding: 10px; }
            QPushButton:hover { background-color: #1084D0; }
            QPushButton#InstallBtn { background-color: #107C41; }
            QPushButton#InstallBtn:hover { background-color: #0F6A37; }
            QPushButton#DeleteBtn { background-color: #D13438; }
            QPushButton#DeleteBtn:hover { background-color: #E81123; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        self.lbl_title = QLabel("µP PRARAMBH APP MANAGER")
        self.lbl_title.setStyleSheet("font-size: 16px; font-weight: 900; color: #00E5FF;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        self.lbl_status = QLabel("Checking version status...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.btn_install = QPushButton("INSTALL SANDBOX APPLICATION")
        self.btn_install.setObjectName("InstallBtn")
        self.btn_install.clicked.connect(self.install_app)

        self.btn_update = QPushButton("CHECK & APPLY UPDATES")
        self.btn_update.clicked.connect(self.check_for_updates)

        self.btn_reinstall = QPushButton("REPAIR / REINSTALL CORE APP")
        self.btn_reinstall.clicked.connect(self.reinstall_app)

        self.btn_delete = QPushButton("UNINSTALL / REMOVE APP FILES")
        self.btn_delete.setObjectName("DeleteBtn")
        self.btn_delete.clicked.connect(self.delete_app)

        layout.addWidget(self.btn_install)
        layout.addWidget(self.btn_update)
        layout.addWidget(self.btn_reinstall)
        layout.addWidget(self.btn_delete)

        self.refresh_status()

    def is_installed(self):
        binary_name = "Sandbox.exe" if sys.platform == "win32" else "Sandbox"
        binary_path = os.path.join("app", binary_name)
        return os.path.exists(binary_path) and os.path.exists("current_version.json")

    def get_local_version(self):
        if os.path.exists("current_version.json"):
            try:
                with open("current_version.json", "r") as f:
                    return json.load(f).get("version", "Unknown")
            except Exception:
                return "Corrupted"
        return "Not Installed"

    def get_platform_download_url(self, remote_info):
        if sys.platform == "win32":
            return remote_info.get("download_url_windows", remote_info.get("download_url"))
        return remote_info.get("download_url_linux", remote_info.get("download_url"))

    def refresh_status(self):
        installed = self.is_installed()
        ver = self.get_local_version()

        if installed:
            self.lbl_status.setText(f"Installed Core Engine Version: {ver}")
            self.btn_install.setVisible(False)
            self.btn_update.setVisible(True)
            self.btn_reinstall.setVisible(True)
            self.btn_delete.setVisible(True)
        else:
            self.lbl_status.setText("Status: Sandbox Application Not Installed")
            self.btn_install.setVisible(True)
            self.btn_update.setVisible(False)
            self.btn_reinstall.setVisible(False)
            self.btn_delete.setVisible(False)

    def install_app(self):
        try:
            res = requests.get(MANIFEST_URL, timeout=5)
            res.raise_for_status()
            remote_info = res.json()
            url = self.get_platform_download_url(remote_info)
            self.download_and_install(url, remote_info)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch manifest/installer link:\n{str(e)}")

    def check_for_updates(self):
        try:
            res = requests.get(MANIFEST_URL, timeout=5)
            res.raise_for_status()
            remote_info = res.json()
            remote_ver = remote_info["version"]
            local_ver = self.get_local_version()

            if local_ver != remote_ver:
                reply = QMessageBox.question(
                    self, "Update Available", 
                    f"New version {remote_ver} available!\nLocal version: {local_ver}\n\nUpdate now?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    url = self.get_platform_download_url(remote_info)
                    self.download_and_install(url, remote_info)
            else:
                QMessageBox.information(self, "Up to Date", f"You are on the latest version ({local_ver}).")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check updates:\n{str(e)}")

    def reinstall_app(self):
        try:
            res = requests.get(MANIFEST_URL, timeout=5)
            res.raise_for_status()
            remote_info = res.json()
            url = self.get_platform_download_url(remote_info)
            self.download_and_install(url, remote_info)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch manifest:\n{str(e)}")

    def download_and_install(self, url, remote_info):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Downloading core package...")
        self.set_buttons_enabled(False)

        self.worker = DownloadWorker(url, "update.zip")
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(lambda ok, msg: self.install_zip(ok, msg, remote_info))
        self.worker.start()

    def set_buttons_enabled(self, enabled):
        self.btn_install.setEnabled(enabled)
        self.btn_update.setEnabled(enabled)
        self.btn_reinstall.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    def install_zip(self, success, msg, remote_info):
        self.progress_bar.setVisible(False)
        self.set_buttons_enabled(True)

        if not success:
            QMessageBox.critical(self, "Download Failed", msg)
            self.refresh_status()
            return

        self.lbl_status.setText("Extracting package...")
        try:
            if os.path.exists("app"):
                shutil.rmtree("app")
            
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                zip_ref.extractall("app")
            
            if os.path.exists("update.zip"):
                os.remove("update.zip")

            # Restore executable bits on Linux automatically
            if sys.platform != "win32":
                for root, _, files in os.walk("app"):
                    for file in files:
                        if file in ["Sandbox", "iverilog", "vvp", "ivl", "ivlpp"]:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
                            except Exception:
                                pass

            with open("current_version.json", "w") as f:
                json.dump(remote_info, f)

            QMessageBox.information(self, "Success", "Application successfully installed/updated!")
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "Extraction Error", str(e))
            self.refresh_status()

    def delete_app(self):
        reply = QMessageBox.warning(
            self, "Confirm Delete", 
            "Are you sure you want to delete the local application files?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if os.path.exists("app"):
                shutil.rmtree("app")
            if os.path.exists("current_version.json"):
                os.remove("current_version.json")
            QMessageBox.information(self, "Deleted", "Application files removed.")
            self.refresh_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppManagerWindow()
    window.show()
    sys.exit(app.exec_())