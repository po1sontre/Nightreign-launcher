# 🌙 Nightreign Launcher

> **A powerful game manager for Elden Ring Nightreign with Seamless Co-op mod**

---

## ✨ Features

- 🎮 **Launch Game** - Start with admin privileges
- 🔄 **Update Game** - Download and install latest version
- 🛠️ **Patch Game** - Install required online files
- 🔧 **Verify Files** - Check game structure and Steam status
- 🎯 **Controller Fix** - Install Steam controller configurations
- 💾 **Backup Saves** - Create backups of your save files
- ⚙️ **Game Settings** - Apply mods, performance settings, and FPS unlock
- 🎨 **Custom Themes** - Multiple color themes available
- 📁 **Folder Management** - Easy game and Steam directory selection

---

## 🚀 Quick Start

### Prerequisites
- **Steam** must be running
- **Administrator privileges** (run launcher as admin)
- **Elden Ring Nightreign** installation

### Installation

1. **Download** the launcher executable
2. **Extract** all files to a folder
3. **Ensure** all required files are in the same directory as the launcher exe

### Required File Structure
```
📁 Your Launcher Folder/
├── 🎯 NightreignLauncher.exe
├── 📁 online_patch/
├── 📁 templates/
├── 📁 fps unlock/
├── 📁 nograssnoshadows/
├── 📁 mods/
├── 📄 regulation.bin
├── 📄 update.exe
├── 📄 game_actions_480.vdf
└── 📄 icon.ico
```

> **⚠️ Important:** All resource folders and files must be in the same directory as `NightreignLauncher.exe` for the launcher to function properly.

---

## 🎯 First Time Setup

1. **Run as Administrator** - Right-click launcher → "Run as administrator"
2. **Select Game Folder** - Choose your Nightreign installation directory
3. **Patch Game** - Click "Patch Game" to install required files
4. **Update Game** - Click "Update Game" to get the latest version
5. **Start Playing** - Click "Start Game" to launch with admin privileges

---

## 🛠️ Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Game won't start | Run launcher as administrator |
| Missing files | Click "Verify Game Files" to check installation |
| Controller not working | Use "Controller Fix" button |
| Antivirus blocking | Add launcher folder to exclusions |
| Steam not detected | Ensure Steam is running |

### Antivirus Interference
Many antivirus programs may flag the launcher or its components. To resolve:
1. Add the launcher folder to antivirus exclusions
2. Temporarily disable real-time protection
3. Check antivirus quarantine for deleted files

---

## 🔧 Advanced Features

### Game Settings
- **FPS Unlock** - Remove 60 FPS cap
- **Performance Settings** - Disable grass and shadows
- **Mod Management** - Apply and manage game mods

### Backup & Restore
- **Save Backups** - Create timestamped backups
- **Mod Backups** - Automatic backup of original files

---

## 🏗️ Building from Source

### Requirements
- Python 3.8+
- PySide6
- PyInstaller

### Build Steps
```bash
# Install dependencies
pip install -r requirements.txt

# Build executable
pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
```

### Development
```bash
# Run in development mode
python main.py
```

---

## 📋 File Requirements

### Required Folders
- `online_patch/` - Game patching files
- `templates/` - Steam controller templates
- `fps unlock/` - FPS unlocker files
- `nograssnoshadows/` - Performance settings
- `mods/` - Game modification files

### Required Files
- `regulation.bin` - Game regulation file
- `update.exe` - Game updater
- `game_actions_480.vdf` - Steam controller configuration

---

## 🤝 Support

- **Discord:** [Join our community](https://discord.gg/YDtHQNqnqj)
- **Issues:** Report bugs on GitHub
- **Contributions:** Pull requests welcome

---

## ⚠️ Disclaimer

This launcher is an independent project and is not officially affiliated with:
- FromSoftware Inc.
- The creators of Elden Ring
- The Seamless Co-op mod developers
- Any associated patch/update developers

Use at your own discretion.

---

## 👨‍💻 Credits

**Built with ❤️ by po1sontre**

---

*Last updated: December 2024* 