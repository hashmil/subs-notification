# Subscription Manager Web Interface and Email Notifier

This is a subscription manager that allows you to keep track of your subscriptions on a web interface and get email notifications for upcoming expirations.

### Installation

1. Clone this repository:

```
git clone https://github.com/hashmil/subs-notification.git
```

2. Change into the `subs-notification` directory:

```
cd subscription-tracker
```

3. Install the required packages:

```
pip install -r requirements.txt
```

4. Create a `config.ini` file in the root directory with the following contents:

```
[email]
sender_email = your_email@gmail.com
sender_password = your_app_password
recipient_email = recipient_email@gmail.com
```

**Note:** The `sender_email` field must be a Gmail address, and you may need to create an app password in your Google account settings. To create an app password, follow these steps:

- Go to your Google account settings
- Click on "Security" in the left-hand menu
- Scroll down to the "Less secure app access" section and turn it on (if it's not already on)
- Click on "App passwords"
- Select "Mail" and "Other (custom name)" from the dropdown menus
- Enter a name for the app password (e.g. "Subscription Tracker") and click "Generate"
- Use the generated password as the `sender_password` field in your `config.ini` file
-

### Usage

To run the application, execute the following command:

```
python main.py
```

### Functionality

#### Homepage

The homepage displays a table of all subscriptions in the database. Subscriptions that are expiring within the next 7 days are highlighted in red. The table shows the product name, expiry date and an edit and delete button for each subscription.

#### Adding a Subscription

To add a new subscription, click the "Add Subscription" button on the homepage. Fill in the product name and expiry date, and click "Submit".

#### Editing a Subscription

To edit a subscription, click the "Edit" button next to the subscription on the homepage. This will take you to a page where you can edit the product name and expiry date. Click "Save" to update the subscription.

#### Deleting a Subscription

To delete a subscription, click the "Delete" button next to the subscription on the homepage. This will remove the subscription from the database.

## Subscription Expiration Notifier

This is a Python script that sends email notifications to a user for any subscriptions that are expiring within the next 7 days. It uses the same database file as the Subscription Manager Web Application.

### Usage

To run the script, execute the following command:

```
python notifications.py
```

This will start the script and schedule it to run once every day at 6:00 PM.

### Functionality

#### Email Notifications

The script checks the database for any subscriptions that are expiring within the next 7 days. If any are found, an email is sent to the specified recipient email address with the product name and expiry date for each subscription. If no subscriptions are found to be expiring within the next 7 days, no email is sent.

#### Scheduling

The script uses the `schedule` library to schedule the `check_and_send_email()` function to run once every day at 6:00 PM. This can be customized by changing the `schedule.every().day.at("18:00")` line in the script.

#### Database

The script uses the same database file as the Subscription Manager Web Application to retrieve subscription data. The database is checked for subscriptions that are expiring within the next 7 days, and if any are found, an email is sent with the relevant data.
