import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# ---- Load knowledge dataset ----
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


def build_prompt(user_text):
    """
    Δημιουργία structured coaching prompt βάσει του dataset.
    """

    # Principles
    principles_text = "\n".join(f"- {p}" for p in DATA["principles"])

    # Coaching Questions  
    questions_text = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    # Style
    style_tone = DATA["style"]["tone"]
    style_approach = DATA["style"]["approach"]

    system_prompt = f"""
Είσαι AI Life & Business Coach που ακολουθεί 100% τη φιλοσοφία και το ύφος της πελάτισσας.
Δεν δίνεις έτοιμες λύσεις – μόνο coaching ερωτήσεις και κατανόηση.

Τόνος: {style_tone}
Προσέγγιση: {style_approach}

Αρχές Coaching:
{principles_text}

Coaching Ερωτήσεις:
{questions_text}

Οδηγίες:
- Απαντάς πάντα ζεστά και ενσυναισθητικά.
- Κάνεις πάντα ανοιχτές coaching ερωτήσεις.
- Δεν δίνεις διαγνώσεις.
- Αν δεν έχει σχετικές πληροφορίες λες:
  "Δεν έχω πληροφορία για αυτό από το υλικό μου, αλλά μπορώ να σε βοηθήσω με μια coaching ερώτηση."

Τώρα απάντησε στον χρήστη με αυτό το ύφος.
"""
    return f"{system_prompt}\n\nΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {user_text}\nΑΠΑΝΤΗΣΗ:"


def ask_ai(prompt):
    """
    Σταθερή και ασφαλής κλήση στο HuggingFace API.
    """
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)

    # Προσπάθεια parsing
    try:
        data = response.json()
    except Exception:
        return "Υπάρχει προσωρινό τεχνικό θέμα με το μοντέλο. Δοκίμασε ξανά σε λίγο."

    # CASE 1: HuggingFace returns generated text inside list
    if isinstance(data, list):
        for item in data:
            if "generated_text" in item:
                return item["generated_text"]

    # CASE 2: HF returns a dict with 'generated_text'
    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"]

    # CASE 3: HF returns an error message
    if isinstance(data, dict) and "error" in data:
        return "Το μοντέλο καθυστερεί λίγο. Δοκίμασε ξανά σε λίγο."

    # CASE 4: fallback – unknown format
    return "Δεν μπόρεσα να δημιουργήσω απάντηση αυτή τη στιγμή. Δοκίμασε ξανά."


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)