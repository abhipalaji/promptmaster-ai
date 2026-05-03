from flask import Flask, render_template, request, jsonify
import requests
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("API_KEY")

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("contacts.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- CONTEXT ----------------
CATEGORY_CONTEXT = {
    "blog": "Focus on long-form blog writing.",
    "ads": "Focus on marketing and conversion.",
    "code": "Focus on programming clarity.",
    "general": "Make it clear and useful."
}

TONE_CONTEXT = {
    "professional": "Use professional tone.",
    "creative": "Make it creative.",
    "friendly": "Make it friendly."
}

MODELS = [
    "meta-llama/llama-3-8b-instruct",
    "openchat/openchat-3.5"
]

# ---------------- ROUTES ----------------
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/blog")
def blog():
    return render_template("blog.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

# ---------------- ADMIN PANEL ----------------
@app.route("/admin")
def admin():
    if request.args.get("key") != "1234":
        return "Unauthorized", 403

    conn = sqlite3.connect("contacts.db")
    cursor = conn.cursor()

    cursor.execute("SELECT id, email, message, created_at FROM contacts ORDER BY id DESC")
    contacts = cursor.fetchall()

    conn.close()

    return render_template("admin.html", contacts=contacts)

# ---------------- AI ROUTE ----------------
@app.route("/enhance", methods=["POST"])
def enhance():
    try:
        data = request.get_json()

        prompt = data.get("prompt", "").strip()
        tone = data.get("tone", "professional")
        category = data.get("category", "general")

        if not prompt:
            return jsonify({"error": "Prompt is empty"}), 400

        SYSTEM_PROMPT = f"""
You are an expert prompt engineer.

Rewrite and improve prompts.

Context:
- {CATEGORY_CONTEXT.get(category)}
- {TONE_CONTEXT.get(tone)}

Rules:
- Do NOT answer
- Output ONLY improved prompt

Enhance by:
- Adding role (Act as...)
- Adding clarity
- Adding constraints
"""

        for model in MODELS:
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.6
                    },
                    timeout=15
                )

                if res.status_code != 200:
                    continue

                data = res.json()

                if "choices" in data:
                    output = data["choices"][0]["message"]["content"].strip()
                    return jsonify({"result": output})

            except:
                continue

        return jsonify({"error": "AI failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------- CONTACT API ----------------
@app.route("/contact-submit", methods=["POST"])
def contact_submit():
    try:
        data = request.get_json()

        email = data.get("email", "").strip()
        message = data.get("message", "").strip()

        if not email or not message:
            return jsonify({"error": "Fill all fields"}), 400

        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO contacts (email, message) VALUES (?, ?)",
            (email, message)
        )

        conn.commit()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)