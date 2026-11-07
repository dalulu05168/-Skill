$ErrorActionPreference = "Stop"
$root = Join-Path $env:RUNNER_TEMP "EW-Template-Installer-Windows-Smoke"
if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Force -Recurse }
$stage = Join-Path $root "stage"
$payload = Join-Path $stage "payload\resources\modules\market"
$target = Join-Path $root "app\payload\resources\modules\market"
New-Item -Type Directory -Force -Path (Join-Path $payload "assets"), (Join-Path $target "assets") | Out-Null
$exe = Join-Path $root "app\ElleryWestcott.exe"
[IO.File]::WriteAllText($exe, "TEST-STUB - not executable")
$originalRender = "def render(key, data, width=1920, demo=False, theme='graphite'):`n    return 'original'`n"
foreach ($file in @("rendering.py", "market_cards.py", "market_data.py", "application.py", "intraday.py", "chart_draw.py")) {
    $f = Join-Path $target $file
    [IO.File]::WriteAllText($f, $(if ($file -eq "rendering.py") {$originalRender} else {"# untouched $file`n"}))
}
$baseline = @{}
foreach ($file in @("rendering.py","market_cards.py","market_data.py","application.py","intraday.py","chart_draw.py")) {
    $baseline[$file] = (Get-FileHash -LiteralPath (Join-Path $target $file) -Algorithm SHA256).Hash
}
$files = @(
    [pscustomobject]@{name="canva_market.py";old="5e3c470b47ebaccca876d932954b095cdc0d49af2ba54537acc8185982fb2015"},
    [pscustomobject]@{name="assets\canva_flow_approved_blank_4k.png";old="944bef5bd38a240b9a09cf02a19db2ce2c5c14d68f95c302f1c51ddee3507ee5"},
    [pscustomobject]@{name="assets\canva_glass_approved_blank_4k.png";old="38d5b394a753e6a8d4070a534c41d86e4e844551a368a5ddc468ab43f8581b88"},
    [pscustomobject]@{name="assets\canva_graphite_approved_blank_4k.png";old="1f2cc3cfbc6701722bfce72295f3331c765bde79a3a78c9f60dae1c2e35d5066"}
)
$installer = Get-Content -LiteralPath "$PSScriptRoot\Update.ps1" -Raw -Encoding UTF8
if ($installer -match "ConvertFrom-Json") { throw "Unexpected JSON manifest usage" }
foreach ($item in $files) {
    $f = Join-Path $payload $item.name
    [IO.File]::WriteAllText($f, "FAKE FIXTURE DATA FOR $($item.name)")
    $hash=(Get-FileHash -LiteralPath $f -Algorithm SHA256).Hash
    $installer=$installer.Replace($item.old,$hash.ToLowerInvariant())
}
$hook = "# EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN`n# fixture`n# EW_CLAUDE_TEMPLATE_DISPATCH_V5_END`n"
[IO.File]::WriteAllText((Join-Path $stage "renderer_hook.txt"),$hook)
$hookHash=(Get-FileHash -LiteralPath (Join-Path $stage "renderer_hook.txt") -Algorithm SHA256).Hash
$installer=$installer.Replace("6a9c7fdfe9b795cf8f71152cd9208450661631e818f00eb4155160701a92220d",$hookHash.ToLowerInvariant())
# Disable the console-only YES prompt within the isolated test fixture.
# The distributed updater retains its manual YES confirmation.
$installer=$installer.Replace('$agree = Read-Host ', '$agree = "YES"; # Read-Host ')
$testScript = Join-Path $stage "Update.ps1"
[IO.File]::WriteAllText($testScript,$installer,(New-Object System.Text.UTF8Encoding($false)))
$tokens = $null
$parseErrors = $null
$null=[System.Management.Automation.Language.Parser]::ParseFile($testScript,[ref]$tokens,[ref]$parseErrors)
if ($parseErrors.Count) { throw "Windows PowerShell syntax errors: $($parseErrors | Out-String)" }
Write-Host "NATIVE POWERSHELL PARSE PASSED"
$output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File $testScript -VerifyOnly -AppExe $exe 2>&1
Write-Host ($output | Out-String)
if ($LASTEXITCODE -ne 0 -or ($output | Out-String) -notmatch "PREFLIGHT PASSED") {throw "Native Windows preflight did not pass"}
foreach ($file in $baseline.Keys) {
    if ($baseline[$file] -ne (Get-FileHash -LiteralPath (Join-Path $target $file) -Algorithm SHA256).Hash) {
        throw "Read-only mode modified $file"
    }
}
Write-Host "NATIVE WINDOWS READ-ONLY CHECK PASSED"
$output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File $testScript -AppExe $exe 2>&1
Write-Host ($output | Out-String)
if ($LASTEXITCODE -ne 0 -or ($output | Out-String) -notmatch "INSTALL SUCCESS") {throw "Native Windows install did not pass"}
foreach ($item in $files) {
    $src = (Get-FileHash -LiteralPath (Join-Path $payload $item.name) -Algorithm SHA256).Hash
    $dest = (Get-FileHash -LiteralPath (Join-Path $target $item.name) -Algorithm SHA256).Hash
    if ($src -ne $dest) {throw "Installed file mismatch $($item.name)"}
}
foreach ($file in @("market_cards.py","market_data.py","application.py","intraday.py","chart_draw.py")) {
    if ($baseline[$file] -ne (Get-FileHash -LiteralPath (Join-Path $target $file) -Algorithm SHA256).Hash) {throw "Protected $file changed"}
}
$rendered=Get-Content -LiteralPath (Join-Path $target "rendering.py") -Raw
if ($rendered -notmatch "EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN") {throw "rendering.py hook not connected"}
$backups = @(Get-ChildItem -LiteralPath (Join-Path $target "_UpdateBackups") -Directory)
if ($backups.Count -lt 1) {throw "Missing backup directory"}
$originalBackup = Join-Path $backups[0].FullName "rendering.py"
if ((Get-FileHash -LiteralPath $originalBackup -Algorithm SHA256).Hash -ne $baseline["rendering.py"]) {throw "Original rendering.py backup incorrect"}
Write-Host "NATIVE WINDOWS INSTALL AND BACKUP PASSED"
$output = & powershell.exe -NoProfile -ExecutionPolicy Bypass -STA -File $testScript -AppExe $exe 2>&1
if ($LASTEXITCODE -ne 0 -or ($output | Out-String) -notmatch "INSTALL SUCCESS") {throw "Idempotent repeat install failed"}
$rendered=Get-Content -LiteralPath (Join-Path $target "rendering.py") -Raw
if (($rendered -split "EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN").Count -ne 2) {throw "Duplicate renderer hook"}
Write-Host "NATIVE WINDOWS IDEMPOTENT REINSTALL PASSED"
