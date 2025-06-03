# main.py - Cloud Function entry point
import functions_framework
from app import app

@functions_framework.http
def app_function(request):
    """
    HTTP Cloud Function entry point for Flask app.
    
    Args:
        request: The request object from Cloud Functions
        
    Returns:
        Flask response
    """
    # Use the request context to handle the Flask app
    with app.test_request_context(
        path=request.full_path,
        method=request.method,
        headers=list(request.headers.items()),
        data=request.get_data(),
        content_type=request.content_type
    ):
        # Dispatch the request to Flask
        response = app.full_dispatch_request()
        return response