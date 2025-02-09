#
# canister/catcher.py
#
# Defines the Catcher class, which runs a web server to use as 
# a target for tests. The service will respond to any GET/POST request with
# a 200 OK, and echo the request headers and body back in the response.
#

import base64
import http.server
import socketserver
import ssl
import sys
import threading
import time

from logger import Logger



class RequestHandler(http.server.BaseHTTPRequestHandler):
    #
    # Handle GET and POST requests by echoing back the request headers
    # and body in the response body.
    #

    def log_message(self, f, *args):
        #
        # Override base class to log via Canister logger rather than
        # print stuff to stdout.
        #
        text = f'tc:{threading.active_count()} {self.client_address[0]}:{self.client_address[1]} {f % args}'
        Logger.log(1, text)


    def do_GET(self):

        #
        # EICAR file
        #
        if self.path == "/eicar.exe":
            eicarb64 = "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNUQU5EQVJELUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo="
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename=\"eicar.exe\"")
            self.end_headers()
            self.wfile.write(base64.b64decode(eicarb64))

        #
        # NG EICAR file
        #
        if self.path == "/ngeicar.exe":
            ngeicarb64 = "WDVPIVAlQEFQWzRcUFpYNTQoUF4pN0NDKTd9JEVJQ0FSLVNFTlRJTkVMLUFOVElWSVJVUy1URVNULUZJTEUhJEgrSCo="
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename=\"ngeicar.exe\"")
            self.end_headers()
            self.wfile.write(base64.b64decode(ngeicarb64))

        #
        # Zipped EICAR
        #
        if self.path == "/eicar.zip":
            zipfile = "UEsDBAoAAAAAADKs6yjRINsxuAAAALgAAAANAAAAZWljYXJfY29tLnppcFBLAwQKAAAAAADgmLgoPM9RaEQAAABEAAAACQAAAGVpY2FyLmNvbVg1TyFQJUBBUFs0XFBaWDU0KFBeKTdDQyk3fSRFSUNBUi1TVEFOREFSRC1BTlRJVklSVVMtVEVTVC1GSUxFISRIK0gqUEsBAhQACgAAAAAA4Ji4KDzPUWhEAAAARAAAAAkAAAAAAAAAAQAgAP+BAAAAAGVpY2FyLmNvbVBLBQYAAAAAAQABADcAAABrAAAAAABQSwECFAAKAAAAAAAyrOso0SDbMbgAAAC4AAAADQAAAAAAAAAAACAAtoEAAAAAZWljYXJfY29tLnppcFBLBQYAAAAAAQABADsAAADjAAAAAAA=="
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Disposition", "attachment; filename=\"eicar.zip\"")
            self.end_headers()
            self.wfile.write(base64.b64decode(zipfile))

        #
        # Default GET: ignore the body, only send back the request headers.
        #
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f'{self.requestline}\n'.encode())
            for header, value in self.headers.items():
                self.wfile.write(f"{header}: {value}\n".encode())


    def do_POST(self):
        #
        # Default POST: ignore body, send back the request headers.
        #
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(f'{self.requestline}\n'.encode())
        for header, value in self.headers.items():
            self.wfile.write(f"{header}: {value}\n".encode())



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


    def start(self):
        #
        # Starts the web service on a separate thread, running forever until killed or shutdown
        #
        # This is an extremely small, limited, primitive implementation of a web server.
        # This should not be exposed to the Internet at large or used to serve other content.
        #
        def go():
            try:
                self.httpd = http.server.ThreadingHTTPServer(
                    (self.host, self.port), 
                    RequestHandler
                )
                self.httpd.request_queue_size = 100
                self.httpd.timeout = 3
                if self.enable_ssl:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                    context.load_cert_chain(self.certfile, self.keyfile)
                    self.httpd.socket = context.wrap_socket(
                        self.httpd.socket,
                        server_side=True
                    )
                    protocol = "https"
                else:
                    protocol = "http"
                self.httpd.serve_forever()
            except PermissionError as e:
                Logger.log(0, f"PermissionError:{e} - try using a port number > 1024")
                sys.exit(1)
            except Exception as e:
                Logger.log(0, f"Exception:{e}")
                sys.exit(1)
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



#
# The main() function allows us to call this module from the command line
# with no additional scripting required. The only parameters are the server
# IP and port - when calling from the CLI we assume that TLS is required
# and that the TLS certificate will be the default. We also leave the log
# level at the default.
#

def main():
    #
    # Example command line would be:
    # 
    # python3 -m catcher <server_ip> <server_port>
    #
    # server_ip: the local IP to listen on.
    # server_port: the port to listen on.
    #

    #
    # Process command line
    #
    if len(sys.argv) < 3:
        print("Error: not enough arguments. Both the server IP and port must be specified.")
        print("For example: python3 -m catcher 127.0.0.1 8443")
        sys.exit(1)
    ip = sys.argv[1]
    port = int(sys.argv[2])

    #
    # Execute, looping on input() until Ctrl-C
    #
    C = Catcher(host=ip, port=port)
    C.start()
    while True:
        try:
            input()
        except KeyboardInterrupt:
            Logger.log(1, "Received KeyboardInterrupt")
            C.shutdown()
            time.sleep(2)
            break


if __name__ == "__main__":
    main()

