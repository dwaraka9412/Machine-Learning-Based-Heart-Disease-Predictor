from flask import Flask, request, jsonify, render_template, send_file
import joblib
import pandas as pd
import numpy as np
import os
import sys
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

# ---------- app bootstrap ----------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_PATH, exist_ok=True)

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    instance_path=INSTANCE_PATH,
    instance_relative_config=True
)

# -------------------------
# Load pipeline (scaler+model)
# -------------------------
PIPELINE_PATH = os.path.join(BASE_DIR, 'pipeline_with_scaler.pkl')

if not os.path.exists(PIPELINE_PATH):
    msg = f"Pipeline file not found: {PIPELINE_PATH}\nMake sure 'pipeline_with_scaler.pkl' exists in the project folder."
    print(msg, file=sys.stderr)
    raise FileNotFoundError(msg)

try:
    pipeline = joblib.load(PIPELINE_PATH)
except Exception as e:
    print(f"Failed to load pipeline from {PIPELINE_PATH}: {e}", file=sys.stderr)
    raise

# -------------------------
# Config
# -------------------------
FEATURE_ORDER = [
    'age','sex','cp','trestbps','chol','fbs',
    'restecg','thalach','exang','oldpeak','slope','ca','thal'
]

DECISION_THRESHOLD = 0.4

# -------------------------
# Routes
# -------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON provided"}), 400

    features = data.get('features')
    features_dict = data.get('features_dict')

    # Build row
    if features_dict is not None:
        try:
            row = [features_dict[f] for f in FEATURE_ORDER]
        except KeyError as e:
            return jsonify({"error": f"Missing feature {e}"}), 400
    elif features is not None:
        if len(features) != len(FEATURE_ORDER):
            return jsonify({"error": f"Expected {len(FEATURE_ORDER)} features. Got {len(features)}."}), 400
        row = features
    else:
        return jsonify({"error":"Send 'features' (list) or 'features_dict' (dict)."}), 400

    # Validation
    if any(v is None for v in row):
        return jsonify({"error": "Some features are missing (one or more values are null)."}), 400

    try:
        row_num = [float(x) for x in row]
    except Exception:
        return jsonify({"error": "All feature values must be numeric."}), 400

    # Map to variables
    age, sex, cp, trestbps, chol, fbs, restecg, thalach, exang, oldpeak, slope, ca, thal = row_num

    # Simple validation (can be adjusted)
    if not (0 <= age <= 120):
        return jsonify({"error":"Invalid 'age' — expected between 0 and 120."}), 400
    if int(sex) not in (0,1):
        return jsonify({"error":"Invalid 'sex' — expected 0 or 1."}), 400
    if not (0 <= cp <= 3):
        return jsonify({"error":"Invalid 'cp' — expected 0..3."}), 400
    if trestbps <= 0:
        return jsonify({"error":"Invalid 'trestbps' — must be positive."}), 400
    if chol <= 0:
        return jsonify({"error":"Invalid 'chol' — must be positive."}), 400
    if int(fbs) not in (0,1):
        return jsonify({"error":"Invalid 'fbs' — expected 0 or 1."}), 400
    if not (0 <= restecg <= 2):
        return jsonify({"error":"Invalid 'restecg' — expected 0..2."}), 400
    if thalach <= 0:
        return jsonify({"error":"Invalid 'thalach' — must be positive."}), 400
    if int(exang) not in (0,1):
        return jsonify({"error":"Invalid 'exang' — expected 0 or 1."}), 400
    if oldpeak < 0:
        return jsonify({"error":"Invalid 'oldpeak' — must be >= 0."}), 400
    if not (0 <= slope <= 2):
        return jsonify({"error":"Invalid 'slope' — expected 0..2."}), 400
    if not (0 <= ca <= 4):
        return jsonify({"error":"Invalid 'ca' — expected 0..4."}), 400
    if not (0 <= thal <= 3):
        return jsonify({"error":"Invalid 'thal' — expected 0..3."}), 400

    # Predict
    try:
        df = pd.DataFrame([row_num], columns=FEATURE_ORDER).astype(float)
    except Exception as e:
        return jsonify({"error":"Failed to build DataFrame from features: "+str(e)}), 400

    try:
        proba = pipeline.predict_proba(df)[0].tolist()
        raw_pred = int(pipeline.predict(df)[0])
    except Exception as e:
        return jsonify({"error":"Model inference failed: "+str(e)}), 500

    pred_by_threshold = 1 if proba[1] >= DECISION_THRESHOLD else 0

    return jsonify({
        "prediction_model_raw": raw_pred,
        "prediction_by_threshold": pred_by_threshold,
        "probabilities": proba,
        "feature_order": FEATURE_ORDER,
        "threshold_used": DECISION_THRESHOLD
    })


# -------------------------
# PDF report helpers + route
# -------------------------
def split_text(text, max_chars):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + 1 + len(w) <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def build_pdf_bytes(inputs_dict, proba, pred_by_threshold, threshold_used, patient_name=None, notes=None):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 18 * mm
    x = margin
    y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x, y, "Heart Disease Prediction Report")
    c.setFont("Helvetica", 9)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.drawRightString(width - margin, y, f"Generated: {now}")
    y -= 12 * mm

    # Patient name if provided
    c.setFont("Helvetica-Bold", 11)
    if patient_name:
        c.drawString(x, y, f"Patient: {patient_name}")
        y -= 8 * mm

    # Separator
    c.setLineWidth(0.5)
    c.line(x, y, width - margin, y)
    y -= 8 * mm

    # Inputs table
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Input features")
    y -= 8 * mm
    c.setFont("Helvetica", 10)
    for k, v in inputs_dict.items():
        if y < margin + 40:
            c.showPage(); y = height - margin
        c.drawString(x, y, f"{k}:")
        c.drawString(x + 70 * mm, y, str(v))
        y -= 6 * mm

    y -= 6 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x, y, "Prediction")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    label = "HIGH RISK (Heart disease)" if pred_by_threshold == 1 else "LOW RISK (No heart disease)"
    c.drawString(x, y, f"Result: {label}")
    y -= 7 * mm
    c.drawString(x, y, f"Threshold used: {threshold_used:.2f}")
    y -= 7 * mm
    c.drawString(x, y, f"Probability (No disease p0): {proba[0]:.4f}   Probability (Disease p1): {proba[1]:.4f}")
    y -= 10 * mm

    # Small colored bar for p1
    bar_x = x
    bar_w = width - margin*2
    bar_h = 8 * mm
    c.setFillColorRGB(0.95,0.95,0.95)
    c.rect(bar_x, y - bar_h, bar_w, bar_h, fill=1, stroke=0)
    c.setFillColorRGB(0.89,0.15,0.27)  # red-ish
    c.rect(bar_x, y - bar_h, bar_w * proba[1], bar_h, fill=1, stroke=0)
    y -= (bar_h + 10 * mm)

    # Notes if provided
    if notes:
        c.setFont("Helvetica-Bold", 11)
        c.drawString(x, y, "Clinician Notes:")
        y -= 7 * mm
        c.setFont("Helvetica", 10)
        for line in split_text(notes, 90):
            if y < margin + 20:
                c.showPage(); y = height - margin
            c.drawString(x, y, line)
            y -= 5 * mm
        y -= 6 * mm

    # Footer note
    c.setFont("Helvetica-Oblique", 8)
    text = ("Note: This report is generated by a machine learning model (logistic regression). "
            "This output is for educational/demo purposes and is not a medical diagnosis. "
            "Clinical decisions must be made by qualified medical professionals.")
    for line in split_text(text, 90):
        if y < margin + 20:
            c.showPage(); y = height - margin
        c.drawString(x, y, line)
        y -= 5 * mm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

@app.route('/report', methods=['POST'])
def report():
    data = request.get_json(force=True)
    if not data:
        return jsonify({"error": "No JSON provided"}), 400

    features = data.get('features')
    features_dict = data.get('features_dict')

    # optional fields
    patient_name = data.get('patient_name') or data.get('name') or None
    notes = data.get('notes') or data.get('clinician_notes') or None

    if features_dict is not None:
        try:
            row = [features_dict[f] for f in FEATURE_ORDER]
            input_map = {f: features_dict.get(f) for f in FEATURE_ORDER}
        except KeyError as e:
            return jsonify({"error": f"Missing feature {e}"}), 400
    elif features is not None:
        if len(features) != len(FEATURE_ORDER):
            return jsonify({"error": f"Expected {len(FEATURE_ORDER)} features. Got {len(features)}."}), 400
        row = features
        input_map = {FEATURE_ORDER[i]: features[i] for i in range(len(FEATURE_ORDER))}
    else:
        return jsonify({"error":"Send 'features' or 'features_dict'."}), 400

    try:
        row_num = [float(x) for x in row]
    except Exception:
        return jsonify({"error":"All features must be numeric."}), 400

    try:
        df = pd.DataFrame([row_num], columns=FEATURE_ORDER).astype(float)
        proba = pipeline.predict_proba(df)[0].tolist()
        raw_pred = int(pipeline.predict(df)[0])
        pred_by_threshold = 1 if proba[1] >= DECISION_THRESHOLD else 0
    except Exception as e:
        return jsonify({"error": "Model inference failed: " + str(e)}), 500

    pdf_buffer = build_pdf_bytes(input_map, proba, pred_by_threshold, DECISION_THRESHOLD, patient_name=patient_name, notes=notes)
    filename = f"heart_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(pdf_buffer, as_attachment=True, download_name=filename, mimetype='application/pdf')


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)