import logging
import re
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define answer key URLs (replace with your actual URLs)
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
    "04s1": "https://json.extendsclass.com/bin/e02a72e68a41",
    "04s2": "https://json.extendsclass.com/bin/d45bb3017d92",
    "05s1": "https://json.extendsclass.com/bin/f0a2446e7f12",
    "05s2": "https://json.extendsclass.com/bin/9a5213793a4e",
    "06s1": "https://json.extendsclass.com/bin/2508ed9bac9a",
    "06s2": "https://json.extendsclass.com/bin/b3f147fa1f70",
    "08s1": "https://json.extendsclass.com/bin/497e7d9b9d04",
    "08s2": "https://json.extendsclass.com/bin/a54406466af0",
    "09s1": "https://json.extendsclass.com/bin/59f50c0b8bf4",
    "09s2": "https://json.extendsclass.com/bin/760b804b0fd8",
}

# Function to fetch and process the response sheet
async def process_response_sheet(url):
    try:
        # Fetch the response sheet HTML
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract session and shift information
        table_rows = soup.select("table tbody tr")
        session = table_rows[3].select_one("td:last-child").text.strip().split("/")[0]
        shift = "1" if "am" in table_rows[4].select_one("td:last-child").text.strip().lower() else "2"
        key = f"{session}s{shift}"

        # Fetch the answer key
        answer_key_url = ANSWER_KEYS.get(key)
        if not answer_key_url:
            return "Answer key not found for this session and shift."

        answer_key = requests.get(answer_key_url).json()

        # Process the response sheet
        results = []
        for table in soup.select("table.menu-tbl > tbody"):
            rows = table.select("tr")
            question_type = rows[0].select_one("td:last-child").text.strip()
            question_id = rows[1].select_one("td:last-child").text.strip()
            options = [rows[i].select_one("td:last-child").text.strip() for i in range(2, 6)]
            marked_answer = rows[7].select_one("td:last-child").text.strip() if question_type == "MCQ" else rows[0].select_one("td:last-child").text.strip()
            correct_answer = answer_key.get(question_id, "")
            score = 4 if marked_answer == correct_answer else (-1 if marked_answer != "--" else 0)
            results.append({
                "type": question_type,
                "id": question_id,
                "marked": marked_answer,
                "score": score,
            })

        # Calculate scores
        total_score = sum(result["score"] for result in results)
        correct = sum(1 for result in results if result["score"] == 4)
        incorrect = sum(1 for result in results if result["score"] == -1)
        attempted = correct + incorrect
        unattempted = len(results) - attempted

        # Subject-wise scores
        physics = sum(result["score"] for result in results[:25])
        chemistry = sum(result["score"] for result in results[25:50])
        maths = sum(result["score"] for result in results[50:75])

        # Generate result message
        result_message = (
            f"TOTAL: {total_score}/300\n\n"
            f"Correct: {correct}\n"
            f"Incorrect: {incorrect}\n"
            f"Attempted: {attempted}\n"
            f"Unattempted: {unattempted}\n\n"
            f"Physics: {physics}/100\n"
            f"Chemistry: {chemistry}/100\n"
            f"Maths: {maths}/100"
        )
        return result_message

    except Exception as e:
        logger.error(f"Error processing response sheet: {e}")
        return "Failed to process the response sheet. Please check the URL and try again."

# Start command handler
async def start(update: Update, context):
    await update.message.reply_text("Welcome! Please send me your JEE response sheet URL.")

# Message handler
async def handle_message(update: Update, context):
    url = update.message.text
    if not re.match(r"https?://", url):
        await update.message.reply_text("Please provide a valid URL.")
        return

    await update.message.reply_text("Processing your response sheet...")
    result = await process_response_sheet(url)
    await update.message.reply_text(result)

# Main function
def main():
    # Create the Application and pass it your bot's token
    application = ApplicationBuilder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
