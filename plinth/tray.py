"""The icon that stays in the taskbar tray after Plinth hides."""

import ctypes
import queue
import threading
from ctypes import (
    WINFUNCTYPE,
    Structure,
    byref,
    c_int,
    c_size_t,
    c_ssize_t,
    c_ubyte,
    c_uint,
    c_ushort,
    c_void_p,
    c_wchar,
    c_wchar_p,
    sizeof,
)

from plinth.win32 import (
    GWL_WNDPROC,
    HWND,
    BOOL,
    DWORD,
    LPARAM,
    LRESULT,
    WPARAM,
    POINT,
    WndProc,
    _alive,
    cursor_pos,
    gdi32,
    kernel32,
    user32,
)

TRAY_MESSAGE = 0x8001
NIM_ADD = 0
NIM_MODIFY = 1
NIM_DELETE = 2
NIF_MESSAGE = 0x01
NIF_ICON = 0x02
NIF_TIP = 0x04
NIF_INFO = 0x10
WM_LBUTTONDBLCLK = 0x0203
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
MF_SEPARATOR = 0x800
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY = 0x0080

shell32 = ctypes.windll.shell32


class GUID(Structure):
    _fields_ = [
        ("Data1", c_uint),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_ubyte * 8),
    ]


class NOTIFYICONDATAW(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("hWnd", HWND),
        ("uID", c_uint),
        ("uFlags", c_uint),
        ("uCallbackMessage", c_uint),
        ("hIcon", c_void_p),
        ("szTip", c_wchar * 128),
        ("dwState", DWORD),
        ("dwStateMask", DWORD),
        ("szInfo", c_wchar * 256),
        ("uTimeout", c_uint),
        ("szInfoTitle", c_wchar * 64),
        ("dwInfoFlags", DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", c_void_p),
    ]


class ICONINFO(Structure):
    _fields_ = [
        ("fIcon", c_int),
        ("xHotspot", DWORD),
        ("yHotspot", DWORD),
        ("hbmMask", HWND),
        ("hbmColor", HWND),
    ]


user32.CallWindowProcW.argtypes = [c_ssize_t, HWND, c_uint, WPARAM, LPARAM]
gdi32.CreateCompatibleDC.argtypes = [HWND]
gdi32.CreateCompatibleDC.restype = HWND
gdi32.CreateCompatibleBitmap.argtypes = [HWND, c_int, c_int]
gdi32.CreateCompatibleBitmap.restype = HWND
gdi32.CreateBitmap.argtypes = [c_int, c_int, c_uint, c_uint, c_void_p]
gdi32.CreateBitmap.restype = HWND
gdi32.SelectObject.argtypes = [HWND, HWND]
gdi32.SelectObject.restype = HWND
gdi32.GetStockObject.argtypes = [c_int]
gdi32.GetStockObject.restype = HWND
gdi32.CreateSolidBrush.argtypes = [DWORD]
gdi32.CreateSolidBrush.restype = HWND
gdi32.Ellipse.argtypes = [HWND, c_int, c_int, c_int, c_int]
gdi32.Ellipse.restype = BOOL
gdi32.PatBlt.argtypes = [HWND, c_int, c_int, c_int, c_int, DWORD]
gdi32.PatBlt.restype = BOOL
gdi32.DeleteDC.argtypes = [HWND]
gdi32.DeleteDC.restype = BOOL
user32.GetDC.argtypes = [HWND]
user32.GetDC.restype = HWND
user32.ReleaseDC.argtypes = [HWND, HWND]
user32.ReleaseDC.restype = c_int
user32.CreateIconIndirect.argtypes = [ctypes.POINTER(ICONINFO)]
user32.CreateIconIndirect.restype = HWND
user32.DestroyIcon.argtypes = [HWND]
user32.DestroyIcon.restype = BOOL
user32.LoadIconW.argtypes = [HWND, c_void_p]
user32.LoadIconW.restype = HWND
user32.CreatePopupMenu.restype = HWND
user32.AppendMenuW.argtypes = [HWND, c_uint, c_size_t, c_wchar_p]
user32.AppendMenuW.restype = BOOL
user32.TrackPopupMenu.argtypes = [HWND, c_uint, c_int, c_int, c_int, HWND, c_void_p]
user32.TrackPopupMenu.restype = c_uint
user32.DestroyMenu.argtypes = [HWND]
user32.DestroyMenu.restype = BOOL
user32.SetForegroundWindow.argtypes = [HWND]
user32.SetForegroundWindow.restype = BOOL
user32.PostMessageW.argtypes = [HWND, c_uint, WPARAM, LPARAM]
user32.PostMessageW.restype = BOOL
shell32.Shell_NotifyIconW.argtypes = [DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
shell32.Shell_NotifyIconW.restype = BOOL

WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
BALLOON_MESSAGE = 0x8002
HWND_MESSAGE = c_void_p(-3)


class WNDCLASSW(Structure):
    _fields_ = [
        ("style", c_uint),
        ("lpfnWndProc", WndProc),
        ("cbClsExtra", c_int),
        ("cbWndExtra", c_int),
        ("hInstance", HWND),
        ("hIcon", HWND),
        ("hCursor", HWND),
        ("hbrBackground", HWND),
        ("lpszMenuName", c_wchar_p),
        ("lpszClassName", c_wchar_p),
    ]


class MSG(Structure):
    _fields_ = [
        ("hwnd", HWND),
        ("message", c_uint),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", DWORD),
        ("pt", POINT),
    ]


user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
user32.RegisterClassW.restype = c_ushort
user32.CreateWindowExW.argtypes = [DWORD, c_wchar_p, c_wchar_p, DWORD, c_int, c_int, c_int, c_int, HWND, HWND, HWND, c_void_p]
user32.CreateWindowExW.restype = HWND
user32.DefWindowProcW.argtypes = [HWND, c_uint, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), HWND, c_uint, c_uint]
user32.GetMessageW.restype = c_int
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.TranslateMessage.restype = BOOL
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.restype = LRESULT
user32.PostQuitMessage.argtypes = [c_int]


def make_icon():
    """A green circle, or the plain Windows icon if drawing fails."""
    try:
        screen = user32.GetDC(None)
        color_dc = gdi32.CreateCompatibleDC(screen)
        mask_dc = gdi32.CreateCompatibleDC(screen)
        color = gdi32.CreateCompatibleBitmap(screen, 16, 16)
        mask = gdi32.CreateBitmap(16, 16, 1, 1, None)
        gdi32.SelectObject(color_dc, color)
        gdi32.SelectObject(mask_dc, mask)
        gdi32.SelectObject(mask_dc, gdi32.GetStockObject(0))
        gdi32.PatBlt(mask_dc, 0, 0, 16, 16, 0x00F00021)
        gdi32.SelectObject(mask_dc, gdi32.GetStockObject(4))
        gdi32.SelectObject(mask_dc, gdi32.GetStockObject(8))
        gdi32.Ellipse(mask_dc, 1, 1, 15, 15)
        brush = gdi32.CreateSolidBrush(0x0058D130)
        gdi32.SelectObject(color_dc, brush)
        gdi32.SelectObject(color_dc, gdi32.GetStockObject(8))
        gdi32.Ellipse(color_dc, 1, 1, 15, 15)
        info = ICONINFO()
        info.fIcon = True
        info.hbmMask = mask
        info.hbmColor = color
        icon = user32.CreateIconIndirect(byref(info))
        gdi32.DeleteObject(brush)
        gdi32.DeleteObject(color)
        gdi32.DeleteObject(mask)
        gdi32.DeleteDC(color_dc)
        gdi32.DeleteDC(mask_dc)
        user32.ReleaseDC(None, screen)
        if icon:
            return icon
    except (OSError, AttributeError):
        pass
    return user32.LoadIconW(None, c_void_p(32512))


class Tray:
    def __init__(self, signals, is_awake):
        self.signals = signals
        self.is_awake = is_awake
        self.hwnd = None
        self.icon = make_icon()
        self.added = False
        self.events = queue.Queue()
        self._ready = threading.Event()
        self._callback = WndProc(self._proc)
        _alive.append(self._callback)
        self._thread = threading.Thread(target=self._run, name="PlinthTray", daemon=True)
        self._thread.start()
        self._ready.wait(3)

    def pop(self):
        try:
            return self.events.get_nowait()
        except queue.Empty:
            return None

    def notify_hidden(self):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, BALLOON_MESSAGE, 0, 0)

    def choose(self, awake):
        menu = user32.CreatePopupMenu()
        label = "Hide Plinth" if awake else "Show Plinth"
        user32.AppendMenuW(menu, 0, 1, label)
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, 0, 2, "Quit")
        user32.SetForegroundWindow(self.hwnd)
        pos = cursor_pos() or (0, 0)
        command = user32.TrackPopupMenu(
            menu,
            TPM_RETURNCMD | TPM_NONOTIFY,
            int(pos[0]),
            int(pos[1]),
            0,
            self.hwnd,
            None,
        )
        user32.PostMessageW(self.hwnd, 0, 0, 0)
        user32.DestroyMenu(menu)
        if command == 1:
            return "toggle"
        if command == 2:
            return "exit"
        return None

    def remove(self):
        if self.hwnd:
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            self._thread.join(2)
            self.hwnd = None
        if self.icon:
            user32.DestroyIcon(self.icon)
            self.icon = None

    def _run(self):
        try:
            self._create_window()
            if self.hwnd:
                self.added = self._notify(NIM_ADD, tip="Plinth")
        finally:
            self._ready.set()
        if not self.hwnd:
            return
        message = MSG()
        while user32.GetMessageW(byref(message), None, 0, 0) > 0:
            user32.TranslateMessage(byref(message))
            user32.DispatchMessageW(byref(message))

    def _create_window(self):
        instance = kernel32.GetModuleHandleW(None)
        klass = WNDCLASSW()
        klass.lpfnWndProc = self._callback
        klass.hInstance = instance
        klass.lpszClassName = "PlinthTray"
        atom = user32.RegisterClassW(byref(klass))
        if not atom and kernel32.GetLastError() not in (0, 1410):
            self.signals["tray_error"] = kernel32.GetLastError()
            return
        self.hwnd = user32.CreateWindowExW(
            0, "PlinthTray", "PlinthTray", 0, 0, 0, 0, 0, HWND_MESSAGE, None, instance, None
        )
        if not self.hwnd:
            self.signals["tray_error"] = kernel32.GetLastError()

    def _proc(self, window, msg, wparam, lparam):
        if msg == TRAY_MESSAGE:
            mouse = int(lparam) & 0xFFFF
            if mouse in (WM_RBUTTONUP, WM_CONTEXTMENU):
                try:
                    awake = bool(self.is_awake())
                except Exception:
                    awake = False
                choice = self.choose(awake)
                if choice:
                    self.events.put(choice)
            elif mouse == WM_LBUTTONDBLCLK:
                self.events.put("toggle")
            return 0
        if msg == BALLOON_MESSAGE:
            self._notify(
                NIM_MODIFY,
                tip="Plinth",
                title="Plinth",
                info="Still running. Ctrl+Shift+Q brings it back. Right-click this icon and choose Quit to close it.",
            )
            return 0
        if msg == WM_CLOSE:
            if self.added:
                data = self._data(NIM_DELETE)
                shell32.Shell_NotifyIconW(NIM_DELETE, byref(data))
                self.added = False
            user32.DestroyWindow(window)
            return 0
        if msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(window, msg, wparam, lparam)

    def _notify(self, action, tip="", title="", info=""):
        data = self._data(action, tip, title, info)
        ok = bool(shell32.Shell_NotifyIconW(action, byref(data)))
        if not ok:
            self.signals["tray_error"] = kernel32.GetLastError()
        return ok

    def _data(self, action, tip="", title="", info=""):
        data = NOTIFYICONDATAW()
        data.cbSize = sizeof(NOTIFYICONDATAW)
        data.hWnd = self.hwnd
        data.uID = 1
        data.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        data.uCallbackMessage = TRAY_MESSAGE
        data.hIcon = self.icon
        data.szTip = tip
        if info:
            data.uFlags |= NIF_INFO
            data.szInfo = info
            data.szInfoTitle = title
            data.dwInfoFlags = 1
            data.uTimeout = 8000
        return data
