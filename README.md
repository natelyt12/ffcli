# FFCLI - FFmpeg CLI Manager

An interactive command-line interface designed to streamline media processing workflows using FFmpeg.

## Features

- **Interactive Navigation**: Use arrow keys to navigate menus and select files or commands, eliminating the need for manual path or command typing.
- **Automatic Media Discovery**: Automatically scans the current working directory for supported video, audio, and image formats.
- **Command Presets**: Store and execute frequently used FFmpeg configurations for common tasks such as compression, format conversion, or volume adjustment.
- **Preset Management**: Create, edit, and delete command presets directly within the interface.
- **Manual Command Input**: Flexibility to enter custom FFmpeg options for specific processing requirements.
- **Integrated Utilities**: Access detailed file metadata via `ffprobe`, preview media files using default system players, and manage source files.
- **Color-Coded UI**: Uses a clean, color-coded terminal interface for improved readability and user experience.

## Prerequisites

1. **Python 3.x**: Must be installed and available in the system environment.
2. **FFmpeg**: Both `ffmpeg` and `ffprobe` must be installed and accessible via the system PATH.

## Installation

1. Clone or download the repository to your local machine:
   ```bash
   git clone https://github.com/natelyt12/ffcli.git
   cd ffcli
   ```
2. (Optional) To use the tool from any directory on Windows, add the path to the `ffcli` folder to your system's Environment Variables (PATH).

## Usage

1. Open your terminal in the directory containing the media files you intend to process.
2. Launch the application:
   ```bash
   ffcli
   ```
3. Navigation controls:
   - **Arrow Keys**: Move selection up or down.
   - **Enter**: Confirm the current selection.
   - **Esc**: Return to the previous menu or exit the application.

## Project Structure

- `ffmgr.py`: The primary Python script containing the application logic.
- `ffcli.bat`: A batch wrapper for execution on Windows systems.
- `ffmpeg_commands.json`: A JSON configuration file used to store saved command presets.

---
Developed by [natelyt12](https://github.com/natelyt12)
