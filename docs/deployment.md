# Deployment Guide

This guide explains how to deploy the Sherlock Bot CV Review service to Firebase.

## Prerequisites

- Firebase CLI installed (`npm install -g firebase-tools`)
- Python 3.10+ installed
- All environment variables configured

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sherlock-bot.git
   cd sherlock-bot

2. Create a virtual environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:
bashpip install -r requirements.txt

Configure environment variables:
bashcp .env.example .env
# Edit .env with your actual values

Set up Firebase:
bashfirebase login
firebase init

Run locally:
bashpython app.py


Deployment Steps

Run pre-deployment checks:
bashpython scripts/pre_deploy_check.py

Deploy to Firebase:
bashchmod +x scripts/deploy.sh
./scripts/deploy.sh

Test the deployment:
bashpython scripts/test_whatsapp.py +YOUR_PHONE_NUMBER


Environment Variables
Ensure all required environment variables are set:

SECRET_KEY: Flask secret key
FIREBASE_SERVICE_ACCOUNT: Path to service account JSON
FIREBASE_STORAGE_BUCKET: Firebase storage bucket name
TWILIO_ACCOUNT_SID: Twilio account SID
TWILIO_AUTH_TOKEN: Twilio auth token
TWILIO_PHONE_NUMBER: Twilio WhatsApp number
PAYSTACK_SECRET_KEY: Paystack secret key
SENDGRID_API_KEY: SendGrid API key
EMAIL_FROM: Sender email address
ADMIN_USERNAME: Admin dashboard username
ADMIN_PASSWORD: Admin dashboard password
BASE_URL: Application base URL

Post-Deployment

Configure Twilio webhook URLs in Twilio Console
Test WhatsApp integration
Test payment flow
Monitor logs for any issues

Troubleshooting

Check Firebase Functions logs: firebase functions:log
Verify environment variables are set correctly
Ensure Firebase rules allow proper access
Check Twilio webhook configuration