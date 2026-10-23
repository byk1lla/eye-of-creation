// Eye of Creation — Windows ekran koruyucusu (.scr)
//
// Windows ekran koruyucuyu şu argümanlarla çağırır:
//   /s           tam ekran çalıştır
//   /p <hwnd>    ayarlar penceresindeki küçük önizleme
//   /c           ayarlar (bu koruyucuda ayar yok)
// Argümansız açılırsa (çift tıklama) /s gibi davranır.
//
// Video EyeOfCreation.mp4, .scr ile aynı klasörde ya da
// %LOCALAPPDATA%\EyeOfCreation\ içinde aranır.

using System;
using System.IO;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Interop;
using System.Windows.Media;
using Forms = System.Windows.Forms;

namespace EyeOfCreation
{
    internal static class Program
    {
        [STAThread]
        private static int Main(string[] args)
        {
            var (mode, previewHandle) = ParseArgs(args);

            if (mode == "c")
            {
                Forms.MessageBox.Show(
                    "Eye of Creation'ın ayarı yok.\n\ngithub.com/byk1lla/eye-of-creation",
                    "Eye of Creation", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Information);
                return 0;
            }

            var video = FindVideo();
            if (video == null)
            {
                if (mode != "p")
                {
                    Forms.MessageBox.Show(
                        "EyeOfCreation.mp4 bulunamadı.\n\nVideoyu .scr dosyasıyla aynı klasöre ya da\n%LOCALAPPDATA%\\EyeOfCreation\\ içine koy.",
                        "Eye of Creation", Forms.MessageBoxButtons.OK, Forms.MessageBoxIcon.Warning);
                }
                return 1;
            }

            var app = new Application { ShutdownMode = ShutdownMode.OnMainWindowClose };

            if (mode == "p")
            {
                if (previewHandle == IntPtr.Zero) return 0;
                var preview = new PreviewHost(previewHandle, video);
                app.Run();
                GC.KeepAlive(preview);
                return 0;
            }

            // Her monitöre bir pencere
            var screens = Forms.Screen.AllScreens.OrderByDescending(s => s.Primary).ToArray();
            SaverWindow first = null;
            foreach (var screen in screens)
            {
                var w = new SaverWindow(video, screen.Bounds);
                if (first == null) first = w;
                w.Show();
            }
            app.MainWindow = first;
            app.Run();
            return 0;
        }

        private static (string mode, IntPtr hwnd) ParseArgs(string[] args)
        {
            if (args.Length == 0) return ("s", IntPtr.Zero);

            var a = args[0].Trim().ToLowerInvariant().TrimStart('/', '-');
            var mode = a.Length > 0 ? a.Substring(0, 1) : "s";
            string hwndText = null;

            var colon = a.IndexOf(':');
            if (colon >= 0) hwndText = a.Substring(colon + 1);
            else if (args.Length > 1) hwndText = args[1];

            var hwnd = IntPtr.Zero;
            if (hwndText != null && long.TryParse(hwndText, out var h)) hwnd = new IntPtr(h);

            if (mode != "s" && mode != "p" && mode != "c") mode = "s";
            return (mode, hwnd);
        }

        private static string FindVideo()
        {
            var exeDir = AppDomain.CurrentDomain.BaseDirectory;
            var local = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "EyeOfCreation");
            foreach (var dir in new[] { exeDir, local })
            {
                var p = Path.Combine(dir, "EyeOfCreation.mp4");
                if (File.Exists(p)) return p;
            }
            return null;
        }

        internal static MediaElement CreatePlayer(string video)
        {
            var media = new MediaElement
            {
                Source = new Uri(video, UriKind.Absolute),
                LoadedBehavior = MediaState.Manual,
                UnloadedBehavior = MediaState.Manual,
                Stretch = Stretch.UniformToFill,
                IsMuted = true,
                Volume = 0,
            };
            media.MediaEnded += (s, e) =>
            {
                media.Position = TimeSpan.Zero;
                media.Play();
            };
            media.Loaded += (s, e) => media.Play();
            return media;
        }
    }

    internal sealed class SaverWindow : Window
    {
        private Point? _startMouse;

        public SaverWindow(string video, System.Drawing.Rectangle bounds)
        {
            WindowStyle = WindowStyle.None;
            ResizeMode = ResizeMode.NoResize;
            ShowInTaskbar = false;
            Topmost = true;
            Background = Brushes.Black;
            Cursor = Cursors.None;
            WindowStartupLocation = WindowStartupLocation.Manual;

            // Pencereyi doğru monitöre koyup orada büyütüyoruz (DPI farklarından bağımsız)
            Left = bounds.Left;
            Top = bounds.Top;
            Width = Math.Max(100, bounds.Width / 2.0);
            Height = Math.Max(100, bounds.Height / 2.0);
            SourceInitialized += (s, e) =>
            {
                var hwnd = new WindowInteropHelper(this).Handle;
                NativeMethods.SetWindowPos(hwnd, IntPtr.Zero, bounds.Left, bounds.Top,
                    bounds.Width, bounds.Height, NativeMethods.SWP_NOZORDER | NativeMethods.SWP_NOACTIVATE);
                WindowState = WindowState.Maximized;
            };

            Content = Program.CreatePlayer(video);

            KeyDown += (s, e) => Quit();
            MouseDown += (s, e) => Quit();
            MouseWheel += (s, e) => Quit();
            MouseMove += OnMouseMove;
            Deactivated += (s, e) => { /* çoklu monitörde odak değişebilir, kapanma */ };
        }

        private void OnMouseMove(object sender, MouseEventArgs e)
        {
            var p = PointToScreen(e.GetPosition(this));
            if (_startMouse == null) { _startMouse = p; return; }
            if (Math.Abs(p.X - _startMouse.Value.X) > 12 || Math.Abs(p.Y - _startMouse.Value.Y) > 12)
                Quit();
        }

        private static void Quit() => Application.Current.Shutdown();
    }

    /// Ayarlar penceresindeki küçük önizleme kutusuna gömülen görüntü.
    internal sealed class PreviewHost
    {
        private readonly HwndSource _source;

        public PreviewHost(IntPtr parent, string video)
        {
            NativeMethods.GetClientRect(parent, out var r);
            var p = new HwndSourceParameters("EyeOfCreationPreview")
            {
                ParentWindow = parent,
                PositionX = 0,
                PositionY = 0,
                Width = r.Right - r.Left,
                Height = r.Bottom - r.Top,
                WindowStyle = NativeMethods.WS_CHILD | NativeMethods.WS_VISIBLE,
            };
            _source = new HwndSource(p)
            {
                RootVisual = new Grid { Background = Brushes.Black, Children = { Program.CreatePlayer(video) } },
            };
            _source.Disposed += (s, e) => Application.Current?.Shutdown();

            // Önizleme kutusu kapanınca biz de kapanalım
            var timer = new System.Windows.Threading.DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
            timer.Tick += (s, e) =>
            {
                if (!NativeMethods.IsWindow(parent)) Application.Current.Shutdown();
            };
            timer.Start();
        }
    }

    internal static class NativeMethods
    {
        public const int WS_CHILD = 0x40000000;
        public const int WS_VISIBLE = 0x10000000;
        public const uint SWP_NOZORDER = 0x0004;
        public const uint SWP_NOACTIVATE = 0x0010;

        [StructLayout(LayoutKind.Sequential)]
        public struct RECT { public int Left, Top, Right, Bottom; }

        [DllImport("user32.dll")]
        public static extern bool GetClientRect(IntPtr hWnd, out RECT rect);

        [DllImport("user32.dll")]
        public static extern bool IsWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool SetWindowPos(IntPtr hWnd, IntPtr after, int x, int y, int cx, int cy, uint flags);
    }
}
