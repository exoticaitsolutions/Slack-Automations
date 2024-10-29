import datetime
import re
import time, os
import json, traceback, sys, logging, schedule, requests, pyperclip, subprocess
from pynput.keyboard import Key, Controller as KeyboardController
from pynput.mouse import Button, Controller as MouseController
import pygetwindow as gw
from telegram_msg import *
from dotenv import load_dotenv

# Set up logging
# logging.basicConfig(filename='logs/slack_automation.log', level=logging.INFO,
#                     format='%(asctime)s - %(levelname)s - %(message)s')

# Load the .env file
load_dotenv()

SLACK_PATH = os.getenv("SLACK_PATH")
CHANNEL_NAME = os.getenv("CHANNEL_NAME")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

check_script_for_every_hours = datetime.datetime.now() 

# Replace these with your relative coordinates within the Slack app window
MESSAGE_AREA = {
    'x1': 960,
    'y1': 430,
    'width': 430,  
    'height': 960 
    
}

# Global variables
last_clipboard_content = ""
message_counter = 0 # Initialize the message counter

def launch_slack():
    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.Popen(SLACK_PATH, startupinfo=startupinfo)
        logging.info("Slack application launched successfully.")
    except Exception as e:
        logging.error(f"Error launching Slack: {str(e)}")
        log_and_notify_error(f"Error launching Slack: {str(e)}\n{traceback.format_exc()}")

def activate_slack_window():
    try:
        # Attempt to find the Slack window with the specified title
        slack_windows = gw.getWindowsWithTitle(CHANNEL_NAME)
        
        # If no Slack window is found, log the event, send notification, and launch Slack
        if not slack_windows:
            error_message = 'Slack window not found, launching Slack...'
            logging.info(error_message)
            log_and_notify_error(error_message)  
            launch_slack()
            time.sleep(5)  
            
            # Re-check for any Slack window (not necessarily titled)
            slack_windows = gw.getWindowsWithTitle('Slack')
        
        # If Slack window is found after retry, activate it
        if slack_windows:
            slack_window = slack_windows[0]
            slack_window.activate()
            logging.info('Slack window activated.')
            print('Slack window activated...')
            time.sleep(20)
        else:
            # Log error if Slack is still not found after launch attempt
            error_message = 'Failed to  Slack window activated.'
            logging.error(error_message)
            log_and_notify_error(error_message)
            print(error_message)
        
    except Exception as e:
        logging.error(f"Error while activating Slack window: {str(e)}")
        log_and_notify_error(f"Error while activating Slack window: {str(e)}\n{traceback.format_exc()}")


def filter_message_content(message):
    """Filter out emojis, Slack reactions, and irrelevant content from the message."""
    # Remove emojis
    filtered_message = re.sub(r':[^\s:]+:', '', message)

    # Ignore empty messages, reactions, and irrelevant content
    if (not filtered_message or
        filtered_message.startswith('Reaction:') or
        filtered_message.lower() in ['typing...', 'seen', 'delivered','Make a note of something']):
        return None

    return filtered_message

def copy_latest_message():
    global last_clipboard_content
    global message_counter
    global check_script_for_every_hours
    activate_slack_window()
    
    if datetime.datetime.now() >= check_script_for_every_hours:
        logging.info("Scheduled job execution initiated: Task running at hourly interval.")
        send_telegram_message("Scheduled job execution initiated: Task running at hourly interval.")
        check_script_for_every_hours = datetime.datetime.now() + datetime.timedelta(hours=1) 
    
    try:
        mouse_controller = MouseController()
        keyboard_controller = KeyboardController()

        # Click to focus message area
        mouse_controller.position = (MESSAGE_AREA['x1'], MESSAGE_AREA['y1'])
        mouse_controller.click(Button.left, 1)

        # Select all and copy
        with keyboard_controller.pressed(Key.ctrl):
            keyboard_controller.press('a')
            keyboard_controller.release('a')
            keyboard_controller.press('c')
            keyboard_controller.release('c')
        
        time.sleep(0.5)  # Wait for clipboard content to update
        clipboard_content = pyperclip.paste()

        # Check if clipboard content has changed
        if clipboard_content != last_clipboard_content:
            last_lines = last_clipboard_content.splitlines()
            new_lines = clipboard_content.splitlines()

            # Find the new lines not present in the last lines
            delta_lines = [line for line in new_lines if line not in last_lines]

            # Filter and collect valid new messages
            filtered_delta_lines = [filter_message_content(line) for line in delta_lines if line]

            if filtered_delta_lines:
                delta_content = ' '.join(filter(None, filtered_delta_lines))
                # Remove timestamps in the format HH:MM
                time_pattern = r'\b\d{1,2}:\d{2}\b'
                new_text = re.sub(time_pattern, '', delta_content)
                if message_counter != 0:
                    logging.info(f'New Message(s): {new_text}')

                    # Send the messages to the API
                    send_messages_to_api(new_text)
                message_counter +=1

            # Update last clipboard content
            last_clipboard_content = clipboard_content

    except Exception as e:
        log_and_notify_error(f"Error copying latest message: {str(e)}")

def send_messages_to_api(message_text):
    # The message payload
    message = {
        'massage': message_text
    }
    # Send the POST request to the webhook URL
    response = requests.post(
        WEBHOOK_URL, 
        data=json.dumps(message),
        headers={'Content-Type': 'application/json'}
    )
    # Check the response
    if response.status_code in (200, 201):
        print('Message sent successfully!')
        logging.info("Message sent to API successfully.")
    else:
        logging.error(f'Failed to send message. Status code: {response.status_code}, response: {response.text}')
        log_and_notify_error(f'Failed to send message. Status code: {response.status_code}, response: {response.text}')

def start_monitoring():
    schedule.every(10).seconds.do(copy_latest_message)
    logging.info("Starting Slack message monitoring.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logging.error(f"Error in monitoring loop: {str(e)}")
            time.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    try:  
        start_monitoring()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        log_and_notify_error(f"An error occurred: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)
