#!/bin/bash
# scripts/deploy.sh - Comprehensive deployment script for Firebase

# Exit on error
set -e

# Load environment variables
if [ -f .env ]; then
  echo "Loading environment variables from .env"
  export $(grep -v '^#' .env | xargs)
fi

# Check for required variables
if [ -z "$FIREBASE_PROJECT_ID" ]; then
  echo "Error: FIREBASE_PROJECT_ID not set. Please add it to your .env file."
  exit 1
fi

echo "Deploying to Firebase Project: $FIREBASE_PROJECT_ID"

# Create or update .firebaserc
echo "{
  \"projects\": {
    \"default\": \"$FIREBASE_PROJECT_ID\"
  }
}" > .firebaserc

# Generate .env.yaml for Cloud Functions from .env
echo "# Auto-generated from .env" > functions/.env.yaml
while IFS= read -r line; do
  # Skip comments and empty lines
  if [[ $line != \#* ]] && [ -n "$line" ]; then
    key=$(echo $line | cut -d= -f1)
    value=$(echo $line | cut -d= -f2-)
    echo "$key: \"$value\"" >> functions/.env.yaml
  fi
done < .env

# Install dependencies if needed
if [ "$1" == "--install-deps" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt
fi

# Run tests
echo "Running tests..."
python -m pytest tests/

# Deploy Firestore security rules
echo "Deploying Firestore security rules..."
firebase deploy --only firestore:rules

# Deploy Storage security rules
echo "Deploying Storage security rules..."
firebase deploy --only storage

# Deploy Firestore indexes
echo "Deploying Firestore indexes..."
firebase deploy --only firestore:indexes

# Deploy Cloud Functions
echo "Deploying Cloud Functions..."
firebase deploy --only functions

# Deploy Hosting
echo "Deploying static assets to Hosting..."
firebase deploy --only hosting

echo "Deployment completed successfully!"