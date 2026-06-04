param(
    [string]$EnvFile
)

. (Join-Path $PSScriptRoot "_common.ps1")

$repoRoot = Get-RepoRoot
$EnvFile = if ($EnvFile) { $EnvFile } else { Join-Path $repoRoot ".env.fabric" }
if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Missing $EnvFile. Run 01-bootstrap-network.ps1 first."
}

Import-DotEnvFile -Path $EnvFile

$testNetworkDir = $env:FABRIC_TEST_NETWORK_DIR
if (-not $testNetworkDir) {
    throw "FABRIC_TEST_NETWORK_DIR is not set in $EnvFile"
}

$chaincodePath = $env:FABRIC_CHAINCODE_PATH
if (-not $chaincodePath) {
    throw "FABRIC_CHAINCODE_PATH is not set in $EnvFile"
}

$chaincodePathBash = Convert-ToBashPath $chaincodePath

Write-Host "Deploying chaincode $($env:FABRIC_CHAINCODE_NAME) to channel $($env:FABRIC_CHANNEL_NAME)..."
Invoke-FabricBash -WorkingDirectory $testNetworkDir -Command "./network.sh" -Arguments @(
    "deployCC",
    "-c",
    $env:FABRIC_CHANNEL_NAME,
    "-ccn",
    $env:FABRIC_CHAINCODE_NAME,
    "-ccp",
    $chaincodePathBash,
    "-ccl",
    "go"
)

Write-Host "Chaincode deployed."
Write-Host "Next: run scripts/fabric/03-start-demo.ps1"
