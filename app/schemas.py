from typing import List

from pydantic import BaseModel


class PredictionItem(BaseModel):
    code: str
    label: str
    score: float


class PredictionResponse(BaseModel):
    model_dir: str
    top_k: int
    predictions: List[PredictionItem]


class TriageResponse(BaseModel):
    model_dir: str
    top_k: int
    predicted_code: str
    predicted_label: str
    confidence: float
    gap: float
    entropy: float
    risk_level: str
    risk_title: str
    recommendation: str
    views_used: List[str]
    predictions: List[PredictionItem]
    note: str


class PredictionBlockItem(BaseModel):
    index: int
    timestamp: str
    source: str
    image_name: str
    image_sha256: str
    model_dir: str
    top_k: int
    predictions: List[PredictionItem]
    previous_hash: str
    hash: str
    signature: str


class LedgerResponse(BaseModel):
    valid: bool
    length: int
    blocks: List[PredictionBlockItem]


class LedgerValidateResponse(BaseModel):
    valid: bool
    length: int
    broken_index: int = -1
    reason: str = ""


class ExplanationResponse(BaseModel):
    predicted_code: str
    predicted_label: str
    confidence: float
    rationale: str
    overlay_png_base64: str
    predictions: List[PredictionItem]
    focus_hint: str
    note: str
