from http.server import SimpleHTTPRequestHandler
from threading import Thread
from ursus.config import config
import logging
import socketserver


class HttpRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=config.output_path, **kwargs)

    def do_GET(self):
        abs_path = config.output_path / self.path.removeprefix('/')
        abs_html_path = abs_path.with_suffix('.html')
        abs_index_path = abs_path / 'index.html'

        if not abs_path.exists():
            if abs_path.suffix == config.html_url_extension and abs_html_path.exists():
                self.path = str(abs_html_path.relative_to(config.output_path))
            elif abs_index_path.exists():
                self.path = str(abs_index_path.relative_to(config.output_path))
        return super().do_GET()

    def log_message(self, format, *args):
        logging.debug(f"Request to {self.path}")


def serve(port: int = 80):
    """Start a static file server that serves Ursus on the given port.

    Args:
        port (int, optional): The port on which to serve the static site. Default is port 80.
    """
    with socketserver.ThreadingTCPServer(("", port), HttpRequestHandler) as server:
        logging.info(f"Serving static site on port {port}")
        server.serve_forever()


def serve_async(port: int = 80):
    thread = Thread(target=serve, args=(port, ), daemon=True)
    thread.start()
    return thread
