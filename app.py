import os
import sqlite3
import datetime
import queue
import threading
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime, timedelta
from configparser import ConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl
import smtplib
import schedule
import time

app = Flask(__name__)

# Load configuration from config.ini file
config = ConfigParser()

# Config path
config_path = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "config.ini")

config.read(config_path)

# Create a queue to store database connections
connection_pool = queue.Queue()

# Check for database directory, if not create one

database_dir = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), 'database')

if not os.path.exists(database_dir):
    os.makedirs(database_dir)
    print(f"Directory '{database_dir}' created successfully.")
else:
    print(f"Directory '{database_dir}' already exists.")

# Database path
database_path = os.path.join(os.path.abspath(
    os.path.dirname(__file__)), "database/subscriptions.db")

# Create a database if it doesnt exist


def create_database():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product TEXT NOT NULL,
        expiry_date TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def send_email(subject, body, recipient_email, sender_email, password):
    message = MIMEMultipart()
    message["From"] = f"Subscription Manager <{sender_email}>"
    message["To"] = recipient_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, recipient_email, message.as_string())    


def check_and_send_email(is_test_email=False):
    # Use the config object passed in from the settings function
    sender_email = config.get("email", "sender_email")
    password = config.get("email", "sender_password")
    recipient_email = config.get("email", "recipient_email")
    scheduled_time = config.get("email", "scheduled_time")

    with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        # Get the subscriptions expiring in the next 7 days
        expiring_subscriptions = cursor.execute(
            "SELECT * FROM subscriptions WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')").fetchall()

        # Only send an email if there are any subscriptions expiring in the next 7 days
        if expiring_subscriptions and (is_test_email or datetime.now().strftime('%H:%M') >= scheduled_time):
            body = "The following subscriptions will be expiring within the next 7 days:\n\n"
            for subscription in expiring_subscriptions:
                body += f"Product: {subscription[1]}\nExpiry Date: {subscription[2]}\n\n"

            subject = "Upcoming Subscription Expirations"
            send_email(subject, body, recipient_email, sender_email, password)

            # Log the time the email was sent
            print(f"📧 --> An email was sent with the list of upcoming expiring subscriptions at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            return True
        else:
            print("❎ --> No expiring subscriptions found within the next 7 days.")
            print("Current time: ", datetime.now().strftime('%H:%M'))
            return False

@app.route("/")
def index():
    create_database()
    with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        # Retrieve all subscriptions from the database
        cursor.execute("SELECT * FROM subscriptions")
        subscriptions = cursor.fetchall()

        # Get the current date and the date 7 days from now
        current_date = datetime.now().date()
        next_week = current_date + timedelta(days=7)

        # Filter the subscriptions that are expiring within the next 7 days
        expiring_subscriptions = [sub for sub in subscriptions if (datetime.strptime(
            sub[2], "%Y-%m-%d").date() >= current_date) and (datetime.strptime(sub[2], "%Y-%m-%d").date() < next_week)]
        remaining_subscriptions = [sub for sub in subscriptions if datetime.strptime(
            sub[2], "%Y-%m-%d").date() not in [datetime.strptime(x[2], "%Y-%m-%d").date() for x in expiring_subscriptions]]

    return render_template("index.html", expiring_subscriptions=expiring_subscriptions, remaining_subscriptions=remaining_subscriptions)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        # Connect to the database
        with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()

                    # Retrieve the product and expiry date from the form data
        product = request.form["product"]
        expiry_date_str = request.form["expiry_date"]

        # Check if the date input is not an empty string
        if not expiry_date_str:
            return render_template("add.html", error="Expiry date cannot be empty.")

        # Check if the date input is valid
        try:
            expiry_date = datetime.strptime(
                expiry_date_str, '%Y-%m-%d').date()
        except ValueError:
            # If the date is not in the correct format, return an error message
            return render_template("add.html", error="Invalid date format. Please use YYYY-MM-DD.")

        # Insert the new subscription into the database
        cursor.execute(
            "INSERT INTO subscriptions (product, expiry_date) VALUES (?, ?)", (product, expiry_date))
        conn.commit()

        # Schedule an email check for the next day
        run_threaded(schedule.run_pending)
        print("📅 --> An email check has been scheduled for the next day.")

        # Redirect the user to the index page
        return redirect(url_for("index"))
    else:
        # Render the add.html template
        return render_template("add.html")

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            try:
                product = request.form["product"]
                expiry_date_str = request.form["expiry_date"]

                if not expiry_date_str:
                    return render_template("edit.html", subscription=subscription, error="Expiry date is required.")

                # Ensure the expiry date is in the correct format
                expiry_date = datetime.strptime(
                    expiry_date_str, "%Y-%m-%d").date().strftime("%Y-%m-%d")

                # Update the subscription in the database
                cursor.execute(
                    "UPDATE subscriptions SET product=?, expiry_date=? WHERE id=?", (product, expiry_date, id))
                conn.commit()

                return redirect(url_for("index"))
            except Exception as e:
                print("Error updating subscription: ", e)
                return "Error updating subscription", 500

        else:
            # Retrieve the subscription from the database
            cursor.execute("SELECT * FROM subscriptions WHERE id=?", (id,))
            subscription = cursor.fetchone()

            if subscription is None:
                return "Subscription not found", 404
            else:
                return render_template("edit.html", subscription=subscription)

@app.route("/delete/<int:id>")
def delete(id):
    with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        # Delete the subscription from the database
        cursor.execute("DELETE FROM subscriptions WHERE id=?", (id,))
        conn.commit()

    return redirect(url_for("index"))

@app.route("/settings", methods=["GET", "POST"])
def settings():
    # Load the email configuration from the config.ini file
    config = ConfigParser()
    config.read(config_path)

    success = None

    if request.method == "POST":
        # Get the updated email settings from the form data
        sender_email = request.form["sender_email"]
        sender_password = request.form["sender_password"]
        recipient_email = request.form["recipient_email"]
        scheduled_time = request.form["scheduled_time"]

        # Update the email configuration in the config.ini file
        config.set("email", "sender_email", sender_email)
        config.set("email", "sender_password", sender_password)
        config.set("email", "recipient_email", recipient_email)
        config.set("email", "scheduled_time", scheduled_time)

        with open(config_path, "w") as config_file:
            config.write(config_file)

        # Reschedule the check_and_send_email function to run at the new scheduled time
        schedule.clear(tag="check_and_send_email")
        schedule.every().day.at(scheduled_time).do(check_and_send_email).tag("check_and_send_email")

        success = "Email settings updated successfully."

        # Render the settings.html template with a success message
        return render_template("settings.html", sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, scheduled_time=scheduled_time, success="Email settings updated successfully.")

    else:
        sender_email = config.get("email", "sender_email")
        sender_password = config.get("email", "sender_password")
        recipient_email = config.get("email", "recipient_email")
        scheduled_time = config.get("email", "scheduled_time")

        # Render the settings.html template
        return render_template("settings.html", sender_email=sender_email, sender_password=sender_password, recipient_email=recipient_email, scheduled_time=scheduled_time)


@app.route("/test-email", methods=["POST"])
def test_email():
    # Load the email configuration from the config.ini file
    config.read(config_path)
    sender_email = config.get("email", "sender_email")
    password = config.get("email", "sender_password")
    recipient_email = config.get("email", "recipient_email")
    scheduled_time = config.get("email", "scheduled_time")

    # Get the subscriptions expiring in the next 7 days
    expiring_subscriptions = []
    with sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()
        expiring_subscriptions = cursor.execute(
            "SELECT * FROM subscriptions WHERE expiry_date BETWEEN date('now') AND date('now', '+7 days')").fetchall()

    # Only send a test email if there are any subscriptions expiring in the next 7 days
    if not expiring_subscriptions:
        message = "No expiring subscriptions found within the next 7 days."
        return render_template("settings.html", message=message)

    # Get the current date and time
    current_time = datetime.now().strftime('%H:%M')

    # Prepare the email body
    body = "This is a test email to confirm that the email notification settings are working.\n\n"
    body += "The following subscriptions will be expiring within the next 7 days:\n\n"
    for subscription in expiring_subscriptions:
        body += f"Product: {subscription[1]}\nExpiry Date: {subscription[2]}\n\n"

    # Send a test email
    subject = "Test Email Notification"
    send_email(subject, body, recipient_email, sender_email, password)

    # Display a success message to the user
    message = "Test email sent successfully."
    return render_template("settings.html", message=message)


def run_threaded(function):
    # Running the function in a separate thread
    thread = threading.Thread(target=function)
    thread.start()


def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    create_database()
    scheduled_time = config.get("email", "scheduled_time")
    schedule.every().day.at(scheduled_time).do(check_and_send_email).tag("check_and_send_email")
    schedule.run_all()
    t = threading.Thread(target=run_schedule)
    t.start()
    app.run(debug=True, host='0.0.0.0', port=3000)




