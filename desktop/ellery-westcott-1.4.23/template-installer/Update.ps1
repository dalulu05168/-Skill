param([switch]$VerifyOnly, [string]$AppExe = '', [string]$MarketDir = '')
$ErrorActionPreference = 'Stop'
try {
    $StageMarket = Join-Path $PSScriptRoot 'payload\resources\modules\market'
    $Files = @(
        [pscustomobject]@{ rel='canva_market.py'; sha='5e3c470b47ebaccca876d932954b095cdc0d49af2ba54537acc8185982fb2015' },
        [pscustomobject]@{ rel='assets\canva_flow_approved_blank_4k.png'; sha='944bef5bd38a240b9a09cf02a19db2ce2c5c14d68f95c302f1c51ddee3507ee5' },
        [pscustomobject]@{ rel='assets\canva_glass_approved_blank_4k.png'; sha='38d5b394a753e6a8d4070a534c41d86e4e844551a368a5ddc468ab43f8581b88' },
        [pscustomobject]@{ rel='assets\canva_graphite_approved_blank_4k.png'; sha='1f2cc3cfbc6701722bfce72295f3331c765bde79a3a78c9f60dae1c2e35d5066' }
    )
    $ExpectedHookSha = '6a9c7fdfe9b795cf8f71152cd9208450661631e818f00eb4155160701a92220d'
    $HookFile = Join-Path $PSScriptRoot 'renderer_hook.txt'
    if (-not (Test-Path -LiteralPath $HookFile -PathType Leaf)) { throw 'DISPATCH_HOOK_MISSING' }
    if ((Get-FileHash -LiteralPath $HookFile -Algorithm SHA256).Hash -ne $ExpectedHookSha) { throw 'DISPATCH_HOOK_HASH_MISMATCH' }
    if ($Files.Count -ne 4) { throw 'INTERNAL_SOURCE_COUNT_ERROR' }
    $Plan = @()
    foreach ($item in $Files) {
        $source = Join-Path $StageMarket $item.rel
        if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw ('SOURCE_MISSING: ' + $item.rel) }
        if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash -ne $item.sha) {
            throw ('SOURCE_HASH_MISMATCH: ' + $item.rel)
        }
        $Plan += [pscustomobject]@{ src=$source; rel=$item.rel; sha=$item.sha }
    }
    Write-Host 'SOURCE VERIFIED: 4 art+code files and dispatch hook.' -ForegroundColor Green
    # Direct-folder option is only used when the user explicitly selects it.
    # Source paths always come from the extracted ZIP, NEVER the installed payload.
    if ([string]::IsNullOrWhiteSpace($MarketDir)) {
        if ([string]::IsNullOrWhiteSpace($AppExe)) {
            Add-Type -AssemblyName System.Windows.Forms
            $dlg = New-Object System.Windows.Forms.OpenFileDialog
            $dlg.Title = 'Select ELLERY WESTCOTT installed main EXE (not the installer)'
            $dlg.Filter = 'Applications (*.exe)|*.exe'
            $dlg.CheckFileExists = $true
            if ($dlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
                Write-Host 'CANCELLED: No files changed.'
                exit 2
            }
            $AppExe = $dlg.FileName
        }
        $AppExe = [System.IO.Path]::GetFullPath($AppExe)
        if (-not (Test-Path -LiteralPath $AppExe -PathType Leaf)) { throw 'INSTALLED_EXE_NOT_FOUND' }
        if ([System.IO.Path]::GetExtension($AppExe).ToLowerInvariant() -ne '.exe') { throw 'SELECTED_FILE_IS_NOT_EXE' }
        $AppRoot = Split-Path -Parent $AppExe
        $Candidates = @(
            (Join-Path $AppRoot 'payload\resources\modules\market'),
            (Join-Path $AppRoot 'resources\modules\market'),
            (Join-Path $AppRoot 'resources\app\resources\modules\market'),
            (Join-Path $AppRoot '..\payload\resources\modules\market'),
            (Join-Path $AppRoot '..\resources\modules\market'),
            (Join-Path $AppRoot '..\resources\app\resources\modules\market')
        )
        $Valid = @()
        foreach ($candidate in $Candidates) {
            $mustHave = @('rendering.py', 'market_cards.py', 'market_data.py', 'application.py')
            $found = $true
            foreach ($f in $mustHave) {
                if (-not (Test-Path -LiteralPath (Join-Path $candidate $f) -PathType Leaf)) {
                    $found = $false
                    break
                }
            }
            if ($found) {
                $resolved = (Resolve-Path -LiteralPath $candidate).Path
                if ($Valid -notcontains $resolved) { $Valid += $resolved }
            }
        }
        if ($Valid.Count -gt 1) {
            throw ('AMBIGUOUS_MARKET_FOLDERS: ' + $Valid.Count + ' found. No files changed.')
        }
        if ($Valid.Count -eq 1) {
            $MarketDir = [string]$Valid[0]
        } else {
            Write-Host 'Auto detection did not find the active market module.' -ForegroundColor Yellow
            Write-Host 'Please select its actual folder containing rendering.py / market_cards.py.'
            Add-Type -AssemblyName System.Windows.Forms
            $folderDlg = New-Object System.Windows.Forms.FolderBrowserDialog
            $folderDlg.Description = 'Select installed resources / modules / market folder (not update ZIP)'
            $folderDlg.ShowNewFolderButton = $false
            if ($folderDlg.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
                Write-Host 'CANCELLED: No files changed.'
                exit 2
            }
            $MarketDir = $folderDlg.SelectedPath
        }
    } else {
        $MarketDir = [System.IO.Path]::GetFullPath($MarketDir)
    }
    $MarketDir = [System.IO.Path]::GetFullPath($MarketDir)
    foreach ($required in @('rendering.py','market_cards.py','market_data.py','application.py')) {
        if (-not (Test-Path -LiteralPath (Join-Path $MarketDir $required) -PathType Leaf)) {
            throw ('TARGET_NOT_RECOGNIZED: missing ' + $required + ' in ' + $MarketDir + '. No files changed.')
        }
    }
    # Keep backups with the actual detected module: never infer an app root
    # using a layout that may vary between Electron/unpacked versions.
    $AppRoot = Split-Path -Parent $MarketDir
    $RendererPath = Join-Path $MarketDir 'rendering.py'
    $RendererBefore = [System.IO.File]::ReadAllText($RendererPath, [System.Text.Encoding]::UTF8)
    if (-not [regex]::IsMatch($RendererBefore, '(?m)^def render\(')) {
        throw 'RENDER_ENTRYPOINT_INCOMPATIBLE: rendering.py has no render() entrypoint.'
    }
    if (($RendererBefore.Contains('EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN')) -xor
        ($RendererBefore.Contains('EW_CLAUDE_TEMPLATE_DISPATCH_V5_END'))) {
        throw 'PARTIAL_PREVIOUS_V5_HOOK: source requires manual review; nothing changed.'
    }
    $HookPresent = $RendererBefore.Contains('EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN')
    $Hook = [System.IO.File]::ReadAllText($HookFile, [System.Text.Encoding]::UTF8)
    foreach ($item in $Plan) {
        $item | Add-Member -NotePropertyName dest -NotePropertyValue (Join-Path $MarketDir $item.rel)
    }
    Write-Host ('SELECTED EXE: ' + $AppExe)
    Write-Host ('ACTIVE MARKET MODULE: ' + $MarketDir)
    Write-Host 'RENDER ENTRY: rendering.py => canva_market.py (Romania only).'
    Write-Host 'US and provider API code will not be overwritten.'
    if ($VerifyOnly) {
        Write-Host 'PREFLIGHT PASSED: sources valid, active renderer found, no files changed.' -ForegroundColor Green
        exit 0
    }
    $running = @(Get-Process -ErrorAction SilentlyContinue | Where-Object {
        try { (-not [string]::IsNullOrWhiteSpace($AppExe)) -and $_.Path -and [string]::Equals($_.Path, $AppExe, [System.StringComparison]::OrdinalIgnoreCase) }
        catch { $false }
    })
    if ($running.Count -gt 0) { throw 'PROGRAM_STILL_RUNNING: Close it before installation. No files changed.' }
    $agree = Read-Host 'Back up and change three RO templates plus the active renderer? Type YES'
    if ($agree -cne 'YES') { Write-Host 'CANCELLED: No files changed.'; exit 2 }
    $Backup = Join-Path $MarketDir ('_UpdateBackups\RO-Claude-three-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
    New-Item -ItemType Directory -Path $Backup -Force | Out-Null
    # Snapshot everything BEFORE writing a single installed file.
    $Touched = @()
    foreach ($item in $Plan) {
        $originalExists = Test-Path -LiteralPath $item.dest -PathType Leaf
        $item | Add-Member -NotePropertyName originalExists -NotePropertyValue $originalExists
        if ($originalExists) {
            $destBackup = Join-Path $Backup $item.rel
            New-Item -ItemType Directory -Path (Split-Path -Parent $destBackup) -Force | Out-Null
            Copy-Item -LiteralPath $item.dest -Destination $destBackup -Force -ErrorAction Stop
            if ((Get-FileHash -LiteralPath $item.dest -Algorithm SHA256).Hash -ne
                (Get-FileHash -LiteralPath $destBackup -Algorithm SHA256).Hash) {
                throw ('BACKUP_HASH_ERROR: '+ $item.rel)
            }
        }
    }
    $RenderBackup = Join-Path $Backup 'rendering.py'
    Copy-Item -LiteralPath $RendererPath -Destination $RenderBackup -Force -ErrorAction Stop
    if ((Get-FileHash -LiteralPath $RendererPath -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $RenderBackup -Algorithm SHA256).Hash) { throw 'ACTIVE_RENDER_BACKUP_FAILED' }
    try {
        foreach ($item in $Plan) {
            $Touched += $item
            New-Item -ItemType Directory -Path (Split-Path -Parent $item.dest) -Force | Out-Null
            Copy-Item -LiteralPath $item.src -Destination $item.dest -Force -ErrorAction Stop
            if ((Get-FileHash -LiteralPath $item.dest -Algorithm SHA256).Hash -ne $item.sha) {
                throw ('COPIED_FILE_HASH_MISMATCH: ' + $item.rel)
            }
        }
        if (-not $HookPresent) {
            # Append to existing module, preserving all original US behavior.
            [System.IO.File]::WriteAllText($RendererPath,
                $RendererBefore + [Environment]::NewLine + $Hook,
                ([System.Text.UTF8Encoding]::new($false)))
        }
        $resultCode = [System.IO.File]::ReadAllText($RendererPath, [System.Text.Encoding]::UTF8)
        if (-not $resultCode.Contains('EW_CLAUDE_TEMPLATE_DISPATCH_V5_BEGIN')) {
            throw 'ACTIVE_RENDER_DISPATCH_NOT_APPLIED'
        }
    } catch {
        $why = $_.Exception.Message
        $restorationErrors = @()
        foreach ($item in $Touched) {
            try {
                if ($item.originalExists) {
                    Copy-Item -LiteralPath (Join-Path $Backup $item.rel) -Destination $item.dest -Force -ErrorAction Stop
                } elseif (Test-Path -LiteralPath $item.dest -PathType Leaf) {
                    Remove-Item -LiteralPath $item.dest -Force -ErrorAction Stop
                }
            } catch { $restorationErrors += ($item.rel + ': ' + $_.Exception.Message) }
        }
        try { Copy-Item -LiteralPath $RenderBackup -Destination $RendererPath -Force -ErrorAction Stop }
        catch { $restorationErrors += ('rendering.py: ' + $_.Exception.Message) }
        if ($restorationErrors.Count -gt 0) {
            throw ('INSTALL_FAILED_ROLLBACK_INCOMPLETE: ' + $why + '; ' + ($restorationErrors -join '; '))
        }
        throw ('INSTALL_FAILED_ROLLED_BACK: ' + $why)
    }
    Write-Host 'INSTALL SUCCESS: 3 templates connected to the active rendering.py' -ForegroundColor Green
    Write-Host 'Background images FLOW/GLASS/GRAPHITE are used without extra frame/logo overlay.'
    Write-Host ('BACKUP AT: ' + $Backup)
    exit 0
} catch {
    Write-Host ('UPDATE FAILED: ' + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'If INSTALL SUCCESS is absent, do not assume the program is updated.'
    exit 1
}
