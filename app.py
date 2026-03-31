import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Δεν χρειάζεται τίποτα άλλο

# ΔΩΡΕΑΝ proxy μοντέλο – δεν απαιτεί API key
AI_URL = "https://api.aimlapi.com/v1/chat/completions"

MODEL = "gpt-4o-mini"   # FREE MODEL

with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

def build_prompt(user_text):
    principles = "\n".join(f"- {p}" for p in DATA["principles"])
    questions = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    tone = DATA["style"]["tone"]
    approach = DATA["style"]["approach"]

    return f"""
Είσαι AI Coach με βάση το υλικό της πελάτισσας.

Τόνος: {tone}
Προσέγγιση: {approach}

Αρχές:
{principles}

Ερωτήσεις:
{questions}

Ερώτηση χρήστη: {user_text}
Απάντησε μόνον με coaching τρόπο.
"""

def ask_ai(prompt):

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Είσαι CoachingAssistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        r = requests.post(AI_URL, json=payload, timeout=20)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return "Δεν μπορώ να απαντήσω τώρα – δοκίμασε ξανά."

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        answer = ask_ai(build_prompt(text))
        send_message(chat_id, answer)

    return "OK"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)