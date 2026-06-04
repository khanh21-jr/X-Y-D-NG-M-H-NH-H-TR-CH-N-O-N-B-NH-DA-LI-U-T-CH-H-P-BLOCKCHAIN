from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import Response

from app.ledger import (
    _fabric_direct_append_block,
    _fabric_direct_export_chain_csv,
    _fabric_direct_export_chain_json,
    _fabric_direct_get_chain,
    _fabric_direct_validate_chain,
)


app = FastAPI(title="Fabric Ledger Gateway", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    return {
        "status": "ok",
        "backend": "fabric-direct",
    }


@app.post("/ledger/append")
def append_block(block: Dict[str, Any]) -> Dict[str, Any]:
    stored = _fabric_direct_append_block(block)
    return stored.__dict__


@app.get("/ledger")
def ledger(limit: Optional[int] = 20) -> List[Dict[str, Any]]:
    return _fabric_direct_get_chain(limit=limit)


@app.get("/ledger/validate")
def ledger_validate() -> Dict[str, Any]:
    return _fabric_direct_validate_chain()


@app.get("/ledger/export.json")
def ledger_export_json(limit: Optional[int] = None) -> Response:
    payload = _fabric_direct_export_chain_json(limit=limit)
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.json"'},
    )


@app.get("/ledger/export.csv")
def ledger_export_csv(limit: Optional[int] = None) -> Response:
    payload = _fabric_direct_export_chain_csv(limit=limit)
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.csv"'},
    )

