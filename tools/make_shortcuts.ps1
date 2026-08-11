# Creates Desktop and Start Menu shortcuts for the venv-based install.
param(
    [Parameter(Mandatory = $true)][string]$Root
)

$ErrorActionPreference = 'Stop'

$pythonw = Join-Path $Root '.venv\Scripts\pythonw.exe'
$script = Join-Path $Root 'RillerasConverter.py'
$icon = Join-Path $Root 'convert.ico'

if (-not (Test-Path $pythonw)) {
    Write-Warning "pythonw.exe not found at $pythonw - skipping shortcuts."
    exit 0
}

$shell = New-Object -ComObject WScript.Shell

$targets = @(
    [Environment]::GetFolderPath('Desktop'),
    (Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs')
)

foreach ($dir in $targets) {
    if (-not (Test-Path $dir)) { continue }
    $linkPath = Join-Path $dir 'Rilleras Converter.lnk'
    try {
        $link = $shell.CreateShortcut($linkPath)
        $link.TargetPath = $pythonw
        $link.Arguments = '"{0}"' -f $script
        $link.WorkingDirectory = $Root
        $link.Description = 'Convert between PDF, Word and image formats'
        if (Test-Path $icon) { $link.IconLocation = $icon }
        $link.Save()
        Write-Host "  Shortcut: $linkPath"
    }
    catch {
        Write-Warning "  Could not create $linkPath : $_"
    }
}
