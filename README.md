<div align="center">

# ⚡ µP PRARAMBH Sandbox

**An interactive workspace for debugging and verifying Verilog simulations.**

[![GitHub Release](https://img.shields.io/github/v/release/Jmehta134/PRARAMBH-Sandbox?style=for-the-badge&color=0078D7)](https://github.com/Jmehta134/PRARAMBH-Sandbox/releases)
[![Platform Support](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-00E5FF?style=for-the-badge)](https://github.com/Jmehta134/PRARAMBH-Sandbox/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg?style=for-the-badge)](LICENSE)

---

[Quick Start](#-quick-start) • [Key Features](#-key-features) • [Building from Source](#-building-from-source) • [License](#-license)

</div>

---

## 📌 Overview

**µP PRARAMBH Sandbox** is an interactive debugging interface for Verilog logic circuit simulations. Designed for rapid verification and experiment analysis rather than full-scale code editing, it pairs a visual debugging GUI with pre-bundled **Icarus Verilog (`iverilog`)** toolchains—delivering zero-configuration simulation execution on Windows and Linux.

The application is managed via **`Installer`**, a portable utility handling automated installation, updates, repairs, and uninstalls.

---

## 🚀 Quick Start

No prior toolchain configuration or Python setup is required. Download `Installer` for your operating system:

### 1. Download Installer

| Platform | Download Link | File Name |
| :--- | :--- | :--- |
| **Windows** (10/11) | [**Download Installer.exe**](https://github.com/Jmehta134/PRARAMBH-Sandbox/releases/latest/download/Installer.exe) | `Installer.exe` |
| **Linux** (Ubuntu/Debian) | [**Download Installer**](https://github.com/Jmehta134/PRARAMBH-Sandbox/releases/latest/download/Installer) | `Installer` |

### 2. Install & Run

- **Windows**: Double-click `Installer.exe` and click **INSTALL SANDBOX APPLICATION**.
- **Linux**: Open terminal in your download directory, grant permissions, and run:
  ```bash
  chmod +x Installer
  ./Installer

---

## ✨ Key Features

* **Interactive Simulation Debugger**: Real-time signal testing, waveform inspection, and execution log monitoring.
* **Pre-bundled Verilog Engine**: Native `iverilog` and `vvp` binaries are bundled into platform payloads—no path variables or external dependencies needed.
* **AppManager Lifecycle Utility**: Automated GitHub release installation, remote version checking, clean uninstall, and repair.
* **Fully Portable**: Runs isolated within its local directory without system clutter or registry changes.
* **Cross-Platform**: Parity across native Windows and Linux (including WSL2 / WSLg).

---

## 📂 Project Structure

```
PRARAMBH-Sandbox/
├── bin/            # Bundled Windows and Linux iverilog & vvp binaries
├── examples/       # Pre-configured Verilog simulation testbenches
├── src/main.py     # Main PyQt5 interactive debugging interface
├── launcher.py     # AppManager utility source
└── version.json    # Version manifest for automated updates
```

---

## 🛠 Building from Source

### Prerequisites
* Python 3.8+ (`PyQt5`, `requests`, `pyinstaller`)

### Build Commands

```bash
# Windows (PowerShell)
pyinstaller --noconfirm --onedir --windowed --name "Sandbox" --add-data "examples;examples" --add-data "bin;bin" src/main.py
pyinstaller --noconfirm --onefile --windowed --name "Installer" launcher.py

# Linux (Bash / WSL2)
pyinstaller --noconfirm --onedir --windowed --name "Sandbox" --hidden-import=pkgutil --add-data "examples:examples" --add-data "bin:bin" src/main.py
pyinstaller --noconfirm --onefile --windowed --name "Installer" launcher.py
```

---

## 📜 License

This project is open-source software licensed under the **GNU General Public License v3.0 (GPL-3.0)**. See [`LICENSE`](LICENSE) for details.
