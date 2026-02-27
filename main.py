from flask import Flask, Response, make_response, request
import yaml

app = Flask(__name__)

CONFIG_FILE = 'config.yaml'
DEFAULT_STATUS_CODE = 200   # default status code if not set


class AnyMethodMiddleware:
    """WSGI middleware that allows any HTTP method (including non-standard ones).
    Werkzeug rejects unknown methods before routing, so we store the real method
    in RAW_METHOD and override REQUEST_METHOD to GET for routing purposes."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        environ['RAW_METHOD'] = environ.get('REQUEST_METHOD', 'GET')
        environ['REQUEST_METHOD'] = 'GET'
        return self.wsgi_app(environ, start_response)


app.wsgi_app = AnyMethodMiddleware(app.wsgi_app)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def handle_request(path):
    actual_method = request.environ.get('RAW_METHOD', request.method)

    with open(CONFIG_FILE, 'r') as f:
        endpoints = yaml.safe_load(f)

    for endpoint_config in endpoints:
        config_method = endpoint_config.get('method')
        method_matches = config_method is None or config_method.upper() == actual_method.upper()
        if endpoint_config['path'] == '/' + path and method_matches:
            body_type = endpoint_config['body']['type'] # body type config
            if body_type == 'text':
                response = make_response()
                try:
                    response.data = endpoint_config['body']['content']
                except:
                    None
            elif body_type == 'file':
                with open(endpoint_config['body']['content'], 'rb') as file:
                    file_binary = file.read()
                    response = make_response(file_binary)
            else:
                return "Invalid body type in configuration", 500
            try:
                response.status = endpoint_config['status_code']
            except:
                response.status = DEFAULT_STATUS_CODE # set default status code
            
           # For custom headers
            if(len(endpoint_config.get('headers', {}))):
                response.headers = endpoint_config.get('headers', {})

            return response

    return Response("Endpoint not found", status=404, headers={"Content-Type": "text/html"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
