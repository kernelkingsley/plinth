$ErrorActionPreference = "Stop"
$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& $csc `
  /nologo `
  /target:winexe `
  /platform:x64 `
  /optimize+ `
  /debug:pdbonly `
  /out:"$root\Plinth.exe" `
  /win32manifest:"$root\app.manifest" `
  /reference:System.Windows.Forms.dll `
  /reference:System.Drawing.dll `
  "$root\src\NativeMethods.cs" `
  "$root\src\ShellController.cs" `
  "$root\src\Ui.cs" `
  "$root\src\Program.cs"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Output "Built $root\Plinth.exe"
