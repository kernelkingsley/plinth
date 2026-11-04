"""Small wrappers around the Windows calls Plinth needs."""

import ctypes
from ctypes import (
    WINFUNCTYPE,
    Structure,
    byref,
    c_bool,
    c_int,
    c_short,
    c_size_t,
    c_ssize_t,
    c_uint,
    c_void_p,
    c_wchar_p,
    sizeof,
)

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32
gdi32 = ctypes.windll.gdi32

HWND = c_void_p
LRESULT = c_ssize_t
WPARAM = c_size_t
LPARAM = c_ssize_t
DWORD = c_uint
BOOL = c_bool

HWND_TOPMOST = c_void_p(-1)
HWND_BOTTOM = c_void_p(1)

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040

WM_KEYDOWN = 0x0100
WM_MOUSEACTIVATE = 0x0021
MA_NOACTIVATE = 3
WH_KEYBOARD_LL = 13
GWL_EXSTYLE = -20
GWL_WNDPROC = -4

WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

ABM_GETSTATE = 4
ABM_GETTASKBARPOS = 5
ABM_SETSTATE = 10
ABS_AUTOHIDE = 0x1
ABS_ALWAYSONTOP = 0x2
ABE_LEFT = 0
ABE_TOP = 1
ABE_RIGHT = 2
ABE_BOTTOM = 3

SPI_SETWORKAREA = 0x002F
SPI_GETWORKAREA = 0x0030
SPIF_SENDCHANGE = 0x0002
MONITOR_DEFAULTTONEAREST = 2
GA_ROOT = 2
NULLREGION = 1
ERROR_ALREADY_EXISTS = 183

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_ESCAPE = 0x1B
VK_Q = 0x51


class RECT(Structure):
    _fields_ = [
        ("left", c_int),
        ("top", c_int),
        ("right", c_int),
        ("bottom", c_int),
    ]


class APPBARDATA(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("hWnd", HWND),
        ("uCallbackMessage", c_uint),
        ("uEdge", c_uint),
        ("rc", RECT),
        ("lParam", LPARAM),
    ]


class MONITORINFO(Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
    ]


class KBDLLHOOKSTRUCT(Structure):
    _fields_ = [
        ("vkCode", DWORD),
        ("scanCode", DWORD),
        ("flags", DWORD),
        ("time", DWORD),
        ("dwExtraInfo", c_size_t),
    ]


LowLevelProc = WINFUNCTYPE(LRESULT, c_int, WPARAM, LPARAM)
WndProc = WINFUNCTYPE(LRESULT, HWND, c_uint, WPARAM, LPARAM)

user32.FindWindowW.argtypes = [c_wchar_p, c_wchar_p]
user32.FindWindowW.restype = HWND
user32.GetWindowRect.argtypes = [HWND, ctypes.POINTER(RECT)]
user32.GetWindowRect.restype = BOOL
user32.SetWindowPos.argtypes = [HWND, HWND, c_int, c_int, c_int, c_int, c_uint]
user32.SetWindowPos.restype = BOOL
user32.SetWindowRgn.argtypes = [HWND, HWND, BOOL]
user32.SetWindowRgn.restype = c_int
user32.GetWindowRgn.argtypes = [HWND, HWND]
user32.GetWindowRgn.restype = c_int
user32.GetCursorPos.argtypes = [ctypes.POINTER(RECT)]
user32.SystemParametersInfoW.argtypes = [c_uint, c_uint, ctypes.POINTER(RECT), c_uint]
user32.SystemParametersInfoW.restype = BOOL
user32.MonitorFromWindow.argtypes = [HWND, DWORD]
user32.MonitorFromWindow.restype = HWND
user32.GetMonitorInfoW.argtypes = [HWND, ctypes.POINTER(MONITORINFO)]
user32.GetMonitorInfoW.restype = BOOL
user32.GetDpiForWindow.argtypes = [HWND]
user32.GetDpiForWindow.restype = c_uint
user32.GetWindowLongPtrW.argtypes = [HWND, c_int]
user32.GetWindowLongPtrW.restype = c_ssize_t
user32.SetWindowLongPtrW.argtypes = [HWND, c_int, c_ssize_t]
user32.SetWindowLongPtrW.restype = c_ssize_t
user32.CallWindowProcW.argtypes = [c_ssize_t, HWND, c_uint, WPARAM, LPARAM]
user32.CallWindowProcW.restype = LRESULT
user32.GetParent.argtypes = [HWND]
user32.GetParent.restype = HWND
user32.WindowFromPoint.argtypes = [c_int, c_int]
user32.WindowFromPoint.restype = HWND
user32.GetAncestor.argtypes = [HWND, c_uint]
user32.GetAncestor.restype = HWND
user32.GetForegroundWindow.restype = HWND
user32.GetClassNameW.argtypes = [HWND, c_wchar_p, c_int]
user32.GetClassNameW.restype = c_int
user32.GetWindowTextW.argtypes = [HWND, c_wchar_p, c_int]
user32.GetWindowTextW.restype = c_int
user32.SetWindowsHookExW.argtypes = [c_int, LowLevelProc, HWND, DWORD]
user32.SetWindowsHookExW.restype = HWND
user32.CallNextHookEx.argtypes = [HWND, c_int, WPARAM, LPARAM]
user32.CallNextHookEx.restype = LRESULT
user32.UnhookWindowsHookEx.argtypes = [HWND]
user32.UnhookWindowsHookEx.restype = BOOL
user32.GetAsyncKeyState.argtypes = [c_int]
user32.GetAsyncKeyState.restype = c_short
user32.MessageBoxW.argtypes = [HWND, c_wchar_p, c_wchar_p, c_uint]
user32.MessageBoxW.restype = c_int
user32.SetProcessDpiAwarenessContext.argtypes = [c_void_p]
user32.SetProcessDpiAwarenessContext.restype = BOOL

shell32.SHAppBarMessage.argtypes = [c_uint, ctypes.POINTER(APPBARDATA)]
shell32.SHAppBarMessage.restype = c_size_t

gdi32.CreateRectRgn.argtypes = [c_int, c_int, c_int, c_int]
gdi32.CreateRectRgn.restype = HWND
gdi32.DeleteObject.argtypes = [HWND]
gdi32.DeleteObject.restype = BOOL

kernel32.CreateMutexW.argtypes = [c_void_p, BOOL, c_wchar_p]
kernel32.CreateMutexW.restype = HWND
kernel32.GetLastError.restype = DWORD
kernel32.GetModuleHandleW.argtypes = [c_wchar_p]
kernel32.GetModuleHandleW.restype = HWND

# Keep window-procedure callbacks alive. Windows calls them later.
_alive = []


class Box:
    """A screen rectangle in pixels."""

    def __init__(self, left=0, top=0, right=0, bottom=0):
        self.left = int(left)
        self.top = int(top)
        self.right = int(right)
        self.bottom = int(bottom)

    @property
    def width(self):
        return self.right - self.left

    @property
    def height(self):
        return self.bottom - self.top

    def contains(self, x, y):
        return self.left <= x < self.right and self.top <= y < self.bottom

    def same_as(self, other):
        return (
            self.left == other.left
            and self.top == other.top
            and self.right == other.right
            and self.bottom == other.bottom
        )

    def copy(self):
        return Box(self.left, self.top, self.right, self.bottom)

    def to_rect(self):
        return RECT(self.left, self.top, self.right, self.bottom)

    @classmethod
    def from_rect(cls, rect):
        return cls(rect.left, rect.top, rect.right, rect.bottom)

    def __str__(self):
        return "%d,%d %dx%d" % (self.left, self.top, self.width, self.height)


def enable_dpi_awareness():
    try:
        user32.SetProcessDpiAwarenessContext(c_void_p(-4))
    except (OSError, AttributeError):
        pass


def message_box(text):
    user32.MessageBoxW(None, text, "Plinth", 0x40)


def find_taskbar():
    return user32.FindWindowW("Shell_TrayWnd", None)


def new_appbar():
    data = APPBARDATA()
    data.cbSize = sizeof(APPBARDATA)
    data.hWnd = find_taskbar()
    return data


def get_taskbar_state():
    data = new_appbar()
    return shell32.SHAppBarMessage(ABM_GETSTATE, byref(data))


def get_taskbar_pos():
    data = new_appbar()
    result = shell32.SHAppBarMessage(ABM_GETTASKBARPOS, byref(data))
    return result, int(data.uEdge), Box.from_rect(data.rc), data.cbSize


def set_taskbar_state(auto_hide, always_on_top):
    flags = 0
    if auto_hide:
        flags |= ABS_AUTOHIDE
    if always_on_top:
        flags |= ABS_ALWAYSONTOP
    data = new_appbar()
    data.lParam = flags
    result = shell32.SHAppBarMessage(ABM_SETSTATE, byref(data))
    return flags, result


def get_work_area():
    rect = RECT()
    user32.SystemParametersInfoW(SPI_GETWORKAREA, 0, byref(rect), 0)
    return Box.from_rect(rect)


def set_work_area(box):
    rect = box.to_rect()
    return bool(user32.SystemParametersInfoW(SPI_SETWORKAREA, 0, byref(rect), SPIF_SENDCHANGE))


def monitor_info(hwnd):
    monitor = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    info = MONITORINFO()
    info.cbSize = sizeof(MONITORINFO)
    if user32.GetMonitorInfoW(monitor, byref(info)):
        return Box.from_rect(info.rcMonitor), bool(info.dwFlags & 1)
    return None, False


def dpi_for(hwnd):
    try:
        dpi = user32.GetDpiForWindow(hwnd)
    except (OSError, AttributeError):
        return 96
    return dpi if dpi >= 96 else 96


def window_rect(hwnd):
    rect = RECT()
    if hwnd and user32.GetWindowRect(hwnd, byref(rect)):
        return Box.from_rect(rect)
    return None


def move_window(hwnd, box, on_top):
    if not hwnd or box.width < 1 or box.height < 1:
        return
    insert = HWND_TOPMOST if on_top else HWND_BOTTOM
    flags = SWP_NOACTIVATE
    if on_top:
        flags |= SWP_SHOWWINDOW
    user32.SetWindowPos(hwnd, insert, box.left, box.top, box.width, box.height, flags)


def hide_taskbar_pixels(hwnd):
    if not hwnd:
        return
    region = gdi32.CreateRectRgn(0, 0, 0, 0)
    user32.SetWindowRgn(hwnd, region, True)


def show_taskbar_pixels(hwnd):
    if not hwnd:
        return
    user32.SetWindowRgn(hwnd, None, True)


def taskbar_is_clipped(hwnd):
    if not hwnd:
        return False
    probe = gdi32.CreateRectRgn(0, 0, 0, 0)
    kind = user32.GetWindowRgn(hwnd, probe)
    gdi32.DeleteObject(probe)
    return kind == NULLREGION


class POINT(Structure):
    _fields_ = [("x", c_int), ("y", c_int)]


user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = BOOL
user32.WindowFromPoint.argtypes = [POINT]
user32.WindowFromPoint.restype = HWND


def cursor_pos():
    pt = POINT()
    if not user32.GetCursorPos(byref(pt)):
        return None
    return pt.x, pt.y


def window_under_cursor():
    pos = cursor_pos()
    if pos is None:
        return None
    return user32.WindowFromPoint(POINT(pos[0], pos[1]))


def root_window(hwnd):
    if not hwnd:
        return None
    root = user32.GetAncestor(hwnd, GA_ROOT)
    return root or hwnd


def class_name(hwnd):
    if not hwnd:
        return ""
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buffer, 256)
    return buffer.value


def window_text(hwnd):
    if not hwnd:
        return ""
    buffer = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(hwnd, buffer, 256)
    return buffer.value


def foreground_window():
    return user32.GetForegroundWindow()


def widget_hwnd(widget):
    widget.update_idletasks()
    child = widget.winfo_id()
    parent = user32.GetParent(child)
    return parent or child


def place_hwnd(hwnd, x, y, width, height):
    user32.SetWindowPos(
        hwnd,
        HWND_TOPMOST,
        int(x),
        int(y),
        int(width),
        int(height),
        SWP_NOACTIVATE | SWP_SHOWWINDOW,
    )


def raise_hwnd(hwnd):
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)


def make_overlay(hwnd):
    """Keep the window above other apps without taking keyboard focus."""
    style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    style |= WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
    user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, style)

    old = user32.GetWindowLongPtrW(hwnd, GWL_WNDPROC)

    def proc(window, msg, wparam, lparam):
        if msg == WM_MOUSEACTIVATE:
            return MA_NOACTIVATE
        return user32.CallWindowProcW(old, window, msg, wparam, lparam)

    callback = WndProc(proc)
    _alive.append(callback)
    user32.SetWindowLongPtrW(hwnd, GWL_WNDPROC, ctypes.cast(callback, c_void_p).value)


def key_down(vk):
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def install_keyboard_hook(callback):
    handle = user32.SetWindowsHookExW(
        WH_KEYBOARD_LL,
        callback,
        kernel32.GetModuleHandleW(None),
        0,
    )
    return handle


def remove_keyboard_hook(handle):
    if handle:
        user32.UnhookWindowsHookEx(handle)


def call_next_hook(handle, code, wparam, lparam):
    return user32.CallNextHookEx(handle, code, wparam, lparam)


def create_mutex(name):
    handle = kernel32.CreateMutexW(None, True, name)
    already = kernel32.GetLastError() == ERROR_ALREADY_EXISTS
    return handle, already
