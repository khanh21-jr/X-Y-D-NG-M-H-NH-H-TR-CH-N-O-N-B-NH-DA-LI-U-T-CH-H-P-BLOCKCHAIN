from __future__ import annotations

import base64
import io
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
import torch.nn.functional as F
from PIL import Image, ImageOps
from transformers import AutoImageProcessor, AutoModelForImageClassification

from app.labels import LABEL_MAP


def _default_model_dir() -> str:
    env_dir = os.getenv("MODEL_DIR")
    if env_dir:
        # Check if it's a local path or HF repo
        if Path(env_dir).exists() or "/" not in env_dir or "\\" in env_dir:
            return str(Path(env_dir).expanduser().resolve())
        return env_dir
        
    local_default = (Path(__file__).resolve().parents[1] / ".." / "skin-disease-classifier").resolve()
    if local_default.exists():
        return str(local_default)
        
    return "Anwarkh1/Skin_Cancer-Image_Classification"


@lru_cache(maxsize=1)
def load_model_bundle(model_dir: Optional[str] = None) -> Dict[str, Any]:
    resolved = model_dir if model_dir else _default_model_dir()
    
    is_local = Path(resolved).exists() or "\\" in resolved
    
    processor = AutoImageProcessor.from_pretrained(resolved, local_files_only=is_local)
    model = AutoModelForImageClassification.from_pretrained(resolved, local_files_only=is_local)
    model.eval()
    return {"processor": processor, "model": model, "model_dir": resolved}


def predict_image(image: Image.Image, top_k: int = 3, model_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    bundle = load_model_bundle(model_dir)
    processor = bundle["processor"]
    model = bundle["model"]
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0]

    id2label = model.config.id2label
    results = []
    k = min(top_k, probs.shape[-1])
    values, indices = torch.topk(probs, k=k)
    for score, idx in zip(values.tolist(), indices.tolist()):
        label_key = id2label.get(idx, str(idx))
        results.append(
            {
                "code": label_key,
                "label": LABEL_MAP.get(label_key, label_key),
                "score": float(score),
            }
        )
    return results


def _triage_views(image: Image.Image) -> List[Dict[str, Any]]:
    original = image.convert("RGB")
    return [
        {"name": "original", "image": original},
        {"name": "mirror", "image": ImageOps.mirror(original)},
        {"name": "autocontrast", "image": ImageOps.autocontrast(original)},
    ]


def _triage_risk(label_code: str, confidence: float, gap: float) -> Dict[str, str]:
    high_risk = {"MEL", "SCC", "BCC"}
    if label_code in high_risk and confidence >= 0.45:
        return {
            "level": "high",
            "title": "Nguy cơ cao",
            "recommendation": "Nên ưu tiên xem lại bởi bác sĩ da liễu hoặc đối chiếu thêm ảnh lâm sàng.",
        }
    if confidence < 0.45 or gap < 0.12:
        return {
            "level": "review",
            "title": "Cần xem lại",
            "recommendation": "Mẫu ảnh có độ tự tin thấp hoặc các lớp gần nhau, nên chụp lại hoặc đánh giá thủ công.",
        }
    return {
        "level": "low",
        "title": "Nguy cơ thấp hơn",
        "recommendation": "Kết quả có vẻ ổn định hơn, nhưng vẫn chỉ dùng cho nghiên cứu và hỗ trợ tham khảo.",
    }


def _class_rationale(label_code: str) -> str:
    rationales = {
        "AK": "Mô hình đang chú ý nhiều vào vùng bề mặt không đều và khu vực có tương phản cao, thường liên quan đến tổn thương sừng hóa.",
        "BCC": "Mô hình tập trung vào vùng rìa và các mảng có cấu trúc không đồng nhất, là dạng tín hiệu thường gặp ở tổn thương dạng nốt.",
        "BKL": "Mô hình ưu tiên vùng tăng sắc tố nhẹ và biên chưa thật đều, phù hợp với tổn thương lành tính tăng sắc tố.",
        "DF": "Mô hình chú ý vào một nốt nhỏ tương đối khu trú với tâm khá rõ và vùng xung quanh ít biến thiên hơn.",
        "MEL": "Mô hình tập trung vào các vùng có sắc tố đậm, biến thiên màu mạnh và biên không đều, đây là các tín hiệu cảnh báo quan trọng.",
        "NV": "Mô hình thấy cấu trúc màu tương đối đồng nhất và hình khối ổn định hơn, thường phù hợp với nốt ruồi lành tính.",
        "SCC": "Mô hình chú ý vào vùng tăng sừng và mảng tổn thương có biên rõ, thường xuất hiện ở tổn thương ác tính dạng biểu bì.",
        "VASC": "Mô hình tập trung vào các vùng đỏ/tím và cụm mạch máu nổi bật, gợi ý tổn thương mạch máu.",
    }
    return rationales.get(label_code, "Mô hình dựa vào các vùng có ảnh hưởng lớn trong ảnh để ra quyết định.")


def triage_prediction(
    image: Image.Image,
    top_k: int = 3,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    bundle = load_model_bundle(model_dir)
    processor = bundle["processor"]
    model = bundle["model"]

    views = _triage_views(image)
    view_probabilities = []
    for view in views:
        inputs = processor(images=view["image"], return_tensors="pt")
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        view_probabilities.append(probs)

    stacked = torch.stack(view_probabilities, dim=0)
    mean_probs = stacked.mean(dim=0)
    entropy = float((-(mean_probs * torch.log(mean_probs.clamp_min(1e-8))).sum()).item())

    id2label = model.config.id2label
    top_k = min(top_k, mean_probs.shape[-1])
    values, indices = torch.topk(mean_probs, k=top_k)
    predictions = []
    for probability, idx in zip(values.tolist(), indices.tolist()):
        code = id2label.get(idx, str(idx))
        predictions.append(
            {
                "code": code,
                "label": LABEL_MAP.get(code, code),
                "score": float(probability),
            }
        )

    predicted_index = int(indices[0].item())
    predicted_code = id2label.get(predicted_index, str(predicted_index))
    predicted_label = LABEL_MAP.get(predicted_code, predicted_code)
    confidence = float(values[0].item())
    gap = float((values[0] - values[1]).item()) if len(values) > 1 else confidence
    risk = _triage_risk(predicted_code, confidence, gap)

    return {
        "predicted_code": predicted_code,
        "predicted_label": predicted_label,
        "confidence": confidence,
        "gap": gap,
        "entropy": entropy,
        "risk_level": risk["level"],
        "risk_title": risk["title"],
        "recommendation": risk["recommendation"],
        "views_used": [view["name"] for view in views],
        "predictions": predictions,
        "note": "Chế độ triage dùng nhiều góc nhìn của cùng một ảnh để giảm phụ thuộc vào một lần suy luận duy nhất.",
    }


def explain_prediction(
    image: Image.Image,
    top_k: int = 3,
    model_dir: Optional[str] = None,
) -> Dict[str, Any]:
    bundle = load_model_bundle(model_dir)
    processor = bundle["processor"]
    model = bundle["model"]
    original = image.convert("RGB")
    inputs = processor(images=original, return_tensors="pt")
    pixel_values = inputs["pixel_values"].clone().detach().requires_grad_(True)

    model.zero_grad(set_to_none=True)
    outputs = model(pixel_values=pixel_values)
    probs = torch.softmax(outputs.logits, dim=-1)[0]

    target_index = int(torch.argmax(probs).item())
    target_score = float(probs[target_index].item())

    score = outputs.logits[0, target_index]
    score.backward()

    grads = pixel_values.grad.detach().abs().mean(dim=1)[0]
    grads = grads - grads.min()
    max_value = grads.max().clamp_min(1e-8)
    grads = grads / max_value
    grads = F.interpolate(
        grads.unsqueeze(0).unsqueeze(0),
        size=original.size[::-1],
        mode="bilinear",
        align_corners=False,
    )[0, 0]

    heatmap = (grads * 255.0).clamp(0, 255).byte().cpu()
    heatmap_image = Image.new("L", original.size)
    heatmap_image.putdata(heatmap.flatten().tolist())

    color_map = Image.merge("RGB", (
        heatmap_image.point(lambda p: min(255, int(p * 1.8))),
        heatmap_image.point(lambda p: int(p * 0.25)),
        heatmap_image.point(lambda p: int(p * 0.10)),
    ))
    overlay = Image.blend(original, color_map, alpha=0.42)

    buffer = io.BytesIO()
    overlay.save(buffer, format="PNG")
    overlay_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    id2label = model.config.id2label
    label_code = id2label.get(target_index, str(target_index))
    label_name = LABEL_MAP.get(label_code, label_code)
    top_k = min(top_k, probs.shape[-1])
    values, indices = torch.topk(probs, k=top_k)
    predictions = []
    for probability, idx in zip(values.tolist(), indices.tolist()):
        code = id2label.get(idx, str(idx))
        predictions.append(
            {
                "code": code,
                "label": LABEL_MAP.get(code, code),
                "score": float(probability),
            }
        )

    explanation = {
        "predicted_code": label_code,
        "predicted_label": label_name,
        "confidence": target_score,
        "rationale": _class_rationale(label_code),
        "overlay_png_base64": overlay_b64,
        "predictions": predictions,
        "focus_hint": "Vùng màu nóng trên bản đồ bên cạnh là phần ảnh có ảnh hưởng lớn nhất đến quyết định của model.",
        "note": "Đây là giải thích theo saliency map, mang tính hỗ trợ nghiên cứu chứ không thay thế chẩn đoán y khoa.",
    }
    return explanation


def load_image(path: str) -> Image.Image:
    return Image.open(path)
