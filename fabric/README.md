# Hyperledger Fabric Scaffold

Thu muc nay chua scaffold toi thieu de luu lich su du doan bang Fabric.

## Y tuong

- FastAPI app du doan hinh anh nhu cu.
- Sau khi co ket qua, app goi qua `FABRIC_LEDGER_API_URL`.
- Gateway API nay se noi voi Fabric network va chaincode `prediction-ledger`.
- Source cho gateway REST nam trong `fabric/gateway-api`.

## Client API ma app dang mong doi

- `POST /predictions`
- `GET /predictions?limit=N`
- `GET /predictions/validate`
- `GET /predictions/export/json?limit=N`
- `GET /predictions/export/csv?limit=N`

## Chaincode

Chaincode scaffold nam trong:

- `fabric/chaincode/prediction-ledger/index.js`

Chaincode luu:

- `source`
- `image_name`
- `image_sha256`
- `model_dir`
- `top_k`
- `predictions`
- `previous_hash`
- `hash`
- `signature` = tx id

## Cac buoc tiep theo

1. Dung Fabric test network toi thieu.
2. Deploy chaincode `prediction-ledger`.
3. Chay `fabric/gateway-api` voi cert, key va TLS root cert cua test-network.
4. Set `LEDGER_BACKEND=fabric` va `FABRIC_LEDGER_API_URL` trong `.env`.
