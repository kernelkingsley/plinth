"""The pill and the invisible click strips on either side of it."""

import tkinter as tk

from plinth.win32 import make_overlay, place_hwnd, widget_hwnd


class Hit:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, px, py):
        return self.x <= px < self.x + self.width and self.y <= py < self.y + self.height

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def right(self):
        return self.x + self.width


class Metrics:
    def __init__(self, width, compact, scale):
        pad = max(8, int(round(10 * scale)))
        art = max(16, compact - pad * 2)
        art_y = max(0, (compact - art) // 2)
        self.pad = pad
        self.art = Hit(pad, art_y, art, art)
        self.play = Hit(max(pad, width - pad - art), art_y, art, art)

        bar_h = max(3, int(round(4 * scale)))
        bar_y = compact + max(6, int(round(8 * scale)))
        self.progress = Hit(pad, bar_y, max(1, width - pad * 2), bar_h)

        text_y = self.progress.bottom + max(6, int(round(8 * scale)))
        text_h = max(28, int(round(36 * scale)))
        self.help = Hit(pad, text_y, max(1, width - pad * 2), text_h)

        button_h = max(24, int(round(30 * scale)))
        button_w = max(72, int(round(96 * scale)))
        button_y = self.help.bottom + max(6, int(round(8 * scale)))
        self.pause = Hit(pad, button_y, button_w, button_h)
        self.quit = Hit(pad + button_w + pad, button_y, button_w, button_h)
        bottom = max(8, int(round(12 * scale)))
        self.expanded_height = self.quit.bottom + bottom


def round_points(x1, y1, x2, y2, radius):
    radius = max(2, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    return [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]


class Overlay(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self._styled = False

    def place_at(self, x, y, width, height):
        width = max(1, int(width))
        height = max(1, int(height))
        self.geometry("%dx%d+%d+%d" % (width, height, int(x), int(y)))
        self.update_idletasks()
        hwnd = widget_hwnd(self)
        if not self._styled:
            make_overlay(hwnd)
            self._styled = True
        place_hwnd(hwnd, x, y, width, height)
        return hwnd


class Slot(Overlay):
    """An invisible strip. Clicking it asks the taskbar to come back."""

    IDLE = 0.02
    HOVER = 0.38

    def __init__(self, root, on_reveal):
        super().__init__(root)
        self.configure(bg="#121214")
        self.attributes("-alpha", self.IDLE)
        self.configure(cursor="hand2")
        self._on_reveal = on_reveal
        self.bind("<Enter>", self._hover_on)
        self.bind("<Leave>", self._hover_off)
        self.bind("<Button-1>", self._click)

    def reset_visual(self):
        self.attributes("-alpha", self.IDLE)

    def _hover_on(self, _event):
        self.attributes("-alpha", self.HOVER)

    def _hover_off(self, _event):
        self.attributes("-alpha", self.IDLE)

    def _click(self, _event):
        self._on_reveal()


class Pill(Overlay):
    def __init__(self, root, on_expand, on_quit):
        super().__init__(root)
        self.configure(bg="magenta")
        self.attributes("-transparentcolor", "magenta")
        self.canvas = tk.Canvas(self, bg="magenta", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)
        self.expanded = False
        self.playing = True
        self.progress = 0.18
        self.scale = 1.0
        self.compact_height = 40
        self.title = "Night Drive"
        self.subtitle = "Click either side"
        self.help = "Click either side to show the taskbar.\nCtrl+Shift+Q quits and restores it."
        self._on_expand = on_expand
        self._on_quit = on_quit
        self._metrics = None
        self.canvas.bind("<Button-1>", self._click)
        self.canvas.bind("<Button-3>", self._right_click)
        self.after(50, self._tick)

    def _tick(self):
        if self.playing:
            self.progress += 0.0025
            if self.progress >= 1:
                self.progress = 0
            if self.expanded:
                self.redraw()
        self.after(50, self._tick)

    def redraw(self):
        width = max(self.winfo_width(), 8)
        height = max(self.winfo_height(), 8)
        metrics = Metrics(width, self.compact_height, self.scale)
        self._metrics = metrics
        canvas = self.canvas
        canvas.delete("all")
        radius = max(12, int(round(22 * self.scale))) if self.expanded else height // 2
        canvas.create_polygon(
            round_points(1, 1, width - 2, height - 2, radius),
            smooth=True,
            fill="#101012",
            outline="#3a3a3e",
        )
        self._orb(metrics.art, "#30d158" if self.playing else "#6e6e76")
        self._play_button(metrics.play)
        self._compact_text(metrics)
        if height <= self.compact_height + 8:
            return
        self._progress(metrics.progress)
        canvas.create_text(
            metrics.help.x,
            metrics.help.y,
            text=self.help,
            anchor="nw",
            fill="#c4c4c8",
            font=("Segoe UI", 9),
            width=metrics.help.width,
        )
        self._button(metrics.pause, "Pause" if self.playing else "Play", True)
        self._button(metrics.quit, "Quit", False)

    def _orb(self, hit, color):
        self.canvas.create_oval(hit.x, hit.y, hit.right, hit.bottom, fill=color, outline="")
        inset = max(3, hit.width // 5)
        self.canvas.create_oval(
            hit.x + inset,
            hit.y + inset,
            hit.right - inset,
            hit.bottom - inset,
            fill="#101012",
            outline="",
        )

    def _play_button(self, hit):
        self.canvas.create_oval(hit.x, hit.y, hit.right, hit.bottom, fill="white", outline="")
        if self.playing:
            inset = max(4, hit.width // 4)
            bar_w = max(2, hit.width // 8)
            gap = max(2, hit.width // 10)
            total = bar_w * 2 + gap
            x = hit.x + (hit.width - total) // 2
            y = hit.y + inset
            bottom = hit.bottom - inset
            self.canvas.create_rectangle(x, y, x + bar_w, bottom, fill="#141416", outline="")
            self.canvas.create_rectangle(x + bar_w + gap, y, x + bar_w + gap + bar_w, bottom, fill="#141416", outline="")
        else:
            inset = max(4, hit.width // 4)
            self.canvas.create_polygon(
                hit.x + inset + 1, hit.y + inset,
                hit.x + inset + 1, hit.bottom - inset,
                hit.right - inset, hit.y + hit.height // 2,
                fill="#141416",
                outline="",
            )

    def _compact_text(self, metrics):
        left = metrics.art.right + metrics.pad
        right = metrics.play.x - metrics.pad
        if right - left < 8:
            return
        center = self.compact_height // 2
        self.canvas.create_text(
            left,
            center - 8,
            text=self.title,
            anchor="w",
            fill="white",
            font=("Segoe UI", 11, "bold"),
        )
        self.canvas.create_text(
            left,
            center + 8,
            text=self.subtitle,
            anchor="w",
            fill="#aeaeb4",
            font=("Segoe UI", 8),
        )

    def _button(self, hit, text, primary):
        radius = max(8, hit.height // 2)
        fill = "#30d158" if primary else "#34343a"
        ink = "#0c1810" if primary else "white"
        self.canvas.create_polygon(
            round_points(hit.x, hit.y, hit.right, hit.bottom, radius),
            smooth=True,
            fill=fill,
            outline="",
        )
        self.canvas.create_text(
            hit.x + hit.width // 2,
            hit.y + hit.height // 2,
            text=text,
            fill=ink,
            font=("Segoe UI", 9, "bold"),
        )

    def _progress(self, hit):
        self.canvas.create_rectangle(hit.x, hit.y, hit.right, hit.bottom, fill="#3a3a3e", outline="")
        fill_w = int(round(hit.width * max(0.0, min(1.0, self.progress))))
        if fill_w > 0:
            self.canvas.create_rectangle(hit.x, hit.y, hit.x + fill_w, hit.bottom, fill="#30d158", outline="")

    def _click(self, event):
        metrics = self._metrics or Metrics(self.winfo_width(), self.compact_height, self.scale)
        if self.expanded and metrics.quit.contains(event.x, event.y):
            self._on_quit()
            return
        if metrics.play.contains(event.x, event.y) or (self.expanded and metrics.pause.contains(event.x, event.y)):
            self.playing = not self.playing
            self.redraw()
            return
        self._on_expand()

    def _right_click(self, _event):
        if not self.expanded:
            self._on_expand()
