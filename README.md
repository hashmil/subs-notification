# Subscription Notification Web Interface

Notify 7 days within a subscriptions expire. And a web interfece.

This code is a Flask application that allows you to manage your subscriptions by adding, editing and deleting them. The application uses a SQLite database to store the subscriptions. It also features a homepage that displays all your subscriptions, along with a list of subscriptions that are expiring within the next 7 days. The application has a basic UI that allows you to add and edit your subscriptions, and you can access this UI by visiting the "/add" or "/edit" routes. The "/delete" route allows you to delete subscriptions from the database. The application is configured using a "config.ini" file, and it sends email notifications using the smtplib library. The code uses the schedule library to schedule tasks in the background.
