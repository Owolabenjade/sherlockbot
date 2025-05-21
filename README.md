# Sherlock Bot - CV Review Service

Sherlock Bot is a WhatsApp-based CV review service that offers both free basic and paid advanced CV reviews. Users can upload their CV via WhatsApp, receive personalized feedback, and get comprehensive reports to improve their job application materials.

## Features

- **WhatsApp Integration**: Conversational interface via WhatsApp
- **Document Processing**: Analyze PDF and DOCX CV files
- **Two-tier Service**:
  - Free basic review with key improvement areas
  - Paid advanced review with comprehensive analysis and PDF report
- **Payment Integration**: Secure payment processing via Paystack
- **Email Delivery**: Option to receive reports via email
- **Admin Dashboard**: Monitor usage, reviews, and payments

## Technology Stack

- **Backend**: Python (Flask)
- **Database**: Firebase Firestore
- **Storage**: Firebase Storage
- **Messaging**: Twilio WhatsApp API
- **Payments**: Paystack
- **Email**: SendGrid
- **Deployment**: Firebase Cloud Functions/Google Cloud Run

## Installation

### Prerequisites

- Python 3.10 or higher
- Firebase account
- Twilio account
- Paystack account
- SendGrid account

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/sherlock-bot.git
cd sherlock-bot