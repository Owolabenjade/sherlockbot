from firebase_functions import https_fn
import sys
import os
import io

# Add sherlock-bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sherlock-bot'))

@https_fn.on_request(
    region="africa-south1",
    memory=512,
    timeout_sec=300,
)
def app_function(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function entry point for Sherlock Bot in africa-south1."""
    from app import app
    
    # Debug logging
    print(f"🔄 Received {req.method} request to {req.path}")
    print(f"Headers: {dict(req.headers)}")
    
    # Convert Firebase request to WSGI environ
    environ = {
        'REQUEST_METHOD': req.method,
        'PATH_INFO': req.path or '/',
        'QUERY_STRING': req.query_string or '',
        'CONTENT_TYPE': req.headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(req.data)) if req.data else '0',
        'HTTP_HOST': req.headers.get('host', ''),
        'wsgi.input': io.BytesIO(req.data),
        'wsgi.url_scheme': 'https',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'SERVER_NAME': req.headers.get('host', '').split(':')[0] if req.headers.get('host') else 'localhost',
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
    }
    
    # Add all headers with proper formatting
    for key, value in req.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value
    
    # Debug environ
    print(f"WSGI environ PATH_INFO: {environ['PATH_INFO']}")
    print(f"WSGI environ REQUEST_METHOD: {environ['REQUEST_METHOD']}")
    
    try:
        # Handle the request with Flask
        response_data = []
        
        def start_response(status, headers):
            response_data.extend([status, headers])
        
        app_response = app(environ, start_response)
        response_body = b''.join(app_response)
        
        # Extract status code
        status_code = int(response_data[0].split()[0]) if response_data else 200
        
        # Extract headers
        headers = {}
        if len(response_data) > 1:
            for header, value in response_data[1]:
                headers[header] = value
        
        print(f"✅ Response: {status_code}")
        
        return https_fn.Response(
            response_body,
            status=status_code,
            headers=headers
        )
        
    except Exception as e:
        print(f"❌ Error in app_function: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Return error response
        import json
        error_response = json.dumps({
            'error': 'Internal server error',
            'message': str(e),
            'path': req.path,
            'method': req.method
        })
        
        return https_fn.Response(
            error_response,
            status=500,
            headers={'Content-Type': 'application/json'}
        )