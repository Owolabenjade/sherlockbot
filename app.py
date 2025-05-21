# app.py - Main Flask application
import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from firebase_admin import credentials, initialize_app
from middlewares.error_middleware import register_error_handlers
from middlewares.auth_middleware import auth_middleware
from routes.webhook_routes import webhook_bp
from routes.payment_routes import payment_bp
from routes.admin_routes import admin_bp
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Initialize logging
logger = setup_logger()

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load configuration
app.config.from_object('config.Config')

# Initialize Firebase Admin SDK
if os.getenv('FLASK_ENV') == 'production':
    # Use application default credentials in production
    initialize_app()
else:
    # Use service account in development
    cred_path = os.getenv('FIREBASE_SERVICE_ACCOUNT')
    if cred_path:
        cred = credentials.Certificate(cred_path)
        initialize_app(cred, {
            'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET')
        })
    else:
        logger.warning("FIREBASE_SERVICE_ACCOUNT not set, Firebase features will not work")

# Register middlewares
app.before_request(auth_middleware)
register_error_handlers(app)

# Register blueprints
app.register_blueprint(webhook_bp, url_prefix='/webhook')
app.register_blueprint(payment_bp, url_prefix='/payment')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Root endpoint
@app.route('/')
def index():
    return "Sherlock Bot CV Review Service"

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') != 'production')