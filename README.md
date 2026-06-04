# Skin Disease Classifier App

FastAPI app de chay model local `skin-disease-classifier` va luu lich su du doan tren Hyperledger Fabric.

## Tong quan

- App chay inference tu model local.
- Moi lan du doan se ghi mot block vao Fabric ledger.
- FastAPI main app noi qua mot gateway API nho chay local.
- `ledger` co 2 che do:
  - `local`: file JSON hash-chain nhu ban dau
  - `fabric-gateway`: main app goi gateway API, gateway nay ghi/doi voi Fabric

## Cau truc moi

- `app/main.py`: web app va API chinh
- `app/fabric_gateway_api.py`: gateway API noi truc tiep voi Fabric CLI
- `app/ledger.py`: logic luu ledger local, gateway, hoac Fabric direct
- `fabric/chaincode/prediction-ledger-go`: chaincode ghi block du doan
- `scripts/fabric/*`: bo script boot network, deploy chaincode, va start demo

## Yeu cau

- Python 3.11 hoac 3.12
- Docker Desktop
- `fabric-samples` da co san ben canh repo, hoac chi ro duong dan khi chay script 1
- `bash` co san tren may, vi `test-network` la script Bash

## Chay demo bang 3 lenh

Neu `fabric-samples` nam cung cap voi repo:

```powershell
.\scripts\fabric\01-bootstrap-network.ps1
.\scripts\fabric\02-deploy-prediction-ledger.ps1
.\scripts\fabric\03-start-demo.ps1
```

Neu `fabric-samples` nam o duong dan khac, truyen them tham so cho lenh 1:

```powershell
.\scripts\fabric\01-bootstrap-network.ps1 -FabricSamplesDir D:\fabric-samples
.\scripts\fabric\02-deploy-prediction-ledger.ps1
.\scripts\fabric\03-start-demo.ps1
```

Lenh 3 se:

- chay gateway API tren `http://127.0.0.1:8080`
- chay FastAPI app tren `http://127.0.0.1:8000`
- tu dong noi app chinh voi `.env.fabric`

## File env

- `.env.example`: mau cau hinh cho local va Fabric
- `.env.fabric`: file duoc script 1 tao ra sau khi test-network len

Gia tri quan trong:

- `LEDGER_BACKEND=fabric-gateway` cho main app
- `FABRIC_LEDGER_API_URL=http://127.0.0.1:8080`
- `FABRIC_CHAINCODE_NAME=prediction-ledger`
- `FABRIC_CHANNEL_NAME=mychannel`

## Chaincode

Chaincode `prediction-ledger` luu block JSON cua moi lan du doan. App chi gui metadata, khong gui anh raw len ledger.

Truong duoc luu:

- `index`
- `timestamp`
- `source`
- `image_name`
- `image_sha256`
- `model_dir`
- `top_k`
- `predictions`
- `previous_hash`
- `hash`
- `signature`

## API chinh

- `GET /`
- `POST /predict`
- `POST /triage`
- `POST /analyze`
- `POST /screen`
- `GET /ledger`
- `GET /ledger/ui`
- `GET /ledger/validate`
- `GET /ledger/export.json`
- `GET /ledger/export.csv`

## Gang luu y

- Demo nay phuc vu nghien cuu va trinh bay, khong thay the chan doan y khoa.
- Neu ban thay loi khong tim thay `peer`, `docker`, hoac `bash`, hay cai dat truoc khi chay script.
- Neu ban muon quay ve che do local, doi `LEDGER_BACKEND=local`.

