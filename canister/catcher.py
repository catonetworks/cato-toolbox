#
# canister/catcher.py
#
# Defines the Catcher class, which runs a web server to use as 
# a target for tests. The service will respond to any GET/POST request with
# a 200 OK, and echo the request headers and body back in the response.
#


import http.server
import socketserver
import ssl
import threading

from logger import Logger



class RequestHandler(http.server.SimpleHTTPRequestHandler):
    #
    # Handle GET and POST requests by echoing back the request headers
    # and body in the response body.
    #


    def do_GET(self):
        #
        # Default GET: ignore the body, only send back the request headers.
        #
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f'{self.requestline}\n'.encode())
        for header, value in self.headers.items():
            self.wfile.write(f"{header}: {value}\n".encode())


    """
    def do_POST(self):
        # Respond with request headers and body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length) if content_length > 0 else b""
        
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        
        # Write the request headers to the response
        self.wfile.write(b"Request Headers:\n")
        for header, value in self.headers.items():
            self.wfile.write(f"{header}: {value}\n".encode())
        
        # Write the request body to the response
        self.wfile.write(b"\nRequest Body:\n")
        self.wfile.write(request_body)
    """


class Catcher:
    #
    # Web server to act as a target for requests and attacks. The service
    # can provide a http or https service (not both - one or the other).
    #
    # Parameters:
    # ----------
    #   host: IP or hostname of interface to listen on
    #
    #   port: TCP port to listen on.
    #
    #   certfile: PEM format public certificate. The service ships with
    #             a default self-signed certificate.
    #
    #   keyfile: The private key part of the certificate.
    #
    def __init__(self, host="localhost", port=8443, enable_ssl=True, 
                 certfile="cert.pem", keyfile="key.pem"):
        self.host = host
        self.port = port
        self.certfile = certfile
        self.keyfile = keyfile
        self.enable_ssl = enable_ssl
        self.server_thread = None
        Logger.print_output = False


    def start(self):
        #
        # Starts the web service on a separate thread, running forever until killed or shutdown
        #
        def go():
            with socketserver.TCPServer((self.host, self.port), RequestHandler) as self.httpd:
                if self.enable_ssl:
                    self.httpd.socket = ssl.wrap_socket(
                        self.httpd.socket,
                        certfile=self.certfile,
                        keyfile=self.keyfile,
                        server_side=True
                    )
                    protocol = "https"
                else:
                    protocol = "http"
                Logger.log(1, f"Thread: Server started at {protocol}://{self.host}:{self.port}")
                self.httpd.serve_forever()
            Logger.log(1, "Exiting server thread")
        self.server_thread = threading.Thread(target=go)
        self.server_thread.start()


    def shutdown(self):
        #
        # Send a shutdown request to the server
        #
        if self.server_thread is not None:
            Logger.log(1, "Shutting down the server")
            self.httpd.shutdown()

