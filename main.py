from flask import Flask, Response, make_response
import yaml

app = Flask(__name__)

CONFIG_FILE = 'config.yaml'
DEFAULT_STATUS_CODE = 200   # default status code if not set

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def handle_request(path):
    with open(CONFIG_FILE, 'r') as f:
        endpoints = yaml.safe_load(f)

    for endpoint_config in endpoints:
        if endpoint_config['path'] == '/' + path:
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
