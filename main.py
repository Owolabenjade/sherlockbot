from firebase_functions import https_fn
import sys
import os
import io

# Add sherlock-bot directory to Python path (where app.py actually is)
sherlock_bot_dir = os.path.join(os.path.dirname(__file__), 'sherlock-bot')
sys.path.insert(0, sherlock_bot_dir)

# Debug: Print the paths and available files
print(f"Current working directory: {os.getcwd()}")
print(f"__file__ directory: {os.path.dirname(__file__)}")
print(f"sherlock-bot directory: {sherlock_bot_dir}")
print(f"sherlock-bot exists: {os.path.exists(sherlock_bot_dir)}")
if os.path.exists(sherlock_bot_dir):
    print(f"Files in sherlock-bot: {[f for f in os.listdir(sherlock_bot_dir) if f.endswith('.py')]}")
print(f"sys.path first entry: {sys.path[0]}")

@https_fn.on_request(
    region="africa-south1",
    memory=512,
    timeout_sec=300,
)
def app_function(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function entry point for Sherlock Bot."""
    
    try:
        # Debug: Confirm we can see the sherlock-bot directory
        sherlock_bot_dir = os.path.join(os.path.dirname(__file__), 'sherlock-bot')
        print(f"Importing from: {sherlock_bot_dir}")
        print(f"app.py exists: {os.path.exists(os.path.join(sherlock_bot_dir, 'app.py'))}")
        
        # Import Flask app from sherlock-bot directory
        from app import app
        
        # Create a proper BytesIO object that supports seeking
        body = io.BytesIO(req.data)
        
        # Convert Firebase request to WSGI environ
        environ = {
            'REQUEST_METHOD': req.method,
            'SCRIPT_NAME': '',
            'PATH_INFO': req.path or '/',
            'QUERY_STRING': req.query_string or '',
            'CONTENT_TYPE': req.headers.get('content-type', 'application/x-www-form-urlencoded'),
            'CONTENT_LENGTH': str(len(req.data)) if req.data else '0',
            'SERVER_NAME': req.headers.get('host', '').split(':')[0] if req.headers.get('host') else 'localhost',
            'SERVER_PORT': '443',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.version': (1, 0),
            'wsgi.url_scheme': 'https',
            'wsgi.input': body,
            'wsgi.errors': sys.stderr,
            'wsgi.multithread': False,
            'wsgi.multiprocess': True,
            'wsgi.run_once': False,
        }
        
        # Add headers to environ
        for key, value in req.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = f'HTTP_{key}'
            environ[key] = value
        
        # Add REQUEST_URI for better compatibility
        environ['REQUEST_URI'] = req.path or '/'
        
        # Log the request for debugging
        print(f"Request: {req.method} {req.path}")
        print(f"Content-Type: {environ.get('CONTENT_TYPE')}")
        print(f"Content-Length: {environ.get('CONTENT_LENGTH')}")
        print(f"Data preview: {req.data[:100] if req.data else 'No data'}")
        
        # Create WSGI start_response function
        response_data = []
        
        def start_response(status, headers, exc_info=None):
            response_data.clear()
            response_data.append(status)
            response_data.append(headers)
            return lambda s: None
        
        # Call Flask app
        app_response = app(environ, start_response)
        response_body = b''.join(app_response)
        
        # Extract status and headers
        status = response_data[0] if response_data else '500 Internal Server Error'
        headers = response_data[1] if len(response_data) > 1 else []
        
        # Convert status to integer
        status_code = int(status.split()[0])
        
        # Convert headers to dict
        response_headers = {}
        for header_name, header_value in headers:
            response_headers[header_name] = header_value
        
        return https_fn.Response(
            response_body,
            status=status_code,
            headers=response_headers
        )
        
    except Exception as e:
        print(f"Function error: {e}")
        import traceback
        traceback.print_exc()
        
        return https_fn.Response(
            f"Function error: {str(e)}",
            status=500,
            headers={'Content-Type': 'text/plain'}
        )