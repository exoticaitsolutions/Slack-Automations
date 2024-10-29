import logging, requests, os
from dotenv import load_dotenv


# Set up logging
logging.basicConfig(filename='logs/slack_automation.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Load the .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def send_telegram_message(message):
    """Send a message to the Telegram chat."""
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        logging.error(f"Failed to send message to Telegram: {str(e)}")

def log_and_notify_error(error_message):
    """Log an error and send a notification to Telegram."""
    # Send a critical error alert via Telegram
    send_telegram_message(f"Critical error occurred: {error_message}")

def cron_job_msg(message):
    #send a alert via telegram 
    send_telegram_message(f"{message}")
