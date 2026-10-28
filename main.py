from flask import Flask, Response, make_response, request
import yaml

app = Flask(__name__)

CONFIG_FILE = 'config-octokit-ssrf.yaml'
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
    import argparse
    import runpy

    from gunicorn.app.base import BaseApplication

    from ssl_utils import ensure_cert

    parser = argparse.ArgumentParser(description='ssrv: Simple Serve(r)')
    parser.add_argument('--ssl', action='store_true',
                        help='serve over HTTPS using a self-signed certificate')
    parser.add_argument('--ssl-host', metavar='HOSTNAME',
                        help='hostname/IP for the generated certificate (requires --ssl; default: localhost). '
                             'Certs are stored in ./certs/<hostname>.pem|key|cer and reused when still valid')
    args = parser.parse_args()

    if args.ssl_host and not args.ssl:
        parser.error('--ssl-host requires --ssl')

    class SsrvApplication(BaseApplication):
        def load_config(self):
            # same settings (and header stripping) as `gunicorn -c gunicorn_config.py main:app`
            config = runpy.run_path('gunicorn_config.py')
            for key, value in config.items():
                if key in self.cfg.settings and value is not None:
                    self.cfg.set(key.lower(), value)
            if args.ssl:
                certfile, keyfile = ensure_cert(args.ssl_host or 'localhost')
                self.cfg.set('certfile', certfile)
                self.cfg.set('keyfile', keyfile)

        def load(self):
            return app

    SsrvApplication().run()
