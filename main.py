import sys
import os
import subprocess
import ctypes
import configparser
import shutil
import webbrowser
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QSpinBox, QLabel, QFrame, QMessageBox,
                             QFileDialog, QHBoxLayout, QDialog, QComboBox,
                             QFormLayout, QColorDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor, QIcon

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(400)
        
        # Create layout
        layout = QFormLayout(self)
        
        # Game folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel(parent.game_dir)
        self.folder_label.setStyleSheet(f"color: {parent.theme_color};")
        folder_button = QPushButton("Change")
        folder_button.clicked.connect(self.select_folder)
        folder_layout.addWidget(self.folder_label)
        folder_layout.addWidget(folder_button)
        
        # Color selection
        color_layout = QHBoxLayout()
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Teal", "Purple", "Orange", "Pink", "Red", "Green", "Blue"])
        # Initialize with parent's current color name
        self.color_combo.setCurrentText(parent.theme_color_name)
        # Store selected color name immediately, but don't apply until accept
        self.selected_color_name = parent.theme_color_name # Initialize selected color
        self.color_combo.currentTextChanged.connect(self.update_selected_color_name)
        color_layout.addWidget(self.color_combo)
        
        # Add to form
        layout.addRow("Game Folder:", folder_layout)
        layout.addRow("Theme Color:", color_layout)
        
        # Apply button
        apply_button = QPushButton("Apply")
        apply_button.clicked.connect(self.accept) # Accept closes with Accepted result
        layout.addRow("", apply_button)
        
        # Style - use current parent theme color
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #000000;
                color: #ffffff;
            }}
            QLabel {{
                color: #ffffff; /* Keep labels white in settings dialog */
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
            self.folder_label.setText(folder)
    
    def update_selected_color_name(self, color_name):
        self.selected_color_name = color_name

class NightreignLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Nightreign Launcher")
        self.setMinimumSize(500, 600)
        
        # Theme color - Store both hex and name
        self.theme_color = "#00b4b4"
        self.theme_color_name = "Teal"
        
        # Game paths
        self.game_dir = r"C:\Games\ELDEN RING NIGHTREIGN\Game"
        self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
        self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
        self.patch_dir = resource_path("online_patch")
        self.templates_dir = resource_path("templates")
        self.steam_templates_dir = r"C:\Program Files (x86)\Steam\controller_base\templates"
        self.steam_config_dir = r"C:\Program Files (x86)\Steam\controller_config"
        self.vdf_file = resource_path("game_actions_480.vdf")
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Create top bar with settings and Discord
        top_bar = QWidget()
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(10, 10, 10, 10)
        
        # Settings button
        self.settings_button = QPushButton("⚙")
        self.settings_button.setFixedSize(35, 35)
        self.settings_button.setFont(QFont("Segoe UI Symbol", 20))
        self.settings_button.clicked.connect(self.show_settings)
        
        # Discord button
        self.discord_button = QPushButton("Join Discord")
        self.discord_button.setFixedSize(120, 35)
        self.discord_button.setFont(QFont("Arial", 11, QFont.Bold))
        self.discord_button.clicked.connect(lambda: webbrowser.open("https://discord.gg/YDtHQNqnqj"))
        
        top_layout.addWidget(self.settings_button)
        top_layout.addWidget(self.discord_button)
        top_layout.addStretch()
        
        # Create title label - store as instance variable for easy access
        self.title_label = QLabel("NIGHTREIGN")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        
        # Create subtitle - store as instance variable for easy access
        self.subtitle_label = QLabel("Game Manager")
        self.subtitle_label.setFont(QFont("Arial", 14))
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(top_bar)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        
        # Create and style the Start Game button
        self.start_button = QPushButton("Start Game")
        self.start_button.setMinimumSize(200, 50)
        self.start_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_button.clicked.connect(self.start_game)
        
        # Create Patch Game button
        self.patch_button = QPushButton("Patch Game")
        self.patch_button.setMinimumSize(200, 50)
        self.patch_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.patch_button.clicked.connect(self.patch_game)
        
        # Create Controller Fix button
        self.controller_button = QPushButton("Controller Fix")
        self.controller_button.setMinimumSize(200, 50)
        self.controller_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.controller_button.clicked.connect(self.fix_controller)
        
        # Create Select Game Folder button (initially hidden)
        self.select_folder_button = QPushButton("Select Nightreign Game Folder")
        self.select_folder_button.setMinimumSize(200, 50)
        self.select_folder_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.select_folder_button.clicked.connect(self.select_game_folder)
        
        # Create player count container
        player_container = QWidget()
        player_layout = QHBoxLayout(player_container)
        player_layout.setSpacing(10)
        
        # Create player count buttons
        self.player_buttons = []
        for count in [1, 2, 3]:
            button = QPushButton(f"{count} Player{'s' if count > 1 else ''}")
            button.setMinimumSize(120, 40)
            button.setFont(QFont("Arial", 11, QFont.Bold))
            button.setCheckable(True)  # Make button checkable
            button.clicked.connect(lambda checked, c=count: self.set_player_count(c))
            self.player_buttons.append(button)
            player_layout.addWidget(button)
        
        # Set default selection (3 players)
        self.player_buttons[2].setChecked(True)
        
        # Create status label with frame
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.StyledPanel)
        status_frame.setObjectName("statusFrame")  # Set object name for styling
        status_layout = QVBoxLayout(status_frame)
        
        self.status_label = QLabel("Ready to launch")
        self.status_label.setAlignment(Qt.AlignCenter)
        status_layout.addWidget(self.status_label)
        
        # Create credits label - store as instance variable for easy access
        self.credits_label = QLabel("by po1sontre")
        self.credits_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addWidget(self.start_button)
        layout.addWidget(self.patch_button)
        layout.addWidget(self.controller_button)
        layout.addWidget(self.select_folder_button)
        layout.addWidget(player_container)
        layout.addStretch()
        layout.addWidget(status_frame)
        layout.addWidget(self.credits_label)
        
        # Apply initial theme
        self.update_theme_color(self.theme_color_name)
        
        # Check if game directory exists and update UI accordingly
        self.check_game_directory()

    def check_game_directory(self):
        if not os.path.exists(self.game_dir):
            self.select_folder_button.show()
            self.start_button.setEnabled(False)
            self.patch_button.setEnabled(False)
            self.controller_button.setEnabled(False)
            self.status_label.setText("Game directory not found. Please select your Nightreign game folder.")
        else:
            self.select_folder_button.hide()
            self.start_button.setEnabled(True)
            self.patch_button.setEnabled(True)
            self.controller_button.setEnabled(True)
            self.status_label.setText("Ready to launch")

    def select_game_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Nightreign Game Folder",
            "C:\\",
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            self.game_dir = folder
            self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
            self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
            self.check_game_directory()

    def update_player_count(self, count):
        try:
            # Read the original file content
            with open(self.settings_path, 'r') as file:
                lines = file.readlines()
            
            # Find and update the player_count line while preserving comments and format
            for i, line in enumerate(lines):
                if line.strip().startswith('player_count ='):
                    # Keep the exact same indentation and format
                    indent = line[:line.find('player_count')]
                    lines[i] = f"{indent}player_count = {count}\n"
                    break
            
            # Write back the modified content
            with open(self.settings_path, 'w') as file:
                file.writelines(lines)
            
            return True
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update settings: {str(e)}")
            return False

    def patch_game(self):
        if not os.path.exists(self.patch_dir):
            QMessageBox.critical(self, "Error", "Patch files not found!")
            return
            
        if not os.path.exists(self.game_dir):
            QMessageBox.critical(self, "Error", "Game directory not found!")
            return
            
        try:
            self.status_label.setText("Patching game files...")
            
            # Copy all files from patch directory to game directory
            for item in os.listdir(self.patch_dir):
                source = os.path.join(self.patch_dir, item)
                destination = os.path.join(self.game_dir, item)
                
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                elif os.path.isdir(source):
                    if os.path.exists(destination):
                        shutil.rmtree(destination)
                    shutil.copytree(source, destination)
            
            self.status_label.setText("Game patched successfully!")
            QMessageBox.information(self, "Success", "Game files have been patched successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to patch game: {str(e)}")
            self.status_label.setText("Failed to patch game")

    def fix_controller(self):
        try:
            self.status_label.setText("Applying controller fix...")
            
            # Create Steam directories if they don't exist
            os.makedirs(self.steam_templates_dir, exist_ok=True)
            os.makedirs(self.steam_config_dir, exist_ok=True)
            
            # Copy template files
            for item in os.listdir(self.templates_dir):
                source = os.path.join(self.templates_dir, item)
                destination = os.path.join(self.steam_templates_dir, item)
                
                if os.path.isfile(source):
                    shutil.copy2(source, destination)
                elif os.path.isdir(source):
                    if os.path.exists(destination):
                        shutil.rmtree(destination)
                    shutil.copytree(source, destination)
            
            # Copy VDF file
            vdf_destination = os.path.join(self.steam_config_dir, "game_actions_480.vdf")
            shutil.copy2(self.vdf_file, vdf_destination)
            
            self.status_label.setText("Controller fix applied successfully!")
            QMessageBox.information(self, "Success", "Controller configuration has been updated successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply controller fix: {str(e)}")
            self.status_label.setText("Failed to apply controller fix")

    def set_player_count(self, count):
        # Uncheck all buttons
        for button in self.player_buttons:
            button.setChecked(False)
        
        # Check the clicked button
        self.player_buttons[count-1].setChecked(True)
        
        # Update the INI file
        if self.update_player_count(count):
            self.status_label.setText(f"Player count set to {count}")
        else:
            self.status_label.setText("Failed to update player count")

    def start_game(self):
        if not os.path.exists(self.game_path):
            QMessageBox.critical(self, "Error", "Game executable not found at the specified path!")
            return

        # Get the selected player count from the checked button
        selected_count = next((i+1 for i, btn in enumerate(self.player_buttons) if btn.isChecked()), 3)
        # Add this line to update the INI file before starting
        if not self.update_player_count(selected_count):
            # If updating fails, show a message and stop the launch process
            self.status_label.setText("Failed to update player count before launch")
            return # Stop execution if INI update fails

        self.status_label.setText(f"Launching game with {selected_count} player(s)...")
        
        try:
            # Use ShellExecute to run as admin
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",  # This requests admin privileges
                self.game_path,
                None,  # No arguments needed
                os.path.dirname(self.game_path),  # Working directory
                1  # SW_SHOWNORMAL
            )
            self.status_label.setText("Game launched successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to launch game: {str(e)}")
            self.status_label.setText("Failed to launch game")

    def show_settings(self):
        dialog = SettingsDialog(self)
        # Check if dialog was accepted (Apply button pressed)
        if dialog.exec() == QDialog.Accepted:
            # Update game directory if changed
            new_game_dir = dialog.folder_label.text()
            if new_game_dir != self.game_dir:
                self.game_dir = new_game_dir
                self.game_path = os.path.join(self.game_dir, "nrsc_launcher.exe")
                self.settings_path = os.path.join(self.game_dir, "SeamlessCoop", "nrsc_settings.ini")
                self.check_game_directory()
            
            # Get the selected color name from the dialog and update theme
            selected_color_name = dialog.selected_color_name
            if selected_color_name != self.theme_color_name:
                self.update_theme_color(selected_color_name)
    
    def update_theme_color(self, color_name):
        color_map = {
            "Teal": "#00b4b4",
            "Purple": "#b400b4",
            "Orange": "#ff8c00",
            "Pink": "#ff69b4",
            "Red": "#ff4444",
            "Green": "#00ff00",
            "Blue": "#4444ff"
        }
        
        # Store the color name and hex value
        self.theme_color_name = color_name
        self.theme_color = color_map.get(color_name, "#00b4b4")  # Default to Teal if name not found

        # Apply general stylesheet changes using the new color
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
                padding: 15px;
                margin: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.theme_color};
                color: #000000;
            }}
            QPushButton:pressed {{
                background-color: {self.theme_color}cc; /* Slightly darker shade */
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

        # Update specific widget styles that need the theme color
        # Settings gear button
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme_color};
                border: none;
                padding: 0px;
                margin: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #ffffff;
            }}
        """)

        # Discord button
        self.discord_button.setStyleSheet(f"""
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
        """)

        # Title label
        self.title_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        """)

        # Subtitle label
        self.subtitle_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 16px;
            margin-bottom: 30px;
        """)

        # Credits label
        self.credits_label.setStyleSheet(f"""
            color: {self.theme_color};
            font-size: 14px;
            margin-top: 20px;
        """)

        # Select folder button (keep red for error state)
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
        
        # Status label should remain white
        self.status_label.setStyleSheet("""
            color: #ffffff;
            font-size: 12px;
        """)

def main():
    app = QApplication(sys.argv)
    window = NightreignLauncher()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()