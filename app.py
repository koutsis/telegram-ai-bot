import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# ΓΡΗΓΟΡΟ & ΣΤΑΘΕΡΟ μοντέλο
HF_MODEL = "tiiuae/falcon-7b-instruct"


# -----------------------------------------------------
#  Load data.json (coaching dataset)
# -----------------------------------------------------
with open("data.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)


# -----------------------------------------------------
#  Building coaching prompt
# -----------------------------------------------------
def build_prompt(user_text):

    principles_text = "\n".join(f"- {p}" for p in DATA["principles"])
    questions_text = "\n".join(f"- {q}" for q in DATA["coaching_questions"])

    style_tone = DATA["style"]["tone"]
    style_approach = DATA["style"]["approach"]

    system_prompt = f"""
Είσαι AI Life & Business Coach που ακολουθεί 100% την προσέγγιση της πελάτισσας.
Δεν δίνεις έτοιμες λύσεις — κάνεις coaching ερωτήσεις.
Ο τόνος σου είναι: {style_tone}
Η προσέγγιση σου είναι: {style_approach}

ΑΡΧΕΣ COACHING:
{principles_text}

ΧΡΗΣΙΜΕΣ COACHING ΕΡΩΤΗΣΕΙΣ:
{questions_text}

Οδηγίες:
- Μίλα ζεστά, με ενσυναίσθηση και κατανόηση.
- Βοήθα τον άνθρωπο να δει καθαρότερα μόνος του.
- Μην κάνεις ιατρικές/ψυχολογικές διαγνώσεις.
- Αν δεν έχεις περιεχόμενο λες:
  "Δεν έχω πληροφορία από το υλικό μου για αυτό, αλλά μπορώ να σε βοηθήσω με μια coaching ερώτηση."

Απάντησε στον χρήστη με αυτό το ύφος.
"""
    return f"{system_prompt}\n\nΕΡΩΤΗΣΗ ΧΡΗΣΤΗ: {user_text}\nΑΠΑΝΤΗΣΗ:"


# -----------------------------------------------------
#  HuggingFace API call (σταθερή & χωρίς errors)
# -----------------------------------------------------
def ask_ai(prompt):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    payload = {"inputs": prompt}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        data = response.json()
    except Exception:
