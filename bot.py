import csv
import logging
import re
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Keep-Alive Web Server for Cloud Hosting ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "BIN Bot is online and running!"

def run_web_server():
    web_app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web_server)
    t.daemon = True
    t.start()
# -----------------------------------------------

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TOKEN = "8939467154:AAENzIrXYT2jOor1tZW5fM925jXN_xtgMZ0"
BIN_FILE_PATH = "bins.txt"

bin_database = {}

COUNTRY_FLAG_MAP = {
    "UNITED STATES": "🇺🇸", "US": "🇺🇸", "USA": "🇺🇸",
    "UNITED KINGDOM": "🇬🇧", "GREAT BRITAIN": "🇬🇧", "UK": "🇬🇧", "GB": "🇬🇧",
    "CANADA": "🇨🇦", "CA": "🇨🇦", "AUSTRALIA": "🇦🇺", "AU": "🇦🇺",
    "GERMANY": "🇩🇪", "DE": "🇩🇪", "FRANCE": "🇫🇷", "FR": "🇫🇷",
    "BRAZIL": "🇧🇷", "BR": "🇧🇷", "INDIA": "🇮🇳", "IN": "🇮🇳",
    "CHINA": "🇨🇳", "CN": "🇨🇳", "JAPAN": "🇯🇵", "JP": "🇯🇵",
    "MEXICO": "🇲🇽", "MX": "🇲🇽", "UNITED ARAB EMIRATES": "🇦🇪", "UAE": "🇦🇪",
    "RUSSIA": "🇷🇺", "RUSSIAN FEDERATION": "🇷🇺", "RU": "🇷🇺",
    "SINGAPORE": "🇸🇬", "SG": "🇸🇬", "MALAYSIA": "🇲🇾", "MY": "🇲🇾",
    "NETHERLANDS": "🇳🇱", "NL": "🇳🇱", "SPAIN": "🇪🇸", "ES": "🇪🇸",
    "ITALY": "🇮🇹", "IT": "🇮🇹", "TURKEY": "🇹🇷", "TR": "🇹🇷"
}

def get_country_flag(country_name: str) -> str:
    if not country_name or country_name.upper() in ["N/A", "UNKNOWN", ""]:
        return "🌐"
    clean_name = country_name.strip().upper()
    if clean_name in COUNTRY_FLAG_MAP:
        return COUNTRY_FLAG_MAP[clean_name]
    if len(clean_name) == 2 and clean_name.isalpha():
        return "".join(chr(127397 + ord(char)) for char in clean_name)
    return "🌐"

def load_bin_data(file_path: str):
    global bin_database
    bin_database.clear()
    loaded_count = 0
    try:
        with open(file_path, mode="r", encoding="utf-8", errors="ignore") as file:
            reader = csv.DictReader(file)
            for row in reader:
                clean_row = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                bin_key = clean_row.get("bin")
                if bin_key:
                    clean_bin = re.sub(r"\D", "", bin_key)
                    bin_database[clean_bin] = clean_row
                    loaded_count += 1
        logging.info(f"Loaded {loaded_count:,} BIN records.")
    except Exception as e:
        logging.error(f"Error loading BIN file: {e}")

async def bin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ **Usage:** `/bin XXXXXX`\n\n**Example:** `/bin 453211`",
            parse_mode="Markdown"
        )
        return

    raw_digits = re.sub(r"\D", "", context.args[0])
    match = re.search(r"^(\d{6})", raw_digits)

    if not match:
        await update.message.reply_text("❌ Please enter at least 6 digits.")
        return

    bin_number = match.group(1)
    info = bin_database.get(bin_number)

    if not info:
        await update.message.reply_text(f"❌ BIN `{bin_number}` not found.", parse_mode="Markdown")
        return

    brand = (info.get("brand") or "N/A").upper()
    card_type = (info.get("type") or "N/A").upper()
    category = (info.get("category") or "N/A").upper()
    issuer = (info.get("issuer") or "N/A").upper()
    country_name = (info.get("countryname") or info.get("country") or "N/A").upper()
    flag_emoji = get_country_flag(country_name)

    response_text = (
        f"💳 **BIN LOOKUP:** `{bin_number}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ **Brand:** {brand}\n"
        f"⚡ **Type:** {card_type}\n"
        f"📊 **Category:** {category}\n"
        f"🏛️ **Issuer:** {issuer}\n"
        f"{flag_emoji} **Country:** {country_name}"
    )

    await update.message.reply_text(response_text, parse_mode="Markdown")

def main():
    keep_alive()  # Runs HTTP server in background for UptimeRobot ping
    load_bin_data(BIN_FILE_PATH)

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("bin", bin_command))
    app.run_polling()

if __name__ == "__main__":
    main()
