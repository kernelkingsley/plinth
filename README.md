# Plinth

Plinth is a small pill that sits in the taskbar slot on Windows. The real taskbar stays out of the way until you ask for it. Click the empty space on either side of the pill and the bar slides back into that slot, lifting the pill above it. Move the pointer off both of them, or press Escape, and the bar goes away again.

The pill you see is a stand-in player, so there is always something on screen while the rest of the app is still a demo. Night Drive is not a real track.

## Install

People get Plinth from the website. The download is an installer, `Plinth-Setup.exe`. They run that, and the setup screens are where they choose what to allow:

- a desktop shortcut
- start Plinth when Windows signs in
- the pill taking the taskbar's place, which the setup page explains before it finishes

Setup then puts `Plinth.exe` on the machine. It opens from the Start menu, the desktop shortcut, or the sign-in entry if they asked for that. A normal install stays in their user folder and does not ask for an administrator password.

The tray icon, the Ctrl+Shift+Q shortcut, and hiding the taskbar work for the signed-in user, so setup does not show a separate permission for each of them. Anything that needs a Windows privacy prompt, such as the microphone, is asked the first time Plinth actually uses it.

The installer is not in this repository yet. This folder is the source.

## Hide it, and actually quit

Ctrl+Shift+Q does not close Plinth. It hides the pill and puts the taskbar back, and the app keeps running.

A green icon stays in the tray, the row of small icons at the end of the taskbar. Press Ctrl+Shift+Q again and the pill comes back. You can also double-click that icon, or right-click it and choose Show Plinth or Hide Plinth.

Quit is the menu item that really exits. Right-click the tray icon and choose Quit. Plinth removes the tray icon, puts the taskbar back the way it found it, and the shortcut stops working because the process is gone.

If a second copy is started while one is already running, it tells you to use the shortcut or the tray icon instead of opening another pill.

## What you can click

- Either side of the pill brings the taskbar back.
- The pill itself opens a short card. Pause and Hide are on that card. Hide does the same thing as Ctrl+Shift+Q.
- Escape puts the taskbar away again while it is open. It leaves the pill where it is.
- The taskbar stays up while the pointer is on it, and while Start, search, or a tray menu is open.

## If the taskbar disappears

Plinth remembers the taskbar state before it changes anything, in `%LOCALAPPDATA%\Plinth\restore.txt`. If the process is killed, start Plinth once more. It puts the bar back before it hides it again. A normal Quit does that restore on the way out.

A short log of what it did is in `%LOCALAPPDATA%\Plinth\demo.log`.

## Working on the source

From this folder, while the installer is still being built:

```powershell
.\run.ps1
```

That uses the Python 3.12 install from uv when it is there, and `python` otherwise. You can also start it yourself:

```powershell
python -m plinth
```

Python needs tkinter, which ships with the standard Windows install. A launch from this folder still adds Plinth to the current user's sign-in items, through a small launcher under `%LOCALAPPDATA%\Plinth`. The installed app will follow the choices made in setup instead.
