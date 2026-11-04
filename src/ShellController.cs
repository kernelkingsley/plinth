using System;
using System.Globalization;
using System.IO;
using System.Text;

namespace Plinth
{
    internal sealed class ShellController
    {
        const string RecoveryName = "restore.txt";

        public bool OriginalAutoHide;
        public bool OriginalAlwaysOnTop;
        public RECT OriginalWorkArea;
        public RECT TaskbarRect;
        public RECT MonitorRect;
        public int Edge;
        public int Thickness;
        public bool PrimaryMonitor;
        public uint Dpi;
        public bool Applied;

        string recoveryPath;
        string logPath;

        public ShellController()
        {
            string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Plinth");
            Directory.CreateDirectory(dir);
            recoveryPath = Path.Combine(dir, RecoveryName);
            logPath = Path.Combine(dir, "demo.log");
            try
            {
                File.WriteAllText(logPath, "");
            }
            catch
            {
            }
        }

        public void Log(string message)
        {
            try
            {
                string line = DateTime.Now.ToString("HH:mm:ss.fff", CultureInfo.InvariantCulture) + " " + message + Environment.NewLine;
                File.AppendAllText(logPath, line);
            }
            catch
            {
            }
        }

        public bool HasRecovery()
        {
            return File.Exists(recoveryPath);
        }

        public void RecoverFromCrash()
        {
            Log("recovery file found, restoring previous shell state");
            if (!LoadRecovery())
            {
                Log("recovery file unreadable, forcing taskbar visible");
                OriginalAutoHide = false;
                OriginalAlwaysOnTop = true;
            }
            Applied = true;
            Restore();
        }

        public void Capture()
        {
            APPBARDATA data = NativeMethods.NewAppBarData();
            IntPtr statePtr = NativeMethods.SHAppBarMessage(NativeMethods.ABM_GETSTATE, ref data);
            uint state = (uint)statePtr.ToInt64();
            OriginalAutoHide = (state & NativeMethods.ABS_AUTOHIDE) != 0;
            OriginalAlwaysOnTop = (state & NativeMethods.ABS_ALWAYSONTOP) != 0;

            data = NativeMethods.NewAppBarData();
            IntPtr posResult = NativeMethods.SHAppBarMessage(NativeMethods.ABM_GETTASKBARPOS, ref data);
            TaskbarRect = data.rc;
            Edge = (int)data.uEdge;

            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            Dpi = 96;
            if (tray != IntPtr.Zero)
            {
                try
                {
                    uint dpi = NativeMethods.GetDpiForWindow(tray);
                    if (dpi >= 96)
                    {
                        Dpi = dpi;
                    }
                }
                catch
                {
                }
            }

            FixTinyAutohideRect();

            IntPtr monitor = NativeMethods.MonitorFromWindow(tray, NativeMethods.MONITOR_DEFAULTTONEAREST);
            MONITORINFO info = new MONITORINFO();
            info.cbSize = System.Runtime.InteropServices.Marshal.SizeOf(typeof(MONITORINFO));
            if (NativeMethods.GetMonitorInfo(monitor, ref info))
            {
                MonitorRect = info.rcMonitor;
                PrimaryMonitor = (info.dwFlags & 1) != 0;
            }
            else
            {
                MonitorRect = TaskbarRect;
                PrimaryMonitor = true;
            }

            RECT work = new RECT();
            NativeMethods.SystemParametersInfo(NativeMethods.SPI_GETWORKAREA, 0, ref work, 0);
            OriginalWorkArea = work;
            Thickness = Edge == NativeMethods.ABE_LEFT || Edge == NativeMethods.ABE_RIGHT
                ? TaskbarRect.Width
                : TaskbarRect.Height;

            Log("capture state=" + state
                + " autoHide=" + OriginalAutoHide
                + " topMost=" + OriginalAlwaysOnTop
                + " posResult=" + posResult.ToInt64()
                + " edge=" + Edge
                + " taskbar=" + FormatRect(TaskbarRect)
                + " monitor=" + FormatRect(MonitorRect)
                + " primary=" + PrimaryMonitor
                + " work=" + FormatRect(OriginalWorkArea)
                + " dpi=" + Dpi
                + " appbarBytes=" + data.cbSize);
        }

        public void SaveRecovery()
        {
            StringBuilder builder = new StringBuilder();
            builder.AppendLine("autoHide=" + (OriginalAutoHide ? "1" : "0"));
            builder.AppendLine("alwaysOnTop=" + (OriginalAlwaysOnTop ? "1" : "0"));
            builder.AppendLine("left=" + OriginalWorkArea.Left.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("top=" + OriginalWorkArea.Top.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("right=" + OriginalWorkArea.Right.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("bottom=" + OriginalWorkArea.Bottom.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("barLeft=" + TaskbarRect.Left.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("barTop=" + TaskbarRect.Top.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("barRight=" + TaskbarRect.Right.ToString(CultureInfo.InvariantCulture));
            builder.AppendLine("barBottom=" + TaskbarRect.Bottom.ToString(CultureInfo.InvariantCulture));
            File.WriteAllText(recoveryPath, builder.ToString());
            Log("saved recovery");
        }

        public void ApplyDemo()
        {
            ParkTaskbar();
            Applied = true;
            Log("demo shell applied, taskbar parked off-screen");
        }

        public RECT ParkedRect()
        {
            RECT parked = TaskbarRect;
            if (Edge == NativeMethods.ABE_TOP)
            {
                int shift = TaskbarRect.Bottom - MonitorRect.Top;
                parked.Top -= shift;
                parked.Bottom -= shift;
            }
            else if (Edge == NativeMethods.ABE_LEFT)
            {
                int shift = TaskbarRect.Right - MonitorRect.Left;
                parked.Left -= shift;
                parked.Right -= shift;
            }
            else if (Edge == NativeMethods.ABE_RIGHT)
            {
                int shift = MonitorRect.Right - TaskbarRect.Left;
                parked.Left += shift;
                parked.Right += shift;
            }
            else
            {
                int shift = MonitorRect.Bottom - TaskbarRect.Top;
                parked.Top += shift;
                parked.Bottom += shift;
            }
            return parked;
        }

        public RECT GetTaskbarWindowRect()
        {
            RECT rect;
            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            if (tray != IntPtr.Zero && NativeMethods.GetWindowRect(tray, out rect))
            {
                return rect;
            }
            return TaskbarRect;
        }

        public void MoveTaskbar(RECT rect, bool showOnTop)
        {
            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            if (tray == IntPtr.Zero || rect.Width < 1 || rect.Height < 1)
            {
                return;
            }
            IntPtr insert = showOnTop ? NativeMethods.HWND_TOPMOST : new IntPtr(1);
            uint flags = NativeMethods.SWP_NOACTIVATE;
            if (showOnTop)
            {
                flags |= NativeMethods.SWP_SHOWWINDOW;
            }
            NativeMethods.SetWindowPos(tray, insert, rect.Left, rect.Top, rect.Width, rect.Height, flags);
        }

        public void ParkTaskbar()
        {
            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            if (tray == IntPtr.Zero)
            {
                return;
            }
            IntPtr region = NativeMethods.CreateRectRgn(0, 0, 0, 0);
            NativeMethods.SetWindowRgn(tray, region, true);
        }

        public void ShowTaskbar()
        {
            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            if (tray == IntPtr.Zero)
            {
                return;
            }
            NativeMethods.SetWindowRgn(tray, IntPtr.Zero, true);
            if (TaskbarRect.Width > 1)
            {
                MoveTaskbar(TaskbarRect, true);
            }
        }

        public void EnsureParked()
        {
            IntPtr tray = NativeMethods.FindWindow("Shell_TrayWnd", null);
            if (tray == IntPtr.Zero)
            {
                return;
            }
            IntPtr probe = NativeMethods.CreateRectRgn(0, 0, 0, 0);
            int kind = NativeMethods.GetWindowRgn(tray, probe);
            NativeMethods.DeleteObject(probe);
            if (kind == NativeMethods.NULLREGION)
            {
                return;
            }
            Log("taskbar region reset, hiding again");
            ParkTaskbar();
        }

        public void ApplyInset()
        {
            if (!PrimaryMonitor)
            {
                Log("skip work-area inset; taskbar is not on the primary monitor");
                return;
            }
            RECT desired = DesiredWorkArea();
            RECT current = new RECT();
            NativeMethods.SystemParametersInfo(NativeMethods.SPI_GETWORKAREA, 0, ref current, 0);
            if (current.SameAs(desired))
            {
                return;
            }
            bool ok = NativeMethods.SystemParametersInfo(NativeMethods.SPI_SETWORKAREA, 0, ref desired, NativeMethods.SPIF_SENDCHANGE);
            Log("set work area " + FormatRect(desired) + " ok=" + ok);
        }

        public void KeepInset()
        {
            if (!Applied || !PrimaryMonitor)
            {
                return;
            }
            ApplyInset();
        }

        public void Restore()
        {
            if (!Applied && !File.Exists(recoveryPath))
            {
                return;
            }
            try
            {
                ShowTaskbar();
                SetTaskbarState(OriginalAutoHide, OriginalAlwaysOnTop);
                RECT area = OriginalWorkArea;
                bool ok = NativeMethods.SystemParametersInfo(NativeMethods.SPI_SETWORKAREA, 0, ref area, NativeMethods.SPIF_SENDCHANGE);
                Log("restored autoHide=" + OriginalAutoHide + " work=" + FormatRect(area) + " bar=" + FormatRect(TaskbarRect) + " ok=" + ok);
            }
            catch (Exception ex)
            {
                Log("restore failed " + ex.Message);
            }
            Applied = false;
            try
            {
                if (File.Exists(recoveryPath))
                {
                    File.Delete(recoveryPath);
                }
            }
            catch
            {
            }
        }

        public RECT DesiredWorkArea()
        {
            RECT area = MonitorRect;
            if (Edge == NativeMethods.ABE_BOTTOM)
            {
                area.Bottom -= Thickness;
            }
            else if (Edge == NativeMethods.ABE_TOP)
            {
                area.Top += Thickness;
            }
            else if (Edge == NativeMethods.ABE_LEFT)
            {
                area.Left += Thickness;
            }
            else if (Edge == NativeMethods.ABE_RIGHT)
            {
                area.Right -= Thickness;
            }
            return area;
        }

        void FixTinyAutohideRect()
        {
            int width = TaskbarRect.Width;
            int height = TaskbarRect.Height;
            int guess = (int)Math.Round(48.0 * Dpi / 96.0);
            if (guess < 40)
            {
                guess = 48;
            }
            if (Edge == NativeMethods.ABE_BOTTOM || (width > height * 3 && height < 24))
            {
                if (height < 24)
                {
                    Edge = NativeMethods.ABE_BOTTOM;
                    TaskbarRect.Top = TaskbarRect.Bottom - guess;
                    Log("taskbar rect was collapsed, using height " + guess);
                }
            }
            else if (Edge == NativeMethods.ABE_TOP && height < 24)
            {
                TaskbarRect.Bottom = TaskbarRect.Top + guess;
            }
            else if (Edge == NativeMethods.ABE_LEFT && width < 24)
            {
                TaskbarRect.Right = TaskbarRect.Left + guess;
            }
            else if (Edge == NativeMethods.ABE_RIGHT && width < 24)
            {
                TaskbarRect.Left = TaskbarRect.Right - guess;
            }
        }

        public void SetTaskbarState(bool autoHide, bool alwaysOnTop)
        {
            int flags = 0;
            if (autoHide)
            {
                flags |= NativeMethods.ABS_AUTOHIDE;
            }
            if (alwaysOnTop)
            {
                flags |= NativeMethods.ABS_ALWAYSONTOP;
            }
            APPBARDATA data = NativeMethods.NewAppBarData();
            data.lParam = (IntPtr)flags;
            IntPtr result = NativeMethods.SHAppBarMessage(NativeMethods.ABM_SETSTATE, ref data);
            Log("ABM_SETSTATE flags=" + flags + " result=" + result.ToInt64());
        }

        bool LoadRecovery()
        {
            try
            {
                string[] lines = File.ReadAllLines(recoveryPath);
                RECT area = new RECT();
                bool sawWork = false;
                for (int i = 0; i < lines.Length; i++)
                {
                    string line = lines[i];
                    int eq = line.IndexOf('=');
                    if (eq <= 0)
                    {
                        continue;
                    }
                    string key = line.Substring(0, eq);
                    string value = line.Substring(eq + 1);
                    if (key == "autoHide")
                    {
                        OriginalAutoHide = value == "1";
                    }
                    else if (key == "alwaysOnTop")
                    {
                        OriginalAlwaysOnTop = value == "1";
                    }
                    else if (key == "left")
                    {
                        area.Left = int.Parse(value, CultureInfo.InvariantCulture);
                        sawWork = true;
                    }
                    else if (key == "top")
                    {
                        area.Top = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "right")
                    {
                        area.Right = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "bottom")
                    {
                        area.Bottom = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "barLeft")
                    {
                        TaskbarRect.Left = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "barTop")
                    {
                        TaskbarRect.Top = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "barRight")
                    {
                        TaskbarRect.Right = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                    else if (key == "barBottom")
                    {
                        TaskbarRect.Bottom = int.Parse(value, CultureInfo.InvariantCulture);
                    }
                }
                if (sawWork)
                {
                    OriginalWorkArea = area;
                }
                return sawWork;
            }
            catch (Exception ex)
            {
                Log("load recovery failed " + ex.Message);
                return false;
            }
        }

        static string FormatRect(RECT rect)
        {
            return rect.Left + "," + rect.Top + " " + rect.Width + "x" + rect.Height;
        }
    }
}
