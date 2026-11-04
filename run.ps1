$python = Join-Path $env:APPDATA "uv\python\cpython-3.12-windows-x86_64-none\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
& $python -m plinth
