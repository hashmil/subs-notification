import os
import smtplib
import configparser
import sqlite3
import datetime
from flask import Flask, request, render_template, redirect, url_for
import queue
import threading


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
        current_date = datetime.datetime.now().date()
        next_week = current_date + datetime.timedelta(days=7)

        # Filter the subscriptions that are expiring within the next 7 days
        expiring_subscriptions = [sub for sub in subscriptions if (datetime.datetime.strptime(
            sub[2], "%Y-%m-%d").date() >= current_date) and (datetime.datetime.strptime(sub[2], "%Y-%m-%d").date() < next_week)]
        remaining_subscriptions = [sub for sub in subscriptions if datetime.datetime.strptime(
            sub[2], "%Y-%m-%d").date() not in [datetime.datetime.strptime(x[2], "%Y-%m-%d").date() for x in expiring_subscriptions]]

    return render_template("index.html", expiring_subscriptions=expiring_subscriptions, remaining_subscriptions=remaining_subscriptions)


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        with sqlite3.connect("subscriptions.db", detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()

            product = request.form["product"]
            expiry_date = request.form["expiry_date"]

            # Insert the new subscription into the database
            cursor.execute(
                "INSERT INTO subscriptions (product, expiry_date) VALUES (?, ?)", (product, expiry_date))
            conn.commit()

        return redirect(url_for("index"))
    else:
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
                expiry_date = datetime.datetime.strptime(
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


if __name__ == "__main__":
    import datetime

    app.run(debug=True)
