# AION 2 Optimizer

A conservative Windows 10/11 desktop utility for preparing a PC for AION 2. It provides a reversible Windows power-plan switch, a temporary game-process priority option, basic hardware detection, and NVIDIA Control Panel guidance.

> This is an independent community utility. It is not affiliated with or endorsed by NCSOFT. It does not modify AION 2 game files, bypass anti-cheat, overclock hardware, or promise a particular FPS increase.

## Features

- Detects Windows version, CPU name, installed RAM, and NVIDIA GPU name (when `nvidia-smi` is available; otherwise uses Windows video-controller information).
- Saves the currently active Windows power plan, then switches to Windows **High performance**.
- Restores the previously saved power plan.
- Sets a detected AION process to **High** priority while it is running. The priority returns to normal after the game exits.
- Opens NVIDIA Control Panel and displays conservative per-game tuning suggestions.
- Dark desktop interface; no account, telemetry, or network connection required.

## Requirements

- Windows 10 or Windows 11.
- Python 3.10+ to run from source.
- NVIDIA driver / NVIDIA Control Panel for NVIDIA-specific configuration.
- `psutil` dependency (installed from `requirements.txt`).

## Run from source

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
py app.py
```

## Build the EXE

Double-click `build.bat`, or run:

```powershell
py -m pip install -r requirements-dev.txt
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AION2Optimizer app.py
```

The executable will be created at `dist/AION2Optimizer.exe`.

## GitHub Actions build

Push this repository to GitHub. The workflow at `.github/workflows/build-windows.yml` builds the Windows executable and attaches it to the workflow run as an artifact.

## Usage

1. Run `AION2Optimizer.exe`.
2. Review the detected system information.
3. Click **Apply gaming power plan**. The previous plan is backed up under `%APPDATA%\AION2Optimizer\backup.json`.
4. Start AION 2, then optionally click **Set AION process priority to High**.
5. Use **Open NVIDIA Control Panel** and add the actual game executable under **Manage 3D settings → Program Settings**. Suggested settings are shown in the app.
6. Use **Restore saved power plan** to return to the plan that was active before optimization.

## Safety notes

- High Performance can increase power consumption, heat, fan noise, and laptop battery drain.
- High process priority is temporary. Do not use Realtime priority; it can make Windows unresponsive.
- NVIDIA settings are recommendations only. Driver options and game behavior vary; benchmark changes individually.
- The game executable name can change between versions. If the process is not detected, verify its name in Task Manager and update `PROCESS_CANDIDATES` in `app.py`.
- The app does not disable Windows Defender, firewall, updates, or anti-cheat services, and does not apply undocumented network/registry tweaks.
- Restore the saved plan before uninstalling if you want to revert the power-plan change.

## Project structure

```text
AION-2-Optimizer/
├── .github/
│   └── workflows/
│       └── build-windows.yml
├── app.py
├── build.bat
├── requirements.txt
├── requirements-dev.txt
├── .gitignore
├── LICENSE
└── README.md
```

## Disclaimer

Use at your own risk. Test performance changes on your own hardware. No FPS, latency, or compatibility result is guaranteed.
