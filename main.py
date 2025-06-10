from firebase_functions import https_fn
import sys
import os

# Add sherlock-bot directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'sherlock-bot'))

# Specify the region for Africa South 1
@https_fn.on_request(
    region="africa-south1",
    memory=256,  # Optional: specify memory in MB
    timeout_sec=60,  # Optional: specify timeout in seconds
)
def app_function(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function entry point for Sherlock Bot."""
    from app import app
    
    # Convert Firebase request to WSGI environ
    environ = {
        'REQUEST_METHOD': req.method,
        'PATH_INFO': req.path or '/',
        'QUERY_STRING': req.query_string or '',
        'CONTENT_TYPE': req.headers.get('content-type', ''),
        'CONTENT_LENGTH': str(len(req.data)) if req.data else '0',
        'HTTP_HOST': req.headers.get('host', ''),
        'wsgi.input': req.stream,
        'wsgi.url_scheme': 'https',
        'wsgi.errors': sys.stderr,
        'wsgi.multithread': False,
        'wsgi.multiprocess': True,
        'wsgi.run_once': False,
        'SERVER_NAME': req.headers.get('host', '').split(':')[0] if req.headers.get('host') else 'localhost',
        'SERVER_PORT': '443',
        'SERVER_PROTOCOL': 'HTTP/1.1',
    }
    
    # Add all headers
    for key, value in req.headers.items():
        key = key.upper().replace('-', '_')
        if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            key = f'HTTP_{key}'
        environ[key] = value
    
    # Handle the request with Flask
    response_data = []
    
    def start_response(status, headers):
        response_data.extend([status, headers])
    
    app_response = app(environ, start_response)
    response_body = b''.join(app_response)
    
    # Extract status code
    status_code = int(response_data[0].split()[0])
    
    # Extract headers if available
    headers = {}
    if len(response_data) > 1:
        for header, value in response_data[1]:
            headers[header] = value
    
    return https_fn.Response(
        response_body,
        status=status_code,
        headers=headers
    )
