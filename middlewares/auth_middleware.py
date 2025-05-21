# middlewares/auth_middleware.py - Authentication middleware
from flask import request, redirect, url_for, session
from functools import wraps
from utils.logger import get_logger

# Initialize logger
logger = get_logger()

def auth_middleware():
    """
    Authentication middleware to protect admin routes
    
    Returns:
        None
    """
    # Check if route is admin route
    if request.path.startswith('/admin') and request.path != '/admin/login':
        # Check if user is logged in
        if 'admin_logged_in' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return redirect(url_for('admin.login', next=request.path))

def admin_required(f):
    """
    Decorator for admin required routes
    
    Args:
        f: Function to decorate
        
    Returns:
        Function: Decorated function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            logger.warning(f"Unauthorized access attempt to {request.path}")
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function