import sys
import os
import json
import zipfile
import shutil
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, 
    QProgressBar, QMessageBox, QCheckBox
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
        self.setFixedSize(480, 350)  # Increased window size to fit larger text
        self.setStyleSheet("""
            QWidget { background-color: #1E1E1E; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-size: 15px; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 5px; font-weight: bold; padding: 12px; font-size: 14px; }
            QPushButton:hover { background-color: #1084D0; }
            QPushButton#InstallBtn { background-color: #107C41; }
            QPushButton#InstallBtn:hover { background-color: #0F6A37; }
            QPushButton#DeleteBtn { background-color: #D13438; }
            QPushButton#DeleteBtn:hover { background-color: #E81123; }
            QCheckBox { padding: 8px; font-size: 16px; spacing: 10px; }
            QCheckBox::indicator { width: 20px; height: 20px; } 
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        self.lbl_title = QLabel("µP PRARAMBH APP MANAGER")
        self.lbl_title.setStyleSheet("font-size: 20px; font-weight: 900; color: #00E5FF; margin-bottom: 10px;")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_title)

        self.lbl_status = QLabel("Checking version status...")
        self.lbl_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.chk_desktop = QCheckBox("Create Desktop Shortcut")
        self.chk_desktop.setChecked(True)
        layout.addWidget(self.chk_desktop)

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
            self.chk_desktop.setVisible(False)
            self.btn_update.setVisible(True)
            self.btn_reinstall.setVisible(True)
            self.btn_delete.setVisible(True)
        else:
            self.lbl_status.setText("Status: Sandbox Application Not Installed")
            self.btn_install.setVisible(True)
            self.chk_desktop.setVisible(True)
            self.btn_update.setVisible(False)
            self.btn_reinstall.setVisible(False)
            self.btn_delete.setVisible(False)

    def install_app(self):
        try:
            res = requests.get(MANIFEST_URL, timeout=5)
            res.raise_for_status()
            remote_info = res.json()
            url = self.get_platform_download_url(remote_info)
            self.download_and_install(url, remote_info, create_desktop=self.chk_desktop.isChecked())
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
                    # Updates automatically repair shortcuts if they were deleted
                    self.download_and_install(url, remote_info, create_desktop=True)
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
            self.download_and_install(url, remote_info, create_desktop=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch manifest:\n{str(e)}")

    def download_and_install(self, url, remote_info, create_desktop=False):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_status.setText("Downloading core package...")
        self.set_buttons_enabled(False)

        self.worker = DownloadWorker(url, "update.zip")
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(lambda ok, msg: self.install_zip(ok, msg, remote_info, create_desktop))
        self.worker.start()

    def set_buttons_enabled(self, enabled):
        self.btn_install.setEnabled(enabled)
        self.btn_update.setEnabled(enabled)
        self.btn_reinstall.setEnabled(enabled)
        self.btn_delete.setEnabled(enabled)

    def install_zip(self, success, msg, remote_info, create_desktop):
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

            # Generate Shortcuts
            self.create_shortcuts(create_desktop)

            QMessageBox.information(self, "Success", "Application successfully installed/updated!")
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "Extraction Error", str(e))
            self.refresh_status()

    def create_shortcuts(self, create_desktop=True):
        """Generates Start Menu (always) and Desktop shortcuts (optional)."""
        try:
            app_dir = os.path.abspath("app")
            
            if sys.platform == "win32":
                exe_path = os.path.join(app_dir, "Sandbox.exe")
                vbs_script = f"""
                Set ws = WScript.CreateObject("WScript.Shell")
                startMenu = ws.SpecialFolders("Programs")
                Set link2 = ws.CreateShortcut(startMenu & "\\µP PRARAMBH Sandbox.lnk")
                link2.TargetPath = "{exe_path}"
                link2.WorkingDirectory = "{app_dir}"
                link2.IconLocation = "{exe_path},0"
                link2.Save
                """
                if create_desktop:
                    vbs_script += f"""
                    desktop = ws.SpecialFolders("Desktop")
                    Set link = ws.CreateShortcut(desktop & "\\µP PRARAMBH Sandbox.lnk")
                    link.TargetPath = "{exe_path}"
                    link.WorkingDirectory = "{app_dir}"
                    link.IconLocation = "{exe_path},0"
                    link.Save
                    """
                vbs_path = os.path.join(os.environ["TEMP"], "create_shortcut.vbs")
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                subprocess.run(["cscript", "//Nologo", vbs_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                os.remove(vbs_path)

            else:
                exe_path = os.path.join(app_dir, "Sandbox")
                icon_path = os.path.join(app_dir, "icon.png")
                
                desktop_entry = f"""[Desktop Entry]
Name=µP PRARAMBH Sandbox
Comment=Interactive Verilog Simulation Debugger
Exec={exe_path}
Icon={icon_path if os.path.exists(icon_path) else 'utilities-terminal'}
Terminal=false
Type=Application
Categories=Development;Engineering;Electronics;
"""
                # App Menu (Always)
                apps_dir = os.path.expanduser("~/.local/share/applications")
                os.makedirs(apps_dir, exist_ok=True)
                with open(os.path.join(apps_dir, "prarambh-sandbox.desktop"), "w") as f:
                    f.write(desktop_entry)
                
                # Desktop (Optional)
                if create_desktop:
                    desktop_dir = os.path.expanduser("~/Desktop")
                    if os.path.exists(desktop_dir):
                        desktop_file = os.path.join(desktop_dir, "prarambh-sandbox.desktop")
                        with open(desktop_file, "w") as f:
                            f.write(desktop_entry)
                        os.chmod(desktop_file, 0o755)
        except Exception as e:
            print(f"Non-fatal error creating shortcuts: {e}")

    def remove_shortcuts(self):
        """Cleans up Start Menu and Desktop shortcuts upon uninstallation."""
        try:
            if sys.platform == "win32":
                desktop_link = os.path.join(os.environ["USERPROFILE"], "Desktop", "µP PRARAMBH Sandbox.lnk")
                start_link = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "µP PRARAMBH Sandbox.lnk")
                if os.path.exists(desktop_link): os.remove(desktop_link)
                if os.path.exists(start_link): os.remove(start_link)
            else:
                desktop_link = os.path.expanduser("~/Desktop/prarambh-sandbox.desktop")
                app_link = os.path.expanduser("~/.local/share/applications/prarambh-sandbox.desktop")
                if os.path.exists(desktop_link): os.remove(desktop_link)
                if os.path.exists(app_link): os.remove(app_link)
        except Exception as e:
            print(f"Non-fatal error removing shortcuts: {e}")

    def delete_app(self):
        reply = QMessageBox.warning(
            self, "Confirm Uninstall", 
            "Are you sure you want to completely remove the Sandbox and its shortcuts?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.remove_shortcuts()
            if os.path.exists("app"):
                shutil.rmtree("app")
            if os.path.exists("current_version.json"):
                os.remove("current_version.json")
            QMessageBox.information(self, "Uninstalled", "Application and shortcuts have been cleanly removed.")
            self.refresh_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppManagerWindow()
    window.show()
    sys.exit(app.exec_())