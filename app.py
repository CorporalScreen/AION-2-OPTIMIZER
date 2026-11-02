from __future__ import annotations

import ctypes
import json
import os
import platform
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
from pathlib import Path

APP_NAME = "AION 2 OPTIMIZER"
PROCESS_CANDIDATES = ("aion2.exe", "aion.exe", "aionclient.exe")
APP_DIR = Path(os.getenv("APPDATA", str(Path.home()))) / "AION2Optimizer"
BACKUP_FILE = APP_DIR / "backup.json"


def run_command(args: list[str], timeout: int = 12) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                          creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def is_windows() -> bool:
    return sys.platform == "win32"


def get_power_plan() -> str | None:
    if not is_windows():
        return None
    try:
        result = run_command(["powercfg", "/getactivescheme"])
        import re
        match = re.search(r"([0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12})", result.stdout)
        return match.group(1) if result.returncode == 0 and match else None
    except Exception:
        return None


def get_system_info() -> dict:
    info = {
        "OS": platform.platform(),
        "CPU": platform.processor() or "Not reported",
        "RAM": "Not detected",
        "GPU": "Not detected",
    }
    try:
        import psutil
        info["RAM"] = f"{psutil.virtual_memory().total / (1024 ** 3):.1f} GB"
    except Exception:
        pass
    if is_windows():
        try:
            r = run_command(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"], timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                info["GPU"] = r.stdout.strip().splitlines()[0]
        except Exception:
            pass
        if info["GPU"] == "Not detected":
            try:
                ps = ("Get-CimInstance Win32_VideoController | "
                      "Select-Object -ExpandProperty Name")
                r = run_command(["powershell", "-NoProfile", "-Command", ps], timeout=8)
                if r.stdout.strip():
                    info["GPU"] = r.stdout.strip().splitlines()[0]
            except Exception:
                pass
    return info


class OptimizerApp:
    BG = "#10141c"
    PANEL = "#191f2b"
    PANEL2 = "#202838"
    FG = "#edf2fa"
    MUTED = "#9aa8bc"
    ACCENT = "#69a7ff"
    GREEN = "#64d6a0"
    RED = "#ff7d86"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("900x650")
        self.root.minsize(780, 580)
        self.root.configure(bg=self.BG)
        self.root.option_add("*Font", ("Segoe UI", 10))
        self.status = tk.StringVar(value="Ready. No system changes have been made.")
        self.info_labels: dict[str, tk.Label] = {}
        self._build()
        self.refresh_info()

    def _button(self, parent, text, command, primary=False):
        return tk.Button(
            parent, text=text, command=command, cursor="hand2",
            bg=self.ACCENT if primary else self.PANEL2,
            fg="#07111f" if primary else self.FG,
            activebackground="#8bbaff" if primary else "#2a3548",
            activeforeground="#07111f" if primary else self.FG,
            relief="flat", bd=0, padx=14, pady=10,
            font=("Segoe UI Semibold", 10)
        )

    def _build(self):
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=26, pady=(22, 14))
        tk.Label(header, text="AION 2", bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 25, "bold")).pack(anchor="w")
        tk.Label(header, text="OPTIMIZER  •  NVIDIA EDITION",
                 bg=self.BG, fg=self.ACCENT, font=("Segoe UI Semibold", 9)).pack(anchor="w")
        tk.Label(header, text="Windows performance toolkit with reversible changes",
                 bg=self.BG, fg=self.MUTED).pack(anchor="w", pady=(5, 0))

        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True, padx=26, pady=8)
        left = tk.Frame(body, bg=self.PANEL, padx=18, pady=16)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = tk.Frame(body, bg=self.PANEL, padx=18, pady=16, width=280)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        tk.Label(left, text="PERFORMANCE TOOLS", bg=self.PANEL, fg=self.FG,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(0, 12))
        self._button(left, "Apply gaming power plan", self.apply_power_plan, True).pack(fill="x", pady=5)
        self._button(left, "Set AION process priority to High", self.set_game_priority).pack(fill="x", pady=5)
        self._button(left, "Open NVIDIA Control Panel", self.open_nvidia).pack(fill="x", pady=5)
        self._button(left, "Show recommended NVIDIA settings", self.show_nvidia_tips).pack(fill="x", pady=5)
        self._button(left, "Restore saved power plan", self.restore_power_plan).pack(fill="x", pady=5)
        self._button(left, "Refresh PC information", self.refresh_info).pack(fill="x", pady=5)

        note = ("Changes are intentionally conservative. This app does not overclock, "
                "disable security services, edit game files, or apply undocumented registry tweaks.")
        tk.Label(left, text=note, bg=self.PANEL, fg=self.MUTED,
                 wraplength=500, justify="left").pack(anchor="w", pady=(18, 0))

        tk.Label(right, text="YOUR SYSTEM", bg=self.PANEL, fg=self.FG,
                 font=("Segoe UI Semibold", 12)).pack(anchor="w", pady=(0, 12))
        for key in ("OS", "CPU", "RAM", "GPU"):
            tk.Label(right, text=key, bg=self.PANEL, fg=self.MUTED,
                     font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(8, 1))
            label = tk.Label(right, text="Detecting…", bg=self.PANEL, fg=self.FG,
                             wraplength=235, justify="left", anchor="w")
            label.pack(fill="x", anchor="w")
            self.info_labels[key] = label

        footer = tk.Frame(self.root, bg=self.PANEL2, padx=18, pady=11)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, textvariable=self.status, bg=self.PANEL2, fg=self.GREEN,
                 anchor="w").pack(fill="x")

    def set_status(self, message: str, error=False):
        self.status.set(message)
        # Keep the status readable; errors use a red accent.
        for child in self.root.winfo_children():
            if isinstance(child, tk.Frame) and child.winfo_children():
                pass

    def refresh_info(self):
        def worker():
            info = get_system_info()
            self.root.after(0, lambda: [self.info_labels[k].config(text=v) for k, v in info.items()])
            self.root.after(0, lambda: self.set_status("System information updated."))
        threading.Thread(target=worker, daemon=True).start()

    def apply_power_plan(self):
        if not is_windows():
            messagebox.showerror("Windows only", "Power plan controls are available on Windows.")
            return
        current = get_power_plan()
        if not current:
            messagebox.showerror("Power plan", "Could not read the current power plan.")
            return
        APP_DIR.mkdir(parents=True, exist_ok=True)
        backup = {"power_plan_guid": current, "saved_at": datetime.now().isoformat(timespec="seconds")}
        BACKUP_FILE.write_text(json.dumps(backup, indent=2), encoding="utf-8")
        # Windows built-in High performance scheme.
        result = run_command(["powercfg", "/setactive", "SCHEME_MIN"])
        if result.returncode == 0:
            self.set_status("High performance plan enabled. Previous plan saved for restore.")
            messagebox.showinfo("Applied", "Windows High performance power plan is active.\nYour previous plan was saved.")
        else:
            messagebox.showerror("Power plan", result.stderr.strip() or "Windows could not change the power plan.")

    def restore_power_plan(self):
        if not BACKUP_FILE.exists():
            messagebox.showinfo("Restore", "No saved power plan was found.")
            return
        try:
            backup = json.loads(BACKUP_FILE.read_text(encoding="utf-8"))
            guid = backup["power_plan_guid"]
            result = run_command(["powercfg", "/setactive", guid])
            if result.returncode == 0:
                self.set_status("Previous power plan restored.")
                messagebox.showinfo("Restored", "Your saved power plan is active again.")
            else:
                messagebox.showerror("Restore failed", result.stderr.strip() or "Could not restore power plan.")
        except Exception as exc:
            messagebox.showerror("Restore failed", str(exc))

    def set_game_priority(self):
        if not is_windows():
            messagebox.showerror("Windows only", "Process priority is available on Windows.")
            return
        try:
            import psutil
        except ImportError:
            messagebox.showerror("Missing dependency", "Install dependencies with: pip install -r requirements.txt")
            return
        matches = []
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if (proc.info["name"] or "").lower() in PROCESS_CANDIDATES:
                    matches.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        if not matches:
            messagebox.showinfo("AION 2 not found", "Start the game, then try again. The process name may differ by game version.")
            return
        changed, failed = 0, 0
        for proc in matches:
            try:
                proc.nice(psutil.HIGH_PRIORITY_CLASS)
                changed += 1
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.Error):
                failed += 1
        self.set_status(f"Priority updated for {changed} process(es); {failed} could not be changed.")
        messagebox.showinfo("Process priority", f"Updated: {changed}\nNot changed: {failed}\n\nPriority resets when the game closes.")

    def open_nvidia(self):
        if not is_windows():
            messagebox.showerror("Windows only", "This shortcut is available on Windows.")
            return
        candidates = [
            Path(os.getenv("ProgramFiles", r"C:\Program Files")) / "NVIDIA Corporation/Control Panel Client/nvcplui.exe",
            Path(os.getenv("WINDIR", r"C:\Windows")) / "System32/nvcplui.exe",
        ]
        for path in candidates:
            if path.exists():
                os.startfile(str(path))
                self.set_status("Opened NVIDIA Control Panel.")
                return
        try:
            os.startfile("ms-settings:display-advanced")
            self.set_status("Opened Windows display settings; NVIDIA Control Panel was not found.")
        except Exception:
            messagebox.showinfo("NVIDIA", "NVIDIA Control Panel was not found. Install/update it through the Microsoft Store or NVIDIA app.")

    def show_nvidia_tips(self):
        tips = (
            "Suggested per-game NVIDIA settings (starting point):\n\n"
            "• Power management mode: Prefer maximum performance\n"
            "• Low Latency Mode: On (test Ultra only if it behaves well)\n"
            "• Preferred refresh rate: Highest available\n"
            "• Vertical sync: Use the game's setting / test off for latency\n"
            "• Texture filtering – Quality: Quality or Performance\n\n"
            "Add the actual AION 2 executable under NVIDIA Control Panel → Manage 3D settings → Program Settings.\n"
            "Names and available options vary by driver. Change one setting at a time and benchmark."
        )
        messagebox.showinfo("NVIDIA recommendations", tips)

    def run(self):
        if not is_windows():
            self.set_status("Warning: this build targets Windows 10/11.")
        self.root.mainloop()


if __name__ == "__main__":
    root = tk.Tk()
    app = OptimizerApp(root)
    app.run()
