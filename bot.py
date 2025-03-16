import os
import requests
import cloudscraper
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Bot Token from @BotFather
BOT_TOKEN = "TELEGRAM_BOT_TOKEN"

# Answer key URLs for different shifts
ANSWER_KEYS = {
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
}

# Create a CloudScraper instance to bypass Cloudflare
scraper = cloudscraper.create_scraper()


async def start(update: Update, context: CallbackContext):
    """Handles /start command."""
    await update.message.reply_text("Welcome to the JEE Score Bot! Send your response sheet URL to analyze your score.")


async def process_response(update: Update, context: CallbackContext):
    """Processes the JEE response sheet URL and calculates score."""
    url = update.message.text.strip()

    if not url.startswith("https://"):
        await update.message.reply_text("Invalid URL! Please send a valid JEE response sheet URL.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = scraper.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error fetching response sheet:", e)
        await update.message.reply_text("Failed to fetch the response sheet. Please check the URL.")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # Extract shift and date
    table_rows = soup.select("table tbody tr")
    if len(table_rows) < 5:
        await update.message.reply_text("Failed to extract test details from the response sheet.")
        return

    test_date = table_rows[3].find_all("td")[-1].text.strip().split("/")[0]
    test_shift = "1" if "AM" in table_rows[4].find_all("td")[-1].text.strip().upper() else "2"
    test_key = f"{test_date}s{test_shift}"

    if test_key not in ANSWER_KEYS:
        await update.message.reply_text("Answer key for your test is not available yet.")
        return

    # Fetch answer key
    try:
        key_response = requests.get(ANSWER_KEYS[test_key], timeout=10)
        key_response.raise_for_status()
        answer_key = key_response.json()
    except requests.RequestException as e:
        print("Error fetching answer key:", e)
        await update.message.reply_text("Failed to fetch the answer key.")
        return

    # Extract user responses
    questions = []
    for table in soup.select("table.menu-tbl > tbody"):
        cells = table.find_all("td")
        q_type = cells[0].text.strip()
        q_id = cells[1].text.strip()
        options = cells[2:6] if q_type == "MCQ" else []
        marked_option = cells[7].text.strip() if q_type == "MCQ" else cells[8].text.strip()

        correct_option = answer_key.get(q_id, None)
        score = 4 if correct_option == marked_option else (-1 if marked_option else 0)

        questions.append({
            "id": q_id, "type": q_type, "marked": marked_option,
            "correct": correct_option, "score": score
        })

    # Calculate results
    correct = sum(1 for q in questions if q["score"] == 4)
    incorrect = sum(1 for q in questions if q["score"] == -1)
    unattempted = sum(1 for q in questions if not q["marked"])
    total_score = sum(q["score"] for q in questions)

    result_text = (
        f"📝 **JEE Score Analysis**\n"
        f"📅 Date: {test_date} | Shift: {test_shift}\n"
        f"✅ Correct: {correct}\n"
        f"❌ Incorrect: {incorrect}\n"
        f"⚪ Unattempted: {unattempted}\n"
        f"🎯 Total Score: {total_score}/300"
    )

    await update.message.reply_text(result_text)


def main():
    """Starts the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_response))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
