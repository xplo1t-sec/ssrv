from gunicorn.http import wsgi

class RemoveHeaders(wsgi.Response):
    def default_headers(self, *args, **kwargs):
        headers = super().default_headers(*args, **kwargs)
        headers = [h for h in headers if not h.startswith(("Server:", "Date:", "Connection:"))]  
        return headers

wsgi.Response = RemoveHeaders

bind = "0.0.0.0:8000"

workers = 2
worker_class = "gthread"
threads = 2

# logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

daemon = False  # to run as daemon, set to True
