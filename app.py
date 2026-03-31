import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

# Φόρτωμα του data.json
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

def build_prompt(user_text):
    """
    Δημιουργεί coaching prompt βασισμένο στο περιεχόμενο της πελάτισσας.
    """

    # 1. Principles
    principles_text = "\n".join(f"- {p}" for p in DATA["principles"])

    # 2. Coaching questions
    questions_text = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    # 3. Style
    style_tone = DATA["style"]["tone"]
    style_approach = DATA["style"]["approach"]

    system_prompt = f"""
Είσαι AI Life & Business Coach που ακολουθεί 100% τη φιλοσοφία και το ύφος της πελάτισσας.
Ποτέ δεν δίνεις έτοιμες λύσεις. Κάνεις ανοιχτές coaching ερωτήσεις.
Μιλάς με ύφος: {style_tone}.
Η προσέγγισή σου: {style_approach}.

Αρχές coaching:
{principles_text}

Χρήσιμες coaching ερωτήσεις:
{questions_text}

Να χρησιμοποιείς ΜΟΝΟ τις αρχές από πάνω.
Αν δεν έχει σχετικό περιεχόμενο, να λες:
"Δεν έχω πληροφορία για αυτό από το υλικό μου, αλλά μπορώ να σε βοηθήσω με μια coaching ερώτηση."

Τώρα απάντησε στον χρήστη με αυτό το ύφος.
"""
    return f"{system_prompt}\n\nΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {user_text}\nΑΠΑΝΤΗΣΗ:"
    

def ask_ai(prompt):
    """
    Κλήση στο HuggingFace για παραγωγή απάντησης.
    """
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)
    try:
        data = response.json()
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        else:
            return "Υπάρχει ένα προσωρινό τεχνικό θέμα — δοκίμασε ξανά!"
    except:
        return "Παρουσιάστηκε σφάλμα — προσπάθησε πάλι λίγο αργότερα."

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    
    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        prompt = build_prompt(text)
        answer = ask_ai(prompt)

        send_message(chat_id, answer)

    return "OK"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)