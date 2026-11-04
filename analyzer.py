import json, os, re, base64, requests

SYSTEM_PROMPT = """You are ReValue AI, a cautious e-waste visual triage assistant.
Analyze ONLY what is visible in the supplied image. Return valid JSON with this schema:
{
 "device_summary": "short description",
 "items": [
  {"name":"component or visible part", "visual_evidence":"what is visibly supporting this label",
   "confidence":"low|medium|high", "bbox":[x1,y1,x2,y2],
   "possible_path":"reuse|repair_assessment|recycling|special_handling|unknown",
   "reason":"short reason", "verification_needed":"what a human should check"}
 ],
 "sorting_plan":["practical safe sorting steps"],
 "limitations":["uncertainties or what cannot be inferred"],
 "safety_notes":["relevant safety advice"]
}
Bounding boxes must be normalized numbers from 0 to 1000 in [x1,y1,x2,y2] order; include only when reasonably localizable.
Never claim electrical function, chemical composition, battery health, data-bearing status, precious-metal content, or repairability from appearance alone.
If no electronic components are clearly visible, say so. Do not invent detections. Be cautious with batteries, CRTs, damaged devices, and unknown capacitors.
Return JSON only. Confidence is a qualitative visual confidence, not calibrated probability.
"""

def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The vision model did not return a JSON object. Try again.")
    return json.loads(text[start:end+1])

def _call_compatible_vision_api(image_bytes, api_url, api_key, model):
    if not api_url or not api_key:
        return demo_analysis()
    b64 = base64.b64encode(image_bytes).decode("ascii")
    # OpenAI-compatible chat-completions endpoint; set exact provider endpoint in .env.
    payload = {
      "model": model or "vision-model",
      "temperature": 0.1,
      "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": [
          {"type": "text", "text": "Analyze this e-waste image and follow the required JSON schema."},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + b64}}
        ]}
      ]
    }
    response = requests.post(api_url, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=90)
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, list):
        content = "\n".join(x.get("text", "") for x in content if isinstance(x, dict))
    return _extract_json(content)

def demo_analysis():
    # Honest fallback so the UI can be tested without API credentials.
    return {
      "device_summary": "Demo mode: no image model is connected, so this is an illustrative checklist, not detections from your image.",
      "items": [
        {"name":"Unverified electronic part", "visual_evidence":"No model analysis was run in demo mode.",
         "confidence":"low", "bbox":None, "possible_path":"unknown",
         "reason":"A real vision model or human inspection is needed before identifying components.",
         "verification_needed":"Inspect the part and markings; use qualified testing before reuse."}
      ],
      "sorting_plan":[
        "Keep the item intact until it has been inspected.",
        "Separate batteries only if trained and safe to do so; do not puncture, bend, or short them.",
        "Send unknown electronic waste to an authorized e-waste collection or recycling facility."
      ],
      "limitations":[
        "Demo mode does not inspect the uploaded image.",
        "No component identity, condition, repairability, or material value has been verified."
      ],
      "safety_notes":[
        "Do not open swollen, leaking, hot, or damaged batteries.",
        "Do not handle CRTs, capacitors, or damaged power supplies without appropriate training."
      ]
    }

def analyze_image(image_bytes, api_url=None, api_key=None, model=""):
    result = _call_compatible_vision_api(image_bytes, api_url, api_key, model)
    if not isinstance(result, dict) or not isinstance(result.get("items", []), list):
        raise ValueError("Unexpected response schema from the vision model.")
    for item in result.get("items", []):
        box = item.get("bbox")
        if isinstance(box, list) and len(box) == 4:
            try:
                coords = [max(0, min(1000, float(v))) for v in box]
                if coords[2] <= coords[0] or coords[3] <= coords[1]:
                    item["bbox"] = None
                else:
                    item["bbox"] = coords
            except (ValueError, TypeError):
                item["bbox"] = None
        else:
            item["bbox"] = None
    result.setdefault("device_summary", "No summary returned.")
    result.setdefault("sorting_plan", [])
    result.setdefault("limitations", [])
    result.setdefault("safety_notes", [])
    result["mode"] = "live_model" if api_url and api_key else "demo"
    return result

def build_recovery_report(analysis):
    items = analysis.get("items", [])
    counts = {}
    for item in items:
        path = item.get("possible_path", "unknown")
        counts[path] = counts.get(path, 0) + 1
    return {
      "product": "ReValue AI",
      "report_type": "visual_triage_not_certification",
      "created_at_note": "Generated at analysis time by the local application.",
      "analysis_mode": analysis.get("mode", "unknown"),
      "device_summary": analysis.get("device_summary", ""),
      "component_count": len(items),
      "pathway_counts": counts,
      "components": items,
      "sorting_plan": analysis.get("sorting_plan", []),
      "limitations": analysis.get("limitations", []),
      "safety_notes": analysis.get("safety_notes", []),
      "disclaimer": "Visual AI suggestions are preliminary only. They do not establish electrical safety, battery condition, material composition, data-bearing status, or fitness for reuse. Qualified physical inspection and applicable local e-waste rules take precedence."
    }
