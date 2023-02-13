# Subscription Manager

This is a subscription manager that allows you to keep track of your subscriptions on a web interface and get email notifications for upcoming expirations.

### Installation

1. Clone this repository:

```
git clone https://github.com/hashmil/subs-notification.git
```

2.  Change into the `subs-notification` directory:

```
cd subscription-tracker
```

3.  Install the required packages:

```
pip install -r requirements.txt
```

4.  Create a `config.ini` file in the root directory with the following contents:

```
[email]
sender_email = your_email_address@gmail.com
sender_password = your_gmail_app_password
recipient_email = recipient_email_address@example.com
scheduled_time = 12:00
```

**Note:** The `sender_email` field must be a Gmail address, and you may need to create an app password in your Google account settings. To create an app password, follow these steps:

- Go to your Google account settings
- Click on "Security" in the left-hand menu
- Scroll down to the "Less secure app access" section and turn it on (if it's not already on)
- Click on "App passwords"
- Select "Mail" and "Other (custom name)" from the dropdown menus
- Enter a name for the app password (e.g. "Subscription Tracker") and click "Generate"
- Use the generated password as the `sender_password` field in your `config.ini` file

### Usage

To run the application, execute the following command:

```
python app.py
```

The application will then be available at `http://localhost:5000`.

### Functionality

#### Homepage

The homepage displays a table of all subscriptions in the database. Subscriptions that are expiring within the next 7 days are highlighted in red. The table shows the product name, expiry date and an edit and delete button for each subscription.

#### Adding a Subscription

To add a new subscription, click the "Add Subscription" button on the homepage. Fill in the product name and expiry date, and click "Submit".

#### Editing a Subscription

To edit a subscription, click the "Edit" button next to the subscription on the homepage. This will take you to a page where you can edit the product name and expiry date. Click "Save" to update the subscription.

#### Deleting a Subscription

To delete a subscription, click the "Delete" button next to the subscription on the homepage. This will remove the subscription from the database.

#### Email Notifications

The script checks the database for any subscriptions that are expiring within the next 7 days. If any are found, an email is sent to the specified recipient email address with the product name and expiry date for each subscription. If no subscriptions are found to be expiring within the next 7 days, no email is sent. The email address can be updated in the `Settings` page or in `config.ini`

Use the `Send test email` button in the `Settings` page to check if your email settings are working.

#### Scheduling

The script uses the `schedule` library to schedule the `check_and_send_email()` function to run once every day at the chosen time. This time can be changed in the `settings` page or in `config.ini`
