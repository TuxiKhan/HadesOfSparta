# Post a PPSSPP (Windows) menu command to a running instance — no focus needed.
# Used by the Phase 2 frame-data workflow:
#   40165 = File > Record > Dump frames (toggle)   40166 = Use lossless FFV1 (toggle)
#   40035 = Load state (current slot)              40034 = Save state
# IDs are from PPSSPP v1.20.4's menu (enumerate with GetMenu/GetMenuItemID if they drift).
param([Parameter(Mandatory)][int]$Cmd, [int]$ProcessId = 0)
Add-Type @"
using System; using System.Runtime.InteropServices;
public class PpssppMenu { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l); }
"@
$p = if ($ProcessId) { Get-Process -Id $ProcessId } else { Get-Process PPSSPPWindows64 | Select-Object -First 1 }
[PpssppMenu]::PostMessage($p.MainWindowHandle, 0x111, [IntPtr]$Cmd, [IntPtr]0) | Out-Null
"posted $Cmd to pid $($p.Id) at $([DateTime]::Now.ToString('HH:mm:ss.fff'))"
