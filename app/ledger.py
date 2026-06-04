from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


REPO_ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = REPO_ROOT / "data" / "prediction_chain.json"
DEFAULT_LEDGER_SECRET = "dev-only-change-me"


@dataclass
class PredictionBlock:
    index: int
    timestamp: str
    source: str
    image_name: str
    image_sha256: str
    model_dir: str
    top_k: int
    predictions: List[Dict[str, Any]]
    previous_hash: str
    hash: str
    signature: str


def _backend_name() -> str:
    raw = os.getenv("LEDGER_BACKEND", "local").strip().lower()
    aliases = {
        "fabric": "fabric-gateway",
        "gateway": "fabric-gateway",
        "remote": "fabric-gateway",
        "fabric-gateway": "fabric-gateway",
        "fabric-direct": "fabric-direct",
        "local": "local",
    }
    return aliases.get(raw, raw)

def get_backend_name() -> str:
    return _backend_name()

def _is_local_backend() -> bool:
    return _backend_name() == "local"


def _is_gateway_backend() -> bool:
    return _backend_name() == "fabric-gateway"


def _is_direct_backend() -> bool:
    return _backend_name() == "fabric-direct"


def _ensure_parent_dir() -> None:
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)


def _canonical_payload(block_data: Dict[str, Any]) -> str:
    return json.dumps(block_data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _block_hash(block_data: Dict[str, Any]) -> str:
    payload = _canonical_payload(block_data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _secret_key() -> bytes:
    return os.getenv("LEDGER_SECRET_KEY", DEFAULT_LEDGER_SECRET).encode("utf-8")


def _block_signature(block_data: Dict[str, Any]) -> str:
    payload = _canonical_payload(block_data).encode("utf-8")
    return hmac.new(_secret_key(), payload, hashlib.sha256).hexdigest()


def _image_digest(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _load_local_chain() -> List[Dict[str, Any]]:
    if not LEDGER_PATH.exists():
        return []
    with LEDGER_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        return []
    return data


def _save_local_chain(chain: List[Dict[str, Any]]) -> None:
    _ensure_parent_dir()
    tmp_path = LEDGER_PATH.with_suffix(".json.tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(chain, f, ensure_ascii=False, indent=2)
    tmp_path.replace(LEDGER_PATH)


def _sort_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def _sort_key(item: Dict[str, Any]) -> tuple[int, str, str]:
        try:
            index = int(item.get("index", 0))
        except (TypeError, ValueError):
            index = 0
        return (index, str(item.get("timestamp", "")), str(item.get("hash", "")))

    return sorted(blocks, key=_sort_key)


def _fabric_samples_dir() -> Path:
    raw = os.getenv("FABRIC_SAMPLES_DIR")
    if raw:
        return Path(raw)
    return REPO_ROOT.parent / "fabric-samples"


def _fabric_test_network_dir() -> Path:
    raw = os.getenv("FABRIC_TEST_NETWORK_DIR")
    if raw:
        return Path(raw)
    return _fabric_samples_dir() / "test-network"


def _fabric_chaincode_name() -> str:
    return os.getenv("FABRIC_CHAINCODE_NAME", "prediction-ledger")


def _fabric_channel_name() -> str:
    return os.getenv("FABRIC_CHANNEL_NAME", "mychannel")


def _fabric_api_url() -> str:
    return os.getenv("FABRIC_LEDGER_API_URL", "http://127.0.0.1:8080").rstrip("/")


def _fabric_bin_dir() -> Optional[Path]:
    raw = os.getenv("FABRIC_BIN_DIR")
    if not raw:
        return None
    return Path(raw)


def _fabric_env() -> Dict[str, str]:
    env = os.environ.copy()
    fabric_bin_dir = _fabric_bin_dir()
    if fabric_bin_dir is not None:
        env["PATH"] = f"{fabric_bin_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def _fabric_command(args: List[str], *, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["peer", *args],
        cwd=str(cwd),
        env=_fabric_env(),
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            "Fabric CLI command failed.\n"
            f"Command: peer {' '.join(args)}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result


def _fabric_extract_query_payload(stdout: str) -> str:
    text = stdout.strip()
    for marker in ("Query Result:", "Result:"):
        if marker in text:
            text = text.split(marker, 1)[1].strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for candidate in reversed(lines):
        if candidate.startswith("[") or candidate.startswith("{"):
            return candidate
    return text


def _fabric_invoke(function_name: str, args: List[str]) -> None:
    network_dir = _fabric_test_network_dir()
    orderer_address = os.getenv("FABRIC_ORDERER_ADDRESS", "localhost:7050")
    orderer_ca = os.getenv("FABRIC_ORDERER_CA", "")
    orderer_tls_hostname = os.getenv("FABRIC_ORDERER_TLS_HOSTNAME_OVERRIDE", "orderer.example.com")
    if not orderer_ca:
        raise RuntimeError("FABRIC_ORDERER_CA is required for Fabric invoke mode.")

    payload = json.dumps({"function": function_name, "Args": args}, ensure_ascii=False)
    command = [
        "chaincode",
        "invoke",
        "-o",
        orderer_address,
        "--ordererTLSHostnameOverride",
        orderer_tls_hostname,
        "--tls",
        "--cafile",
        orderer_ca,
        "-C",
        _fabric_channel_name(),
        "-n",
        _fabric_chaincode_name(),
        "-c",
        payload,
        "--waitForEvent",
        "--waitForEventTimeout",
        "60s",
    ]
    _fabric_command(command, cwd=network_dir)


def _fabric_query(function_name: str, args: List[str]) -> Any:
    network_dir = _fabric_test_network_dir()
    payload = json.dumps({"function": function_name, "Args": args}, ensure_ascii=False)
    result = _fabric_command(
        [
            "chaincode",
            "query",
            "-C",
            _fabric_channel_name(),
            "-n",
            _fabric_chaincode_name(),
            "-c",
            payload,
        ],
        cwd=network_dir,
    )
    query_payload = _fabric_extract_query_payload(result.stdout)
    if not query_payload:
        return None
    return json.loads(query_payload)


def _fabric_direct_append_block(block_data: Dict[str, Any]) -> PredictionBlock:
    _fabric_invoke("RecordBlock", [json.dumps(block_data, ensure_ascii=False)])
    return PredictionBlock(**block_data)


def _fabric_direct_get_chain(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    raw = _fabric_query("ListBlocks", [])
    if not isinstance(raw, list):
        return []
    blocks = [item for item in raw if isinstance(item, dict)]
    blocks = _sort_blocks(blocks)
    if limit is None or limit >= len(blocks):
        return blocks
    return blocks[-limit:]


def _fabric_direct_validate_chain() -> Dict[str, Any]:
    chain = _fabric_direct_get_chain(limit=None)
    for i, block in enumerate(chain):
        expected_prev = "0" * 64 if i == 0 else chain[i - 1]["hash"]
        payload = {k: block[k] for k in block if k not in ("hash", "signature")}
        expected_hash = _block_hash(payload)
        expected_signature = _block_signature({**payload, "hash": expected_hash})
        if block.get("previous_hash") != expected_prev:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "broken-link"}
        if block.get("hash") != expected_hash:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "hash-mismatch"}
        if block.get("signature") != expected_signature:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "signature-mismatch"}
    return {"valid": True, "length": len(chain)}


def _fabric_direct_export_chain_json(limit: Optional[int] = None) -> str:
    return json.dumps(_fabric_direct_get_chain(limit=limit), ensure_ascii=False, indent=2)


def _fabric_direct_export_chain_csv(limit: Optional[int] = None) -> str:
    chain = _fabric_direct_get_chain(limit=limit)
    output = io.StringIO()
    fieldnames = [
        "index",
        "timestamp",
        "source",
        "image_name",
        "image_sha256",
        "model_dir",
        "top_k",
        "predictions",
        "previous_hash",
        "hash",
        "signature",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for block in chain:
        row = dict(block)
        row["predictions"] = json.dumps(row.get("predictions", []), ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue()


def _remote_json_request(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Any:
    base_url = _fabric_api_url()
    url = f"{base_url}{path}"
    body = None
    headers = {}
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=120) as response:
            data = response.read().decode("utf-8")
            content_type = response.headers.get("Content-Type", "")
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"Could not reach Fabric ledger API at {url}: {exc}") from exc

    if "application/json" in content_type or data.lstrip().startswith(("{", "[")):
        return json.loads(data)
    return data


def _remote_append_block(block_data: Dict[str, Any]) -> PredictionBlock:
    result = _remote_json_request("POST", "/ledger/append", payload=block_data)
    if isinstance(result, dict) and "block" in result and isinstance(result["block"], dict):
        return PredictionBlock(**result["block"])
    if isinstance(result, dict):
        return PredictionBlock(**result)
    return PredictionBlock(**block_data)


def _remote_get_chain(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    query = f"?{urlencode({'limit': limit})}" if limit is not None else ""
    result = _remote_json_request("GET", f"/ledger{query}")
    if not isinstance(result, list):
        return []
    blocks = [item for item in result if isinstance(item, dict)]
    return _sort_blocks(blocks)


def _remote_validate_chain() -> Dict[str, Any]:
    result = _remote_json_request("GET", "/ledger/validate")
    if isinstance(result, dict):
        return result
    return {"valid": False, "length": 0, "reason": "invalid-response"}


def _remote_export_chain_json(limit: Optional[int] = None) -> str:
    query = f"?{urlencode({'limit': limit})}" if limit is not None else ""
    result = _remote_json_request("GET", f"/ledger/export.json{query}")
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False, indent=2)


def _remote_export_chain_csv(limit: Optional[int] = None) -> str:
    query = f"?{urlencode({'limit': limit})}" if limit is not None else ""
    result = _remote_json_request("GET", f"/ledger/export.csv{query}")
    if isinstance(result, str):
        return result
    return str(result)


def _build_block_payload(
    *,
    source: str,
    image_name: str,
    image_bytes: bytes,
    model_dir: str,
    top_k: int,
    predictions: List[Dict[str, Any]],
    chain: List[Dict[str, Any]],
) -> Dict[str, Any]:
    previous_hash = chain[-1]["hash"] if chain else "0" * 64
    block_payload = {
        "index": len(chain),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "source": source,
        "image_name": image_name,
        "image_sha256": _image_digest(image_bytes),
        "model_dir": model_dir,
        "top_k": top_k,
        "predictions": predictions,
        "previous_hash": previous_hash,
    }
    block_hash = _block_hash(block_payload)
    signature = _block_signature({**block_payload, "hash": block_hash})
    return {**block_payload, "hash": block_hash, "signature": signature}


def append_prediction(
    *,
    source: str,
    image_name: str,
    image_bytes: bytes,
    model_dir: str,
    top_k: int,
    predictions: List[Dict[str, Any]],
) -> PredictionBlock:
    if _is_gateway_backend():
        chain = _remote_get_chain(limit=None)
        block_payload = _build_block_payload(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
            chain=chain,
        )
        return _remote_append_block(block_payload)

    if _is_direct_backend():
        chain = _fabric_direct_get_chain(limit=None)
        block_payload = _build_block_payload(
            source=source,
            image_name=image_name,
            image_bytes=image_bytes,
            model_dir=model_dir,
            top_k=top_k,
            predictions=predictions,
            chain=chain,
        )
        return _fabric_direct_append_block(block_payload)

    chain = _load_local_chain()
    block_payload = _build_block_payload(
        source=source,
        image_name=image_name,
        image_bytes=image_bytes,
        model_dir=model_dir,
        top_k=top_k,
        predictions=predictions,
        chain=chain,
    )
    block = PredictionBlock(**block_payload)
    chain.append(asdict(block))
    _save_local_chain(chain)
    return block


def get_chain(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if _is_gateway_backend():
        return _remote_get_chain(limit=limit)
    if _is_direct_backend():
        return _fabric_direct_get_chain(limit=limit)

    chain = _load_local_chain()
    if limit is None or limit >= len(chain):
        return chain
    return chain[-limit:]


def validate_chain() -> Dict[str, Any]:
    if _is_gateway_backend():
        return _remote_validate_chain()
    if _is_direct_backend():
        return _fabric_direct_validate_chain()

    chain = _load_local_chain()
    for i, block in enumerate(chain):
        expected_prev = "0" * 64 if i == 0 else chain[i - 1]["hash"]
        payload = {k: block[k] for k in block if k not in ("hash", "signature")}
        expected_hash = _block_hash(payload)
        expected_signature = _block_signature({**payload, "hash": expected_hash})
        if block.get("previous_hash") != expected_prev:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "broken-link"}
        if block.get("hash") != expected_hash:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "hash-mismatch"}
        if block.get("signature") != expected_signature:
            return {"valid": False, "broken_index": i, "length": len(chain), "reason": "signature-mismatch"}
    return {"valid": True, "length": len(chain)}


def export_chain_json(limit: Optional[int] = None) -> str:
    if _is_gateway_backend():
        return _remote_export_chain_json(limit=limit)
    if _is_direct_backend():
        return _fabric_direct_export_chain_json(limit=limit)
    return json.dumps(get_chain(limit=limit), ensure_ascii=False, indent=2)


def export_chain_csv(limit: Optional[int] = None) -> str:
    if _is_gateway_backend():
        return _remote_export_chain_csv(limit=limit)
    if _is_direct_backend():
        return _fabric_direct_export_chain_csv(limit=limit)

    chain = get_chain(limit=limit)
    output = io.StringIO()
    fieldnames = [
        "index",
        "timestamp",
        "source",
        "image_name",
        "image_sha256",
        "model_dir",
        "top_k",
        "predictions",
        "previous_hash",
        "hash",
        "signature",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for block in chain:
        row = dict(block)
        row["predictions"] = json.dumps(row.get("predictions", []), ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue()
