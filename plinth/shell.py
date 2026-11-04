"""Hide the real taskbar and put it back when Plinth exits."""

import os
from datetime import datetime

from plinth.win32 import (
    ABE_BOTTOM,
    ABE_LEFT,
    ABE_RIGHT,
    ABE_TOP,
    ABS_ALWAYSONTOP,
    ABS_AUTOHIDE,
    Box,
    dpi_for,
    find_taskbar,
    get_taskbar_pos,
    get_taskbar_state,
    get_work_area,
    hide_taskbar_pixels,
    monitor_info,
    move_window,
    set_taskbar_state,
    set_work_area,
    show_taskbar_pixels,
    taskbar_is_clipped,
)


class Shell:
    def __init__(self):
        folder = os.path.join(os.environ.get("LOCALAPPDATA", "."), "Plinth")
        os.makedirs(folder, exist_ok=True)
        self.recovery_path = os.path.join(folder, "restore.txt")
        self.log_path = os.path.join(folder, "demo.log")
        try:
            open(self.log_path, "w").close()
        except OSError:
            pass

        self.original_auto_hide = False
        self.original_always_on_top = False
        self.original_work = Box()
        self.taskbar = Box()
        self.monitor = Box()
        self.edge = ABE_BOTTOM
        self.thickness = 40
        self.primary = True
        self.dpi = 96
        self.applied = False

    def log(self, message):
        try:
            stamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            with open(self.log_path, "a", encoding="utf-8") as handle:
                handle.write("%s %s\n" % (stamp, message))
        except OSError:
            pass

    def has_recovery(self):
        return os.path.exists(self.recovery_path)

    def recover_from_crash(self):
        self.log("recovery file found, restoring previous shell state")
        if not self._load_recovery():
            self.log("recovery file unreadable, forcing taskbar visible")
            self.original_auto_hide = False
            self.original_always_on_top = True
        self.applied = True
        self.restore()

    def capture(self):
        state = get_taskbar_state()
        self.original_auto_hide = bool(state & ABS_AUTOHIDE)
        self.original_always_on_top = bool(state & ABS_ALWAYSONTOP)

        pos_result, edge, rect, appbar_bytes = get_taskbar_pos()
        self.taskbar = rect
        self.edge = edge

        tray = find_taskbar()
        self.dpi = dpi_for(tray) if tray else 96
        self._fix_tiny_rect()

        monitor, primary = monitor_info(tray)
        if monitor is None:
            self.monitor = self.taskbar.copy()
            self.primary = True
        else:
            self.monitor = monitor
            self.primary = primary

        self.original_work = get_work_area()
        if self.edge in (ABE_LEFT, ABE_RIGHT):
            self.thickness = self.taskbar.width
        else:
            self.thickness = self.taskbar.height

        self.log(
            "capture state=%s autoHide=%s topMost=%s posResult=%s edge=%s taskbar=%s monitor=%s primary=%s work=%s dpi=%s appbarBytes=%s"
            % (
                state,
                self.original_auto_hide,
                self.original_always_on_top,
                pos_result,
                self.edge,
                self.taskbar,
                self.monitor,
                self.primary,
                self.original_work,
                self.dpi,
                appbar_bytes,
            )
        )

    def save_recovery(self):
        lines = [
            "autoHide=%s" % ("1" if self.original_auto_hide else "0"),
            "alwaysOnTop=%s" % ("1" if self.original_always_on_top else "0"),
            "left=%d" % self.original_work.left,
            "top=%d" % self.original_work.top,
            "right=%d" % self.original_work.right,
            "bottom=%d" % self.original_work.bottom,
            "barLeft=%d" % self.taskbar.left,
            "barTop=%d" % self.taskbar.top,
            "barRight=%d" % self.taskbar.right,
            "barBottom=%d" % self.taskbar.bottom,
        ]
        with open(self.recovery_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
        self.log("saved recovery")

    def apply_demo(self):
        self.park_taskbar()
        self.applied = True
        self.log("demo shell applied, taskbar parked off-screen")

    def park_taskbar(self):
        hide_taskbar_pixels(find_taskbar())

    def show_taskbar(self):
        tray = find_taskbar()
        show_taskbar_pixels(tray)
        if self.taskbar.width > 1:
            move_window(tray, self.taskbar, True)

    def ensure_parked(self):
        tray = find_taskbar()
        if taskbar_is_clipped(tray):
            return
        self.log("taskbar region reset, hiding again")
        self.park_taskbar()

    def restore(self):
        if not self.applied and not os.path.exists(self.recovery_path):
            return
        try:
            self.show_taskbar()
            flags, result = set_taskbar_state(self.original_auto_hide, self.original_always_on_top)
            ok = set_work_area(self.original_work)
            self.log(
                "restored autoHide=%s work=%s bar=%s flags=%s result=%s ok=%s"
                % (self.original_auto_hide, self.original_work, self.taskbar, flags, result, ok)
            )
        except OSError as exc:
            self.log("restore failed %s" % exc)
        self.applied = False
        try:
            if os.path.exists(self.recovery_path):
                os.remove(self.recovery_path)
        except OSError:
            pass

    def _fix_tiny_rect(self):
        width = self.taskbar.width
        height = self.taskbar.height
        guess = int(round(48.0 * self.dpi / 96.0))
        if guess < 40:
            guess = 48
        if self.edge == ABE_BOTTOM or (width > height * 3 and height < 24):
            if height < 24:
                self.edge = ABE_BOTTOM
                self.taskbar.top = self.taskbar.bottom - guess
                self.log("taskbar rect was collapsed, using height %s" % guess)
        elif self.edge == ABE_TOP and height < 24:
            self.taskbar.bottom = self.taskbar.top + guess
        elif self.edge == ABE_LEFT and width < 24:
            self.taskbar.right = self.taskbar.left + guess
        elif self.edge == ABE_RIGHT and width < 24:
            self.taskbar.left = self.taskbar.right - guess

    def _load_recovery(self):
        try:
            work = Box()
            saw_work = False
            with open(self.recovery_path, "r", encoding="utf-8") as handle:
                lines = handle.readlines()
            for line in lines:
                if "=" not in line:
                    continue
                key, value = line.strip().split("=", 1)
                if key == "autoHide":
                    self.original_auto_hide = value == "1"
                elif key == "alwaysOnTop":
                    self.original_always_on_top = value == "1"
                elif key == "left":
                    work.left = int(value)
                    saw_work = True
                elif key == "top":
                    work.top = int(value)
                elif key == "right":
                    work.right = int(value)
                elif key == "bottom":
                    work.bottom = int(value)
                elif key == "barLeft":
                    self.taskbar.left = int(value)
                elif key == "barTop":
                    self.taskbar.top = int(value)
                elif key == "barRight":
                    self.taskbar.right = int(value)
                elif key == "barBottom":
                    self.taskbar.bottom = int(value)
            if saw_work:
                self.original_work = work
            return saw_work
        except (OSError, ValueError) as exc:
            self.log("load recovery failed %s" % exc)
            return False
