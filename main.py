import os
import smtplib
import configparser
import sqlite3
import datetime
from flask import Flask, request, render_template, redirect, url_for
import queue
import threading
import ssl
from datetime import datetime, timedelta
from configparser import ConfigParser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time


app = Flask(__name__)

# Load configuration from config.ini file
config = configparser.ConfigParser()
config.read("config.ini")

# Create a queue to store database connections
connection_pool = queue.Queue()


@app.route("/")
def index():
    with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
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
        with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()

            # Retrieve the product and expiry date from the form data
            product = request.form["product"]
            expiry_date = request.form["expiry_date"]

            # Insert the new subscription into the database
            cursor.execute(
                "INSERT INTO subscriptions (product, expiry_date) VALUES (?, ?)", (product, expiry_date))
            # Commit the changes to the database
            conn.commit()

        # Redirect the user to the index page
        return redirect(url_for("index"))
    else:
        # Render the add.html template
        return render_template("add.html")


@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        if request.method == "POST":
            try:
                product = request.form["product"]
                expiry_date = request.form["expiry_date"]

                # Ensure the expiry date is in the correct format
                expiry_date = datetime.strptime(
                    expiry_date, "%Y-%m-%d").date().strftime("%Y-%m-%d")

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
    with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
        cursor = conn.cursor()

        # Delete the subscription from the database
        cursor.execute("DELETE FROM subscriptions WHERE id=?", (id,))
        conn.commit()

    return redirect(url_for("index"))

# Email notification


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
            print("An email was sent with the list of upcoming expiring subscriptions.")
        else:
            print("No expiring subscriptions found within the next 7 days.")


# def run_every_day():
#     check_and_send_email()


if __name__ == "__main__":

    app.run(debug=True)
    check_and_send_email()

    # # Schedule the run_every_day function to run every day at 12:00 AM
    # schedule.every().day.at("23:11").do(run_every_day)

    # # Keep the program running and check for pending tasks every second
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
