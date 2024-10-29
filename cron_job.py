import subprocess, schedule, time, os, psutil
from telegram_msg import *
from dotenv import load_dotenv

# Load the .env file
load_dotenv()

# Path to the main script and PID file
main_script = r"C:\Users\hp\Desktop\SlackReal_Time_python\slack_project\slack_automation.py"
pid_file = r"C:\Users\hp\Desktop\SlackReal_Time_python\slack_project\main_script.pid"  

SLACK_PATH = os.getenv("SLACK_PATH")

# Function to check if main script is running
def is_running():
    if os.path.exists(pid_file):
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        return psutil.pid_exists(pid)  
    return False

# Function to start main script
def start_script():
    send_telegram_message("Job execution started: Initiating scheduled task.")
    logging.info("Job execution started: Initiating scheduled task.")
    # Start the main script as a subprocess
    process = subprocess.Popen(["python", main_script], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    # Write the process ID to the PID file
    with open(pid_file, "w") as f:
        f.write(str(process.pid))

# Function to close Slack application
def close_slack():
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] and "Slack" in proc.info['name']:  
            proc.terminate()  # Terminate Slack
            print("Slack application closed.")
            logging.info("Slack application closed.")


# Function to stop main script
def stop_script():
    if is_running():
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        process = psutil.Process(pid)
        process.terminate()  
        print("Main script stopped.")
        logging.info("Job execution completed: Scheduled task finished successfully.")
        send_telegram_message("Job execution completed: Scheduled task finished successfully.")
        os.remove(pid_file)

    # Close Slack when the script stops
    close_slack()

# Schedule the tasks
schedule.every().day.at("9:28").do(start_script)
schedule.every().day.at("16:00").do(stop_script)

def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    run_scheduler()
