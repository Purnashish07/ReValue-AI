# ReValue AI

AI-assisted e-waste visual triage prototype. Upload a photo, receive a preliminary component list, optional normalized bounding-box overlay, sorting suggestions, safety notes, and a downloadable JSON report.

## Important scope

- **Live mode** requires a compatible vision chat-completions endpoint configured in `.env`.
- **Demo mode** is a UI/API smoke-test fallback. It does not inspect the uploaded image and must never be represented as real AI detection.
- SAM-style segmentation requires a separate segmentation-capable model/service; this starter app uses bounding boxes returned by the vision model and does not claim pixel-accurate masks.
- Visual predictions do not establish electrical safety, battery condition, chemical composition, precious-metal content, or suitability for reuse.

## Requirements

- Windows 10/11
- Python 3.10+
- Internet access only if installing dependencies or calling a remote model API

## Setup (PowerShell)

```powershell
cd ReValueAI
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` with your own Meta Model API key from the official developer portal:
- `META_MODEL_API_URL=https://api.meta.ai/v1/chat/completions`
- `META_MODEL_API_KEY=your_private_key`
- `META_MODEL_NAME=muse-spark-1.3`

Meta documents Muse Spark as supporting image input through Model API. See [Meta Model API overview](https://dev.meta.ai/docs/overview) and [model documentation](https://dev.meta.ai/docs/models). API access, billing, account eligibility, model availability, and the exact request schema can change, so verify them in your account before use. Never commit `.env` or expose your key.

**Segmentation status:** this starter version uses model-supplied bounding boxes for visual highlighting. It does not yet call the separate SAM 3.1 segmentation endpoint or render pixel-level masks. That is a distinct integration step; see [SAM segmentation documentation](https://dev.meta.ai/docs/sam/overview).

Run:

```powershell
python app.py
```

Open http://127.0.0.1:5000

Health check: http://127.0.0.1:5000/api/health

## Features

- Image upload with type/size validation and preview
- Optional compatible vision API integration
- Structured component descriptions and confidence labels
- Bounding-box overlays when the model supplies usable normalized coordinates
- Recovery/sorting suggestions, limitations and safety notes
- JSON report export
- Responsive UI

## API

- `GET /api/health`
- `POST /api/analyze` multipart form field `image`
- `POST /api/export` JSON body `{ "report": { ... } }`

## Safety

Treat every output as preliminary triage, not a recycling certificate. Use trained personnel and authorized e-waste handlers. Do not dismantle swollen/leaking batteries, CRTs, power supplies, or unknown capacitors without appropriate training and procedures. Follow applicable local rules.
