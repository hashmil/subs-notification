import sqlite3
import datetime
import queue
import threading
from flask import Flask, request, render_template, redirect, url_for
from datetime import datetime, timedelta

app = Flask(__name__)

# Create a queue to store database connections
connection_pool = queue.Queue()

# Database path
database_path = "database/subscriptions.db"

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


def run_threaded(function):
    # Running the function in a separate thread
    thread = threading.Thread(target=function)
    thread.start()


if __name__ == "__main__":

    # Start the Flask app in a separate thread
    run_threaded(app.run(debug=True, host='0.0.0.0', port=3000))
