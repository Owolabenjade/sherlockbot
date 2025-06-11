from firebase_functions import https_fn
import sys
import os
import io
import json
from urllib.parse import parse_qs, urlencode

# Add sherlock-bot directory to Python path
sherlock_bot_dir = os.path.join(os.path.dirname(__file__), 'sherlock-bot')
sys.path.insert(0, sherlock_bot_dir)

@https_fn.on_request(
    region="africa-south1",
    memory=512,
    timeout_sec=300,
)
def app_function(req: https_fn.Request) -> https_fn.Response:
    """HTTP Cloud Function entry point for Sherlock Bot."""
    
    try:
        # Import Flask app only when the function is called (lazy import)
        from app import app
        
        # Handle request body based on content type
        body_data = b''
        content_type = req.headers.get('content-type', '').lower()
        
        # Debug logging
        print(f"Request: {req.method} {req.path}")
        print(f"Content-Type: {content_type}")
        print(f"Request data type: {type(req.data)}")
        print(f"Request data: {req.data}")
        
        if req.method == 'POST':
            if 'application/x-www-form-urlencoded' in content_type:
                # Handle form data
                if isinstance(req.data, bytes):
                    body_data = req.data
                elif isinstance(req.data, str):
                    body_data = req.data.encode('utf-8')
                elif isinstance(req.data, dict):
                    # If Firebase already parsed it as dict, convert back to form data
                    body_data = urlencode(req.data).encode('utf-8')
                else:
                    # Try to get form data from req.form if available
                    if hasattr(req, 'form') and req.form:
                        body_data = urlencode(dict(req.form)).encode('utf-8')
                    else:
                        body_data = b''
            elif 'application/json' in content_type:
                # Handle JSON data
                if isinstance(req.data, dict):
                    body_data = json.dumps(req.data).encode('utf-8')
                elif isinstance(req.data, str):
                    body_data = req.data.encode('utf-8')
                elif isinstance(req.data, bytes):
                    body_data = req.data
                else:
                    body_data = b'{}'
            else:
                # Handle other content types
                if isinstance(req.data, bytes):
                    body_data = req.data
                elif isinstance(req.data, str):
                    body_data = req.data.encode('utf-8')
                else:
                    body_data = str(req.data).encode('utf-8')
        
        # Create a BytesIO object for the body
        body = io.BytesIO(body_data)
        
        # Log body data for debugging
        print(f"Body data: {body_data}")
        print(f"Content-Length: {len(body_data)}")
        
        # Convert Firebase request to WSGI environ
        environ = {
            'REQUEST_METHOD': req.method,
            'SCRIPT_NAME': '',
            'PATH_INFO': req.path or '/',
            'QUERY_STRING': req.query_string or '',
            'CONTENT_TYPE': req.headers.get('content-type', 'application/x-www-form-urlencoded'),
            'CONTENT_LENGTH': str(len(body_data)),
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