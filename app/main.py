from __future__ import annotations

import io
import os
from typing import Dict, Optional

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, Response
from PIL import Image

from app.ledger import append_prediction, export_chain_csv, export_chain_json, get_backend_name, get_chain, validate_chain
from app.model import explain_prediction, load_model_bundle, predict_image, triage_prediction
from app.schemas import ExplanationResponse, LedgerResponse, LedgerValidateResponse, PredictionBlockItem, PredictionItem, PredictionResponse, TriageResponse
from app.web import render_homepage, render_ledger_page

app = FastAPI(title="Skin Disease Classifier", version="1.0.0")


@app.get("/health")
def health() -> Dict[str, str]:
    try:
        bundle = load_model_bundle()
        return {
            "status": "ok",
            "model_dir": str(bundle.get("model_dir", "")),
            "ledger_backend": get_backend_name(),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "ledger_backend": get_backend_name(),
        }


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    try:
        bundle = load_model_bundle()
        model_dir = str(bundle.get("model_dir", ""))
        error = None
    except Exception as e:
        model_dir = "Chưa tìm thấy model"
        error = f"Lỗi khởi tạo model: {e}. Vui lòng kiểm tra lại cấu hình thư mục chứa model."

    html = render_homepage(model_dir=model_dir, ledger_blocks=get_chain(limit=5), error=error)
    return HTMLResponse(content=html)


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...), top_k: Optional[int] = None) -> PredictionResponse:
    bundle = load_model_bundle()
    raw = await file.read()
    image = Image.open(io.BytesIO(raw))
    effective_top_k = top_k or int(os.getenv("TOP_K", "3"))
    predictions = predict_image(image, top_k=effective_top_k)
    append_prediction(
        source="api",
        image_name=file.filename or "uploaded-image",
        image_bytes=raw,
        model_dir=str(bundle["model_dir"]),
        top_k=effective_top_k,
        predictions=predictions,
    )
    return PredictionResponse(
        model_dir=str(bundle["model_dir"]),
        top_k=effective_top_k,
        predictions=[PredictionItem(**item) for item in predictions],
    )


@app.post("/triage", response_model=TriageResponse)
async def triage(file: UploadFile = File(...), top_k: Optional[int] = None) -> TriageResponse:
    bundle = load_model_bundle()
    raw = await file.read()
    image = Image.open(io.BytesIO(raw))
    effective_top_k = top_k or int(os.getenv("TOP_K", "3"))
    result = triage_prediction(image, top_k=effective_top_k)
    append_prediction(
        source="triage",
        image_name=file.filename or "uploaded-image",
        image_bytes=raw,
        model_dir=str(bundle["model_dir"]),
        top_k=effective_top_k,
        predictions=result["predictions"],
    )
    return TriageResponse(
        model_dir=str(bundle["model_dir"]),
        top_k=effective_top_k,
        predicted_code=result["predicted_code"],
        predicted_label=result["predicted_label"],
        confidence=float(result["confidence"]),
        gap=float(result["gap"]),
        entropy=float(result["entropy"]),
        risk_level=str(result["risk_level"]),
        risk_title=str(result["risk_title"]),
        recommendation=str(result["recommendation"]),
        views_used=[str(item) for item in result["views_used"]],
        predictions=[PredictionItem(**item) for item in result["predictions"]],
        note=str(result["note"]),
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(file: UploadFile = File(...), top_k: int = Form(3)) -> HTMLResponse:
    bundle = load_model_bundle()
    try:
        raw = await file.read()
        image = Image.open(io.BytesIO(raw))
        predictions = predict_image(image, top_k=top_k)
        explanation = explain_prediction(image, top_k=top_k)
        append_prediction(
            source="web",
            image_name=file.filename or "uploaded-image",
            image_bytes=raw,
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            predictions=predictions,
        )
        html = render_homepage(
            predictions=predictions,
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            uploaded_image=raw,
            uploaded_mime_type=file.content_type or "image/jpeg",
            ledger_blocks=get_chain(limit=5),
            explanation=explanation,
        )
        return HTMLResponse(content=html)
    except Exception as exc:
        html = render_homepage(
            predictions=[],
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            error=f"Không thể xử lý ảnh: {exc}",
        )
        return HTMLResponse(content=html, status_code=400)


@app.post("/screen", response_class=HTMLResponse)
async def screen(file: UploadFile = File(...), top_k: int = Form(3)) -> HTMLResponse:
    bundle = load_model_bundle()
    try:
        raw = await file.read()
        image = Image.open(io.BytesIO(raw))
        result = triage_prediction(image, top_k=top_k)
        append_prediction(
            source="screen",
            image_name=file.filename or "uploaded-image",
            image_bytes=raw,
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            predictions=result["predictions"],
        )
        html = render_homepage(
            predictions=result["predictions"],
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            uploaded_image=raw,
            uploaded_mime_type=file.content_type or "image/jpeg",
            ledger_blocks=get_chain(limit=5),
            triage=result,
        )
        return HTMLResponse(content=html)
    except Exception as exc:
        html = render_homepage(
            predictions=[],
            model_dir=str(bundle["model_dir"]),
            top_k=top_k,
            error=f"Không thể xử lý ảnh: {exc}",
        )
        return HTMLResponse(content=html, status_code=400)


@app.post("/explain", response_model=ExplanationResponse)
async def explain(file: UploadFile = File(...), top_k: int = Form(3)) -> ExplanationResponse:
    raw = await file.read()
    image = Image.open(io.BytesIO(raw))
    explanation = explain_prediction(image, top_k=top_k)
    return ExplanationResponse(**explanation)


@app.get("/ledger", response_model=LedgerResponse)
def ledger(limit: int = 20) -> LedgerResponse:
    blocks = get_chain(limit=limit)
    validation = validate_chain()
    return LedgerResponse(
        valid=bool(validation.get("valid", False)),
        length=int(validation.get("length", len(blocks))),
        blocks=[PredictionBlockItem(**block) for block in blocks],
    )


@app.get("/ledger/ui", response_class=HTMLResponse)
def ledger_ui() -> HTMLResponse:
    blocks = get_chain(limit=None)
    validation = validate_chain()
    html = render_ledger_page(blocks=blocks, validation=validation)
    return HTMLResponse(content=html)


@app.get("/ledger/validate", response_model=LedgerValidateResponse)
def ledger_validate() -> LedgerValidateResponse:
    validation = validate_chain()
    return LedgerValidateResponse(
        valid=bool(validation.get("valid", False)),
        length=int(validation.get("length", 0)),
        broken_index=int(validation.get("broken_index", -1)),
        reason=str(validation.get("reason", "")),
    )


@app.get("/ledger/export.json")
def ledger_export_json() -> Response:
    payload = export_chain_json()
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.json"'},
    )


@app.get("/ledger/export.csv")
def ledger_export_csv() -> Response:
    payload = export_chain_csv()
    return Response(
        content=payload,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prediction_chain.csv"'},
    )
