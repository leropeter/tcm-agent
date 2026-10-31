# 开独立窗口 → 用"新增窗口句柄"定位 → 置前台 → 截图
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
using System.Collections.Generic;
public class WinUtil {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb, IntPtr p);
  [DllImport("user32.dll")] public static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
  public delegate bool EnumProc(IntPtr h, IntPtr p);
  public static List<IntPtr> All() {
    var l = new List<IntPtr>();
    EnumWindows((h,p)=>{ if(IsWindowVisible(h)) l.Add(h); return true; }, IntPtr.Zero);
    return l;
  }
  public static string Text(IntPtr h){ var sb=new StringBuilder(512); GetWindowText(h,sb,512); return sb.ToString(); }
}
"@

$before = @{}
foreach ($h in [WinUtil]::All()) { $before[$h] = 1 }

$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
Start-Process $edge -ArgumentList '--new-window', 'http://127.0.0.1:8501'
Start-Sleep -Seconds 16

$target = $null; $title = ''
foreach ($h in [WinUtil]::All()) {
    if (-not $before.ContainsKey($h)) {
        $t = [WinUtil]::Text($h)
        if ($t) { Write-Output "新窗口: $t" }
        if ($t -match '中医药|辨证|8501|Edge') { $target = $h; $title = $t; break }
    }
}
if ($null -eq $target) { Write-Output '未找到新增浏览器窗口'; exit 1 }

[void][WinUtil]::ShowWindow($target, 3)
[void][WinUtil]::SetForegroundWindow($target)
Start-Sleep -Seconds 4

$sc = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bmp = New-Object System.Drawing.Bitmap $sc.Width, $sc.Height
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($sc.X, $sc.Y, 0, 0, $bmp.Size)
$out = 'E:\tcm-agent\ui_live.png'
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
Write-Output "窗口: $title"
Write-Output "截图: $out  $([math]::Round((Get-Item $out).Length/1KB,0)) KB"
