import os
import re
import requests
import json
from bs4 import BeautifulSoup
from flask import Flask, request
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

app = Flask(__name__)

def get_shift_date(response_url):
    """Extracts date and shift from the response sheet."""
    try:
        html = requests.get(response_url).text
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")
        if len(tables) < 3:
            return None, None
        
        date = tables[3].find_all("td")[-1].text.strip().split("/")[0]
        shift_text = tables[4].find_all("td")[-1].text.strip().lower()
        shift = "1" if "am" in shift_text else "2"
        
        return date, shift
    except Exception as e:
        print(f"Error extracting shift and date: {e}")
        return None, None

def get_answer_key(date, shift):
    """Fetches the answer key JSON based on the date and shift."""
    keys = {
        "22s1": "https://raw.githubusercontent.com/Samarth2615/finaljeescrapper/refs/heads/main/Key.json",
        "27s2": "https://json.extendsclass.com/bin/fefdb99829ed",
        "29s1": "https://json.extendsclass.com/bin/904f0d88131c",
        "29s2": "https://json.extendsclass.com/bin/46c43bba08a8",
        "30s1": "https://json.extendsclass.com/bin/81f6b0ed9c31",
        "30s2": "https://json.extendsclass.com/bin/ef17bbd48072",
        "31s1": "https://json.extendsclass.com/bin/4c2836982021",
        "31s2": "https://json.extendsclass.com/bin/a6a0bd4c830b",
        "01s1": "https://json.extendsclass.com/bin/2902b9729668",
        "01s2": "https://json.extendsclass.com/bin/d2ba75006751",
        "04s1": "https://json.extendsclass.com/bin/e02a72e68a41",
        "04s2": "https://json.extendsclass.com/bin/d45bb3017d92",
        "05s1": "https://json.extendsclass.com/bin/f0a2446e7f12",
        "05s2": "https://json.extendsclass.com/bin/9a5213793a4e",
        "06s1": "https://json.extendsclass.com/bin/2508ed9bac9a",
        "06s2": "https://json.extendsclass.com/bin/b3f147fa1f70",
        "08s1": "https://json.extendsclass.com/bin/497e7d9b9d04",
        "08s2": "https://json.extendsclass.com/bin/a54406466af0",
        "09s1": "https://json.extendsclass.com/bin/59f50c0b8bf4",
        "09s2": "https://json.extendsclass.com/bin/760b804b0fd8"
    }
    
    key_url = keys.get(f"{date}s{shift}")
    if key_url:
        return requests.get(key_url).json()
    return None

def calculate_score(response_url):
    """Fetches response sheet, extracts marked answers, and calculates score."""
    date, shift = get_shift_date(response_url)
    if not date or not shift:
        return "Error: Couldn't determine test date and shift."

    answer_key = get_answer_key(date, shift)
    if not answer_key:
        return "Error: Answer key not found for this shift."

    html = requests.get(response_url).text
    soup = BeautifulSoup(html, "html.parser")
    questions = soup.select("table.menu-tbl > tbody")

    score_details = []
    total_score = 0
    correct, incorrect, unattempted = 0, 0, 0
    subject_scores = {"MAT": 0, "PHY": 0, "CHE": 0}
    
    for index, q in enumerate(questions):
        cells = q.find_all("td")
        q_id = cells[1].text.strip()
        marked = cells[-1].text.strip() if "--" not in cells[-1].text else None
        
        correct_answer = answer_key.get(q_id)
        score = 4 if marked == correct_answer else -1 if marked else 0
        total_score += score
        
        if marked:
            if score == 4:
                correct += 1
            else:
                incorrect += 1
        else:
            unattempted += 1

        subject = "MAT" if index < 25 else "PHY" if index < 50 else "CHE"
        subject_scores[subject] += score
        score_details.append(f"Q{index+1:02}: {'✅' if score == 4 else '❌' if score == -1 else '❔'}")

    report = (
        f"\nJEE Score Report ({date} Shift {shift})\n"
        f"TOTAL: {total_score}/300\n"
        f"✔ Correct: {correct}\n❌ Incorrect: {incorrect}\n❔ Unattempted: {unattempted}\n"
        f"📘 Physics: {subject_scores['PHY']}/100\n"
        f"🧪 Chemistry: {subject_scores['CHE']}/100\n"
        f"🧮 Maths: {subject_scores['MAT']}/100\n\n"
        f"Details:\n" + "\n".join(score_details)
    )

    return report

def start(update: Update, context: CallbackContext):
    update.message.reply_text("Send your JEE response sheet URL to get your score.")

def handle_message(update: Update, context: CallbackContext):
    url = update.message.text.strip()
    if re.match(r"https?://.*", url):
        result = calculate_score(url)
        update.message.reply_text(result)
    else:
        update.message.reply_text("Please send a valid JEE response sheet URL.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
