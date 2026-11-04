using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Text;
using System.Windows.Forms;

namespace Plinth
{
    internal sealed class PillMetrics
    {
        public int Pad;
        public Rectangle Art;
        public Rectangle Play;
        public Rectangle Progress;
        public Rectangle Help;
        public Rectangle PauseButton;
        public Rectangle QuitButton;
        public int ExpandedHeight;

        public static PillMetrics Create(int width, int compact, double scale)
        {
            PillMetrics metrics = new PillMetrics();
            int pad = Math.Max(8, (int)Math.Round(10 * scale));
            metrics.Pad = pad;
            int art = Math.Max(16, compact - pad * 2);
            int artY = Math.Max(0, (compact - art) / 2);
            metrics.Art = new Rectangle(pad, artY, art, art);
            metrics.Play = new Rectangle(Math.Max(pad, width - pad - art), artY, art, art);

            int barH = Math.Max(3, (int)Math.Round(4 * scale));
            int barY = compact + Math.Max(6, (int)Math.Round(8 * scale));
            metrics.Progress = new Rectangle(pad, barY, Math.Max(1, width - pad * 2), barH);

            int textY = metrics.Progress.Bottom + Math.Max(6, (int)Math.Round(8 * scale));
            int textH = Math.Max(28, (int)Math.Round(36 * scale));
            metrics.Help = new Rectangle(pad, textY, Math.Max(1, width - pad * 2), textH);

            int buttonH = Math.Max(24, (int)Math.Round(30 * scale));
            int buttonW = Math.Max(72, (int)Math.Round(96 * scale));
            int buttonY = metrics.Help.Bottom + Math.Max(6, (int)Math.Round(8 * scale));
            metrics.PauseButton = new Rectangle(pad, buttonY, buttonW, buttonH);
            metrics.QuitButton = new Rectangle(pad + buttonW + pad, buttonY, buttonW, buttonH);
            int bottom = Math.Max(8, (int)Math.Round(12 * scale));
            metrics.ExpandedHeight = metrics.QuitButton.Bottom + bottom;
            return metrics;
        }
    }

    internal class OverlayForm : Form
    {
        public bool AllowClose;

        public OverlayForm()
        {
            FormBorderStyle = FormBorderStyle.None;
            ShowInTaskbar = false;
            StartPosition = FormStartPosition.Manual;
            TopMost = true;
            AutoScaleMode = AutoScaleMode.None;
            BackColor = Color.Black;
        }

        protected override bool ShowWithoutActivation
        {
            get { return true; }
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ExStyle |= NativeMethods.WS_EX_NOACTIVATE | NativeMethods.WS_EX_TOOLWINDOW | NativeMethods.WS_EX_TOPMOST;
                return cp;
            }
        }

        protected override void WndProc(ref Message m)
        {
            if (m.Msg == NativeMethods.WM_MOUSEACTIVATE)
            {
                m.Result = (IntPtr)NativeMethods.MA_NOACTIVATE;
                return;
            }
            base.WndProc(ref m);
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!AllowClose && e.CloseReason == CloseReason.UserClosing)
            {
                e.Cancel = true;
                return;
            }
            base.OnFormClosing(e);
        }
    }

    internal sealed class SlotForm : OverlayForm
    {
        public const double IdleOpacity = 1.0 / 255.0;
        public const double HoverOpacity = 0.38;

        public bool RevealOnClick;
        public event EventHandler RevealRequested;

        public SlotForm()
        {
            BackColor = Color.FromArgb(18, 18, 20);
            Opacity = IdleOpacity;
            Cursor = Cursors.Hand;
        }

        public void ResetVisual()
        {
            Opacity = IdleOpacity;
        }

        protected override void OnMouseEnter(EventArgs e)
        {
            Opacity = HoverOpacity;
            base.OnMouseEnter(e);
        }

        protected override void OnMouseLeave(EventArgs e)
        {
            Opacity = IdleOpacity;
            base.OnMouseLeave(e);
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            if (RevealOnClick && e.Button == MouseButtons.Left && RevealRequested != null)
            {
                RevealRequested(this, EventArgs.Empty);
            }
            base.OnMouseDown(e);
        }
    }

    internal sealed class PillForm : OverlayForm
    {
        public bool Expanded;
        public bool Playing;
        public string TitleText;
        public string SubtitleText;
        public string HelpText;
        public float Progress;
        public double PixelScale;
        public int CompactHeight;

        public event EventHandler ExpandToggled;
        public event EventHandler QuitRequested;

        Timer playTimer;
        Font titleFont;
        Font subFont;
        Font helpFont;
        Font buttonFont;

        public PillForm()
        {
            TitleText = "Night Drive";
            SubtitleText = "Click either side";
            HelpText = "Click either side to show the taskbar.\r\nCtrl+Shift+Q quits and restores it.";
            Playing = true;
            Progress = 0.18f;
            PixelScale = 1;
            CompactHeight = 40;
            SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.UserPaint | ControlStyles.ResizeRedraw, true);
            UpdateStyles();
            titleFont = new Font("Segoe UI", 11f, FontStyle.Bold, GraphicsUnit.Point);
            subFont = new Font("Segoe UI", 8.5f, FontStyle.Regular, GraphicsUnit.Point);
            helpFont = new Font("Segoe UI", 9f, FontStyle.Regular, GraphicsUnit.Point);
            buttonFont = new Font("Segoe UI", 9f, FontStyle.Bold, GraphicsUnit.Point);
            playTimer = new Timer();
            playTimer.Interval = 50;
            playTimer.Tick += new EventHandler(OnPlayTick);
            playTimer.Start();
        }

        public void Shutdown()
        {
            playTimer.Stop();
            playTimer.Dispose();
        }

        protected override CreateParams CreateParams
        {
            get
            {
                CreateParams cp = base.CreateParams;
                cp.ClassStyle |= NativeMethods.CS_DROPSHADOW;
                return cp;
            }
        }

        protected override void OnPaintBackground(PaintEventArgs e)
        {
        }

        protected override void OnSizeChanged(EventArgs e)
        {
            base.OnSizeChanged(e);
            ApplyRegion();
        }

        public void ApplyRegion()
        {
            if (Width < 4 || Height < 4)
            {
                return;
            }
            int radius = Expanded ? Math.Max(12, (int)Math.Round(22 * PixelScale)) : Height / 2;
            using (GraphicsPath path = Rounded(new Rectangle(0, 0, Width, Height), radius))
            {
                Region old = Region;
                Region = new Region(path);
                if (old != null)
                {
                    old.Dispose();
                }
            }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            PillMetrics metrics = PillMetrics.Create(Width, CompactHeight, PixelScale);
            if (e.Button == MouseButtons.Right)
            {
                if (!Expanded && ExpandToggled != null)
                {
                    ExpandToggled(this, EventArgs.Empty);
                }
                return;
            }
            if (e.Button != MouseButtons.Left)
            {
                return;
            }
            if (Expanded && metrics.QuitButton.Contains(e.Location))
            {
                if (QuitRequested != null)
                {
                    QuitRequested(this, EventArgs.Empty);
                }
                return;
            }
            if (metrics.Play.Contains(e.Location) || (Expanded && metrics.PauseButton.Contains(e.Location)))
            {
                Playing = !Playing;
                Invalidate();
                return;
            }
            if (ExpandToggled != null)
            {
                ExpandToggled(this, EventArgs.Empty);
            }
        }

        void OnPlayTick(object sender, EventArgs e)
        {
            if (!Playing)
            {
                return;
            }
            Progress += 0.0025f;
            if (Progress >= 1f)
            {
                Progress = 0f;
            }
            if (Expanded)
            {
                Invalidate();
            }
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            if (Width < 8 || Height < 8)
            {
                return;
            }
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            g.TextRenderingHint = TextRenderingHint.ClearTypeGridFit;
            PillMetrics metrics = PillMetrics.Create(Width, CompactHeight, PixelScale);
            int radius = Expanded ? Math.Max(12, (int)Math.Round(22 * PixelScale)) : Height / 2;
            Rectangle body = new Rectangle(0, 0, Width - 1, Height - 1);
            using (GraphicsPath path = Rounded(body, radius))
            using (SolidBrush fill = new SolidBrush(Color.FromArgb(16, 16, 18)))
            using (Pen border = new Pen(Color.FromArgb(70, 255, 255, 255), 1f))
            {
                g.FillPath(fill, path);
                g.DrawPath(border, path);
            }

            Color orb = Playing ? Color.FromArgb(48, 209, 88) : Color.FromArgb(110, 110, 118);
            using (SolidBrush brush = new SolidBrush(orb))
            {
                g.FillEllipse(brush, metrics.Art);
            }
            Rectangle hole = Inset(metrics.Art, Math.Max(3, metrics.Art.Width / 5));
            using (SolidBrush brush = new SolidBrush(Color.FromArgb(16, 16, 18)))
            {
                g.FillEllipse(brush, hole);
            }

            using (SolidBrush plate = new SolidBrush(Color.White))
            {
                g.FillEllipse(plate, metrics.Play);
            }
            DrawGlyph(g, metrics.Play, Playing);

            Rectangle textRect = Rectangle.FromLTRB(
                metrics.Art.Right + metrics.Pad,
                0,
                metrics.Play.Left - metrics.Pad,
                CompactHeight);
            DrawCompactText(g, textRect);

            if (Height <= CompactHeight + 8)
            {
                return;
            }

            Rectangle track = metrics.Progress;
            using (SolidBrush trackBrush = new SolidBrush(Color.FromArgb(50, 255, 255, 255)))
            {
                g.FillRectangle(trackBrush, track);
            }
            int fillWidth = (int)Math.Round(track.Width * Math.Max(0f, Math.Min(1f, Progress)));
            if (fillWidth > 0)
            {
                using (SolidBrush fillBrush = new SolidBrush(Color.FromArgb(48, 209, 88)))
                {
                    g.FillRectangle(fillBrush, new Rectangle(track.X, track.Y, fillWidth, track.Height));
                }
            }

            using (SolidBrush helpBrush = new SolidBrush(Color.FromArgb(196, 196, 200)))
            using (StringFormat format = new StringFormat())
            {
                format.Alignment = StringAlignment.Near;
                format.LineAlignment = StringAlignment.Near;
                g.DrawString(HelpText, helpFont, helpBrush, (RectangleF)metrics.Help, format);
            }

            DrawButton(g, metrics.PauseButton, Playing ? "Pause" : "Play", true);
            DrawButton(g, metrics.QuitButton, "Quit", false);
        }

        void DrawCompactText(Graphics g, Rectangle textRect)
        {
            if (textRect.Width < 8)
            {
                return;
            }
            float titleH = titleFont.GetHeight(g);
            float subH = subFont.GetHeight(g);
            float y = Math.Max(0, (CompactHeight - (titleH + subH)) / 2f);
            using (SolidBrush titleBrush = new SolidBrush(Color.White))
            using (SolidBrush subBrush = new SolidBrush(Color.FromArgb(174, 174, 180)))
            using (StringFormat format = new StringFormat())
            {
                format.Alignment = StringAlignment.Near;
                format.LineAlignment = StringAlignment.Near;
                format.Trimming = StringTrimming.EllipsisCharacter;
                format.FormatFlags = StringFormatFlags.NoWrap;
                g.DrawString(TitleText, titleFont, titleBrush, new RectangleF(textRect.X, y, textRect.Width, titleH + 1), format);
                g.DrawString(SubtitleText, subFont, subBrush, new RectangleF(textRect.X, y + titleH - 1, textRect.Width, subH + 1), format);
            }
        }

        void DrawButton(Graphics g, Rectangle bounds, string text, bool primary)
        {
            int radius = Math.Max(8, bounds.Height / 2);
            using (GraphicsPath path = Rounded(bounds, radius))
            using (SolidBrush fill = new SolidBrush(primary ? Color.FromArgb(48, 209, 88) : Color.FromArgb(52, 52, 58)))
            using (SolidBrush textBrush = new SolidBrush(primary ? Color.FromArgb(12, 24, 16) : Color.White))
            using (StringFormat format = new StringFormat())
            {
                format.Alignment = StringAlignment.Center;
                format.LineAlignment = StringAlignment.Center;
                g.FillPath(fill, path);
                g.DrawString(text, buttonFont, textBrush, (RectangleF)bounds, format);
            }
        }

        static void DrawGlyph(Graphics g, Rectangle bounds, bool playing)
        {
            int inset = Math.Max(4, bounds.Width / 4);
            using (SolidBrush brush = new SolidBrush(Color.FromArgb(20, 20, 22)))
            {
                if (playing)
                {
                    int barW = Math.Max(2, bounds.Width / 8);
                    int gap = Math.Max(2, bounds.Width / 10);
                    int total = barW * 2 + gap;
                    int x = bounds.X + (bounds.Width - total) / 2;
                    int y = bounds.Y + inset;
                    int h = bounds.Height - inset * 2;
                    g.FillRectangle(brush, x, y, barW, h);
                    g.FillRectangle(brush, x + barW + gap, y, barW, h);
                }
                else
                {
                    int x = bounds.X + inset + 1;
                    Point[] triangle = new Point[]
                    {
                        new Point(x, bounds.Y + inset),
                        new Point(x, bounds.Bottom - inset),
                        new Point(bounds.Right - inset, bounds.Y + bounds.Height / 2)
                    };
                    g.FillPolygon(brush, triangle);
                }
            }
        }

        static Rectangle Inset(Rectangle rect, int amount)
        {
            return new Rectangle(rect.X + amount, rect.Y + amount, Math.Max(1, rect.Width - amount * 2), Math.Max(1, rect.Height - amount * 2));
        }

        static GraphicsPath Rounded(Rectangle bounds, int radius)
        {
            GraphicsPath path = new GraphicsPath();
            int diameter = Math.Max(2, radius * 2);
            if (diameter > bounds.Width)
            {
                diameter = Math.Max(2, bounds.Width);
            }
            if (diameter > bounds.Height)
            {
                diameter = Math.Max(2, bounds.Height);
            }
            Rectangle arc = new Rectangle(bounds.X, bounds.Y, diameter, diameter);
            path.AddArc(arc, 180, 90);
            arc.X = bounds.Right - diameter;
            path.AddArc(arc, 270, 90);
            arc.Y = bounds.Bottom - diameter;
            path.AddArc(arc, 0, 90);
            arc.X = bounds.X;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }
    }
}
