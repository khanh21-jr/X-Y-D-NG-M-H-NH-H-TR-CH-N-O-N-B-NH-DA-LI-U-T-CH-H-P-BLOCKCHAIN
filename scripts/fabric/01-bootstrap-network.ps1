param(
    [string]$FabricSamplesDir,
    [string]$ChannelName = "mychannel",
    [string]$ChaincodeName = "prediction-ledger"
)

. (Join-Path $PSScriptRoot "_common.ps1")

$repoRoot = Get-RepoRoot
$fabricSamplesDir = if ($FabricSamplesDir) {
    [System.IO.Path]::GetFullPath($FabricSamplesDir)
} else {
    [System.IO.Path]::GetFullPath((Join-Path (Split-Path $repoRoot -Parent) "fabric-samples"))
}
$testNetworkDir = Join-Path $fabricSamplesDir "test-network"
$networkSh = Join-Path $testNetworkDir "network.sh"
$chaincodePath = Join-Path $repoRoot "fabric\chaincode\prediction-ledger-go"
$envFile = Join-Path $repoRoot ".env.fabric"

if (-not (Test-Path -LiteralPath $networkSh)) {
    throw "Could not find fabric-samples test-network at $networkSh"
}

Write-Host "Bringing test-network down..."
Invoke-FabricBash -WorkingDirectory $testNetworkDir -Command "./network.sh" -Arguments @("down")

Write-Host "Starting test-network and channel $ChannelName..."
Invoke-FabricBash -WorkingDirectory $testNetworkDir -Command "./network.sh" -Arguments @("up", "createChannel", "-ca", "-c", $ChannelName)

$org1AdminMsp = Join-Path $testNetworkDir "organizations\peerOrganizations\org1.example.com\users\Admin@org1.example.com\msp"
$peerTlsRootCert = Join-Path $testNetworkDir "organizations\peerOrganizations\org1.example.com\peers\peer0.org1.example.com\tls\ca.crt"
$ordererCa = Join-Path $testNetworkDir "organizations\ordererOrganizations\example.com\orderers\orderer.example.com\msp\tlscacerts\tlsca.example.com-cert.pem"

$values = [ordered]@{
    LEDGER_BACKEND                    = "fabric-gateway"
    FABRIC_LEDGER_API_URL             = "http://127.0.0.1:8080"
    FABRIC_SAMPLES_DIR                = $fabricSamplesDir
    FABRIC_BIN_DIR                    = (Join-Path $fabricSamplesDir "bin")
    FABRIC_TEST_NETWORK_DIR           = $testNetworkDir
    FABRIC_CHANNEL_NAME               = $ChannelName
    FABRIC_CHAINCODE_NAME             = $ChaincodeName
    FABRIC_CHAINCODE_PATH             = $chaincodePath
    FABRIC_ORDERER_ADDRESS            = "localhost:7050"
    FABRIC_ORDERER_CA                 = $ordererCa
    FABRIC_ORDERER_TLS_HOSTNAME_OVERRIDE = "orderer.example.com"
    FABRIC_PEER_ADDRESS               = "localhost:7051"
    FABRIC_PEER_LOCALMSPID            = "Org1MSP"
    FABRIC_PEER_MSPCONFIGPATH         = $org1AdminMsp
    FABRIC_PEER_TLS_ROOTCERT_FILE     = $peerTlsRootCert
    CORE_PEER_TLS_ENABLED             = "true"
    CORE_PEER_LOCALMSPID              = "Org1MSP"
    CORE_PEER_MSPCONFIGPATH           = $org1AdminMsp
    CORE_PEER_ADDRESS                 = "localhost:7051"
    CORE_PEER_TLS_ROOTCERT_FILE       = $peerTlsRootCert
    MODEL_DIR                         = "../skin-disease-classifier"
    TOP_K                             = "3"
}

Write-FabricEnvFile -Path $envFile -Values $values

Write-Host "Wrote Fabric env file: $envFile"
Write-Host "Next: run scripts/fabric/02-deploy-prediction-ledger.ps1"
