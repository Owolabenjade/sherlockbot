#!/bin/bash
# deploy-with-env.sh - Deploy to Firebase with environment variables

# First, set the environment variables in Firebase Functions config
echo "Setting environment variables in Firebase Functions..."

# Set Twilio credentials
firebase functions:config:set \
  twilio.account_sid="$TWILIO_ACCOUNT_SID" \
  twilio.auth_token="$TWILIO_AUTH_TOKEN" \
  twilio.phone_number="$TWILIO_PHONE_NUMBER"

# Set Paystack credentials  
firebase functions:config:set \
  paystack.secret_key="$PAYSTACK_SECRET_KEY" \
  paystack.public_key="$PAYSTACK_PUBLIC_KEY"

# Set SendGrid credentials
firebase functions:config:set \
  sendgrid.api_key="$SENDGRID_API_KEY" \
  email.from="$EMAIL_FROM" \
  email.from_name="$EMAIL_FROM_NAME"

# Set other configs
firebase functions:config:set \
  app.admin_username="$ADMIN_USERNAME" \
  app.admin_password="$ADMIN_PASSWORD" \
  app.cv_analysis_api_url="$CV_ANALYSIS_API_URL" \
  app.storage_bucket="$STORAGE_BUCKET"

# Deploy the functions
echo "Deploying to Firebase..."
firebase deploy --only functions

echo "Deployment complete!"