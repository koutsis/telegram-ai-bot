import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Γρήγορο & σταθερό μοντέλο
HF_MODEL = "tiiuae/falcon-7b-instruct"


# -----------------------------------------------------
# Load data.json
# -----------------------------------------------------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


# -----------------------------------------------------
# Build coaching prompt
# -----------------------------------------------------
def build_prompt(user_text):

    principles_text = "\n".join(f"- {p}" for p in DATA["principles"])
    questions_text = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    style_tone = DATA["style"]["tone"]
    style_approach = DATA["style"]["approach"]

    system_prompt = f"""
Είσαι AI Life & Business Coach που ακολουθεί 100% την προσέγγιση και το ύφος της πελάτισσας.
Δεν δίνεις έτοιμες λύσεις — μόνο coaching ερωτήσεις.

Τόνος: {style_tone}
Προσέγγιση: {style_approach}

ΑΡΧΕΣ:
{principles_text}

COACHING ΕΡΩΤΗΣΕΙΣ:
{questions_text}

Οδηγίες:
- Μίλα ζεστά και ενσυναίσθητα.
- Βάλε τον χρήστη να εξερευνήσει βαθύτερα.
- Μην κάνεις διαγνώσεις.
- Αν δεν έχεις σχετικό περιεχόμενο απάντα:
"Δεν έχω πληροφορία για αυτό από το υλικό μου, αλλά μπορώ να σε βοηθήσω με μια ανοιχτή coaching ερώτηση."
"""

    return f"{system_prompt}\n\nΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {user_text}\nΑΠΑΝΤΗΣΗ:"


# -----------------------------------------------------
# HuggingFace API call (σταθερό)
# -----------------------------------------------------
def ask_ai(prompt):

    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
    except Exception:
        return "Το μοντέλο αργεί λίγο — δοκίμασε ξανά σε λίγο."

    # CASE 1 — generated_text μέσα σε λίστα
    if isinstance(data, list):
        for item in data:
            if "generated_text" in item:
                return item["generated_text"]

    # CASE 2 — generated_text σε dict
    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"]

    # CASE 3 — error από HuggingFace
    if isinstance(data, dict) and "error" in data:
        return "Το μοντέλο καθυστερεί — δοκίμασε σε μερικά δευτερόλεπτα."

    # CASE 4 — fallback απάντηση
    return "Δεν μπορώ να δημιουργήσω απάντηση τώρα — δοκίμασε ξανά."


# -----------------------------------------------------
# Telegram Webhook
# -----------------------------------------------------
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        user_text = update["message"].get("text", "")

        prompt = build_prompt(user_text)
        answer = ask_ai(prompt)

        send_message(chat_id, answer)

    return "OK"


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)


# -----------------------------------------------------
# Local run (Render will ignore this)
# -----------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)