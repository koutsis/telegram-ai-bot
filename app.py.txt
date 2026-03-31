import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = "os.getenv("TELEGRAM_TOKEN")"
HUGGINGFACE_API_KEY = "os.getenv("HUGGINGFACE_API_KEY")"
HF_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"

def ask_ai(prompt):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    response = requests.post(url, headers=headers, json=payload)
    
    try:
        return response.json()[0]["generated_text"]
    except:
        return "Συγγνώμη, δεν μπόρεσα να δημιουργήσω απάντηση αυτή τη στιγμή."

@app.route("/", methods=["POST"])
def handle_webhook():
    update = request.get_json()

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"].get("text", "")

        answer = ask_ai(text)

        send_message(chat_id, answer)

    return "OK"

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    app.run()