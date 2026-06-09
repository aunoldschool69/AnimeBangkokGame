import http.server
import socketserver
import webbrowser
import sys
import socket

# Find an available port starting from 8000 to prevent conflicts
def find_free_port(start_port=8000):
    port = start_port
    while port < 9000:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                # Bind explicitly to 127.0.0.1 (IPv4 loopback) to avoid IPv6 issues
                s.bind(('127.0.0.1', port))
                return port
            except socket.error:
                port += 1
    return 8000

PORT = find_free_port()
class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_POST(self):
        if self.path == '/report':
            import json
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            with open('debug_results.json', 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
            return
        self.send_error(404, "File not found")

Handler = NoCacheHTTPRequestHandler

class MyTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

print("==========================================================")
print("          THAILAND TOY TOUR 2.5D DEVELOPMENT SERVER       ")
print("==========================================================")
print(f"Host IP : 127.0.0.1 (Bypassing IPv6 localhost conflict)")
print(f"Port    : {PORT}")
print("Serving files from local directory...")
print("----------------------------------------------------------")

# Open web browser automatically to 127.0.0.1 which avoids localhost DNS bugs on Windows
url = f"http://127.0.0.1:{PORT}"
try:
    webbrowser.open(url)
    print(f"[OK] Opened default browser to: {url}")
except Exception as e:
    print(f"[Warning] Could not open browser automatically: {e}")

print("Press Ctrl+C in this command window to stop the server.")
print("==========================================================")

try:
    # Explicitly bind to '127.0.0.1' for IPv4 loopback stability on Windows
    with MyTCPServer(('127.0.0.1', PORT), Handler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nStopping server gracefully.")
    sys.exit(0)
except Exception as e:
    print(f"\nError occurred: {e}")
    input("Press Enter to exit...")
