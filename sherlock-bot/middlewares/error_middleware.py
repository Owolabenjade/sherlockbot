# middlewares/error_middleware.py - Error handling middleware
from flask import jsonify
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def register_error_handlers(app):
    """
    Register error handlers for the Flask app
    
    Args:
        app: Flask app instance
        
    Returns:
        None
    """
    @app.errorhandler(400)
    def bad_request(error):
        logger.error(f"400 Bad Request: {error}")
        return jsonify({
            'error': 'Bad Request',
            'message': str(error)
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        logger.error(f"401 Unauthorized: {error}")
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        logger.error(f"403 Forbidden: {error}")
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        logger.error(f"404 Not Found: {error}")
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def server_error(error):
        logger.error(f"500 Server Error: {error}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500