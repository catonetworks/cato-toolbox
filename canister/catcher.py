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



class RequestHandler(http.server.SimpleHTTPRequestHandler):
    #
    # Handle GET and POST requests by echoing back the request headers
    # and body in the response body.
    #


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
        Logger.print_output = False


    def start(self):
        #
        # Starts the web service on a separate thread, running forever until killed or shutdown
        #
        def go():
            with socketserver.TCPServer((self.host, self.port), RequestHandler) as self.httpd:
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



#
# The main() function allows us to call this module from the command line
# with no additional scripting required. The only parameters are the server
# IP and port - when calling from the CLI we assume that TLs is required
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
    # enable_tls: wrap the listening socket in TLS
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
            print("Shutting down")
            C.shutdown()
            time.sleep(2)
            break


if __name__ == "__main__":
    main()

