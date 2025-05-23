# Twilio WhatsApp Integration Guide

This guide explains how to set up and configure Twilio WhatsApp integration for the Sherlock Bot CV Review service.

## Prerequisites

- Twilio Account SID
- Twilio Auth Token
- Twilio Phone Number

## Step 1: Set Up WhatsApp Sandbox

1. Log in to your Twilio account at [https://www.twilio.com/login](https://www.twilio.com/login)
2. Navigate to **Messaging** > **Try it out** > **Send a WhatsApp message**
3. Follow the instructions to join your Twilio WhatsApp Sandbox:
   - Send the provided code (e.g., `join example-word`) from your WhatsApp to Twilio's WhatsApp number
   - This connects your personal WhatsApp to the Twilio Sandbox for testing

## Step 2: Configure Webhook URLs

1. In the Twilio Console, go to **Messaging** > **Settings** > **WhatsApp Sandbox Settings**
2. Set the following webhook URLs:

   **When a message comes in:**
   https://your-firebase-app.web.app/webhook/twilio

**Status callback URL:**
https://your-firebase-app.web.app/webhook/twilio/status

3. Make sure to set the HTTP Method to `POST` for both webhooks

## Step 3: Test Basic Functionality

1. Run the WhatsApp test script to verify the integration:
```bash
python scripts/test_whatsapp.py +YOUR_PHONE_NUMBER

You should receive a test message on your WhatsApp
Reply to the message to verify that two-way communication works

Step 4: Test Webhook Reception
After deploying your application:

Run the webhook test script to verify that your application can receive webhooks:
bashpython scripts/webhook_test.py --url https://your-firebase-app.web.app/webhook/twilio --phone +YOUR_PHONE_NUMBER

Check your application logs to ensure the webhook was received and processed correctly

Step 5: Production Setup (When Ready)
For a production WhatsApp integration:

Apply for a WhatsApp Business API through Twilio:

Go to Messaging > WhatsApp > Senders
Click "Apply for a phone number"
Follow the application process


After approval, update your configuration:

Update TWILIO_PHONE_NUMBER with your new WhatsApp Business number
Create and register message templates for any business-initiated messages


Update your webhooks to the production endpoints

Troubleshooting

Message Not Received: Verify your WhatsApp is still connected to the Twilio Sandbox. The connection expires after 72 hours of inactivity.
Webhook Errors: Check your application logs and Twilio Console debugger for error details.
Authentication Errors: Verify that your Account SID and Auth Token are correct in your environment variables.

Security Notes

Keep your Auth Token secure - never commit it to version control or expose it publicly
In production, use environment variables or a secret management service to store these credentials
Rotate your Auth Token periodically for enhanced security