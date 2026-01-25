$ErrorActionPreference = 'Stop'

# Install wrkmon via pip
Write-Host "Installing wrkmon..."
pip install wrkmon --upgrade

# Verify installation
$wrkmonPath = (Get-Command wrkmon -ErrorAction SilentlyContinue).Path
if ($wrkmonPath) {
    Write-Host "wrkmon installed successfully at: $wrkmonPath"
} else {
    Write-Warning "wrkmon command not found in PATH. You may need to restart your terminal."
}

Write-Host ""
Write-Host "============================================"
Write-Host "  wrkmon installed successfully!"
Write-Host "============================================"
Write-Host ""
Write-Host "Usage: Run 'wrkmon' in your terminal"
Write-Host ""
Write-Host "Controls:"
Write-Host "  F1-F4  : Switch views"
Write-Host "  F5     : Play/Pause"
Write-Host "  F9     : Stop"
Write-Host "  F10    : Add to queue"
Write-Host "  /      : Search"
Write-Host ""
