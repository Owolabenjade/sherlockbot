from firebase_functions import https_fn
import sys
import os
import io
import json

# Add sherlock-bot directory to Python path
sherlock_bot_dir = os.path.join(os.path.dirname(__file__), 'sherlock-bot')
sys.path.insert(0, sherlock_bot_dir)

def parse_form_data(data):
    """Parse form data from various formats"""
    from urllib.parse import parse_qs, urlencode
    
    if isinstance(data, dict):
        return urlencode(data).encode('utf-8')
    elif isinstance(data, str):
        return data.encode('utf-8')
    elif isinstance(data, bytes):
        return data
    else:
        return b''

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
        
        # Create Flask test client and use it to handle the request
        # This is a different approach that might work better with Firebase Functions
        with app.test_client() as client:
            # Prepare the request data
            method = req.method
            path = req.path or '/'
            headers = dict(req.headers)
            
            # Handle form data
            data = None
            json_data = None
            
            if method in ['POST', 'PUT', 'PATCH']:
                content_type = headers.get('content-type', '').lower()
                
                # Try to get form data from various sources
                if hasattr(req, 'form') and req.form:
                    data = dict(req.form)
                elif hasattr(req, 'args') and req.args and 'application/x-www-form-urlencoded' in content_type:
                    # Sometimes Firebase puts POST form data in args
                    data = dict(req.args)
                elif req.data:
                    if isinstance(req.data, dict):
                        if 'application/json' in content_type:
                            json_data = req.data
                        else:
                            data = req.data
                    elif isinstance(req.data, (str, bytes)):
                        if 'application/json' in content_type:
                            try:
                                json_data = json.loads(req.data if isinstance(req.data, str) else req.data.decode('utf-8'))
                            except:
                                data = req.data
                        else:
                            data = req.data
            
            # Make the request using Flask test client
            response = client.open(
                path=path,
                method=method,
                headers=headers,
                data=data,
                json=json_data,
                query_string=req.query_string
            )
            
            # Convert Flask response to Firebase Functions response
            return https_fn.Response(
                response.get_data(),
                status=response.status_code,
                headers=dict(response.headers)
            )
            
    except Exception as e:
        print(f"Function error: {e}")
        import traceback
        traceback.print_exc()
        
        # Try the WSGI approach as fallback
        try:
            from app import app
            from urllib.parse import urlencode
            
            # Prepare body data
            body_data = b''
            if req.method in ['POST', 'PUT', 'PATCH']:
                if hasattr(req, 'form') and req.form:
                    body_data = urlencode(dict(req.form)).encode('utf-8')
                elif hasattr(req, 'args') and req.args:
                    body_data = urlencode(dict(req.args)).encode('utf-8')
                elif req.data:
                    body_data = parse_form_data(req.data)
            
            # Create a BytesIO object
            body = io.BytesIO(body_data)
            
            # Build WSGI environ
            environ = {
                'REQUEST_METHOD': req.method,
                'SCRIPT_NAME': '',
                'PATH_INFO': req.path or '/',
                'QUERY_STRING': req.query_string or '',
                'CONTENT_TYPE': req.headers.get('content-type', 'application/x-www-form-urlencoded'),
                'CONTENT_LENGTH': str(len(body_data)),
                'SERVER_NAME': 'localhost',
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
            
            # Add headers
            for key, value in req.headers.items():
                key = key.upper().replace('-', '_')
                if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                    key = f'HTTP_{key}'
                environ[key] = value
            
            # WSGI call
            response_data = []
            def start_response(status, headers, exc_info=None):
                response_data.append(status)
                response_data.append(headers)
                return lambda s: None
            
            app_response = app(environ, start_response)
            response_body = b''.join(app_response)
            
            status_code = int(response_data[0].split()[0]) if response_data else 500
            headers = dict(response_data[1]) if len(response_data) > 1 else {}
            
            return https_fn.Response(
                response_body,
                status=status_code,
                headers=headers
            )
            
        except Exception as fallback_error:
            print(f"Fallback error: {fallback_error}")
            return https_fn.Response(
                f"Function error: {str(e)}\nFallback error: {str(fallback_error)}",
                status=500,
                headers={'Content-Type': 'text/plain'}
            )