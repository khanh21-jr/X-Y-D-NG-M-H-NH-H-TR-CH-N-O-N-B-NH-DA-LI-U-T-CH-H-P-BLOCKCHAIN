Set-StrictMode -Version Latest

function Get-RepoRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Import-DotEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Dotenv file not found: $Path"
    }

    Get-Content -LiteralPath $Path | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith("#")) {
            return
        }

        $idx = $line.IndexOf("=")
        if ($idx -lt 1) {
            return
        }

        $name = $line.Substring(0, $idx).Trim()
        $value = $line.Substring($idx + 1)
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

function Convert-ToBashPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $full = [System.IO.Path]::GetFullPath($Path)
    if ($full.Length -ge 2 -and $full[1] -eq ':') {
        $drive = $full.Substring(0, 1).ToLowerInvariant()
        $rest = $full.Substring(2).Replace('\', '/')
        return "/$drive$rest"
    }

    return $full.Replace('\', '/')
}

function Quote-BashArg {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return "'" + ($Value -replace "'", "'\"'\"'") + "'"
}

function Invoke-FabricBash {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [Parameter()]
        [string[]]$Arguments = @()
    )

    $bash = Get-Command bash -ErrorAction SilentlyContinue
    if (-not $bash) {
        throw "bash was not found on PATH. Install Git Bash or use WSL, then rerun this script."
    }

    $commandParts = @($Command) + $Arguments
    $escapedParts = $commandParts | ForEach-Object { Quote-BashArg $_ }
    $cdPath = Quote-BashArg (Convert-ToBashPath $WorkingDirectory)
    $bashCommand = "cd $cdPath && " + ($escapedParts -join " ")

    & $bash.Source -lc $bashCommand
    if ($LASTEXITCODE -ne 0) {
        throw "Fabric bash command failed with exit code $LASTEXITCODE."
    }
}

function Write-FabricEnvFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [hashtable]$Values
    )

    $lines = @()
    foreach ($key in $Values.Keys) {
        $lines += "$key=$($Values[$key])"
    }

    Set-Content -LiteralPath $Path -Value $lines -Encoding ascii
}

