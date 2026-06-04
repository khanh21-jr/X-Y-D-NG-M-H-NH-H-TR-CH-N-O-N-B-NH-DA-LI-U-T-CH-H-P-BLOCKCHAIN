from __future__ import annotations

import argparse
import json
import os

from app.ledger import append_prediction
from app.model import load_image, load_model_bundle, predict_image, triage_prediction


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Skin disease image classifier")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--top-k", type=int, default=int(os.getenv("TOP_K", "3")), help="Number of predictions")
    parser.add_argument("--model-dir", default=os.getenv("MODEL_DIR"), help="Local model directory")
    parser.add_argument("--mode", choices=["predict", "triage"], default="predict", help="Inference mode")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = load_model_bundle(args.model_dir)
    image = load_image(args.image)
    with open(args.image, "rb") as f:
        image_bytes = f.read()
    if args.mode == "triage":
        result = triage_prediction(image, top_k=args.top_k, model_dir=str(bundle["model_dir"]))
        append_prediction(
            source="cli-triage",
            image_name=args.image,
            image_bytes=image_bytes,
            model_dir=str(bundle["model_dir"]),
            top_k=args.top_k,
            predictions=result["predictions"],
        )
        print(json.dumps({"image": args.image, "mode": args.mode, **result}, indent=2, ensure_ascii=False))
        return

    predictions = predict_image(image, top_k=args.top_k, model_dir=str(bundle["model_dir"]))
    append_prediction(
        source="cli",
        image_name=args.image,
        image_bytes=image_bytes,
        model_dir=str(bundle["model_dir"]),
        top_k=args.top_k,
        predictions=predictions,
    )
    print(json.dumps({"image": args.image, "mode": args.mode, "predictions": predictions}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
