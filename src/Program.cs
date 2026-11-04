using System;
using System.Drawing;
using System.Threading;
using System.Windows.Forms;

namespace Plinth
{
    internal static class Program
    {
        static Mutex singleInstance;
        static ShellController shell;
        static IslandController island;
        static LowLevelKeyboardProc keyboardProc;
        static IntPtr keyboardHook;

        [STAThread]
        static void Main()
        {
            try
            {
                NativeMethods.SetProcessDpiAwarenessContext(new IntPtr(-4));
            }
            catch
            {
            }

            bool createdNew;
            singleInstance = new Mutex(true, "Local\\Plinth.Demo", out createdNew);
            if (!createdNew)
            {
                MessageBox.Show("Plinth is already running.\r\nRight-click the pill, or press Ctrl+Shift+Q.", "Plinth");
                return;
            }

            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.SetUnhandledExceptionMode(UnhandledExceptionMode.CatchException);
            Application.ThreadException += new ThreadExceptionEventHandler(OnThreadException);
            AppDomain.CurrentDomain.UnhandledException += new UnhandledExceptionEventHandler(OnDomainException);

            shell = new ShellController();
            try
            {
                if (shell.HasRecovery())
                {
                    shell.RecoverFromCrash();
                }
                shell.Capture();
                shell.SaveRecovery();
                shell.ApplyDemo();

                island = new IslandController(shell);
                island.QuitRequested += new EventHandler(OnQuitRequested);
                island.Start();

                keyboardProc = new LowLevelKeyboardProc(OnKey);
                keyboardHook = NativeMethods.SetWindowsHookEx(
                    NativeMethods.WH_KEYBOARD_LL,
                    keyboardProc,
                    NativeMethods.GetModuleHandle(null),
                    0);
                shell.Log("keyboard hook " + keyboardHook.ToInt64());

                Application.ApplicationExit += new EventHandler(OnApplicationExit);
                Application.Run();
            }
            catch (Exception ex)
            {
                shell.Log("fatal " + ex);
                try
                {
                    shell.Restore();
                }
                catch
                {
                }
                MessageBox.Show(ex.ToString(), "Plinth");
            }
        }

        static void OnQuitRequested(object sender, EventArgs e)
        {
            Application.Exit();
        }

        static void OnApplicationExit(object sender, EventArgs e)
        {
            Shutdown();
        }

        static void OnThreadException(object sender, ThreadExceptionEventArgs e)
        {
            if (shell != null)
            {
                shell.Log("thread exception " + e.Exception);
            }
            Shutdown();
            MessageBox.Show(e.Exception.ToString(), "Plinth");
        }

        static void OnDomainException(object sender, UnhandledExceptionEventArgs e)
        {
            if (shell != null)
            {
                shell.Log("domain exception " + e.ExceptionObject);
            }
            Shutdown();
        }

        static void Shutdown()
        {
            if (keyboardHook != IntPtr.Zero)
            {
                NativeMethods.UnhookWindowsHookEx(keyboardHook);
                keyboardHook = IntPtr.Zero;
            }
            if (island != null)
            {
                island.Shutdown();
                island = null;
            }
            if (shell != null)
            {
                shell.Restore();
            }
        }

        static IntPtr OnKey(int nCode, IntPtr wParam, IntPtr lParam)
        {
            if (nCode >= 0 && wParam == (IntPtr)NativeMethods.WM_KEYDOWN && island != null)
            {
                int vk = System.Runtime.InteropServices.Marshal.ReadInt32(lParam);
                bool ctrl = (NativeMethods.GetAsyncKeyState(0x11) & 0x8000) != 0;
                bool shift = (NativeMethods.GetAsyncKeyState(0x10) & 0x8000) != 0;
                if (vk == 0x51 && ctrl && shift)
                {
                    island.BeginInvokeQuit();
                    return (IntPtr)1;
                }
                if (vk == 0x1B && island.IsRevealed && !island.ShellFlyoutOpen())
                {
                    island.BeginInvokeDismiss();
                    return (IntPtr)1;
                }
            }
            return NativeMethods.CallNextHookEx(keyboardHook, nCode, wParam, lParam);
        }
    }

    internal sealed class IslandController
    {
        readonly ShellController shell;
        readonly PillForm pill;
        readonly SlotForm left;
        readonly SlotForm right;
        readonly SlotForm shield;
        readonly System.Windows.Forms.Timer animation;
        readonly System.Windows.Forms.Timer watch;
        readonly System.Windows.Forms.Timer keeper;
        readonly System.Windows.Forms.Timer topmost;

        int topmostPulses;
        bool revealed;
        bool alive;
        int fromTop;
        int toTop;
        int fromHeight;
        int toHeight;
        int shownTop;
        int shownHeight;
        int pillLeft;
        int pillWidth;
        int compactHeight;
        int expandedHeight;
        int gap;
        double scale;
        DateTime animStart;
        DateTime revealedAt;
        DateTime? awaySince;

        public bool IsRevealed
        {
            get { return revealed; }
        }

        public event EventHandler QuitRequested;

        public IslandController(ShellController shell)
        {
            this.shell = shell;
            pill = new PillForm();
            left = new SlotForm();
            right = new SlotForm();
            shield = new SlotForm();
            left.RevealOnClick = true;
            right.RevealOnClick = true;
            shield.RevealOnClick = true;
            left.RevealRequested += new EventHandler(OnRevealRequested);
            right.RevealRequested += new EventHandler(OnRevealRequested);
            shield.RevealRequested += new EventHandler(OnRevealRequested);
            pill.ExpandToggled += new EventHandler(OnExpandToggled);
            pill.QuitRequested += new EventHandler(OnPillQuit);

            animation = new System.Windows.Forms.Timer();
            animation.Interval = 15;
            animation.Tick += new EventHandler(OnAnimate);

            watch = new System.Windows.Forms.Timer();
            watch.Interval = 80;
            watch.Tick += new EventHandler(OnWatch);

            keeper = new System.Windows.Forms.Timer();
            keeper.Interval = 180;
            keeper.Tick += new EventHandler(OnKeepInset);

            topmost = new System.Windows.Forms.Timer();
            topmost.Interval = 80;
            topmost.Tick += new EventHandler(OnTopmostPulse);
        }

        public void Start()
        {
            scale = shell.Dpi / 96.0;
            if (scale < 1)
            {
                scale = 1;
            }
            gap = Math.Max(8, (int)Math.Round(8 * scale));
            compactHeight = Math.Max(36, (int)Math.Round(44 * scale));
            if (shell.Edge == NativeMethods.ABE_BOTTOM || shell.Edge == NativeMethods.ABE_TOP)
            {
                int margin = Math.Max(2, (int)Math.Round(2 * scale));
                int fit = shell.Thickness - margin * 2;
                if (fit >= 28 && fit < compactHeight)
                {
                    compactHeight = fit;
                }
            }
            pillWidth = Math.Max(240, (int)Math.Round(400 * scale));
            int slotSpan = shell.Edge == NativeMethods.ABE_LEFT || shell.Edge == NativeMethods.ABE_RIGHT
                ? shell.TaskbarRect.Height
                : shell.TaskbarRect.Width;
            int maxWidth = Math.Max(220, slotSpan - Math.Max(80, (int)Math.Round(48 * scale)));
            if (pillWidth > maxWidth)
            {
                pillWidth = maxWidth;
            }

            pill.PixelScale = scale;
            pill.CompactHeight = compactHeight;
            expandedHeight = PillMetrics.Create(pillWidth, compactHeight, scale).ExpandedHeight;
            shownHeight = compactHeight;

            PlaceResting(false);
            alive = true;
            left.Show();
            right.Show();
            shield.Show();
            pill.Show();
            LayoutSlots();
            PlacePill(shownTop, shownHeight, false);
            keeper.Start();
            shell.Log("shown pill at " + pillLeft + "," + shownTop + " " + pillWidth + "x" + shownHeight);
        }

        public void Shutdown()
        {
            if (!alive && pill.IsDisposed)
            {
                return;
            }
            alive = false;
            animation.Stop();
            watch.Stop();
            keeper.Stop();
            topmost.Stop();
            try
            {
                pill.Shutdown();
            }
            catch
            {
            }
            pill.AllowClose = true;
            left.AllowClose = true;
            right.AllowClose = true;
            shield.AllowClose = true;
            HideForm(left);
            HideForm(right);
            HideForm(shield);
            HideForm(pill);
            DisposeForm(left);
            DisposeForm(right);
            DisposeForm(shield);
            DisposeForm(pill);
        }

        public void BeginInvokeQuit()
        {
            if (pill.IsHandleCreated)
            {
                pill.BeginInvoke(new MethodInvoker(RaiseQuit));
            }
            else
            {
                RaiseQuit();
            }
        }

        public void BeginInvokeDismiss()
        {
            if (!pill.IsHandleCreated)
            {
                return;
            }
            pill.BeginInvoke(new MethodInvoker(Dismiss));
        }

        public bool ShellFlyoutOpen()
        {
            return FlyoutUnderCursor() || FlyoutInForeground();
        }

        void OnRevealRequested(object sender, EventArgs e)
        {
            Reveal();
        }

        void OnExpandToggled(object sender, EventArgs e)
        {
            pill.Expanded = !pill.Expanded;
            int height = pill.Expanded ? expandedHeight : compactHeight;
            Animate(AnchorTop(height), height);
            pill.ApplyRegion();
            pill.Invalidate();
        }

        void OnPillQuit(object sender, EventArgs e)
        {
            RaiseQuit();
        }

        void RaiseQuit()
        {
            if (QuitRequested != null)
            {
                QuitRequested(this, EventArgs.Empty);
            }
        }

        void Reveal()
        {
            if (!alive || revealed)
            {
                return;
            }
            revealed = true;
            revealedAt = DateTime.UtcNow;
            awaySince = null;
            keeper.Stop();
            left.ResetVisual();
            right.ResetVisual();
            shield.ResetVisual();
            left.Hide();
            right.Hide();
            shield.Hide();
            shell.ShowTaskbar();
            pill.SubtitleText = "Taskbar is open";
            pill.HelpText = "The taskbar has the slot back.\r\nMove the pointer away, or press Escape.";
            Animate(AnchorTop(shownHeight), shownHeight);
            topmostPulses = 6;
            topmost.Start();
            watch.Start();
            pill.Invalidate();
            shell.Log("revealed");
        }

        void Dismiss()
        {
            if (!alive || !revealed)
            {
                return;
            }
            revealed = false;
            awaySince = null;
            watch.Stop();
            shell.ParkTaskbar();
            pill.SubtitleText = "Click either side";
            pill.HelpText = "Click either side to show the taskbar.\r\nCtrl+Shift+Q quits and restores it.";
            if (!left.Visible)
            {
                left.Show();
            }
            if (!right.Visible)
            {
                right.Show();
            }
            if (!shield.Visible)
            {
                shield.Show();
            }
            LayoutSlots();
            Animate(AnchorTop(shownHeight), shownHeight);
            keeper.Start();
            pill.Invalidate();
            shell.Log("dismissed");
        }

        void Animate(int top, int height)
        {
            fromTop = shownTop;
            fromHeight = shownHeight;
            toTop = top;
            toHeight = height;
            animStart = DateTime.UtcNow;
            animation.Start();
        }

        void OnAnimate(object sender, EventArgs e)
        {
            double t = (DateTime.UtcNow - animStart).TotalMilliseconds / 220.0;
            bool done = t >= 1;
            if (done)
            {
                t = 1;
            }
            else
            {
                t = 1 - Math.Pow(1 - t, 3);
            }
            int top = fromTop + (int)Math.Round((toTop - fromTop) * t);
            int height = fromHeight + (int)Math.Round((toHeight - fromHeight) * t);
            PlacePill(top, height, true);
            if (done)
            {
                animation.Stop();
                PlacePill(toTop, toHeight, true);
                if (!revealed)
                {
                    LayoutSlots();
                }
            }
        }

        void OnWatch(object sender, EventArgs e)
        {
            if (!revealed || !alive)
            {
                return;
            }
            if ((DateTime.UtcNow - revealedAt).TotalMilliseconds < 350)
            {
                return;
            }
            if (PointerIsHolding())
            {
                awaySince = null;
                return;
            }
            if (!awaySince.HasValue)
            {
                awaySince = DateTime.UtcNow;
                return;
            }
            if ((DateTime.UtcNow - awaySince.Value).TotalMilliseconds >= 450)
            {
                Dismiss();
            }
        }

        void OnKeepInset(object sender, EventArgs e)
        {
            if (!alive || revealed || animation.Enabled)
            {
                return;
            }
            shell.EnsureParked();
            if (pill.IsHandleCreated)
            {
                NativeMethods.SetWindowPos(pill.Handle, NativeMethods.HWND_TOPMOST, 0, 0, 0, 0, 0x0001 | 0x0002 | NativeMethods.SWP_NOACTIVATE);
            }
        }

        void OnTopmostPulse(object sender, EventArgs e)
        {
            if (pill.IsHandleCreated)
            {
                NativeMethods.SetWindowPos(pill.Handle, NativeMethods.HWND_TOPMOST, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010);
            }
            topmostPulses--;
            if (topmostPulses <= 0)
            {
                topmost.Stop();
            }
        }

        bool PointerIsHolding()
        {
            POINT cursor;
            if (!NativeMethods.GetCursorPos(out cursor))
            {
                return false;
            }
            if (shell.TaskbarRect.Contains(cursor.X, cursor.Y))
            {
                return true;
            }
            Rectangle pillRect = new Rectangle(pillLeft, shownTop, pillWidth, shownHeight);
            if (pillRect.Contains(cursor.X, cursor.Y))
            {
                return true;
            }
            return FlyoutUnderCursor() || FlyoutInForeground();
        }

        bool FlyoutUnderCursor()
        {
            POINT cursor;
            if (!NativeMethods.GetCursorPos(out cursor))
            {
                return false;
            }
            IntPtr hwnd = NativeMethods.WindowFromPoint(cursor);
            return IsFlyout(hwnd);
        }

        bool FlyoutInForeground()
        {
            return IsFlyout(NativeMethods.GetForegroundWindow());
        }

        static bool IsFlyout(IntPtr hwnd)
        {
            if (hwnd == IntPtr.Zero)
            {
                return false;
            }
            IntPtr root = NativeMethods.GetAncestor(hwnd, NativeMethods.GA_ROOT);
            if (root == IntPtr.Zero)
            {
                root = hwnd;
            }
            string cls = NativeMethods.ClassOf(root);
            if (cls == "Shell_TrayWnd" || cls == "Shell_SecondaryTrayWnd" || cls == "NotifyIconOverflowWindow")
            {
                return true;
            }
            if (cls == "XamlExplorerHostIslandWindow" || cls == "TopLevelWindowForOverflowXamlIsland")
            {
                return true;
            }
            if (cls == "Windows.UI.Core.CoreWindow")
            {
                string title = NativeMethods.TextOf(root);
                if (title.Length == 0 || title == "Start" || title == "Search" || title == "Quick settings")
                {
                    return true;
                }
            }
            return false;
        }

        void PlaceResting(bool animate)
        {
            LayoutPillHorizontal();
            int top = AnchorTop(shownHeight);
            if (animate)
            {
                Animate(top, shownHeight);
            }
            else
            {
                shownTop = top;
            }
        }

        void LayoutPillHorizontal()
        {
            if (shell.Edge == NativeMethods.ABE_LEFT || shell.Edge == NativeMethods.ABE_RIGHT)
            {
                pillLeft = shell.TaskbarRect.Top + Math.Max(0, (shell.TaskbarRect.Height - pillWidth) / 2);
            }
            else
            {
                pillLeft = shell.TaskbarRect.Left + Math.Max(0, (shell.TaskbarRect.Width - pillWidth) / 2);
            }
        }

        int AnchorTop(int height)
        {
            if (shell.Edge == NativeMethods.ABE_LEFT || shell.Edge == NativeMethods.ABE_RIGHT)
            {
                int along = shell.TaskbarRect.Top + Math.Max(0, (shell.TaskbarRect.Height - height) / 2);
                if (revealed)
                {
                    if (shell.Edge == NativeMethods.ABE_LEFT)
                    {
                        return shell.TaskbarRect.Right + gap;
                    }
                    return shell.TaskbarRect.Left - gap - pillWidth;
                }
                return along;
            }

            if (revealed)
            {
                if (shell.Edge == NativeMethods.ABE_TOP)
                {
                    return shell.TaskbarRect.Bottom + gap;
                }
                return shell.TaskbarRect.Top - gap - height;
            }

            int compactBottom = shell.TaskbarRect.Top + (shell.Thickness + compactHeight) / 2;
            return compactBottom - height;
        }

        void LayoutSlots()
        {
            if (!alive)
            {
                return;
            }
            RECT bar = shell.TaskbarRect;
            if (shell.Edge == NativeMethods.ABE_LEFT || shell.Edge == NativeMethods.ABE_RIGHT)
            {
                int center = shell.TaskbarRect.Top + Math.Max(0, (shell.TaskbarRect.Height - pillWidth) / 2);
                PlaceForm(left, bar.Left, bar.Top, bar.Width, Math.Max(1, center - bar.Top + 2));
                PlaceForm(shield, bar.Left, center, bar.Width, pillWidth);
                int rightY = center + pillWidth - 2;
                PlaceForm(right, bar.Left, rightY, bar.Width, Math.Max(1, bar.Bottom - rightY));
                return;
            }

            int pillX = bar.Left + Math.Max(0, (bar.Width - pillWidth) / 2);
            PlaceForm(left, bar.Left, bar.Top, Math.Max(1, pillX - bar.Left + 2), bar.Height);
            PlaceForm(shield, pillX, bar.Top, pillWidth, bar.Height);
            int rightX = pillX + pillWidth - 2;
            PlaceForm(right, rightX, bar.Top, Math.Max(1, bar.Right - rightX), bar.Height);
            BringPillAboveSlots();
        }

        void PlacePill(int top, int height, bool aboveSlots)
        {
            shownTop = top;
            shownHeight = height;
            if (shell.Edge == NativeMethods.ABE_LEFT || shell.Edge == NativeMethods.ABE_RIGHT)
            {
                int x = revealed
                    ? (shell.Edge == NativeMethods.ABE_LEFT ? shell.TaskbarRect.Right + gap : shell.TaskbarRect.Left - gap - height)
                    : shell.TaskbarRect.Left + Math.Max(0, (shell.Thickness - height) / 2);
                int y = shell.TaskbarRect.Top + Math.Max(0, (shell.TaskbarRect.Height - pillWidth) / 2);
                if (pill.Expanded)
                {
                    y = shell.TaskbarRect.Top + (shell.TaskbarRect.Height - pillWidth) / 2;
                }
                PlaceForm(pill, x, y, height, pillWidth);
                pillLeft = y;
            }
            else
            {
                PlaceForm(pill, pillLeft, top, pillWidth, height);
            }
            if (aboveSlots)
            {
                BringPillAboveSlots();
            }
        }

        void BringPillAboveSlots()
        {
            if (pill.IsHandleCreated)
            {
                NativeMethods.SetWindowPos(pill.Handle, NativeMethods.HWND_TOPMOST, 0, 0, 0, 0, 0x0001 | 0x0002 | NativeMethods.SWP_NOACTIVATE);
            }
        }

        static void PlaceForm(Form form, int x, int y, int width, int height)
        {
            if (width < 1)
            {
                width = 1;
            }
            if (height < 1)
            {
                height = 1;
            }
            form.Bounds = new Rectangle(x, y, width, height);
            if (form.IsHandleCreated)
            {
                NativeMethods.SetWindowPos(
                    form.Handle,
                    NativeMethods.HWND_TOPMOST,
                    x,
                    y,
                    width,
                    height,
                    NativeMethods.SWP_NOACTIVATE | NativeMethods.SWP_SHOWWINDOW);
            }
        }

        static void HideForm(Form form)
        {
            if (form != null && !form.IsDisposed && form.Visible)
            {
                form.Hide();
            }
        }

        static void DisposeForm(Form form)
        {
            if (form != null && !form.IsDisposed)
            {
                form.Dispose();
            }
        }
    }
}
