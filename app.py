import os, io, json, base64
from datetime import datetime, timezone
from flask import Flask, render_template, request, jsonify, send_file
from PIL import Image
from dotenv import load_dotenv
from analyzer import analyze_image, build_recovery_report

load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
ALLOWED = {"png", "jpg", "jpeg", "webp"}

@app.get("/")
def index():
    return render_template("index.html", meta_api_configured=bool(os.getenv("META_MODEL_API_URL") and os.getenv("META_MODEL_API_KEY")))

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "meta_api_configured": bool(os.getenv("META_MODEL_API_URL") and os.getenv("META_MODEL_API_KEY"))})

@app.post("/api/analyze")
def analyze():
    upload = request.files.get("image")
    if not upload or not upload.filename:
        return jsonify({"error": "Please choose an image first."}), 400
    ext = upload.filename.rsplit(".", 1)[-1].lower() if "." in upload.filename else ""
    if ext not in ALLOWED:
        return jsonify({"error": "Supported formats: PNG, JPG, JPEG, WEBP."}), 400
    try:
        raw = upload.read()
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        if image.width * image.height > 20_000_000:
            return jsonify({"error": "Image is too large. Please use an image under 20 megapixels."}), 400
        image.thumbnail((1400, 1400))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=88)
        jpeg_bytes = buffer.getvalue()
        result = analyze_image(jpeg_bytes, os.getenv("META_MODEL_API_URL"), os.getenv("META_MODEL_API_KEY"), os.getenv("META_MODEL_NAME", ""))
        report = build_recovery_report(result)
        return jsonify({
            "created_at": datetime.now(timezone.utc).isoformat(),
            "image_data": "data:image/jpeg;base64," + base64.b64encode(jpeg_bytes).decode(),
            "analysis": result,
            "report": report
        })
    except Exception as exc:
        app.logger.exception("Image analysis failed")
        return jsonify({"error": str(exc) if os.getenv("DEBUG") == "1" else "Could not analyze this image. Check the image and API configuration, then try again."}), 500

@app.post("/api/export")
def export_report():
    payload = request.get_json(silent=True) or {}
    report = payload.get("report")
    if not isinstance(report, dict):
        return jsonify({"error": "No report supplied."}), 400
    data = json.dumps(report, indent=2, ensure_ascii=False).encode("utf-8")
    return send_file(io.BytesIO(data), mimetype="application/json", as_attachment=True, download_name="revalue_recovery_report.json")

if __name__ == "__main__":
    app.run(debug=os.getenv("DEBUG") == "1", host="127.0.0.1", port=int(os.getenv("PORT", "5000")))
