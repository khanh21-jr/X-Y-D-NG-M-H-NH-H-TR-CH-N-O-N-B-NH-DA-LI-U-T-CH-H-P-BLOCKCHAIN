from __future__ import annotations

import base64
from html import escape
from typing import Any, Dict, List, Optional


def _render_prediction_rows(predictions: List[Dict[str, Any]]) -> str:
    if not predictions:
        return """
        <div class="empty-state">
          <h2>Chua co ket qua</h2>
          <p>Hay tai mot anh da lieu len de xem du doan.</p>
        </div>
        """

    rows = []
    for item in predictions:
        code = escape(str(item.get("code", "")))
        label = escape(str(item.get("label", "")))
        score = float(item.get("score", 0.0))
        rows.append(
            f"""
            <div class="result-row">
              <div>
                <div class="result-code">{code}</div>
                <div class="result-label">{label}</div>
              </div>
              <div class="result-score">{score:.2%}</div>
            </div>
            """
        )
    return "\n".join(rows)


def _render_ledger_rows(blocks: List[Dict[str, Any]]) -> str:
    if not blocks:
        return '<div class="empty-state">Chua co block nao trong so cai.</div>'

    rows = []
    for block in blocks:
        rows.append(
            f"""
            <article class="ledger-row">
              <div class="ledger-main">
                <div class="ledger-title">#{escape(str(block.get("index", "")))} - {escape(str(block.get("image_name", "")))}</div>
                <div class="ledger-meta">
                  {escape(str(block.get("timestamp", "")))} | {escape(str(block.get("source", "")))} | top-k {escape(str(block.get("top_k", "")))}
                </div>
                <div class="ledger-meta">
                  hash {escape(str(block.get("hash", "")))[:16]}... | signature {escape(str(block.get("signature", "")))[:16]}...
                </div>
              </div>
              <div class="ledger-score">{len(block.get("predictions", []))} ket qua</div>
            </article>
            """
        )
    return "\n".join(rows)


def _render_explanation_card(explanation: Optional[Dict[str, Any]]) -> str:
    if not explanation:
        return """
        <section class="card">
          <div class="card-inner">
            <div class="section-title">Giai thich AI</div>
            <div class="empty-state">Sau khi phan tich, phan nay se hien heatmap va ly do model du doan.</div>
          </div>
        </section>
        """

    overlay_html = ""
    overlay_b64 = explanation.get("overlay_png_base64")
    if overlay_b64:
        overlay_html = f"""
        <img class="explain-image" src="data:image/png;base64,{overlay_b64}" alt="Saliency heatmap" />
        """

    return f"""
    <section class="card">
      <div class="card-inner">
        <div class="section-title">Giai thich AI</div>
        <div class="muted">Bang do nhiet duoi day cho thay vung nao anh huong manh den quyet dinh cua model.</div>
        {overlay_html}
        <div class="explain-summary">
          <div class="explain-label">Du doan chinh</div>
          <div class="explain-value">{escape(str(explanation.get("predicted_label", "")))}</div>
          <div class="explain-meta">Do tin cay: {float(explanation.get("confidence", 0.0)):.2%}</div>
        </div>
        <div class="explain-rationale">{escape(str(explanation.get("rationale", "")))}</div>
        <div class="explain-note">{escape(str(explanation.get("focus_hint", "")))}</div>
        <div class="explain-note">{escape(str(explanation.get("note", "")))}</div>
      </div>
    </section>
    """


def _render_triage_card(triage: Optional[Dict[str, Any]]) -> str:
    if not triage:
        return """
        <section class="card">
          <div class="card-inner">
            <div class="section-title">Che do sang loc</div>
            <div class="empty-state">Chuyen sang /screen de xem ket qua triage dua tren nhieu goc nhin cua cung mot anh.</div>
          </div>
        </section>
        """

    views_used = ", ".join(escape(str(item)) for item in triage.get("views_used", []))
    confidence = float(triage.get("confidence", 0.0))
    gap = float(triage.get("gap", 0.0))
    entropy = float(triage.get("entropy", 0.0))

    rows = []
    for item in triage.get("predictions", []):
        rows.append(
            f"""
            <div class="result-row">
              <div>
                <div class="result-code">{escape(str(item.get("code", "")))}</div>
                <div class="result-label">{escape(str(item.get("label", "")))}</div>
              </div>
              <div class="result-score">{float(item.get("score", 0.0)):.2%}</div>
            </div>
            """
        )

    return f"""
    <section class="card">
      <div class="card-inner">
        <div class="section-title">Che do sang loc</div>
        <div class="muted">Day la luong khac voi /analyze: thay vi mot lan du doan, he thong lay trung binh nhieu goc nhin de giam dao dong.</div>
        <div class="triage-summary">
          <div class="triage-label">{escape(str(triage.get("risk_title", "")))}</div>
          <div class="triage-value">{escape(str(triage.get("predicted_label", "")))}</div>
          <div class="triage-meta">Do tin cay {confidence:.2%} | do lech top-1/top-2 {gap:.2%} | entropy {entropy:.3f}</div>
          <div class="triage-note">{escape(str(triage.get("recommendation", "")))}</div>
          <div class="triage-note">Views: {views_used}</div>
          <div class="triage-note">{escape(str(triage.get("note", "")))}</div>
        </div>
        {''.join(rows)}
      </div>
    </section>
    """


def render_homepage(
    *,
    predictions: Optional[List[Dict[str, Any]]] = None,
    triage: Optional[Dict[str, Any]] = None,
    model_dir: Optional[str] = None,
    top_k: int = 3,
    uploaded_image: Optional[bytes] = None,
    uploaded_mime_type: str = "image/jpeg",
    ledger_blocks: Optional[List[Dict[str, Any]]] = None,
    explanation: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
) -> str:
    preview_html = ""
    if uploaded_image:
        encoded = base64.b64encode(uploaded_image).decode("ascii")
        preview_html = f"""
        <section class="card preview-card">
          <div class="section-title">Anh da tai len</div>
          <img class="preview-image" src="data:{escape(uploaded_mime_type)};base64,{encoded}" alt="Uploaded skin lesion" />
        </section>
        """

    predictions_html = _render_prediction_rows(predictions or [])
    triage_html = _render_triage_card(triage)
    ledger_html = ""
    if ledger_blocks is not None:
        ledger_html = f"""
        <section class="card">
          <div class="section-title">Lich su du doan gan nhat</div>
          {_render_ledger_rows(ledger_blocks[-5:][::-1])}
        </section>
        """
    explain_html = _render_explanation_card(explanation)

    error_html = f'<div class="error-box">{escape(error)}</div>' if error else ""
    model_html = escape(model_dir or "local model")
    return f"""
    <!doctype html>
    <html lang="vi">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Skin Disease Classifier</title>
      <style>
        :root {{
          --bg: #07111f;
          --bg2: #0d1730;
          --card: rgba(12, 19, 36, 0.84);
          --card-strong: rgba(14, 24, 43, 0.96);
          --line: rgba(255,255,255,0.10);
          --text: #ecf4ff;
          --muted: #97abc6;
          --accent: #64d2ff;
          --accent2: #8c6dff;
          --good: #47d18c;
          --danger: #ff6b7a;
        }}
        * {{ box-sizing: border-box; }}
        html, body {{ min-height: 100%; }}
        body {{
          margin: 0;
          color: var(--text);
          font-family: "Segoe UI", Tahoma, Arial, sans-serif;
          background:
            radial-gradient(circle at 15% 10%, rgba(100, 210, 255, 0.18), transparent 24%),
            radial-gradient(circle at 85% 16%, rgba(140, 109, 255, 0.16), transparent 22%),
            linear-gradient(160deg, var(--bg), var(--bg2));
        }}
        .shell {{
          max-width: 1240px;
          margin: 0 auto;
          padding: 28px 20px 40px;
        }}
        .hero {{
          position: relative;
          overflow: hidden;
          border: 1px solid var(--line);
          border-radius: 30px;
          background: linear-gradient(135deg, rgba(8, 16, 31, 0.94), rgba(17, 31, 57, 0.9));
          padding: 30px 32px;
          box-shadow: 0 24px 80px rgba(0,0,0,0.32);
        }}
        .hero::after {{
          content: "";
          position: absolute;
          inset: 0;
          background:
            radial-gradient(circle at 88% 28%, rgba(100,210,255,0.30), transparent 12%),
            radial-gradient(circle at 76% 86%, rgba(140,109,255,0.28), transparent 10%);
          pointer-events: none;
        }}
        .eyebrow {{
          position: relative;
          z-index: 1;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--accent);
          font-size: 12px;
          font-weight: 700;
        }}
        .hero h1 {{
          position: relative;
          z-index: 1;
          margin: 12px 0 0;
          max-width: 840px;
          font-size: clamp(34px, 5vw, 58px);
          line-height: 0.96;
        }}
        .hero p {{
          position: relative;
          z-index: 1;
          max-width: 740px;
          margin: 16px 0 0;
          color: var(--muted);
          font-size: 16px;
          line-height: 1.7;
        }}
        .stats {{
          position: relative;
          z-index: 1;
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 18px;
        }}
        .pill, .link-pill {{
          display: inline-flex;
          align-items: center;
          padding: 9px 12px;
          border-radius: 999px;
          border: 1px solid var(--line);
          background: rgba(255,255,255,0.05);
          color: var(--muted);
          font-size: 13px;
          text-decoration: none;
        }}
        .link-pill {{
          color: var(--accent);
          font-weight: 700;
        }}
        .content {{
          display: grid;
          grid-template-columns: minmax(330px, 420px) minmax(0, 1fr);
          gap: 18px;
          margin-top: 18px;
          align-items: start;
        }}
        .left-stack, .right-stack {{
          display: grid;
          gap: 18px;
        }}
        .card {{
          border: 1px solid var(--line);
          background: var(--card);
          border-radius: 26px;
          box-shadow: 0 18px 60px rgba(0,0,0,0.24);
          overflow: hidden;
        }}
        .card-inner {{
          padding: 22px;
        }}
        .section-title {{
          font-size: 18px;
          font-weight: 700;
          margin: 0 0 10px;
        }}
        .muted {{
          color: var(--muted);
          line-height: 1.6;
          font-size: 14px;
        }}
        .form {{
          display: grid;
          gap: 14px;
          margin-top: 18px;
        }}
        .field {{
          display: grid;
          gap: 8px;
        }}
        label {{
          font-size: 14px;
          color: var(--muted);
        }}
        input[type="file"], input[type="number"] {{
          width: 100%;
          background: rgba(255,255,255,0.05);
          color: var(--text);
          border: 1px solid rgba(255,255,255,0.10);
          border-radius: 14px;
          padding: 12px 14px;
          outline: none;
        }}
        input[type="file"]::file-selector-button {{
          margin-right: 12px;
          border: 0;
          background: linear-gradient(135deg, var(--accent), var(--accent2));
          color: white;
          padding: 10px 14px;
          border-radius: 12px;
          cursor: pointer;
        }}
        .btn {{
          border: 0;
          border-radius: 14px;
          padding: 13px 18px;
          font-weight: 700;
          color: #03101c;
          background: linear-gradient(135deg, var(--accent), #c6efff);
          cursor: pointer;
        }}
        .btn:hover {{
          filter: brightness(1.03);
        }}
        .error-box {{
          margin-top: 14px;
          padding: 12px 14px;
          border-radius: 14px;
          background: rgba(255,107,122,0.10);
          color: #ffbcc4;
          border: 1px solid rgba(255,107,122,0.25);
        }}
        .preview-image {{
          display: block;
          width: 100%;
          max-height: 420px;
          object-fit: contain;
          background: var(--card-strong);
          border-top: 1px solid rgba(255,255,255,0.07);
        }}
        .explain-image {{
          display: block;
          width: 100%;
          max-height: 420px;
          object-fit: contain;
          margin-top: 14px;
          border-radius: 18px;
          border: 1px solid rgba(255,255,255,0.08);
          background: var(--card-strong);
        }}
        .explain-summary {{
          margin-top: 14px;
          padding: 14px 16px;
          border-radius: 18px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.08);
        }}
        .explain-label {{
          color: var(--accent);
          font-size: 12px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          font-weight: 700;
        }}
        .explain-value {{
          margin-top: 6px;
          font-size: 22px;
          font-weight: 800;
        }}
        .explain-meta, .explain-note, .explain-rationale {{
          margin-top: 8px;
          color: var(--muted);
          font-size: 14px;
          line-height: 1.6;
        }}
        .triage-summary {{
          margin-top: 14px;
          padding: 14px 16px;
          border-radius: 18px;
          background: linear-gradient(135deg, rgba(100, 210, 255, 0.10), rgba(140, 109, 255, 0.10));
          border: 1px solid rgba(255,255,255,0.08);
        }}
        .triage-label {{
          color: var(--accent);
          font-size: 12px;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          font-weight: 700;
        }}
        .triage-value {{
          margin-top: 6px;
          font-size: 22px;
          font-weight: 800;
        }}
        .triage-meta, .triage-note {{
          margin-top: 8px;
          color: var(--muted);
          font-size: 14px;
          line-height: 1.6;
        }}
        .result-row, .ledger-row {{
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          padding: 16px 0;
          border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .result-row:first-child, .ledger-row:first-child {{
          border-top: 0;
          padding-top: 0;
        }}
        .result-code, .ledger-title {{
          color: var(--accent);
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }}
        .result-label {{
          margin-top: 6px;
          font-size: 17px;
          font-weight: 700;
        }}
        .result-score, .ledger-score {{
          color: var(--good);
          font-weight: 800;
          white-space: nowrap;
        }}
        .ledger-meta {{
          color: var(--muted);
          margin-top: 6px;
          font-size: 13px;
          word-break: break-all;
        }}
        .empty-state {{
          border: 1px dashed rgba(255,255,255,0.14);
          border-radius: 18px;
          padding: 24px;
          color: var(--muted);
          background: rgba(255,255,255,0.03);
        }}
        .footer-note {{
          margin-top: 16px;
          color: var(--muted);
          font-size: 13px;
          line-height: 1.6;
        }}
        @media (max-width: 980px) {{
          .content {{
            grid-template-columns: 1fr;
          }}
          .hero {{
            padding: 24px;
          }}
          .card-inner {{
            padding: 18px;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="shell">
        <section class="hero">
          <div class="eyebrow">Skin Disease Classifier</div>
          <h1>Upload anh va nhan du doan nhanh tu model local</h1>
          <p>Giao dien da duoc can lai de co mot cot phu cho form va mot cot chinh cho anh du doan, ket qua, cung nhu lich su blockchain cua cac lan phan tich truoc do.</p>
          <div class="stats">
            <span class="pill">{model_html}</span>
            <span class="pill">8 lop benh</span>
            <span class="pill">224 x 224 input</span>
            <a class="link-pill" href="/ledger/ui">Xem toan bo lich su</a>
            <a class="link-pill" href="/docs">API docs</a>
          </div>
        </section>

        <main class="content">
          <section class="left-stack">
            <section class="card">
              <div class="card-inner">
                <div class="section-title">Tai anh len</div>
                <div class="muted">Chon anh ton thuong da, he thong se tra ve top-k du doan tu model local.</div>
                <form class="form" action="/analyze" method="post" enctype="multipart/form-data">
                  <div class="field">
                    <label for="file">Anh dau vao</label>
                    <input id="file" name="file" type="file" accept="image/*" required />
                  </div>
                  <div class="field">
                    <label for="top_k">Top K</label>
                    <input id="top_k" name="top_k" type="number" min="1" max="8" value="{int(top_k)}" />
                  </div>
                  <button class="btn" type="submit">Phan tich anh</button>
                </form>
                {error_html}
                <div class="footer-note">Ket qua chi dung cho nghien cuu va demo, khong thay the chan doan y khoa.</div>
              </div>
            </section>

            <section class="card">
              <div class="card-inner">
                <div class="section-title">Sang loc 2 buoc</div>
                <div class="muted">Che do moi se lay trung binh 3 goc nhin cua cung mot anh, sau do gan nhan nguy co va khuyen nghi xem lai.</div>
                <form class="form" action="/screen" method="post" enctype="multipart/form-data">
                  <div class="field">
                    <label for="screen_file">Anh dau vao</label>
                    <input id="screen_file" name="file" type="file" accept="image/*" required />
                  </div>
                  <div class="field">
                    <label for="screen_top_k">Top K</label>
                    <input id="screen_top_k" name="top_k" type="number" min="1" max="8" value="{int(top_k)}" />
                  </div>
                  <button class="btn" type="submit">Chay sang loc</button>
                </form>
              </div>
            </section>

            <section class="card">
              <div class="card-inner">
                <div class="section-title">Thong tin</div>
                <div class="muted">
                  Ledger nay luu block theo hash-chain va co the chay local hoac qua Fabric gateway de phat hien sua doi.
                  Ban co the xem validation tai /ledger/validate va tai du lieu tai /ledger/export.json hoac /ledger/export.csv.
                </div>
              </div>
            </section>
          </section>

          <section class="right-stack">
            {preview_html}
            {explain_html}
            {triage_html}
            <section class="card">
              <div class="card-inner">
                <div class="section-title">Ket qua</div>
                {predictions_html}
              </div>
            </section>
            {ledger_html}
          </section>
        </main>
      </div>
    </body>
    </html>
    """


def render_ledger_page(
    *,
    blocks: Optional[List[Dict[str, Any]]] = None,
    validation: Optional[Dict[str, Any]] = None,
) -> str:
    blocks = blocks or []
    validation = validation or {"valid": False, "length": 0}
    valid_text = "Hop le" if validation.get("valid") else "Khong hop le"
    valid_class = "good" if validation.get("valid") else "bad"
    broken_index = validation.get("broken_index", -1)
    reason = validation.get("reason", "")

    return f"""
    <!doctype html>
    <html lang="vi">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>Ledger History</title>
      <style>
        body {{
          margin: 0;
          font-family: "Segoe UI", Tahoma, Arial, sans-serif;
          color: #ecf4ff;
          background: linear-gradient(160deg, #07111f, #0d1730);
        }}
        .wrap {{
          max-width: 1240px;
          margin: 0 auto;
          padding: 28px 20px 40px;
        }}
        .hero, .card {{
          border: 1px solid rgba(255,255,255,0.10);
          background: rgba(12,19,36,0.84);
          border-radius: 26px;
          box-shadow: 0 18px 60px rgba(0,0,0,0.24);
        }}
        .hero {{
          padding: 26px 28px;
        }}
        h1 {{
          margin: 0;
          font-size: clamp(30px, 4vw, 48px);
        }}
        .muted {{
          margin-top: 10px;
          color: #97abc6;
          line-height: 1.6;
        }}
        .actions {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 16px;
        }}
        .btn {{
          display: inline-block;
          text-decoration: none;
          border-radius: 14px;
          padding: 12px 16px;
          color: #03101c;
          background: linear-gradient(135deg, #64d2ff, #c6efff);
          font-weight: 700;
        }}
        .btn.secondary {{
          background: rgba(255,255,255,0.08);
          color: #ecf4ff;
          border: 1px solid rgba(255,255,255,0.10);
        }}
        .status {{
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 18px;
        }}
        .pill {{
          display: inline-flex;
          padding: 8px 12px;
          border-radius: 999px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.10);
          color: #97abc6;
        }}
        .pill.good {{ color: #47d18c; }}
        .pill.bad {{ color: #ff6b7a; }}
        .warning {{
          margin-top: 12px;
          padding: 12px 14px;
          border-radius: 14px;
          border: 1px solid rgba(255,107,122,0.25);
          background: rgba(255,107,122,0.10);
          color: #ffbcc4;
        }}
        .stack {{
          display: grid;
          gap: 18px;
          margin-top: 18px;
        }}
        .card {{
          padding: 22px;
        }}
        .section-title {{
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 10px;
        }}
        .ledger-row {{
          display: flex;
          justify-content: space-between;
          gap: 16px;
          align-items: center;
          padding: 16px 0;
          border-top: 1px solid rgba(255,255,255,0.08);
        }}
        .ledger-row:first-child {{
          border-top: 0;
          padding-top: 0;
        }}
        .ledger-title {{
          color: #64d2ff;
          font-size: 13px;
          font-weight: 700;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }}
        .ledger-meta {{
          color: #97abc6;
          margin-top: 6px;
          font-size: 13px;
          word-break: break-all;
        }}
        .ledger-score {{
          color: #47d18c;
          font-weight: 800;
          white-space: nowrap;
        }}
        .empty-state {{
          border: 1px dashed rgba(255,255,255,0.14);
          border-radius: 18px;
          padding: 24px;
          color: #97abc6;
          background: rgba(255,255,255,0.03);
        }}
        @media (max-width: 900px) {{
          .ledger-row {{
            align-items: flex-start;
            flex-direction: column;
          }}
        }}
      </style>
    </head>
    <body>
      <div class="wrap">
        <section class="hero">
          <h1>Toan bo lich su du doan</h1>
          <div class="muted">Trang nay hien toan bo block trong so cai ledger hien tai, kem trang thai validate chuoi va chu ky HMAC.</div>
          <div class="actions">
            <a class="btn secondary" href="/">Ve trang chinh</a>
            <a class="btn" href="/ledger/export.json">Xuat JSON</a>
            <a class="btn" href="/ledger/export.csv">Xuat CSV</a>
          </div>
          <div class="status">
            <span class="pill {valid_class}">Chain {valid_text}</span>
            <span class="pill">Tong block: {int(validation.get("length", 0))}</span>
            <span class="pill">Broken index: {int(broken_index) if broken_index is not None else -1}</span>
          </div>
          {f'<div class="warning">Reason: {escape(str(reason))}</div>' if reason else ""}
        </section>

        <div class="stack">
          <section class="card">
            <div class="section-title">Danh sach block</div>
            {_render_ledger_rows(blocks)}
          </section>
        </div>
      </div>
    </body>
    </html>
    """
