# Nightreign Launcher

## Note: This launcher is intended for use with the cr@ck#d version of the game.

This is a simple launcher and game manager for the Nightreign mod, built with Python and PySide6.

## Features:

- Launch the game
- Patch game files
- apply the update
- Apply controller fixes (Steam configurations)
- Select player count
- Customizable theme color
- Configurable game directory

## How to Use:

- To use the Nightreign Launcher, you need to build the executable from the source code.
- Please follow the instructions in the "Building from Source" section below to create the executable.

## Building from Source:

1. Clone this repository.
2. Create a virtual environment (`python -m venv venv`).
3. Activate the virtual environment (`.\venv\Scripts\activate` on Windows).
4. Install dependencies (`pip install -r requirements.txt`).
5. Run the application (`python main.py`).
6. To build the executable, run the PyInstaller command (ensure you have converted `icon.jpg` to `icon.ico` and placed it in the project root):
   ```bash
   pyinstaller --noconfirm --onefile --windowed --icon=icon.ico main.py
   ```

## Contributing:

Feel free to open issues or submit pull requests.

## Credits:

Built by po1sontre 