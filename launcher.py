import sys
import os
import json
import zipfile
import shutil
import requests
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QProgressBar, QMessageBox, QCheckBox, QDialog, QLineEdit, QFileDialog
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

class InstallLocationDialog(QDialog):
    def __init__(self, default_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Install Location")
        self.setFixedSize(500, 160)
        self.setStyleSheet("""
            QDialog { background-color: #1E1E1E; color: #FFFFFF; font-family: 'Segoe UI', sans-serif; }
            QLabel { font-size: 14px; font-weight: bold; color: #E0E0E0; }
            QLineEdit { background-color: #2D2D30; color: #FFFFFF; border: 1px solid #555555; padding: 8px; font-size: 13px; border-radius: 4px; }
            QPushButton { background-color: #0078D7; color: white; border-radius: 4px; font-weight: bold; padding: 8px 15px; }
            QPushButton:hover { background-color: #1084D0; }
            QPushButton#CancelBtn { background-color: #555555; }
            QPushButton#CancelBtn:hover { background-color: #666666; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel("Select the installation folder:")
        layout.addWidget(lbl)
        
        h_layout = QHBoxLayout()
        self.path_edit = QLineEdit(default_path)
        btn_browse = QPushButton("Browse...")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self.browse)
        
        h_layout.addWidget(self.path_edit)
        h_layout.addWidget(btn_browse)
        layout.addLayout(h_layout)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("CancelBtn")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        
        btn_ok = QPushButton("Install Here")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)
        
    def browse(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Folder", self.path_edit.text(), QFileDialog.ShowDirsOnly)
        if dir_path:
            # Auto-append the app folder name so files don't spill into a generic directory
            if os.path.basename(dir_path) != "uP_Verilog_Sandbox":
                dir_path = os.path.join(dir_path, "uP_Verilog_Sandbox")
            self.path_edit.setText(os.path.normpath(dir_path))
            
    def get_path(self):
        return os.path.normpath(self.path_edit.text())


class AppManagerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("µP Verilog Sandbox - App Manager")
        self.setFixedSize(480, 350)
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
        
        self.target_install_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)

        self.lbl_title = QLabel("µP VERILOG SANDBOX APP MANAGER")
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

    # --- Path Management & Tracking ---
    
    def get_launcher_config_path(self):
        """Global launcher registry to remember where the user installed the app."""
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        else:
            base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return os.path.join(base, "uP_Verilog_Sandbox_Launcher", "config.json")

    def get_saved_install_path(self):
        conf = self.get_launcher_config_path()
        if os.path.exists(conf):
            try:
                with open(conf, "r") as f:
                    return json.load(f).get("install_path")
            except Exception:
                pass
        return None

    def save_install_path(self, path):
        conf = self.get_launcher_config_path()
        os.makedirs(os.path.dirname(conf), exist_ok=True)
        with open(conf, "w") as f:
            json.dump({"install_path": path}, f)

    def get_default_install_path(self):
        """Industry standard user-level install directories (No Admin rights required)."""
        if sys.platform == "win32":
            base = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
            return os.path.normpath(os.path.join(base, "Programs", "uP_Verilog_Sandbox"))
        else:
            return os.path.expanduser("~/.local/share/uP_Verilog_Sandbox")

    def is_installed(self):
        path = self.get_saved_install_path()
        if not path or not os.path.exists(path): return False
        
        binary_name = "Sandbox.exe" if sys.platform == "win32" else "Sandbox"
        return os.path.exists(os.path.join(path, binary_name)) and os.path.exists(os.path.join(path, "current_version.json"))

    def get_local_version(self):
        path = self.get_saved_install_path()
        if path and os.path.exists(os.path.join(path, "current_version.json")):
            try:
                with open(os.path.join(path, "current_version.json"), "r") as f:
                    return json.load(f).get("version", "Unknown")
            except Exception:
                return "Corrupted"
        return "Not Installed"

    def get_platform_download_url(self, remote_info):
        if sys.platform == "win32":
            return remote_info.get("download_url_windows", remote_info.get("download_url"))
        return remote_info.get("download_url_linux", remote_info.get("download_url"))

    # --- UI Logic ---

    def refresh_status(self):
        installed = self.is_installed()
        ver = self.get_local_version()

        if installed:
            self.lbl_status.setText(f"Installed Engine Version: {ver}\nLocation: {self.get_saved_install_path()}")
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
        default_path = self.get_saved_install_path() or self.get_default_install_path()
        
        dialog = InstallLocationDialog(default_path, self)
        if dialog.exec_() == QDialog.Accepted:
            self.target_install_path = dialog.get_path()
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
                    self.target_install_path = self.get_saved_install_path()
                    url = self.get_platform_download_url(remote_info)
                    self.download_and_install(url, remote_info, create_desktop=True)
            else:
                QMessageBox.information(self, "Up to Date", f"You are on the latest version ({local_ver}).")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check updates:\n{str(e)}")

    def reinstall_app(self):
        try:
            self.target_install_path = self.get_saved_install_path()
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
            if os.path.exists(self.target_install_path):
                shutil.rmtree(self.target_install_path)
            
            os.makedirs(self.target_install_path, exist_ok=True)
            
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                zip_ref.extractall(self.target_install_path)
            
            if os.path.exists("update.zip"):
                os.remove("update.zip")

            if sys.platform != "win32":
                for root, _, files in os.walk(self.target_install_path):
                    for file in files:
                        if file in ["Sandbox", "iverilog", "vvp", "ivl", "ivlpp"]:
                            file_path = os.path.join(root, file)
                            try:
                                os.chmod(file_path, os.stat(file_path).st_mode | 0o111)
                            except Exception:
                                pass

            # Save the version inside the install folder, and update global registry
            with open(os.path.join(self.target_install_path, "current_version.json"), "w") as f:
                json.dump(remote_info, f)
            
            self.save_install_path(self.target_install_path)
            self.create_shortcuts(create_desktop)

            QMessageBox.information(self, "Success", "Application successfully installed/updated!")
            self.refresh_status()
        except Exception as e:
            QMessageBox.critical(self, "Extraction Error", str(e))
            self.refresh_status()

    def create_shortcuts(self, create_desktop=True):
        try:
            app_dir = self.target_install_path
            
            if sys.platform == "win32":
                exe_path = os.path.join(app_dir, "Sandbox.exe")
                vbs_script = f"""
                Set ws = WScript.CreateObject("WScript.Shell")
                startMenu = ws.SpecialFolders("Programs")
                Set link2 = ws.CreateShortcut(startMenu & "\\uP Verilog Sandbox.lnk")
                link2.TargetPath = "{exe_path}"
                link2.WorkingDirectory = "{app_dir}"
                link2.IconLocation = "{exe_path},0"
                link2.Save
                """
                if create_desktop:
                    vbs_script += f"""
                    desktop = ws.SpecialFolders("Desktop")
                    Set link = ws.CreateShortcut(desktop & "\\uP Verilog Sandbox.lnk")
                    link.TargetPath = "{exe_path}"
                    link.WorkingDirectory = "{app_dir}"
                    link.IconLocation = "{exe_path},0"
                    link.Save
                    """
                vbs_path = os.path.join(os.environ["TEMP"], "create_shortcut.vbs")
                with open(vbs_path, "w", encoding="utf-8") as f:
                    f.write(vbs_script)
                subprocess.run(["cscript", "//Nologo", vbs_path], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                if os.path.exists(vbs_path):
                    os.remove(vbs_path)

            else:
                exe_path = os.path.join(app_dir, "Sandbox")
                icon_path = os.path.join(app_dir, "icon.png")
                
                desktop_entry = f"""[Desktop Entry]
Name=uP Verilog Sandbox
Comment=Interactive Verilog Simulation Debugger
Exec={exe_path}
Icon={icon_path if os.path.exists(icon_path) else 'utilities-terminal'}
Terminal=false
Type=Application
Categories=Development;Engineering;Electronics;
"""
                apps_dir = os.path.expanduser("~/.local/share/applications")
                os.makedirs(apps_dir, exist_ok=True)
                with open(os.path.join(apps_dir, "verilog-sandbox.desktop"), "w", encoding="utf-8") as f:
                    f.write(desktop_entry)
                
                if create_desktop:
                    desktop_dir = os.path.expanduser("~/Desktop")
                    if os.path.exists(desktop_dir):
                        desktop_file = os.path.join(desktop_dir, "verilog-sandbox.desktop")
                        with open(desktop_file, "w", encoding="utf-8") as f:
                            f.write(desktop_entry)
                        os.chmod(desktop_file, 0o755)
        except Exception as e:
            print(f"Non-fatal error creating shortcuts: {e}")

    def remove_shortcuts(self):
        try:
            if sys.platform == "win32":
                desktop_link = os.path.join(os.environ["USERPROFILE"], "Desktop", "uP Verilog Sandbox.lnk")
                start_link = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "uP Verilog Sandbox.lnk")
                
                old_desktop_link = os.path.join(os.environ["USERPROFILE"], "Desktop", "µP Verilog Sandbox.lnk")
                old_start_link = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "µP Verilog Sandbox.lnk")

                for path in [desktop_link, start_link, old_desktop_link, old_start_link]:
                    if os.path.exists(path):
                        try:
                            os.remove(path)
                        except Exception:
                            pass
            else:
                desktop_link = os.path.expanduser("~/Desktop/verilog-sandbox.desktop")
                app_link = os.path.expanduser("~/.local/share/applications/verilog-sandbox.desktop")
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
            
            # Remove main files
            path = self.get_saved_install_path()
            if path and os.path.exists(path):
                shutil.rmtree(path)
                
            # Remove registry/config
            conf = self.get_launcher_config_path()
            if os.path.exists(conf):
                os.remove(conf)
                
            QMessageBox.information(self, "Uninstalled", "Application and shortcuts have been cleanly removed.")
            self.refresh_status()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppManagerWindow()
    window.show()
    sys.exit(app.exec_())