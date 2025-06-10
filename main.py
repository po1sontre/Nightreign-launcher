import sys
import os
import subprocess
import ctypes
import configparser
import shutil
import webbrowser
import zipfile
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QSpinBox, QLabel, QFrame, QMessageBox,
                             QFileDialog, QHBoxLayout, QDialog, QComboBox,
                             QFormLayout, QColorDialog, QGraphicsOpacityEffect,
                             QScrollArea, QProgressBar, QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QFont, QPalette, QColor, QIcon
import time
from pathlib import Path

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def safe_file_operation(source, destination, operation_type='copy', retries=5, delay=0.5):
    """
    Safely perform file operations with retries and error handling.
    This function now handles internal cleanup (removing existing destinations)
    within its retry mechanism.
    
    Args:
        source (str): Source file/directory path. (For 'write_test', this can be None).
        destination (str): Destination file/directory path.
        operation_type (str): Type of operation ('copy', 'move', 'delete', 'write_test').
        retries (int): Number of retry attempts.
        delay (float): Delay between retries in seconds.
    
    Returns:
        bool: True if operation succeeded, False otherwise.
    """
    
    for attempt in range(retries):
        try:
            # Ensure parent directory exists for destination
            Path(destination).parent.mkdir(parents=True, exist_ok=True)

            if operation_type == 'copy':
                # Handle existing destination before copying
                if os.path.exists(destination):
                    if os.path.isfile(destination):
                        os.remove(destination)
                    elif os.path.isdir(destination):
                        shutil.rmtree(destination)
                
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                elif os.path.isdir(source):
                    shutil.copytree(source, destination)
            
            elif operation_type == 'move':
                # Similar to copy, but also remove source
                if os.path.exists(destination):
                    if os.path.isfile(destination):
                        os.remove(destination)
                    elif os.path.isdir(destination):
                        shutil.rmtree(destination)
                
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                    os.remove(source)
                elif os.path.isdir(source):
                    shutil.copytree(source, destination)
                    shutil.rmtree(source) # Remove source after successful copy
            
            elif operation_type == 'delete':
                if os.path.isfile(destination):
                    os.remove(destination)
                elif os.path.isdir(destination):
                    shutil.rmtree(destination)
            
            elif operation_type == 'write_test':
                temp_file = os.path.join(destination, f"temp_write_test_{os.getpid()}.tmp")
                with open(temp_file, 'w') as f:
                    f.write("test")
                os.remove(temp_file)
            
            # Verification (optional, but good for robustness)
            if operation_type in ['copy', 'move']:
                if os.path.isfile(source) and not os.path.exists(destination):
                    raise Exception(f"Verification failed: Destination file '{destination}' not found.")
                elif os.path.isdir(source) and not os.path.exists(destination):
                    raise Exception(f"Verification failed: Destination directory '{destination}' not found.")
            
            return True
            
        except (PermissionError, OSError) as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue # Retry
            else:
                print(f"Failed '{operation_type}' operation on '{source if source else destination}' after {retries} attempts due to permission/OS error: {str(e)}")
                return False
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(delay)
                continue # Retry
            else:
                print(f"Failed '{operation_type}' operation on '{source if source else destination}' after {retries} attempts: {str(e)}")
                return False
    return False

def get_user_save_directory():
    """ Get the current user's Nightreign save directory """
    username = os.getenv('USERNAME')
    if username:
        save_dir = os.path.join(f"C:\\Users\\{username}\\AppData\\Roaming\\Nightreign")
        if os.path.exists(save_dir):
            return save_dir
    return None

def validate_game_directory(potential_dir):
    """ Validates if the given directory is the correct game folder or finds it within """
    if not potential_dir or not os.path.exists(potential_dir):
        return None

    # Check if the expected game executable exists directly in the potential_dir
    if os.path.exists(os.path.join(potential_dir, "nrsc_launcher.exe")):
        return potential_dir

    # If not found directly, check common subdirectories like 'Game'
    common_subdirs = ["Game"]
    for subdir_name in common_subdirs:
        subdir_path = os.path.join(potential_dir, subdir_name)
        if os.path.exists(os.path.join(subdir_path, "nrsc_launcher.exe")):
            return subdir_path

    # If still not found, return None
    return None

def get_config_path():
    """Get the path to the config file"""
    if hasattr(sys, '_MEIPASS'):
        # When running as exe, store in the same directory as the exe
        return os.path.join(os.path.dirname(sys.executable), "launcher_config.ini")
    else:
        # When running as script, store in the same directory as the script
        return os.path.join(os.path.dirname(__file__), "launcher_config.ini")

def load_settings():
    """Load settings from config file"""
    config = configparser.ConfigParser()
    config_path = get_config_path()
    
    if os.path.exists(config_path):
        config.read(config_path)
    
    # Set defaults if not present
    if 'Settings' not in config:
        config['Settings'] = {}
    if 'theme_color' not in config['Settings']:
        config['Settings']['theme_color'] = 'Teal'
    if 'regulation_moved' not in config['Settings']:
        config['Settings']['regulation_moved'] = 'False'
    if 'game_dir' not in config['Settings']:
        config['Settings']['game_dir'] = r"C:\Games\ELDEN RING NIGHTREIGN\Game"
    
    return config

def save_settings(config):
    """Save settings to config file"""
    with open(get_config_path(), 'w') as f:
        config.write(f)

def check_antivirus_interference():
    """Check for common antivirus processes that might interfere with the launcher"""
    try:
        import psutil
        antivirus_processes = {
            'avast': ['AvastSvc.exe', 'AvastUI.exe'],
            'avg': ['AVGSvc.exe', 'AVGUI.exe'],
            'bitdefender': ['bdredline.exe', 'bdagent.exe'],
            'kaspersky': ['avp.exe', 'kavstart.exe'],
            'mcafee': ['mcshield.exe', 'mcafee.exe'],
            'norton': ['NortonSecurity.exe', 'NS.exe'],
            'windows defender': ['MsMpEng.exe', 'NisSrv.exe'],
            'malwarebytes': ['MBAMService.exe', 'mbam.exe']
        }
        
        detected_av = []
        for av_name, processes in antivirus_processes.items():
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] in processes:
                    detected_av.append(av_name)
                    break
        
        return detected_av
    except ImportError:
        return []

def get_steam_templates_dir(steam_dir):
    # Remove trailing controller_base/templates if present
    norm = os.path.normpath(steam_dir)
    parts = norm.lower().split(os.sep)
    if len(parts) >= 2 and parts[-2] == 'controller_base' and parts[-1] == 'templates':
        steam_dir = os.path.dirname(os.path.dirname(norm))
    return os.path.join(steam_dir, "controller_base", "templates")

def get_steam_config_dir(steam_dir):
    # Remove trailing controller_config if present
    norm = os.path.normpath(steam_dir)
    parts = norm.lower().split(os.sep)
    if parts and parts[-1] == 'controller_config':
        steam_dir = os.path.dirname(norm)
    return os.path.join(steam_dir, "controller_config")

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Nightreign Launcher")
        self.setMinimumSize(600, 400)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Title
        title = QLabel("Welcome to Nightreign!")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Let's get you started")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(subtitle)
        
        # Add some spacing
        content_layout.addSpacing(20)
        
        # Welcome message
        self.message = QLabel("""
This launcher will help you manage your Nightreign game installation. Here's what you can do:

• Start the game with admin privileges
• Update to the latest version
• Patch game files if needed
• Apply controller fixes
• Backup your save files
• Customize the launcher's appearance

The first time you run the game, you'll need to:
1. Select your game folder
2. Apply the patch
3. Start the game

Would you like to select your game folder now?
        """)
        self.message.setWordWrap(True)
        self.message.setAlignment(Qt.AlignLeft)
        content_layout.addWidget(self.message)
        
        # Add some spacing
        content_layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.select_folder_btn = QPushButton("Select Game Folder")
        self.select_folder_btn.setMinimumSize(150, 40)
        self.select_folder_btn.clicked.connect(self.accept)
        
        self.skip_btn = QPushButton("Skip for Now")
        self.skip_btn.setMinimumSize(150, 40)
        self.skip_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.select_folder_btn)
        button_layout.addWidget(self.skip_btn)
        content_layout.addLayout(button_layout)
        
        # Add content to main layout
        layout.addWidget(content)
        
        # Set up fade-in animation
        self.opacity_effect = QGraphicsOpacityEffect()
        content.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(500)  # 500ms
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Style the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 10px;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color if parent else '#00b4b4'};
                color: #000000;
            }}
        """)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.animation.start()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        layout = QFormLayout(self)
        
        # Game folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(parent.game_dir)
        self.folder_label.setStyleSheet(f"color: {parent.theme_color};")
        folder_button = QPushButton("Change")
        folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_button)
        
        # Steam folder selection
        steam_folder_layout = QHBoxLayout()
        self.steam_folder_label = QLabel(parent.steam_templates_dir)
        self.steam_folder_label.setStyleSheet(f"color: {parent.theme_color};")
        steam_folder_button = QPushButton("Change")
        steam_folder_button.clicked.connect(self.select_steam_folder)
        steam_folder_layout.addWidget(self.steam_folder_label)
        steam_folder_layout.addWidget(steam_folder_button)
        
        # Theme color selection
        color_layout = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Teal", "Purple", "Orange", "Pink", "Red", "Green", "Blue"])
        self.color_combo.setCurrentText(parent.theme_color_name)
        self.selected_color_name = parent.theme_color_name
        self.color_combo.currentTextChanged.connect(self.update_selected_color_name)
        color_layout.addWidget(self.color_combo)
        
        layout.addRow("Game Folder:", folder_layout)
        layout.addRow("Steam Folder:", steam_folder_layout)
        layout.addRow("Theme Color:", color_layout)
        
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept)
        layout.addRow("", apply_button)
        
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color};
                color: #000000;
            }}
            QComboBox {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QComboBox:hover {{
                border-color: {parent.theme_color};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Nightreign Game Folder",
            self.folder_label.text(),
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            validated_folder = validate_game_directory(folder)
            if validated_folder:
                self.folder_label.setText(validated_folder)
            else:
                QMessageBox.warning(self, "Invalid Folder", "The selected folder does not appear to be the correct Nightreign game directory or its parent. Please select the folder containing 'nrsc_launcher.exe'.")
    
    def select_steam_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Steam Folder",
            self.steam_folder_label.text(),
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            # Validate that this is a Steam folder by checking for common Steam files/directories
            steam_files = ["steam.exe", "Steam.dll", "steamapps"]
            is_steam_folder = any(os.path.exists(os.path.join(folder, file)) for file in steam_files)
            
            if is_steam_folder:
                self.steam_folder_label.setText(folder)
            else:
                QMessageBox.warning(self, "Invalid Folder", "The selected folder does not appear to be a valid Steam installation. Please select your Steam installation folder.")
    
    def update_selected_color_name(self, color_name):
        self.selected_color_name = color_name

class PatchNotesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Patch Notes")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Version History")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Version selector
        version_layout = QHBoxLayout()
        version_label = QLabel("Select Version:")
        self.version_combo = QComboBox()
        self.version_combo.addItems([
            "4.0.0 - Latest",
            "3.0.0",
            "2.0.0",
            "1.0.0"
        ])
        self.version_combo.currentTextChanged.connect(self.update_notes)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_combo)
        layout.addLayout(version_layout)
        
        # Notes display
        self.notes_text = QLabel()
        self.notes_text.setWordWrap(True)
        self.notes_text.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.notes_text.setStyleSheet("padding: 10px;")
        
        # Add notes text to a scroll area
        scroll = QScrollArea()
        scroll.setWidget(self.notes_text)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        # Set initial notes
        self.update_notes(self.version_combo.currentText())
        
        # Style the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color if parent else '#00b4b4'};
                color: #000000;
            }}
            QComboBox {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QComboBox:hover {{
                border-color: {parent.theme_color if parent else '#00b4b4'};
            }}
            QScrollArea {{
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                background-color: #1a1a1a;
            }}
        """)
    
    def update_notes(self, version):
        notes = {
            "4.0.0 - Latest": """
• Added Patch Notes/Version History
• Added Troubleshooting feature
• Added Steam folder selection in settings
• Added welcome screen that no one is gonna read and ping instead to explain everything thats written in the welcome screen
• Improved update process handling
• Added automatic regulation file moving after updates
• Made window resizable
• Fixed various bugs and improved stability
            """,
            "3.0.0": """
• Added About dialog
• Added backup save files feature
• Added controller fix feature
• Improved game folder validation
• Added theme color customization
• Added Discord button
• Added settings dialog
            """,
            "2.0.0": """
• Added update game feature
• Added patch game feature
• Added player count selection
• Added status messages
• Improved error handling
            """,
            "1.0.0": """
• Initial release
• Basic game launching functionality
• Game folder selection
            """
        }
        self.notes_text.setText(notes.get(version, "No notes available for this version."))

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Help & About")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Help & About")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Content
        content = QLabel("""
Nightreign Launcher
Version: 4.0.0

This is a fan-made launcher for Elden Ring Nightreign with the Seamless Co-op mod.

Quick Help:
1. First Time Setup:
   • Select your game folder (if its not selectd by default)
   • Click "Patch Game" to install required online files
   • Click "Update Game" to install the latest version of the game
   • Start the game with admin privileges

2. Common Issues:
   • If the game doesn't start or crashes, try "Troubleshoot" this will check if the game is installed correctly and if the patch is applied completely incase the antivirus ate a file
   • If controller doesn't work, use "Controller Fix" this will install the custom steam controller configuration
   • If update fails, make sure you selected the correct folder

3. Important Notes:
   • Player count is preset to 3 (usually doesn't need changing)
   • the game requires Steam to be running
   • Always run the launcher as administrator

4. Features:
   • Start Game: Launches the game with admin privileges
   • Update Game: Downloads and installs the latest version
   • Patch Game: Installs required game files
   • Troubleshoot: Checks game files and Steam status
   • Controller Fix: Installs Steam controller configuration
   • Backup Save Files: Creates a backup of your save data
   • Settings: Configure game folder, Steam folder, and theme

Developed by: po1sontre

Disclaimer: This launcher is an independent project and is not officially affiliated with the creators of the base game, the Seamless Co-op mod, or any associated patch/update developers.
        """)
        content.setWordWrap(True)
        content.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        content.setStyleSheet("padding: 10px;")
        
        # Add content to a scroll area
        scroll = QScrollArea()
        scroll.setWidget(content)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        # Style the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color if parent else '#00b4b4'};
                color: #000000;
            }}
            QScrollArea {{
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                background-color: #1a1a1a;
            }}
        """)

class ModMenuDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mod Menu")
        self.setMinimumSize(400, 300)
        
        # Create backup of original regulation.bin if it doesn't exist
        self.create_original_backup()
        
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select a Mod")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Mod list
        self.mod_list = QComboBox()
        self.mod_list.setMinimumHeight(40)
        self.mod_list.setFont(QFont("Arial", 12))
        
        # Get list of mods from the mods directory
        mods_dir = os.path.join(os.path.dirname(sys.executable), "mods")
        if not os.path.exists(mods_dir):
            mods_dir = os.path.join(os.path.dirname(__file__), "mods")
        
        if os.path.exists(mods_dir):
            for mod_folder in os.listdir(mods_dir):
                mod_path = os.path.join(mods_dir, mod_folder)
                if os.path.isdir(mod_path) and os.path.exists(os.path.join(mod_path, "regulation.bin")):
                    self.mod_list.addItem(mod_folder)
        
        layout.addWidget(self.mod_list)
        
        # Description
        self.description = QLabel("Select a mod to apply its regulation.bin file to your game.")
        self.description.setWordWrap(True)
        self.description.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.description)
        
        # Button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setSpacing(10)
        
        # Apply button
        apply_button = QPushButton("Apply Mod")
        apply_button.setMinimumHeight(40)
        apply_button.setFont(QFont("Arial", 12, QFont.Bold))
        apply_button.clicked.connect(self.apply_mod)
        button_layout.addWidget(apply_button)
        
        # Reset button
        reset_button = QPushButton("Reset to Normal")
        reset_button.setMinimumHeight(40)
        reset_button.setFont(QFont("Arial", 12, QFont.Bold))
        reset_button.clicked.connect(self.reset_to_normal)
        button_layout.addWidget(reset_button)
        
        layout.addWidget(button_container)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setMinimumHeight(40)
        close_button.setFont(QFont("Arial", 12))
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        # Style the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color if parent else '#00b4b4'};
                color: #000000;
            }}
            QComboBox {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QComboBox:hover {{
                border-color: {parent.theme_color if parent else '#00b4b4'};
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
        """)
    
    def create_original_backup(self):
        """Create a backup of the original regulation.bin if it doesn't exist"""
        try:
            game_regulation = os.path.join(self.parent().game_dir, "regulation.bin")
            original_regulation = os.path.join(os.path.dirname(sys.executable), "regulation.bin")
            if not os.path.exists(original_regulation):
                original_regulation = os.path.join(os.path.dirname(__file__), "regulation.bin")
            
            # Check if we have the original regulation.bin
            if not os.path.exists(original_regulation):
                return
            
            # Create backups directory if it doesn't exist
            backups_dir = os.path.join(self.parent().game_dir, "regulation_backups")
            os.makedirs(backups_dir, exist_ok=True)
            
            # Check if we already have a backup of the original
            original_backup = os.path.join(backups_dir, "regulation_original.bin")
            if not os.path.exists(original_backup):
                # Create backup of original regulation.bin using safe_file_operation
                if not safe_file_operation(original_regulation, original_backup, 'copy'):
                    print(f"Warning: Failed to create original regulation.bin backup at {original_backup}")
        except Exception as e:
            print(f"Failed to create original backup: {str(e)}")
    
    def apply_mod(self):
        if self.mod_list.currentText():
            try:
                # Get paths
                mods_dir = os.path.join(os.path.dirname(sys.executable), "mods")
                if not os.path.exists(mods_dir):
                    mods_dir = os.path.join(os.path.dirname(__file__), "mods")
                
                mod_folder = os.path.join(mods_dir, self.mod_list.currentText())
                mod_regulation = os.path.join(mod_folder, "regulation.bin")
                game_regulation = os.path.join(self.parent().game_dir, "regulation.bin")
                
                # Check if mod regulation.bin exists
                if not os.path.exists(mod_regulation):
                    QMessageBox.critical(self, "Error", f"regulation.bin not found in {mod_folder}")
                    return
                
                # Copy mod regulation.bin to game folder using safe_file_operation
                if not safe_file_operation(mod_regulation, game_regulation, 'copy'):
                    QMessageBox.critical(self, "Error", 
                        f"Failed to apply mod {self.mod_list.currentText()}.\n\n"
                        "This might be caused by permissions or antivirus. Please ensure:\n"
                        "1. The game is not running\n"
                        "2. Your antivirus is not blocking access\n"
                        "3. You have run the launcher as administrator")
                    return
                
                QMessageBox.information(self, "Success", 
                    f"Successfully applied {self.mod_list.currentText()} mod!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to apply mod: {str(e)}")
    
    def reset_to_normal(self):
        try:
            # Get paths
            game_regulation = os.path.join(self.parent().game_dir, "regulation.bin")
            original_backup = os.path.join(self.parent().game_dir, "regulation_backups", "regulation_original.bin")
            
            # Check if original backup exists
            if not os.path.exists(original_backup):
                QMessageBox.critical(self, "Error", 
                    "Original regulation.bin backup not found.\n"
                    "Please run Update Game first to get the original file.")
                return
            
            # Copy original backup to game folder using safe_file_operation
            if not safe_file_operation(original_backup, game_regulation, 'copy'):
                QMessageBox.critical(self, "Error", 
                    "Failed to reset to normal regulation.bin.\n\n"
                    "This might be caused by permissions or antivirus. Please ensure:\n"
                    "1. The game is not running\n"
                    "2. Your antivirus is not blocking access\n"
                    "3. You have run the launcher as administrator")
                return
            
            QMessageBox.information(self, "Success", 
                "Successfully reset to normal regulation.bin!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset regulation.bin: {str(e)}")
    
class GameSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Game Settings")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(self)
        
        # Performance Settings Group
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QVBoxLayout(performance_group)
        
        # FPS Unlock
        fps_layout = QHBoxLayout()
        self.fps_button = QPushButton("Unlock FPS (Remove 60 FPS Cap)")
        self.fps_button.setMinimumHeight(40)
        self.fps_button.setFont(QFont("Arial", 12))
        self.fps_button.clicked.connect(self.unlock_fps)
        fps_layout.addWidget(self.fps_button)
        performance_layout.addLayout(fps_layout)
        
        # Performance Settings Button
        self.performance_button = QPushButton("Apply Performance Settings (Disable Grass & Shadows)")
        self.performance_button.setMinimumHeight(40)
        self.performance_button.setFont(QFont("Arial", 12))
        self.performance_button.clicked.connect(self.apply_performance_settings)
        performance_layout.addWidget(self.performance_button)
        
        layout.addWidget(performance_group)
        
        # Mod Settings Group
        mod_group = QGroupBox("Mod Settings")
        mod_layout = QVBoxLayout(mod_group)
        
        # Mod Selection
        mod_selection_layout = QHBoxLayout()
        self.mod_combo = QComboBox()
        self.mod_combo.setMinimumHeight(30)
        self.mod_combo.setFont(QFont("Arial", 12))
        
        # Get list of mods from the mods directory
        mods_dir = os.path.join(os.path.dirname(sys.executable), "mods")
        if not os.path.exists(mods_dir):
            mods_dir = os.path.join(os.path.dirname(__file__), "mods")
        
        if os.path.exists(mods_dir):
            for mod_folder in os.listdir(mods_dir):
                mod_path = os.path.join(mods_dir, mod_folder)
                if os.path.isdir(mod_path) and os.path.exists(os.path.join(mod_path, "regulation.bin")):
                    self.mod_combo.addItem(mod_folder)
        
        mod_selection_layout.addWidget(self.mod_combo)
        mod_layout.addLayout(mod_selection_layout)
        
        # Mod Buttons
        mod_buttons_layout = QHBoxLayout()
        apply_mod_button = QPushButton("Apply Mod")
        apply_mod_button.clicked.connect(self.apply_mod)
        reset_mod_button = QPushButton("Reset to Normal")
        reset_mod_button.clicked.connect(self.reset_to_normal)
        mod_buttons_layout.addWidget(apply_mod_button)
        mod_buttons_layout.addWidget(reset_mod_button)
        mod_layout.addLayout(mod_buttons_layout)
        
        layout.addWidget(mod_group)
        
        # Close Button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        # Style the dialog
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {parent.theme_color if parent else '#00b4b4'};
                color: #000000;
            }}
            QComboBox {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QComboBox:hover {{
                border-color: {parent.theme_color if parent else '#00b4b4'};
            }}
            QGroupBox {{
                color: {parent.theme_color if parent else '#00b4b4'};
                border: 2px solid {parent.theme_color if parent else '#00b4b4'};
                border-radius: 5px;
                margin-top: 1em;
                padding-top: 1em;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }}
        """)
    
    def apply_performance_settings(self):
        """Copy the contents of the 'nograssnoshadows' folder into the game directory, replacing existing files."""
        try:
            # Find the nograssnoshadows folder (next to exe or script)
            src_dir = os.path.join(os.path.dirname(sys.executable), "nograssnoshadows")
            if not os.path.exists(src_dir):
                src_dir = os.path.join(os.path.dirname(__file__), "nograssnoshadows")
            if not os.path.exists(src_dir):
                raise Exception("'nograssnoshadows' folder not found next to the launcher.")
            dest_dir = self.parent().game_dir
            # Copy each file from src_dir to dest_dir, replacing
            for item in os.listdir(src_dir):
                src_path = os.path.join(src_dir, item)
                dest_path = os.path.join(dest_dir, item)
                if not safe_file_operation(src_path, dest_path, 'copy'):
                    raise Exception(f"Failed to copy {item} to game folder. Please ensure the game is not running and you have administrator privileges.")
            QMessageBox.information(self, "Success", "Performance settings applied successfully! (Grass and shadows disabled)")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply performance settings: {str(e)}")
    
    def unlock_fps(self):
        """Run the FPS unlocker executable"""
        try:
            # Get the path to the FPS unlocker executable
            fps_unlocker_dir = os.path.join(os.path.dirname(sys.executable), "fps unlock")
            if not os.path.exists(fps_unlocker_dir):
                fps_unlocker_dir = os.path.join(os.path.dirname(__file__), "fps unlock")
            
            fps_unlocker_exe = os.path.join(fps_unlocker_dir, "NightReignFPSUnlocker.exe")
            
            if not os.path.exists(fps_unlocker_exe):
                raise Exception("FPS unlocker executable not found")
            
            # Run the FPS unlocker
            result = subprocess.run([fps_unlocker_exe], 
                                 capture_output=True, 
                                 text=True,
                                 check=False)  # Don't raise exception on non-zero exit
            
            if result.returncode == 0:
                QMessageBox.information(self, "Success", 
                    "FPS unlocker has been launched successfully!\n\n"
                    "Please follow the instructions in the FPS unlocker window.")
            else:
                error_message = "FPS unlocker failed to start"
                if result.stdout:
                    error_message += f"\n\nDetails:\n{result.stdout}"
                if result.stderr:
                    error_message += f"\n\nError:\n{result.stderr}"
                
                QMessageBox.warning(self, "Error", error_message)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to run FPS unlocker: {str(e)}\n\n"
                "Please ensure:\n"
                "1. The FPS unlocker executable exists in the 'fps unlock' folder\n"
                "2. You have run the launcher as administrator\n"
                "3. Your antivirus is not blocking the FPS unlocker")
    
    def apply_mod(self):
        """Apply the selected mod"""
        if self.mod_combo.currentText():
            try:
                # Get paths
                mods_dir = os.path.join(os.path.dirname(sys.executable), "mods")
                if not os.path.exists(mods_dir):
                    mods_dir = os.path.join(os.path.dirname(__file__), "mods")
                
                mod_folder = os.path.join(mods_dir, self.mod_combo.currentText())
                mod_regulation = os.path.join(mod_folder, "regulation.bin")
                game_regulation = os.path.join(self.parent().game_dir, "regulation.bin")
                
                # Check if mod regulation.bin exists
                if not os.path.exists(mod_regulation):
                    raise Exception(f"regulation.bin not found in {mod_folder}")
                
                # Copy mod regulation.bin to game folder
                if not safe_file_operation(mod_regulation, game_regulation, 'copy'):
                    raise Exception("Failed to apply mod. Please ensure the game is not running and you have administrator privileges.")
                
                QMessageBox.information(self, "Success", 
                    f"Successfully applied {self.mod_combo.currentText()} mod!")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to apply mod: {str(e)}")
    
    def reset_to_normal(self):
        """Reset to normal regulation.bin"""
        try:
            # Get paths
            game_regulation = os.path.join(self.parent().game_dir, "regulation.bin")
            original_backup = os.path.join(self.parent().game_dir, "regulation_backups", "regulation_original.bin")
            
            # Check if original backup exists
            if not os.path.exists(original_backup):
                raise Exception("Original regulation.bin backup not found. Please run Update Game first.")
            
            # Copy original backup to game folder
            if not safe_file_operation(original_backup, game_regulation, 'copy'):
                raise Exception("Failed to reset to normal regulation.bin. Please ensure the game is not running and you have administrator privileges.")
            
            QMessageBox.information(self, "Success", 
                "Successfully reset to normal regulation.bin!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset regulation.bin: {str(e)}")

class NightreignLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nightreign Launcher")
        self.resize(700, 700)  # Default size, but window is resizable
        # Move window higher on the screen
        self.move(self.x(), 100)
        
        # Load settings
        self.config = load_settings()
        self.theme_color_name = self.config['Settings']['theme_color']
        self.theme_color = self.get_theme_color(self.theme_color_name)
        
        # Load saved game directory or use default
        self.game_dir = self.config['Settings']['game_dir']
        self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
        self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
        
        # Set patch directory to be in the same directory as the executable
        if hasattr(sys, '_MEIPASS'):
            # When running as exe, look in the same directory as the exe
            self.patch_dir = os.path.join(os.path.dirname(sys.executable), "online_patch")
            # First try to get templates from the executable
            self.templates_dir = resource_path("templates")
            # If templates don't exist in the executable, look next to the exe
            if not os.path.exists(self.templates_dir):
                self.templates_dir = os.path.join(os.path.dirname(sys.executable), "templates")
        else:
            # When running as script, look in the same directory as the script
            self.patch_dir = os.path.join(os.path.dirname(__file__), "online_patch")
            self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
            
        # Load saved Steam directory or use default
        if 'steam_dir' in self.config['Settings']:
            self.steam_dir = self.config['Settings']['steam_dir']
        else:
            self.steam_dir = r"C:\Program Files (x86)\Steam"
        self.steam_templates_dir = get_steam_templates_dir(self.steam_dir)
        self.steam_config_dir = get_steam_config_dir(self.steam_dir)
        self.vdf_file = resource_path("game_actions_480.vdf")
        
        # Path for update.exe - works for both dev and packaged versions
        if hasattr(sys, '_MEIPASS'):
            # When running as exe, look in the same directory as the exe
            self.update_exe_path = os.path.join(os.path.dirname(sys.executable), "update.exe")
            self.regulation_path = os.path.join(os.path.dirname(sys.executable), "regulation.bin")
        else:
            # When running as script, look in the same directory as the script
            self.update_exe_path = os.path.join(os.path.dirname(__file__), "update.exe")
            self.regulation_path = os.path.join(os.path.dirname(__file__), "regulation.bin")
        
        # Get user's save directory
        self.save_dir = get_user_save_directory()
        
        # Check for antivirus interference only on first launch
        if 'first_launch' not in self.config['Settings'] or self.config['Settings'].getboolean('first_launch'):
            detected_av = check_antivirus_interference()
            if detected_av:
                QMessageBox.warning(self, "Antivirus Detected", 
                    f"Detected antivirus software: {', '.join(detected_av)}\n\n"
                    "Your antivirus might interfere with the launcher. Please add these folders to your antivirus exclusions:\n\n"
                    f"1. This launcher's folder:\n   {os.path.dirname(sys.executable)}\n\n"
                    f"2. Your Elden Ring Nightreign folder:\n   {self.game_dir}\n\n"
                    "If you're still having issues:\n"
                    "1. Temporarily disable real-time protection when using the launcher\n"
                    "2. Check your antivirus quarantine for any deleted files\n"
                    "3. Make sure to run the launcher as administrator")
            
            # Mark first launch as complete
            self.config['Settings']['first_launch'] = 'False'
            save_settings(self.config)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        
        # Top Bar
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 10, 10, 10)
        top_layout.setSpacing(10)
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setFixedSize(120, 35)
        self.settings_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.settings_button.clicked.connect(self.show_settings)
        
        # Discord button
        self.discord_button = QPushButton("Discord")
        self.discord_button.setFixedSize(120, 35)
        self.discord_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.discord_button.clicked.connect(lambda: webbrowser.open("https://discord.gg/YDtHQNqnqj"))
        
        # Patch Notes button
        self.patch_notes_button = QPushButton("Updates")
        self.patch_notes_button.setFixedSize(120, 35)
        self.patch_notes_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.patch_notes_button.clicked.connect(self.show_patch_notes)
        
        # Help button
        self.help_button = QPushButton("Help")
        self.help_button.setFixedSize(120, 35)
        self.help_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.help_button.clicked.connect(self.show_help)
        
        # Add buttons with equal spacing
        top_layout.addStretch(1)
        top_layout.addWidget(self.settings_button)
        top_layout.addStretch(1)
        top_layout.addWidget(self.discord_button)
        top_layout.addStretch(1)
        top_layout.addWidget(self.patch_notes_button)
        top_layout.addStretch(1)
        top_layout.addWidget(self.help_button)
        top_layout.addStretch(1)
        
        # Title and Subtitle
        self.title_label = QLabel("NIGHTREIGN")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        
        self.subtitle_label = QLabel("Game Manager")
        self.subtitle_label.setFont(QFont("Arial", 14))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Main Buttons
        self.start_button = QPushButton("Start Game")
        self.start_button.setMinimumSize(250, 55)
        self.start_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.start_button.clicked.connect(self.start_game)
        
        self.update_button = QPushButton("Update Game")
        self.update_button.setMinimumSize(250, 55)
        self.update_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.update_button.clicked.connect(self.update_game)
        
        self.patch_button = QPushButton("Patch Game (online fix)")
        self.patch_button.setMinimumSize(250, 55)
        self.patch_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.patch_button.clicked.connect(self.patch_game)
        
        self.troubleshoot_button = QPushButton("Verify Game Files")
        self.troubleshoot_button.setMinimumSize(250, 55)
        self.troubleshoot_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.troubleshoot_button.clicked.connect(self.verify_game_files)
        
        self.controller_button = QPushButton("Controller Fix")
        self.controller_button.setMinimumSize(250, 55)
        self.controller_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.controller_button.clicked.connect(self.fix_controller)
        
        self.backup_button = QPushButton("Backup Save Files")
        self.backup_button.setMinimumSize(250, 55)
        self.backup_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.backup_button.clicked.connect(self.backup_saves)
        
        # New Game Settings button
        self.game_settings_button = QPushButton("Game Settings")
        self.game_settings_button.setMinimumSize(250, 55)
        self.game_settings_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.game_settings_button.clicked.connect(self.show_game_settings)
        
        self.select_folder_button = QPushButton("Select Nightreign Game Folder")
        self.select_folder_button.setMinimumSize(250, 55)
        self.select_folder_button.setFont(QFont("Arial", 13, QFont.Bold))
        self.select_folder_button.clicked.connect(self.select_game_folder)
        
        # Player Count Selection
        player_container = QWidget()
        player_layout = QHBoxLayout(player_container)
        player_layout.setSpacing(10)
        
        self.player_buttons = []
        for count in [1, 2, 3]:
            button = QPushButton(f"{count} Player{'s' if count > 1 else ''}")
            button.setMinimumSize(120, 40)
            button.setFont(QFont("Arial", 11, QFont.Bold))
            button.setCheckable(True)
            button.clicked.connect(lambda checked, c=count: self.set_player_count(c))
            self.player_buttons.append(button)
            player_layout.addWidget(button)
        
        self.player_buttons[2].setChecked(True)
        
        # Status Bar
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setObjectName("statusFrame")
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Ready to launch")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        self.credits_label = QLabel("by po1sontre")
        self.credits_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(top_bar)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.update_button)
        layout.addWidget(self.patch_button)
        layout.addWidget(self.troubleshoot_button)
        layout.addWidget(self.controller_button)
        layout.addWidget(self.backup_button)
        layout.addWidget(self.game_settings_button)  # New Game Settings button
        layout.addWidget(self.select_folder_button)
        layout.addWidget(player_container)
        layout.addStretch()
        layout.addWidget(status_frame)
        layout.addWidget(self.credits_label)
        
        self.update_theme_color(self.theme_color_name)
        
        self.check_game_directory()
        self.check_save_directory()
        self.check_update_exe()

        # Check if this is first launch
        if 'first_launch' not in self.config['Settings']:
            self.config['Settings']['first_launch'] = 'True'
            save_settings(self.config)
            self.show_welcome_dialog()

    def show_game_settings(self):
        """Show the game settings dialog"""
        dialog = GameSettingsDialog(self)
        dialog.exec()

    def check_game_directory(self):
        if not os.path.exists(self.game_dir):
            self.select_folder_button.show()
            self.start_button.setEnabled(False)
            self.patch_button.setEnabled(False)
            self.controller_button.setEnabled(False)
            self.status_label.setText("Game directory not found. Please select your Nightreign game folder.")
            return False
            
        # Check if nrsc_launcher.exe exists
        if not os.path.exists(os.path.join(self.game_dir, "nrsc_launcher.exe")):
            self.status_label.setText("Game needs to be patched. Patching automatically...")
            self.patch_game()
            # After patching, check again if the file exists
            if not os.path.exists(os.path.join(self.game_dir, "nrsc_launcher.exe")):
                self.select_folder_button.show()
                self.start_button.setEnabled(False)
                self.patch_button.setEnabled(True)
                self.controller_button.setEnabled(False)
                self.status_label.setText("Automatic patching failed. Please try patching manually.")
                return False
        
        self.select_folder_button.hide()
        self.start_button.setEnabled(True)
        self.patch_button.setEnabled(True)
        self.controller_button.setEnabled(True)
        self.status_label.setText("Ready to launch")
        return True

    def check_save_directory(self):
        """Check if save directory exists and enable/disable backup button accordingly"""
        if self.save_dir and os.path.exists(self.save_dir):
            self.backup_button.setEnabled(True)
        else:
            self.backup_button.setEnabled(False)
            if not self.save_dir:
                print("Could not determine save directory for current user")

    def check_update_exe(self):
        """Check if update.exe exists and enable/disable update button accordingly"""
        if os.path.exists(self.update_exe_path):
            self.update_button.setEnabled(True)
        else:
            self.update_button.setEnabled(False)
            print(f"Update executable not found at: {self.update_exe_path}")

    def update_game(self):
        """Run the update.exe file"""
        if not os.path.exists(self.update_exe_path):
            QMessageBox.critical(self, "Error", f"Update executable not found!\nExpected location: {self.update_exe_path}")
            return
        
        try:
            self.status_label.setText("Running game update...")
            
            # Run update.exe and capture output
            result = subprocess.run([self.update_exe_path], 
                                 capture_output=True, 
                                 text=True,
                                 check=False)  # Don't raise exception on non-zero exit
            
            if result.returncode == 0 or result.returncode == 1:  # Success or user closed
                # Move regulation.bin after successful update
                if os.path.exists(self.regulation_path):
                    try:
                        destination = os.path.join(self.game_dir, "regulation.bin")
                        shutil.copy2(self.regulation_path, destination)
                        self.status_label.setText("Game update completed and regulation file moved!")
                        QMessageBox.information(self, "Success", "Game update has been completed successfully and regulation file has been moved!")
                    except Exception as e:
                        self.status_label.setText("Game update completed but failed to move regulation file!")
                        QMessageBox.warning(self, "Warning", f"Game update completed but failed to move regulation file: {str(e)}")
                else:
                    self.status_label.setText("Game update completed!")
                    QMessageBox.information(self, "Success", "Game update has been completed successfully!")
            else:
                # Handle specific error codes
                error_message = "Update process failed"
                if result.returncode == 2:
                    error_message = "Update failed: Game is running"
                elif result.returncode == 3:
                    error_message = "Update failed: No update available"
                elif result.returncode == 4:
                    error_message = "Update failed: Permission denied"
                elif result.returncode == 5:
                    error_message = "Update failed: Invalid game directory"
                
                # Add any output from the update process if available
                if result.stdout:
                    error_message += f"\n\nDetails:\n{result.stdout}"
                if result.stderr:
                    error_message += f"\n\nError:\n{result.stderr}"
                
                QMessageBox.warning(self, "Update Failed", error_message)
                self.status_label.setText("Update failed")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run update: {str(e)}")
            self.status_label.setText("Failed to run update")

    def select_game_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Nightreign Game Folder",
            self.game_dir,  # Use current game_dir as starting point
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            # Validate the selected folder
            validated_folder = validate_game_directory(folder)
            if validated_folder:
                self.game_dir = validated_folder
                self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
                self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
                
                # Save the new game directory to config
                self.config['Settings']['game_dir'] = self.game_dir
                save_settings(self.config)
                
                self.check_game_directory()
            else:
                QMessageBox.warning(self, "Invalid Folder", "The selected folder does not appear to be the correct Nightreign game directory or its parent. Please select the folder containing 'nrsc_launcher.exe'.")

    def backup_saves(self):
        """Create a backup of the save files"""
        if not self.save_dir or not os.path.exists(self.save_dir):
            QMessageBox.critical(self, "Error", "Save directory not found!\nExpected location: C:\\Users\\[username]\\AppData\\Roaming\\Nightreign")
            return
        
        # Check if there are any files to backup
        if not os.listdir(self.save_dir):
            QMessageBox.information(self, "Info", "Save directory is empty. Nothing to backup.")
            return
        
        # Generate default backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"Nightreign_Backup_{timestamp}.zip"
        
        # Ask user where to save the backup
        backup_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Backup As",
            default_filename,
            "Zip Files (*.zip);;All Files (*)"
        )
        
        if not backup_path:
            return  # User cancelled
        
        try:
            self.status_label.setText("Creating backup...")
            
            # Create zip file
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through the save directory and add all files
                for root, dirs, files in os.walk(self.save_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Create relative path for zip archive
                        arc_path = os.path.relpath(file_path, self.save_dir)
                        zipf.write(file_path, arc_path)
            
            self.status_label.setText("Backup created successfully!")
            QMessageBox.information(self, "Success", f"Save files backed up successfully to:\n{backup_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create backup: {str(e)}")
            self.status_label.setText("Failed to create backup")

    def update_player_count(self, count):
        try:
            with open(self.settings_path, 'r') as file:
                lines = file.readlines()
            
            for i, line in enumerate(lines):
                if line.strip().startswith('player_count ='):
                    indent = line[:line.find('player_count')]
                    lines[i] = f"{indent}player_count = {count}\n"
                    break
            
            with open(self.settings_path, 'w') as file:
                file.writelines(lines)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update settings: {str(e)}")
            return False

    def patch_game(self):
        if not os.path.exists(self.patch_dir):
            QMessageBox.critical(self, "Error", "Patch files not found! Please make sure the 'online_patch' folder is in the same directory as the launcher.")
            return False
            
        if not os.path.exists(self.game_dir):
            QMessageBox.critical(self, "Error", "Game directory not found!")
            return False
            
        try:
            self.status_label.setText("Patching game files...")
            
            # First check if we have all required files
            required_files = [
                "OnlineFix64.dll",
                "OnlineFix.ini",
                "OnlineFix.url",
                "dlllist.txt",
                "nrsc_launcher.exe",
                "steam_api64.dll",
                "winmm.dll"
            ]
            
            missing_files = []
            for file in required_files:
                if not os.path.exists(os.path.join(self.patch_dir, file)):
                    missing_files.append(file)
            
            if missing_files:
                QMessageBox.critical(self, "Error", 
                    f"Missing required files in online_patch folder:\n{', '.join(missing_files)}\n\n"
                    "This might be caused by your antivirus. Please:\n"
                    "1. Check your antivirus quarantine\n"
                    "2. Add the launcher folder to antivirus exclusions\n"
                    "3. Temporarily disable real-time protection")
                return False
            
            # Check for SeamlessCoop folder
            seamless_dir = os.path.join(self.patch_dir, "SeamlessCoop")
            if not os.path.exists(seamless_dir):
                QMessageBox.critical(self, "Error", 
                    "SeamlessCoop folder not found in online_patch directory!\n\n"
                    "This might be caused by your antivirus. Please:\n"
                    "1. Check your antivirus quarantine\n"
                    "2. Add the launcher folder to antivirus exclusions\n"
                    "3. Temporarily disable real-time protection")
                return False
            
            # Copy all files from online_patch to game directory using safe_file_operation
            success = True
            for item in os.listdir(self.patch_dir):
                source = os.path.join(self.patch_dir, item)
                destination = os.path.join(self.game_dir, item)
                
                if not safe_file_operation(source, destination, 'copy'):
                    success = False
                    QMessageBox.critical(self, "Error", 
                        f"Failed to copy {item} to {destination}.\n\n"
                        "Please ensure:\n"
                        "1. The game is not running\n"
                        "2. Your antivirus is not blocking access\n"
                        "3. You have run the launcher as administrator")
                    break # Stop copying on first failure
            
            if not success:
                self.status_label.setText("Patching failed")
                return False
            
            self.status_label.setText("Game patched successfully!")
            QMessageBox.information(self, "Success", "Game files have been patched successfully!")
            
            # Move regulation.bin after successful patching
            if os.path.exists(self.regulation_path):
                destination = os.path.join(self.game_dir, "regulation.bin")
                if not safe_file_operation(self.regulation_path, destination, 'copy'):
                    QMessageBox.warning(self, "Warning", 
                        f"Game patched successfully but failed to move regulation file to {destination}.\n\n"
                        "This might be caused by your antivirus or permissions. Please:\n"
                        "1. Check your antivirus quarantine\n"
                        "2. Add the game folder to antivirus exclusions\n"
                        "3. Temporarily disable real-time protection")
                    self.status_label.setText("Game patched, but regulation file move failed!")
                    return False # Indicate partial failure
                else:
                    self.status_label.setText("Game patched successfully and regulation file moved!")
            else:
                self.status_label.setText("Game patched successfully, but regulation.bin was not found!")
                QMessageBox.warning(self, "Warning", 
                    "Game patched successfully, but regulation.bin was not found in the launcher directory.\n"
                    "Please run Update Game first.\n\n"
                    "If the file is missing, check your antivirus quarantine.")

            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to patch game: {str(e)}\n\n"
                "This might be caused by your antivirus. Please:\n"
                "1. Check your antivirus quarantine\n"
                "2. Add the launcher and game folders to antivirus exclusions\n"
                "3. Temporarily disable real-time protection")
            self.status_label.setText("Failed to patch game")
            return False

    def fix_controller(self):
        try:
            self.status_label.setText("Applying controller fix...")
            
            # Check if we have write permissions to Steam directories using safe_file_operation
            if not safe_file_operation(None, self.steam_templates_dir, 'write_test'):
                QMessageBox.critical(self, "Error", 
                    "No permission to write to Steam directories.\n\n"
                    "Please run the launcher as administrator and make sure:\n"
                    "1. Steam is not running\n"
                    "2. No other programs are using Steam files\n"
                    "3. Your antivirus is not blocking access")
                self.status_label.setText("Failed to apply controller fix - Permission denied")
                return
            
            # Create Steam directories if they don't exist
            try:
                os.makedirs(self.steam_templates_dir, exist_ok=True)
                os.makedirs(self.steam_config_dir, exist_ok=True)
            except (PermissionError, OSError) as e:
                QMessageBox.critical(self, "Error", 
                    f"Failed to create Steam directories: {str(e)}\n\n"
                    "Please run the launcher as administrator")
                self.status_label.setText("Failed to create Steam directories")
                return
            
            # First, copy all template files to Steam's controller_base/templates directory
            if not os.path.exists(self.templates_dir):
                QMessageBox.critical(self, "Error", 
                    "Templates directory not found in launcher directory.\n"
                    "Please reinstall the launcher.")
                self.status_label.setText("Failed to apply controller fix - Missing templates")
                return
                
            # Copy all files from templates directory to Steam's templates directory
            success = True
            for item in os.listdir(self.templates_dir):
                source = os.path.join(self.templates_dir, item)
                destination = os.path.join(self.steam_templates_dir, item)
                
                if not safe_file_operation(source, destination, 'copy'):
                    success = False
                    QMessageBox.critical(self, "Error", 
                        f"Failed to copy {item} to {destination}.\n\n"
                        "Please ensure:\n"
                        "1. Steam is not running\n"
                        "2. Your antivirus is not blocking access\n"
                        "3. You have run the launcher as administrator")
                    break # Stop copying on first failure
            
            if not success:
                self.status_label.setText("Controller fix failed")
                return
            
            # Then, copy the VDF file to Steam's controller_config directory
            if not os.path.exists(self.vdf_file):
                QMessageBox.critical(self, "Error", 
                    "game_actions_480.vdf not found in launcher directory.\n"
                    "Please reinstall the launcher.")
                self.status_label.setText("Failed to apply controller fix - Missing VDF file")
                return
                
            vdf_destination = os.path.join(self.steam_config_dir, "game_actions_480.vdf")
            if not safe_file_operation(self.vdf_file, vdf_destination, 'copy'):
                QMessageBox.critical(self, "Error", 
                    f"Failed to copy VDF file to {vdf_destination}.\n\n"
                    "Please ensure:\n"
                    "1. Steam is not running\n"
                    "2. Your antivirus is not blocking access\n"
                    "3. You have run the launcher as administrator")
                self.status_label.setText("Controller fix failed - VDF copy failed")
                return
            
            self.status_label.setText("Controller fix applied successfully!")
            QMessageBox.information(self, "Success", 
                "Controller configuration has been updated successfully!\n\n"
                f"Templates copied to: {self.steam_templates_dir}\n"
                f"VDF file copied to: {self.steam_config_dir}\n\n"
                "You can now restart Steam to apply the changes.")
            
        except Exception as e:
            error_msg = str(e)
            if "Permission denied" in error_msg:
                error_msg = "Permission denied. Please run the launcher as administrator."
            elif "not found" in error_msg:
                error_msg = f"Required files not found: {error_msg}"
            
            QMessageBox.critical(self, "Error", 
                f"Failed to apply controller fix: {error_msg}\n\n"
                "Please make sure:\n"
                "1. You're running the launcher as administrator\n"
                "2. Steam is not running\n"
                "3. Steam is installed in the default location\n"
                "4. All required files are present in the launcher directory\n"
                "5. Your antivirus is not blocking access")
            self.status_label.setText("Failed to apply controller fix")

    def set_player_count(self, count):
        for button in self.player_buttons:
            button.setChecked(False)
        
        self.player_buttons[count-1].setChecked(True)
        
        if self.update_player_count(count):
            self.status_label.setText(f"Player count set to {count}")
        else:
            self.status_label.setText("Failed to update player count")

    def get_theme_color(self, color_name):
        """Get the hex color code for a theme color name"""
        color_map = {
            "Teal": "#00b4b4",
            "Purple": "#b400b4",
            "Orange": "#ff8c00",
            "Pink": "#ff69b4",
            "Red": "#ff4444",
            "Green": "#00ff00",
            "Blue": "#4444ff"
        }
        return color_map.get(color_name, "#00b4b4")

    def move_regulation_bin(self):
        """Move regulation.bin to game directory if it hasn't been moved before"""
        if self.config['Settings'].getboolean('regulation_moved'):
            return True
            
        if not os.path.exists(self.regulation_path):
            QMessageBox.warning(self, "Warning", "regulation.bin not found in launcher directory!")
            return False
            
        try:
            destination = os.path.join(self.game_dir, "regulation.bin")
            if not safe_file_operation(self.regulation_path, destination, 'copy'):
                QMessageBox.critical(self, "Error", f"Failed to move regulation.bin to game directory.\n\n"
                                                    "This might be caused by permissions or antivirus. Please ensure:\n"
                                                    "1. The game is not running\n"
                                                    "2. Your antivirus is not blocking access\n"
                                                    "3. You have run the launcher as administrator")
                return False
            
            self.config['Settings']['regulation_moved'] = 'True'
            save_settings(self.config)
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to move regulation.bin: {str(e)}")
            return False

    def start_game(self):
        if not os.path.exists(self.game_path):
            # Try to patch the game first
            if not self.patch_game():
                QMessageBox.critical(self, "Error", "Game executable not found and patching failed!")
                return
            # Check if patching was successful
            if not os.path.exists(self.game_path):
                QMessageBox.critical(self, "Error", "Game executable not found after patching!")
                return

        # Move regulation.bin if it hasn't been moved before
        if not self.move_regulation_bin():
            return

        selected_count = next((i+1 for i, btn in enumerate(self.player_buttons) if btn.isChecked()), 3)
        if not self.update_player_count(selected_count):
            self.status_label.setText("Failed to update player count before launch")
            return

        self.status_label.setText(f"Launching game with {selected_count} player(s)...")
        
        try:
            # First try to run as admin using ShellExecuteW
            result = ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",
                self.game_path,
                None,
                os.path.dirname(self.game_path),
                1
            )
            
            # Check if ShellExecuteW failed
            if result <= 32:  # ShellExecuteW returns values <= 32 on error
                error_codes = {
                    0: "Out of memory",
                    2: "File not found",
                    3: "Path not found",
                    5: "Access denied",
                    8: "Out of memory",
                    26: "Sharing violation",
                    27: "Association incomplete",
                    28: "DDE timeout",
                    29: "DDE fail",
                    30: "DDE busy",
                    31: "No association",
                    32: "DLL not found"
                }
                error_msg = error_codes.get(result, f"Unknown error (code: {result})")
                
                # Try alternative method using subprocess
                try:
                    subprocess.run(
                        [self.game_path],
                        cwd=os.path.dirname(self.game_path),
                        shell=True,
                        check=True
                    )
                except subprocess.CalledProcessError as e:
                    QMessageBox.critical(self, "Error", 
                        f"Failed to launch game with admin privileges.\n\n"
                        f"First attempt error: {error_msg}\n"
                        f"Second attempt error: {str(e)}\n\n"
                        "Please try the following:\n"
                        "1. Right-click the launcher and select 'Run as administrator'\n"
                        "2. Make sure your antivirus is not blocking the game\n"
                        "3. Check if the game folder has proper permissions")
                    self.status_label.setText("Failed to launch game")
                    return
                
            self.status_label.setText("Game launched successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to launch game: {str(e)}\n\n"
                "Please try the following:\n"
                "1. Right-click the launcher and select 'Run as administrator'\n"
                "2. Make sure your antivirus is not blocking the game\n"
                "3. Check if the game folder has proper permissions")
            self.status_label.setText("Failed to launch game")

    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.Accepted:
            # Get the selected folder text from the dialog's label
            selected_folder_text = dialog.folder_label.text()
            # Validate this path before updating game_dir
            validated_folder = validate_game_directory(selected_folder_text)

            if validated_folder:
                # Only update if the validated folder is different from the current game_dir
                if validated_folder != self.game_dir:
                    self.game_dir = validated_folder
                    self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
                    self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
                    
                    # Save the new game directory to config
                    self.config['Settings']['game_dir'] = self.game_dir
                    save_settings(self.config)
                    
                    self.check_game_directory()

                # Get the selected Steam folder
                selected_steam_folder = dialog.steam_folder_label.text()
                if selected_steam_folder != self.steam_dir:
                    self.steam_dir = selected_steam_folder
                    self.steam_templates_dir = get_steam_templates_dir(self.steam_dir)
                    self.steam_config_dir = get_steam_config_dir(self.steam_dir)
                    
                    # Save the new Steam directory to config
                    self.config['Settings']['steam_dir'] = self.steam_dir
                    save_settings(self.config)

                # Get the selected color name from the dialog and update theme
                selected_color_name = dialog.selected_color_name
                if selected_color_name != self.theme_color_name:
                    self.update_theme_color(selected_color_name)
            else:
                 # This case should ideally not happen if validation is done in the dialog,
                 # but as a fallback, if the folder text from the dialog is somehow invalid,
                 # we could show a warning here too.
                 pass # Or add a warning if deemed necessary

    def update_theme_color(self, color_name):
        self.theme_color_name = color_name
        self.theme_color = self.get_theme_color(color_name)
        
        # Save the theme color to config
        self.config['Settings']['theme_color'] = color_name
        save_settings(self.config)

        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: #000000;
            }}
            QWidget {{
                background-color: #000000;
                color: #ffffff;
            }}
            QPushButton {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {self.theme_color};
                border-radius: 5px;
                padding: 8px 15px; /* Adjusted padding */
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.theme_color};
                color: #000000;
            }}
            QPushButton:pressed {{
                background-color: {self.theme_color}cc;
                color: #000000;
            }}
            QPushButton:disabled {{
                background-color: #1a1a1a;
                border: 2px solid #333333;
                color: #666666;
            }}
            QPushButton:checked {{
                background-color: {self.theme_color};
                color: #000000;
            }}
            QSpinBox {{
                background-color: #1a1a1a;
                color: white;
                border: 2px solid {self.theme_color};
                border-radius: 3px;
                padding: 5px;
                margin: 5px;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                width: 0px;
                border: none;
            }}
            QLabel {{
                color: #ffffff;
            }}
            QFrame#statusFrame {{
                background-color: #1a1a1a;
                border: 2px solid {self.theme_color};
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }}
        """)

        # Apply consistent style to all top bar buttons
        top_button_style = f"""
            QPushButton {{
                background-color: #1a1a1a;
                color: {self.theme_color};
                border: 2px solid {self.theme_color};
                border-radius: 5px;
                padding: 5px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.theme_color};
                color: #000000;
            }}
        """
        self.settings_button.setStyleSheet(top_button_style)
        self.discord_button.setStyleSheet(top_button_style)
        self.patch_notes_button.setStyleSheet(top_button_style)
        self.help_button.setStyleSheet(top_button_style)

        self.title_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        """)

        self.subtitle_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 16px;
            margin-bottom: 30px;
        """)

        self.credits_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 14px;
            margin-top: 20px;
        """)

        self.select_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #1a1a1a;
                color: white;
                border: 2px solid #ff4444;
                border-radius: 5px;
                padding: 15px;
                margin: 5px;
            }
            QPushButton:hover {
                background-color: #ff4444;
                color: #000000;
            }
            QPushButton:pressed {
                background-color: #cc3333;
                color: #000000;
            }
        """)
        
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
        """)

    def show_patch_notes(self):
        """Show the patch notes dialog"""
        dialog = PatchNotesDialog(self)
        dialog.exec()

    def show_welcome_dialog(self):
        """Show the welcome dialog on first launch"""
        dialog = WelcomeDialog(self)
        
        # Check if the game directory is valid (contains nrsc_launcher.exe)
        is_valid_game_dir = os.path.exists(os.path.join(self.game_dir, "nrsc_launcher.exe"))
        
        if not is_valid_game_dir:
            dialog.message.setText("""
This launcher will help you manage your Nightreign game installation. Here's what you can do:

• Start the game with admin privileges
• Update to the latest version
• Patch game files if needed
• Apply controller fixes
• Backup your save files
• Customize the launcher's appearance

First, you need to select your Nightreign game folder.
The current path does not contain the game files.

Would you like to select your game folder now?
            """)
            dialog.select_folder_btn.setText("Select Game Folder")
            dialog.skip_btn.setText("Skip for Now")
        else:
            dialog.message.setText("""
This launcher will help you manage your Nightreign game installation. Here's what you can do:

• Start the game with admin privileges
• Update to the latest version
• Patch game files if needed
• Apply controller fixes
• Backup your save files
• Customize the launcher's appearance

Your game folder is already set up correctly!

Important Instructions:
1. Click "Patch Game" to install the necessary game files
2. For updates, make sure to select the main Nightreign folder (C:\\Games\\ELDEN RING NIGHTREIGN) and NOT the Game folder

You can start using the launcher right away!

            """)
            dialog.select_folder_btn.setText("Finish")
            dialog.skip_btn.hide()  # Hide the skip button since we only need Finish
        
        if dialog.exec() == QDialog.Accepted:
            if not is_valid_game_dir:
                # User clicked "Select Game Folder"
                self.select_game_folder()
            # No else needed - Finish button just closes the dialog

    def verify_game_files(self):
        """Check game structure and Steam status"""
        if not os.path.exists(self.game_dir):
            QMessageBox.critical(self, "Error", "Game directory not found!")
            return
        
        issues = []
        fixes = []
        
        # Check required files
        required_files = [
            "amd_ags_x64.dll",
            "bink2w64.dll",
            "data0.bdt",
            "data0.bhd",
            "data1.bdt",
            "data1.bhd",
            "data2.bdt",
            "data2.bhd",
            "data3.bdt",
            "data3.bhd",
            "dlllist.txt",
            "eossdk-win64-shipping.dll",
            "eossdk-win64-shipping.so",
            "nightreign.exe",
            "nrsc_launcher.exe",
            "OnlineFix.ini",
            "OnlineFix.url",
            "OnlineFix64.dll",
            "oo2core_9_win64.dll",
            "regulation.bin",
            "start_protected_game.exe",
            "steam_api64.dll",
            "steam_api64.rne",
            "steam_emu.ini",
            "steam_input_for_ps4_controller.vdf",
            "steam_input_for_ps5_controller.vdf",
            "steam_input_for_steam_controller.vdf",
            "steam_input_for_steam_deck.vdf",
            "steam_input_for_switch_pro_controller.vdf",
            "steam_input_for_xboxone_controller.vdf",
            "steam_input_manifest.vdf",
            "winmm.dll"
        ]
        
        for file in required_files:
            file_path = os.path.join(self.game_dir, file)
            if not os.path.exists(file_path):
                issues.append(f"Missing required file: {file}")
                fixes.append(f"Click 'Patch Game' to install {file}")
        
        # Check SeamlessCoop directory
        seamless_dir = os.path.join(self.game_dir, "SeamlessCoop")
        if not os.path.exists(seamless_dir):
            issues.append("Missing SeamlessCoop directory")
            fixes.append("Click 'Patch Game' to install SeamlessCoop files")
        else:
            # Check required SeamlessCoop files
            seamless_files = [
                "nrsc.dll",
                "nrsc_settings.ini"
            ]
            for file in seamless_files:
                file_path = os.path.join(seamless_dir, file)
                if not os.path.exists(file_path):
                    issues.append(f"Missing SeamlessCoop file: {file}")
                    fixes.append(f"Click 'Patch Game' to install {file}")
        
        # Check if Steam is running
        try:
            import psutil
            steam_running = False
            for proc in psutil.process_iter(['name']):
                if 'steam' in proc.info['name'].lower():
                    steam_running = True
                    break
            
            if not steam_running:
                issues.append("Steam is not running")
                fixes.append("Please start Steam before launching the game")
        except ImportError:
            issues.append("Could not check Steam status (psutil not installed)")
            fixes.append("Install psutil package to enable Steam status checking")
        
        # Show results
        if issues:
            message = "Found the following issues:\n\n"
            for i, (issue, fix) in enumerate(zip(issues, fixes), 1):
                message += f"{i}. {issue}\n   → {fix}\n\n"
            
            QMessageBox.warning(self, "Verification Results", message)
        else:
            QMessageBox.information(self, "Verification Results", 
                "No issues found! Your game installation appears to be correct.")

    def show_help(self):
        """Show the help dialog"""
        dialog = HelpDialog(self)
        dialog.exec()

    def show_mod_menu(self):
        """Show the mod menu dialog"""
        dialog = ModMenuDialog(self)
        dialog.exec()

    def apply_performance_settings(self):
        """Copy the contents of the 'nograssnoshadows' folder into the game directory, replacing existing files."""
        src_dir = os.path.join(os.path.dirname(sys.executable), "nograssnoshadows")
        if not os.path.exists(src_dir):
            src_dir = os.path.join(os.path.dirname(__file__), "nograssnoshadows")
        if not os.path.exists(src_dir):
            raise Exception("'nograssnoshadows' folder not found next to the launcher.")
        dest_dir = self.game_dir
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dest_path = os.path.join(dest_dir, item)
            if not safe_file_operation(src_path, dest_path, 'copy'):
                raise Exception(f"Failed to copy {item} to game folder. Please ensure the game is not running and you have administrator privileges.")

def main():
    app = QApplication(sys.argv)
    window = NightreignLauncher()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()