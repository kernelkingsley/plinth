"""Puts the pill in the taskbar slot and lifts it when the bar comes back."""

import time
import tkinter as tk
from ctypes import cast, POINTER

from plinth.shell import Shell
from plinth.ui import Metrics, Pill, Slot
from plinth.win32 import (
    ABE_BOTTOM,
    ABE_LEFT,
    ABE_RIGHT,
    ABE_TOP,
    KBDLLHOOKSTRUCT,
    LowLevelProc,
    VK_CONTROL,
    VK_ESCAPE,
    VK_Q,
    VK_SHIFT,
    WM_KEYDOWN,
    call_next_hook,
    class_name,
    create_mutex,
    cursor_pos,
    enable_dpi_awareness,
    find_taskbar,
    foreground_window,
    install_keyboard_hook,
    key_down,
    message_box,
    raise_hwnd,
    remove_keyboard_hook,
    root_window,
    widget_hwnd,
    window_text,
    window_under_cursor,
)


class Island:
    def __init__(self, root, shell):
        self.root = root
        self.shell = shell
        self._on_hide = None
        self.pill = Pill(root, self.toggle_expanded, self._request_hide)
        self.left = Slot(root, self.reveal)
        self.right = Slot(root, self.reveal)
        self.shield = Slot(root, self.reveal)
        self.revealed = False
        self.alive = False
        self.animating = False
        self.from_top = 0
        self.to_top = 0
        self.from_height = 0
        self.to_height = 0
        self.shown_top = 0
        self.shown_height = 0
        self.pill_left = 0
        self.pill_width = 400
        self.compact_height = 36
        self.expanded_height = 160
        self.gap = 8
        self.scale = 1.0
        self.anim_start = 0.0
        self.revealed_at = 0.0
        self.away_since = None
        self.awake = False
        self._keeper = None
        self._watch = None

    def start(self):
        self.scale = max(1.0, self.shell.dpi / 96.0)
        self.gap = max(8, int(round(8 * self.scale)))
        self.compact_height = max(36, int(round(44 * self.scale)))
        if self.shell.edge in (ABE_BOTTOM, ABE_TOP):
            margin = max(2, int(round(2 * self.scale)))
            fit = self.shell.thickness - margin * 2
            if 28 <= fit < self.compact_height:
                self.compact_height = fit

        self.pill_width = max(240, int(round(400 * self.scale)))
        if self.shell.edge in (ABE_LEFT, ABE_RIGHT):
            span = self.shell.taskbar.height
        else:
            span = self.shell.taskbar.width
        max_width = max(220, span - max(80, int(round(48 * self.scale))))
        if self.pill_width > max_width:
            self.pill_width = max_width

        self.pill.scale = self.scale
        self.pill.compact_height = self.compact_height
        self.expanded_height = Metrics(self.pill_width, self.compact_height, self.scale).expanded_height
        self.shown_height = self.compact_height
        self.shown_top = self.anchor_top(self.shown_height)
        self.alive = True
        self.awake = True
        self.pill.deiconify()
        for slot in (self.left, self.right, self.shield):
            slot.deiconify()
        self.layout_slots()
        self.place_pill(self.shown_top, self.shown_height)
        self.pill.redraw()
        self._keeper = self.root.after(180, self._keep)
        self.shell.log(
            "shown pill at %s,%s %sx%s" % (self.pill_left, self.shown_top, self.pill_width, self.shown_height)
        )

    def _request_hide(self):
        if self._on_hide is not None:
            self._on_hide()

    def hide_to_tray(self):
        if not self.awake:
            return
        self.awake = False
        self.revealed = False
        self.animating = False
        self.away_since = None
        self.pill.expanded = False
        self._cancel(self._keeper)
        self._cancel(self._watch)
        self._keeper = None
        self._watch = None
        self.pill.withdraw()
        for slot in (self.left, self.right, self.shield):
            slot.withdraw()
        self.shell.show_taskbar()
        self.shell.log("hidden to tray")

    def show_from_tray(self):
        if self.awake:
            return
        if not find_taskbar():
            self.shell.log("show skipped, taskbar missing")
            return
        self.shell.capture()
        self.shell.save_recovery()
        self.shell.apply_demo()
        self.pill.expanded = False
        self.pill.subtitle = "Click either side"
        self.pill.help = (
            "Ctrl+Shift+Q hides Plinth. It stays in the tray.\n"
            "Right-click that icon and choose Quit to close it."
        )
        self.revealed = False
        self.start()
        self.shell.log("shown from tray")

    def toggle_expanded(self):
        self.pill.expanded = not self.pill.expanded
        height = self.expanded_height if self.pill.expanded else self.compact_height
        self.animate(self.anchor_top(height), height)

    def reveal(self):
        if not self.alive or self.revealed:
            return
        self.revealed = True
        self.revealed_at = time.monotonic()
        self.away_since = None
        self._cancel(self._keeper)
        self._keeper = None
        for slot in (self.left, self.right, self.shield):
            slot.reset_visual()
            slot.withdraw()
        self.shell.show_taskbar()
        self.pill.subtitle = "Taskbar is open"
        self.pill.help = "The taskbar has the slot back.\nMove the pointer away, or press Escape."
        self.animate(self.anchor_top(self.shown_height), self.shown_height)
        self._watch = self.root.after(80, self._watch_pointer)
        self.shell.log("revealed")

    def dismiss(self):
        if not self.alive or not self.revealed:
            return
        self.revealed = False
        self.away_since = None
        self._cancel(self._watch)
        self._watch = None
        self.shell.park_taskbar()
        self.pill.subtitle = "Click either side"
        self.pill.help = (
            "Ctrl+Shift+Q hides Plinth. It stays in the tray.\n"
            "Right-click that icon and choose Quit to close it."
        )
        for slot in (self.left, self.right, self.shield):
            slot.deiconify()
        self.layout_slots()
        self.animate(self.anchor_top(self.shown_height), self.shown_height)
        self._keeper = self.root.after(180, self._keep)
        self.shell.log("dismissed")

    def animate(self, top, height):
        self.from_top = self.shown_top
        self.from_height = self.shown_height
        self.to_top = top
        self.to_height = height
        self.anim_start = time.monotonic()
        self.animating = True
        self.root.after(15, self._step)

    def anchor_top(self, height):
        bar = self.shell.taskbar
        if self.revealed:
            if self.shell.edge == ABE_TOP:
                return bar.bottom + self.gap
            return bar.top - self.gap - height
        compact_bottom = bar.top + (self.shell.thickness + self.compact_height) // 2
        return compact_bottom - height

    def layout_slots(self):
        bar = self.shell.taskbar
        pill_x = bar.left + max(0, (bar.width - self.pill_width) // 2)
        self.pill_left = pill_x
        self.left.place_at(bar.left, bar.top, max(1, pill_x - bar.left + 2), bar.height)
        self.shield.place_at(pill_x, bar.top, self.pill_width, bar.height)
        right_x = pill_x + self.pill_width - 2
        self.right.place_at(right_x, bar.top, max(1, bar.right - right_x), bar.height)
        raise_hwnd(widget_hwnd(self.pill))

    def place_pill(self, top, height):
        self.shown_top = int(top)
        self.shown_height = int(height)
        self.pill.place_at(self.pill_left, self.shown_top, self.pill_width, self.shown_height)
        self.pill.redraw()
        raise_hwnd(widget_hwnd(self.pill))

    def _step(self):
        if not self.awake or not self.animating:
            return
        t = (time.monotonic() - self.anim_start) / 0.220
        done = t >= 1
        if done:
            t = 1
        else:
            t = 1 - (1 - t) ** 3
        top = self.from_top + round((self.to_top - self.from_top) * t)
        height = self.from_height + round((self.to_height - self.from_height) * t)
        self.place_pill(top, height)
        if done:
            self.animating = False
            self.place_pill(self.to_top, self.to_height)
            if not self.revealed:
                self.layout_slots()
        else:
            self.root.after(15, self._step)

    def _keep(self):
        if not self.alive or not self.awake or self.revealed or self.animating:
            return
        self.shell.ensure_parked()
        raise_hwnd(widget_hwnd(self.pill))
        self._keeper = self.root.after(180, self._keep)

    def _watch_pointer(self):
        if not self.awake or not self.revealed or not self.alive:
            return
        if (time.monotonic() - self.revealed_at) < 0.35:
            self._watch = self.root.after(80, self._watch_pointer)
            return
        if self._pointer_is_holding():
            self.away_since = None
        elif self.away_since is None:
            self.away_since = time.monotonic()
        elif (time.monotonic() - self.away_since) >= 0.45:
            self.dismiss()
            return
        self._watch = self.root.after(80, self._watch_pointer)

    def _pointer_is_holding(self):
        pos = cursor_pos()
        if pos is None:
            return False
        x, y = pos
        if self.shell.taskbar.contains(x, y):
            return True
        if self.pill_left <= x < self.pill_left + self.pill_width and self.shown_top <= y < self.shown_top + self.shown_height:
            return True
        return flyout_open()

    def _cancel(self, token):
        if token is not None:
            try:
                self.root.after_cancel(token)
            except tk.TclError:
                pass


def flyout_open():
    return _is_flyout(window_under_cursor()) or _is_flyout(foreground_window())


def _is_flyout(hwnd):
    hwnd = root_window(hwnd)
    if not hwnd:
        return False
    name = class_name(hwnd)
    if name in ("Shell_TrayWnd", "Shell_SecondaryTrayWnd", "NotifyIconOverflowWindow"):
        return True
    if name in ("XamlExplorerHostIslandWindow", "TopLevelWindowForOverflowXamlIsland"):
        return True
    if name == "Windows.UI.Core.CoreWindow":
        title = window_text(hwnd)
        if title in ("", "Start", "Search", "Quick settings"):
            return True
    return False


def main():
    enable_dpi_awareness()
    _mutex, already = create_mutex("Local\\Plinth.Demo")
    if already:
        message_box("Plinth is already running.\nPress Ctrl+Shift+Q, or right-click its tray icon.")
        return

    shell = Shell()
    try:
        from plinth.startup import install_startup

        shell.log("startup %s" % install_startup())
    except OSError as exc:
        shell.log("startup failed %s" % exc)

    if not _wait_for_taskbar():
        shell.log("taskbar missing")
        message_box("Plinth can't find the taskbar yet.")
        return

    root = tk.Tk()
    root.withdraw()
    root.title("Plinth")
    state = {"hook": None, "pending": None}
    tray = None
    callback = None

    def on_key(code, wparam, lparam):
        # The hook runs inside the key message. Touching Tk here can kill the process
        # before the taskbar is restored, so this only stores the key.
        if code >= 0 and wparam == WM_KEYDOWN and island is not None:
            info = cast(lparam, POINTER(KBDLLHOOKSTRUCT)).contents
            vk = info.vkCode
            if vk == VK_Q and key_down(VK_CONTROL) and key_down(VK_SHIFT):
                state["pending"] = "toggle"
                return 1
            if vk == VK_ESCAPE and island.awake and island.revealed and not flyout_open():
                state["pending"] = "dismiss"
                return 1
        return call_next_hook(state["hook"], code, wparam, lparam)

    def hide():
        if island.awake:
            island.hide_to_tray()
            if tray is not None:
                tray.notify_hidden()

    def toggle():
        if island.awake:
            hide()
        else:
            island.show_from_tray()

    def poll():
        action = state["pending"]
        state["pending"] = None
        if action is None and tray is not None:
            action = tray.pop()
        if action == "toggle":
            toggle()
        elif action == "dismiss":
            island.dismiss()
        elif action == "exit":
            root.quit()
            return
        root.after(40, poll)

    island = None
    try:
        if shell.has_recovery():
            shell.recover_from_crash()
        shell.capture()
        shell.save_recovery()
        root.update()
        island = Island(root, shell)
        island._on_hide = hide
        from plinth.tray import Tray

        tray = Tray(state, lambda: island.awake)
        shell.log("tray icon %s hwnd=%s error=%s" % (tray.added, tray.hwnd or 0, state.get("tray_error", 0)))
        shell.apply_demo()
        island.start()
        callback = LowLevelProc(on_key)
        state["hook"] = install_keyboard_hook(callback)
        shell.log("keyboard hook %s" % (state["hook"] or 0))
        root.after(40, poll)
        root.mainloop()
    except Exception as exc:
        shell.log("fatal %s" % exc)
        message_box(str(exc))
    finally:
        remove_keyboard_hook(state["hook"])
        if tray is not None:
            tray.remove()
        shell.restore()
        try:
            root.destroy()
        except tk.TclError:
            pass


def _wait_for_taskbar():
    for _ in range(40):
        if find_taskbar():
            return True
        time.sleep(0.25)
    return False
