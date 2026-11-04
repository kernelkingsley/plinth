"""Start Plinth when Windows signs in."""

import os
import sys
import winreg

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def install_startup():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pythonw = sys.executable
    if pythonw.lower().endswith("python.exe"):
        candidate = pythonw[:-4] + "w.exe"
        if os.path.exists(candidate):
            pythonw = candidate

    folder = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Plinth")
    os.makedirs(folder, exist_ok=True)
    launcher = os.path.join(folder, "start-plinth.vbs")
    script = "\r\n".join(
        [
            'Set shell = CreateObject("Wscript.Shell")',
            'shell.CurrentDirectory = "%s"' % root,
            'shell.Run """%s"" -m plinth", 0, False' % pythonw,
            "",
        ]
    )
    with open(launcher, "w", encoding="utf-8") as handle:
        handle.write(script)

    command = 'wscript.exe //B //Nologo "%s"' % launcher
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
    except FileNotFoundError:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY)
    with key:
        winreg.SetValueEx(key, "Plinth", 0, winreg.REG_SZ, command)
    return command
