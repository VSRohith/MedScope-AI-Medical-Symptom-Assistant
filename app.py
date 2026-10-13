from flask import Flask, render_template, request, send_file
import ollama
import io
from datetime import datetime

app = Flask(__name__)
MODEL = "llama3.2"

EMERGENCY_TERMS = [
    "severe difficulty breathing", "cannot breathe",
    "can't breathe", "chest pain", "chest pressure",
    "blue lips", "blue skin", "unconscious",
    "new confusion", "severe bleeding"
]


def build_prompt(data):
    return f"""
You are MedScope AI, an educational symptom information assistant.
You are not a doctor. Never provide a definitive diagnosis or
claim that a serious condition is ruled out.

Patient information:
Age: {data['age']}
Sex: {data.get('sex') or 'Not provided'}
Symptoms: {data['symptoms']}
Duration: {data.get('duration') or 'Not provided'}
Severity: {data.get('severity') or 'Not provided'}
Medical history: {data.get('history') or 'Not provided'}
Medications: {data.get('medications') or 'Not provided'}
Allergies: {data.get('allergies') or 'Not provided'}

Create a clear report with these headings:

1. SUMMARY OF REPORTED SYMPTOMS
2. POSSIBLE EXPLANATIONS (NOT A DIAGNOSIS)
3. IMPORTANT MISSING INFORMATION
4. FOLLOW-UP QUESTIONS
5. GENERAL SELF-CARE INFORMATION
6. WHEN TO SEEK MEDICAL HELP
7. DISCLAIMER

Instructions:
- Give up to 3 possible explanations, with uncertainty clearly stated.
- Ask 3 to 5 relevant follow-up questions.
- Do not prescribe medicines or provide medication dosages.
- Do not invent probabilities or medical facts.
- Explain when professional assessment may be needed.
- Mention emergency signs such as severe breathing difficulty,
  persistent chest pain, blue or grey lips, fainting or new confusion.
- For severe or life-threatening symptoms, advise immediate
  emergency medical care.
- Use simple English and concise formatting.
"""


@app.route("/")
def home():
    return render_template(
        "index.html",
        report=None,
        form_data={}
    )


@app.route("/analyze", methods=["POST"])
def analyze():
    data = {
        "age": request.form.get("age", "").strip(),
        "sex": request.form.get("sex", "").strip(),
        "symptoms": request.form.get("symptoms", "").strip(),
        "duration": request.form.get("duration", "").strip(),
        "severity": request.form.get("severity", "").strip(),
        "history": request.form.get("history", "").strip(),
        "medications": request.form.get("medications", "").strip(),
        "allergies": request.form.get("allergies", "").strip()
    }

    if not data["age"] or not data["symptoms"]:
        return render_template(
            "index.html",
            report=None,
            form_data=data,
            error="Please enter age and describe the symptoms."
        ), 400

    try:
        age = int(data["age"])
        if not 0 <= age <= 120:
            raise ValueError
    except ValueError:
        return render_template(
            "index.html",
            report=None,
            form_data=data,
            error="Enter a valid age between 0 and 120."
        ), 400

    urgent = any(
        term in data["symptoms"].lower()
        for term in EMERGENCY_TERMS
    )

    try:
        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Provide cautious educational health information. "
                        "Never diagnose or prescribe treatment."
                    )
                },
                {
                    "role": "user",
                    "content": build_prompt(data)
                }
            ],
            options={
                "temperature": 0.2,
                "num_predict": 900
            }
        )
        report = response["message"]["content"].strip()

    except Exception:
        return render_template(
            "index.html",
            report=None,
            form_data=data,
            error=(
                "Could not connect to Ollama. Check that Ollama "
                "is running and llama3.2 is installed."
            )
        ), 503

    safety_notice = ""
    if urgent:
        safety_notice = (
            "SAFETY ALERT: Your symptoms may include a warning sign. "
            "Do not rely on this AI report. Seek urgent medical care. "
            "For severe or life-threatening symptoms, contact local "
            "emergency services immediately."
        )

    report_text = f"""
MEDSCOPE AI - EDUCATIONAL SYMPTOM REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

PATIENT INFORMATION
Age: {data['age']}
Sex: {data['sex'] or 'Not provided'}
Symptoms: {data['symptoms']}
Duration: {data['duration'] or 'Not provided'}
Severity: {data['severity'] or 'Not provided'}
Medical history: {data['history'] or 'Not provided'}
Medications: {data['medications'] or 'Not provided'}
Allergies: {data['allergies'] or 'Not provided'}

{ safety_notice }

AI-GENERATED REPORT
{report}

DISCLAIMER
This report is for educational purposes only. It is not a medical
diagnosis and does not replace professional medical advice.
Seek emergency care for severe or life-threatening symptoms.
"""

    return render_template(
        "index.html",
        report=report,
        report_text=report_text,
        safety_notice=safety_notice,
        form_data=data,
        generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p")
    )


@app.route("/download", methods=["POST"])
def download():
    report_text = request.form.get("report_text", "")

    if not report_text.strip():
        return "No report available.", 400

    buffer = io.BytesIO(report_text.encode("utf-8"))
    buffer.seek(0)

    return send_file(
        buffer,
        mimetype="text/plain",
        as_attachment=True,
        download_name="medscope_symptom_report.txt"
    )


if __name__ == "__main__":
    app.run(debug=True)
