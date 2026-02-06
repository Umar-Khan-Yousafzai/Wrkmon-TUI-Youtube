# wrkmon installer for Windows
# Usage: irm https://raw.githubusercontent.com/Umar-Khan-Yousafzai/Wrkmon-TUI-Youtube/main/install.ps1 | iex

$ErrorActionPreference = "Stop"

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  wrkmon Installer v1.3.1" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as admin for chocolatey
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

# Check Python
Write-Host "Step 1: Checking Python..." -ForegroundColor Yellow
$python = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $python = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $python = "python3"
}

if (-not $python) {
    Write-Host "Python not found. Installing via winget..." -ForegroundColor Yellow
    winget install Python.Python.3.11 --silent --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    $python = "python"
}

$version = & $python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
Write-Host "Python found: $version" -ForegroundColor Green

# Check mpv
Write-Host ""
Write-Host "Step 2: Checking mpv (required)..." -ForegroundColor Yellow
$mpvInstalled = $false

if (Get-Command mpv -ErrorAction SilentlyContinue) {
    Write-Host "mpv is already installed." -ForegroundColor Green
    $mpvInstalled = $true
}

if (-not $mpvInstalled) {
    Write-Host "Installing mpv..." -ForegroundColor Yellow

    # Try winget first
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Write-Host "Using winget to install mpv..." -ForegroundColor Yellow
        winget install mpv --silent --accept-package-agreements
        $mpvInstalled = $true
    }
    # Try chocolatey
    elseif (Get-Command choco -ErrorAction SilentlyContinue) {
        Write-Host "Using chocolatey to install mpv..." -ForegroundColor Yellow
        choco install mpv -y
        $mpvInstalled = $true
    }
    else {
        # Manual download
        Write-Host "Downloading mpv manually..." -ForegroundColor Yellow
        $mpvDir = "$env:LOCALAPPDATA\wrkmon\mpv"
        New-Item -ItemType Directory -Force -Path $mpvDir | Out-Null

        $mpvUrl = "https://sourceforge.net/projects/mpv-player-windows/files/64bit/mpv-x86_64-20240121-git-a39f9b6.7z/download"
        $mpvZip = "$env:TEMP\mpv.7z"

        Write-Host "This may take a moment..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $mpvUrl -OutFile $mpvZip -UseBasicParsing

        # Extract (requires 7zip or expand-archive for zip)
        if (Get-Command 7z -ErrorAction SilentlyContinue) {
            7z x $mpvZip -o"$mpvDir" -y
        } else {
            Write-Host "Please install mpv manually: winget install mpv" -ForegroundColor Red
        }
    }
}

# Check deno (optional but recommended)
Write-Host ""
Write-Host "Step 3: Checking deno (optional, for better YouTube support)..." -ForegroundColor Yellow
$denoInstalled = $false
$jsRuntimeAvailable = $false

if (Get-Command deno -ErrorAction SilentlyContinue) {
    Write-Host "deno is already installed." -ForegroundColor Green
    $denoInstalled = $true
    $jsRuntimeAvailable = $true
} elseif (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "Node.js found - JavaScript runtime available." -ForegroundColor Green
    $jsRuntimeAvailable = $true
}

if (-not $jsRuntimeAvailable) {
    Write-Host "Installing deno for better YouTube compatibility..." -ForegroundColor Yellow

    # Try winget first
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        winget install DenoLand.Deno --silent --accept-package-agreements 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "deno installed via winget." -ForegroundColor Green
            $denoInstalled = $true
        }
    }

    # Try chocolatey
    if (-not $denoInstalled -and (Get-Command choco -ErrorAction SilentlyContinue)) {
        choco install deno -y 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "deno installed via chocolatey." -ForegroundColor Green
            $denoInstalled = $true
        }
    }

    # Try official installer
    if (-not $denoInstalled) {
        try {
            irm https://deno.land/install.ps1 | iex
            Write-Host "deno installed via official installer." -ForegroundColor Green
        } catch {
            Write-Host "Could not install deno automatically." -ForegroundColor Yellow
            Write-Host "For better YouTube support, install manually:" -ForegroundColor Yellow
            Write-Host "  irm https://deno.land/install.ps1 | iex" -ForegroundColor Cyan
        }
    }
}

# Install wrkmon
Write-Host ""
Write-Host "Step 4: Installing wrkmon..." -ForegroundColor Yellow
& $python -m pip install --upgrade pip
& $python -m pip install --upgrade wrkmon

Write-Host ""
Write-Host "==================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green
Write-Host ""
Write-Host "Run 'wrkmon' to start the player." -ForegroundColor Cyan
Write-Host ""
Write-Host "Commands:" -ForegroundColor Yellow
Write-Host "  wrkmon          : Launch TUI player"
Write-Host "  wrkmon update   : Check for updates"
Write-Host "  wrkmon deps     : Check dependencies"
Write-Host ""
Write-Host "Controls:" -ForegroundColor Yellow
Write-Host "  F1-F4  : Switch views (Search, Queue, History, Playlists)"
Write-Host "  F5     : Play/Pause      b : Focus mode"
Write-Host "  F9     : Stop            l : Lyrics"
Write-Host "  F10    : Add to queue    ? : Help"
Write-Host ""
