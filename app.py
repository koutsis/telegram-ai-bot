import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "openai/gpt-3.5-turbo"

# Load dataset
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


def build_prompt(user_text):

    principles_text = "\n".join(f"- {p}" for p in DATA["principles"])
    questions_text = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    style_tone = DATA["style"]["tone"]
    style_approach = DATA["style"]["approach"]

    system_prompt = f"""
Είσαι AI Life & Business Coach που χρησιμοποιεί ΑΠΟΚΛΕΙΣΤΙΚΑ τη φιλοσοφία της πελάτισσας.
Ο τόνος σου: {style_tone}
Η προσέγγισή σου: {style_approach}

ΑΡΧΕΣ:
{principles_text}

COACHING ΕΡΩΤΗΣΕΙΣ:
{questions_text}

Οδηγίες:
- Μην δίνεις έτοιμες λύσεις
- Κάνε ανοιχτές ερωτήσεις
- Μην δίνεις ποτέ διαγνώσεις
"""
    return f"{system_prompt}\n\nΕΡΩΤΗΣΗ: {user_text}\nΑΠΑΝΤΗΣΗ:"


def ask_ai(prompt):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://telegram-ai-bot.onrender.com",
        "X-Title": "TelegramAI-Coach"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "Είσαι CoachingAssistant."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception:
        return "Υπάρχει προσωρινό θέμα σύνδεσης — δοκίμασε ξανά."


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
    requests.post(url, json={"chat_id": chat_id, "text": text})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)