# Nightreign Launcher

This is a simple launcher and game manager for the Nightreign mod, built with Python and PySide6.

## Features:

- Launch the game
- Patch game files
- Apply controller fixes (Steam configurations)
- Select player count
- Customizable theme color
- Configurable game directory

## How to Use:

1. Run the `Nightreign Launcher.exe` from the `dist` folder.
2. If the game directory is not found, use the "Select Nightreign Game Folder" button to point to your Nightreign game installation.
3. Choose your desired player count.
4. Optionally, use the settings icon (⚙) to change the theme color or game folder.
5. Click "Start Game" to launch Nightreign.

## Building from Source:

1. Clone this repository.
2. Create a virtual environment (`python -m venv venv`).
3. Activate the virtual environment (`.\venv\Scripts\activate` on Windows).
4. Install dependencies (`pip install -r requirements.txt`).
5. Run the application (`python main.py`).
6. To build the executable, run the PyInstaller command (ensure you have converted `icon.jpg` to `icon.ico` and placed it in the project root):
   ```bash
   pyinstaller --onefile --windowed --icon=icon.ico --add-data "online_patch;online_patch" --add-data "templates;templates" --add-data "game_actions_480.vdf;." --hidden-import PySide6.QtWidgets --hidden-import PySide6.QtCore --hidden-import PySide6.QtGui --name="Nightreign Launcher" main.py
   ```

## Contributing:

Feel free to open issues or submit pull requests.

## Credits:

Built by po1sontre 