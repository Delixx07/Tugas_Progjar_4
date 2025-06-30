import socket
import logging
from concurrent.futures import ProcessPoolExecutor
from http_server import HttpServer

httpserver = HttpServer()

def ProcessTheClient(connection, address):
    try:
        headers_data = b""
        while True:
            data = connection.recv(1)
            if not data or (data == b'\n' and headers_data.endswith(b'\r\n\r\n')):
                break
            headers_data += data
            if headers_data.endswith(b'\r\n\r\n'):
                break

        content_length = 0
        headers_str = headers_data.decode('latin-1')
        for line in headers_str.split('\r\n'):
            if line.lower().startswith('content-length:'):
                try:
                    content_length = int(line.split(':')[1].strip())
                except (ValueError, IndexError):
                    content_length = 0
                break

        body_data = b""
        if content_length > 0:
            if b'\r\n\r\n' in headers_data:
                body_part_received = headers_data.split(b'\r\n\r\n', 1)[1]
                body_data += body_part_received
    
            while len(body_data) < content_length:
                chunk = connection.recv(content_length - len(body_data))
                if not chunk: break
                body_data += chunk

        full_request = headers_data.split(b'\r\n\r\n', 1)[0] + b'\r\n\r\n' + body_data

        if not full_request.strip(): return

        logging.info(f"Request from {address} is being processed.")
        response = httpserver.proses(full_request)
        connection.sendall(response)

    except Exception as e:
        logging.error(f"Error processing client {address}: {e}")
    finally:
        connection.close()
        logging.info(f"Connection with {address} closed.")
      
def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] (%(processName)-10s) %(message)s')
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('0.0.0.0', 8889)
    my_socket.bind(server_address)
    my_socket.listen(5)
    logging.info(f"Process Pool Server running on port {server_address[1]}...")

    with ProcessPoolExecutor(max_workers=10) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                logging.info(f"Connection from {client_address} received. Dispatching to process.")
                executor.submit(ProcessTheClient, connection, client_address)
            except KeyboardInterrupt:
                logging.info("Server is shutting down.")
                break
            except Exception as e:
                logging.error(f"Error accepting connection: {e}")

if __name__ == "__main__":
    main()
