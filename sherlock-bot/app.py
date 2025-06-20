# app.py - Main Flask application with immediate initialization for Cloud Functions
import os
import sys
import traceback
from flask import Flask, request, jsonify

# Only load environment variables if not in Cloud Functions
if not os.getenv('K_SERVICE') and not os.getenv('FUNCTION_TARGET'):
    from dotenv import load_dotenv
    load_dotenv()

# Initialize logging immediately
from utils.logger import setup_logger
logger = setup_logger()

# Initialize Flask app
app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

# Load configuration
try:
    app.config.from_object('config.Config')
    logger.info("✅ Configuration loaded successfully")
except Exception as e:
    logger.error(f"❌ Error loading configuration: {str(e)}")

# Initialize Firebase
firebase_initialized = False
try:
    from firebase_init import initialize_firebase
    firebase_initialized = initialize_firebase()
    if not firebase_initialized:
        logger.error("❌ Firebase initialization failed, application may not function correctly")
    else:
        logger.info("✅ Firebase initialized successfully")
except Exception as e:
    logger.error(f"❌ Firebase initialization error: {str(e)}")
    firebase_initialized = False

# Register blueprints IMMEDIATELY - this is critical for Cloud Functions
try:
    from routes.webhook_routes import webhook_bp
    app.register_blueprint(webhook_bp, url_prefix='/webhook')
    logger.info("✅ Webhook routes registered at /webhook")
except Exception as e:
    logger.error(f"❌ Error registering webhook routes: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")

try:
    from routes.payment_routes import payment_bp
    app.register_blueprint(payment_bp, url_prefix='/payment')
    logger.info("✅ Payment routes registered at /payment")
except Exception as e:
    logger.error(f"❌ Error registering payment routes: {str(e)}")

try:
    from routes.admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    logger.info("✅ Admin routes registered at /admin")
except Exception as e:
    logger.error(f"❌ Error registering admin routes: {str(e)}")

# Register middlewares
try:
    from middlewares.auth_middleware import auth_middleware
    app.before_request(auth_middleware)
    logger.info("✅ Auth middleware registered")
except Exception as e:
    logger.error(f"❌ Error registering auth middleware: {str(e)}")

try:
    from middlewares.error_middleware import register_error_handlers
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

# Debug routes endpoint
@app.route('/debug/routes')
def debug_routes():
    """Debug endpoint to show all registered routes"""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'endpoint': rule.endpoint,
            'methods': list(rule.methods),
            'path': rule.rule
        })
    
    return jsonify({
        'routes': routes,
        'total': len(routes)
    })

# Debug Firebase endpoint
@app.route('/debug/firebase')
def debug_firebase():
    """Debug Firebase initialization issues"""
    import os
    
    debug_info = {
        'environment': os.getenv('FLASK_ENV', 'production'),
        'is_cloud_function': bool(os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET')),
        'env_vars': {
            'K_SERVICE': os.getenv('K_SERVICE'),
            'FUNCTION_TARGET': os.getenv('FUNCTION_TARGET'),
            'GOOGLE_APPLICATION_CREDENTIALS': os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            'FIREBASE_STORAGE_BUCKET': os.getenv('FIREBASE_STORAGE_BUCKET'),
            'FIREBASE_SERVICE_ACCOUNT': os.getenv('FIREBASE_SERVICE_ACCOUNT'),
            'GCP_PROJECT': os.getenv('GCP_PROJECT'),
            'GOOGLE_CLOUD_PROJECT': os.getenv('GOOGLE_CLOUD_PROJECT'),
        }
    }
    
    # Try to initialize Firebase again
    try:
        import firebase_admin
        
        # Check if already initialized
        if firebase_admin._apps:
            debug_info['firebase_status'] = 'already_initialized'
            debug_info['app_count'] = len(firebase_admin._apps)
        else:
            # Try to initialize
            if os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET'):
                # Cloud Function environment
                firebase_admin.initialize_app(options={
                    'storageBucket': os.getenv('FIREBASE_STORAGE_BUCKET', 'cvreview-d1d4b.appspot.com')
                })
                debug_info['firebase_status'] = 'initialized_with_default_credentials'
            else:
                debug_info['firebase_status'] = 'not_in_cloud_function'
        
        # Test Firestore connection
        from firebase_admin import firestore
        db = firestore.client()
        # Try a simple read
        test_collection = db.collection('_test').limit(1).get()
        debug_info['firestore_test'] = 'connected'
        
    except Exception as e:
        debug_info['firebase_error'] = str(e)
        debug_info['firebase_status'] = 'error'
    
    return jsonify(debug_info)

# Global exception handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"❌ Unhandled exception: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred'
    }), 500

# Log that the app module has loaded
logger.info("🚀 App module loaded, routes should be registered")

# CRITICAL FIX: Multiple checks to prevent Flask server from starting during deployment
def should_start_server():
    """Determine if we should start the Flask development server"""
    
    # Don't start if we're in Cloud Functions
    if os.getenv('K_SERVICE') or os.getenv('FUNCTION_TARGET'):
        logger.info("🚫 Cloud Functions environment detected - not starting Flask server")
        return False
    
    # Don't start if Firebase Functions is deploying
    if os.getenv('FIREBASE_CONFIG'):
        logger.info("🚫 Firebase deployment detected - not starting Flask server")
        return False
    
    # Don't start if we're being imported (not run directly)
    if __name__ != '__main__':
        logger.info("🚫 Module imported, not executed directly - not starting Flask server")
        return False
    
    # Don't start if we detect deployment-related arguments
    deployment_indicators = ['gunicorn', 'uwsgi', 'firebase', 'gcloud', 'functions-framework']
    for arg in sys.argv:
        if any(indicator in arg.lower() for indicator in deployment_indicators):
            logger.info(f"🚫 Deployment indicator found in args: {arg} - not starting Flask server")
            return False
    
    # Don't start if we're in a CI/CD environment
    ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI']
    if any(os.getenv(indicator) for indicator in ci_indicators):
        logger.info("🚫 CI/CD environment detected - not starting Flask server")
        return False
    
    # All checks passed - safe to start server
    logger.info("✅ Safe to start Flask development server")
    return True

# Only start the Flask development server if all conditions are met
if should_start_server():
    try:
        port = int(os.getenv('PORT', 8080))
        debug = os.getenv('FLASK_ENV') != 'production'
        
        logger.info(f"🚀 Starting Sherlock Bot development server on port {port}")
        app.run(host='0.0.0.0', port=port, debug=debug)
    except Exception as e:
        logger.error(f"❌ Error starting Flask server: {str(e)}")
else:
    logger.info("📱 App configured for Cloud Functions - ready for deployment")