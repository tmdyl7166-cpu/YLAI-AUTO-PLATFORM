from prometheus_client import start_http_server

def start_exporter(port: int = 9108):
    start_http_server(port)
    return port
