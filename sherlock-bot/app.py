# app.py - Main Flask application
import os
import traceback
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from firebase_init import initialize_firebase
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

# Load configuration with error handling
try:
    app.config.from_object('config.Config')
    logger.info("✅ Configuration loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading configuration: {str(e)}")

# Initialize Firebase
try:
    firebase_initialized = initialize_firebase()
    if not firebase_initialized:
        logger.error("❌ Firebase initialization failed, application may not function correctly")
    else:
        logger.info("✅ Firebase initialized successfully")
except Exception as e:
    logger.error(f"❌ Firebase initialization error: {str(e)}")
    firebase_initialized = False

# Register middlewares with error handling
try:
    app.before_request(auth_middleware)
    logger.info("✅ Auth middleware registered")
except Exception as e:
    logger.error(f"❌ Error registering auth middleware: {str(e)}")

try:
    register_error_handlers(app)
    logger.info("✅ Error handlers registered")
except Exception as e:
    logger.error(f"❌ Error registering error handlers: {str(e)}")

# Add request logging for debugging
@app.before_request
def log_request_info():
    logger.info(f"🔄 {request.method} {request.path}")
    if request.form:
        logger.info(f"📝 Form data keys: {list(request.form.keys())}")

@app.after_request
def log_response_info(response):
    logger.info(f"✅ Response: {response.status_code} for {request.path}")
    return response

# Register blueprints with error handling
try:
    app.register_blueprint(webhook_bp, url_prefix='/webhook')
    logger.info("✅ Webhook routes registered")
except Exception as e:
    logger.error(f"❌ Error registering webhook routes: {str(e)}")

try:
    app.register_blueprint(payment_bp, url_prefix='/payment')
    logger.info("✅ Payment routes registered")
except Exception as e:
    logger.error(f"❌ Error registering payment routes: {str(e)}")

try:
    app.register_blueprint(admin_bp, url_prefix='/admin')
    logger.info("✅ Admin routes registered")
except Exception as e:
    logger.error(f"❌ Error registering admin routes: {str(e)}")

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        'service': 'Sherlock Bot CV Review Service',
        'status': 'active',
        'firebase': 'connected' if firebase_initialized else 'disconnected',
        'region': 'africa-south1'
    })

# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'ok',
        'firebase': 'connected' if firebase_initialized else 'disconnected',
        'region': 'africa-south1',
        'environment': os.getenv('FLASK_ENV', 'production')
    })

# Global exception handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"❌ Unhandled exception: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_ENV') != 'production'
    
    logger.info(f"🚀 Starting Sherlock Bot on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)