$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root

if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'Windows 10/11 x64 is required for this installer build.'
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    throw 'Python 3.11 was not found. Install Python 3.11 x64 and retry.'
}
$PythonVersion = & $Python.Source --version 2>&1
if ($PythonVersion -notmatch 'Python 3\.11\.') {
    throw "Python 3.11 is required by the reproducible build. Found: $PythonVersion"
}

& $Python.Source -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'Could not upgrade pip.' }
& $Python.Source -m pip install 'pyinstaller>=6,<7' 'pywebview>=5,<6' 'tzdata>=2024.1'
if ($LASTEXITCODE -ne 0) { throw 'Could not install the desktop build dependencies.' }

$BuildDir = Join-Path $Root 'build'
$DistDir = Join-Path $Root 'dist'
$AppDir = Join-Path $DistDir 'RomaniaFinanceSkillHub'
New-Item -ItemType Directory -Force -Path $BuildDir, $DistDir | Out-Null
if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }

$PyInstallerArgs = @(
    '-m', 'PyInstaller',
    '--noconfirm', '--clean', '--windowed', '--onedir',
    '--name', 'RomaniaFinanceSkillHub',
    '--distpath', $DistDir,
    '--workpath', (Join-Path $BuildDir 'pyinstaller'),
    '--specpath', (Join-Path $BuildDir 'pyinstaller'),
    '--paths', (Join-Path $Root 'tools'),
    '--collect-all', 'webview',
    '--collect-all', 'tzdata',
    '--add-data', "$($Root)\skills;skills",
    '--add-data', "$($Root)\.agents;.agents",
    '--add-data', "$($Root)\docs;docs",
    '--add-data', "$($Root)\README.md;.",
    '--add-data', "$($Root)\bundle-manifest.json;.",
    (Join-Path $Root 'tools\desktop_app.py')
)
& $Python.Source @PyInstallerArgs
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller failed.' }

$Bootstrapper = Join-Path $BuildDir 'MicrosoftEdgeWebView2Setup.exe'
Invoke-WebRequest -Uri 'https://go.microsoft.com/fwlink/p/?LinkId=2124703' -OutFile $Bootstrapper
$Signature = Get-AuthenticodeSignature -FilePath $Bootstrapper
if ($Signature.Status -ne 'Valid' -or $Signature.SignerCertificate.Subject -notmatch 'Microsoft') {
    throw 'The downloaded WebView2 bootstrapper did not pass Microsoft signature verification.'
}

$Iscc = (Get-Command ISCC.exe -ErrorAction SilentlyContinue).Source
if (-not $Iscc) {
    $Iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
}
if (-not (Test-Path $Iscc)) {
    $Chocolatey = Get-Command choco -ErrorAction SilentlyContinue
    if (-not $Chocolatey) { throw 'Inno Setup 6 was not found; install Inno Setup 6 or Chocolatey and retry.' }
    & $Chocolatey.Source install innosetup --yes --no-progress
    if ($LASTEXITCODE -ne 0) { throw 'Could not install Inno Setup 6.' }
    $Iscc = Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\ISCC.exe'
}
if (-not (Test-Path $Iscc)) { throw 'ISCC.exe was not found after installing Inno Setup 6.' }

& $Iscc (Join-Path $Root 'packaging\windows\RomaniaFinanceSkillHub.iss')
if ($LASTEXITCODE -ne 0) { throw 'Inno Setup failed.' }

$Installer = Join-Path $DistDir 'installer\RomaniaFinanceSkillHub-Setup.exe'
if (-not (Test-Path $Installer)) { throw "Installer output missing: $Installer" }
Write-Host "Windows installer ready: $Installer"
