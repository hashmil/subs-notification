import smtplib
import configparser
import sqlite3
import queue
import threading
import ssl
import schedule
import time
from configparser import ConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# Load configuration from config.ini file
config = configparser.ConfigParser()
config.read("config.ini")

# Create a queue to store database connections
connection_pool = queue.Queue()


def send_email(subject, body, recipient_email, sender_email, password):
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())


def check_and_send_email():
    # Load the email configuration from the config.ini file
    config = ConfigParser()
    config.read("config.ini")
    sender_email = config.get("email", "sender_email")
    password = config.get("email", "sender_password")
    recipient_email = config.get("email", "recipient_email")

    with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        # Get the subscriptions expiring in the next 7 days
        expiring_subscriptions = cursor.execute(
            "SELECT * FROM subscriptions WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')").fetchall()

        # Only send an email if there are any subscriptions expiring in the next 7 days
        if expiring_subscriptions:
            body = "The following subscriptions will be expiring within the next 7 days:\n\n"
            for subscription in expiring_subscriptions:
                body += f"Product: {subscription[1]}\nExpiry Date: {subscription[2]}\n\n"

            subject = "Upcoming Subscription Expirations"
            send_email(subject, body, recipient_email, sender_email, password)
            print(
                "📧 --> An email was sent with the list of upcoming expiring subscriptions.")
        else:
            print("🤷🏾‍♂️ --> No expiring subscriptions found within the next 7 days.")


def run_threaded(function):
    # Running the function in a separate thread
    thread = threading.Thread(target=function)
    thread.start()


def server_start_email():
    run_threaded(check_and_send_email)
    print("🟠 Startup")


def scheduled_email():
    run_threaded(check_and_send_email)
    print("🟢 Scheduled")


if __name__ == "__main__":
    # Schedule the check_and_send_email function to run once every day at a given time
    schedule.every().day.at("18:00").do(scheduled_email)

    # Start the email notification thread
    server_start_email()

    # Keep the main thread running and checking the scheduled tasks
    while True:
        schedule.run_pending()
        time.sleep(1)
