Local Setup
Install dependencies:
pip install -r requirements.txt

For local testing, start AWS Academy Lab and update the placeholder credentials in app.py and music.py:

AWS_ACCESS_KEY_ID = "PASTE_ACCESS_KEY_HERE"
AWS_SECRET_ACCESS_KEY = "PASTE_SECRET_KEY_HERE"
AWS_SESSION_TOKEN = "PASTE_SESSION_TOKEN_HERE"

Initialise DynamoDB tables and upload images to S3:
python music.py
Run the Flask app locally:
python app.py

Open:
http://127.0.0.1:5000

EC2 Deployment Summary
The app has been tested on EC2 using:
sudo python3 -m gunicorn --workers 2 --bind 0.0.0.0:80 app:app

A systemd service can be used to keep the app running after SSH disconnects.
The EC2 instance should use LabInstanceProfile / LabRole so the app can access DynamoDB and S3 without hardcoded AWS credentials.
