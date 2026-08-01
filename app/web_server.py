"""
Simple web server for healthcheck.
"""
import threading
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger(__name__)

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Handler for health check endpoint."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress log messages."""
        pass

def start_health_server(port=8080):
    """Start health check server in a separate thread."""
    try:
        server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
        logger.info(f"✅ Health check server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Health check server error: {e}")
