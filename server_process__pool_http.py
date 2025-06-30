import socket
import logging
from concurrent.futures import ThreadPoolExecutor
from http import HttpServer # <-- PERUBAHAN DI SINI

# Inisialisasi objek server
httpserver = HttpServer()

def ProcessTheClient(connection, address):
    """Fungsi yang akan dijalankan oleh setiap thread untuk melayani satu klien."""
    try:
        # Baca baris pertama dan headers
        headers_data = b""
        while True:
            data = connection.recv(1)
            if not data or data == b'\n' and headers_data.endswith(b'\r\n\r\n'):
                 break
            headers_data += data
            if headers_data.endswith(b'\r\n\r\n'):
                break
        
        request_str = headers_data.decode('latin-1')
        headers = request_str.split('\r\n')
        
        content_length = 0
        for h in headers:
            if h.lower().startswith('content-length:'):
                content_length = int(h.split(':')[1].strip())
                break
        
        # Baca body berdasarkan Content-Length
        body_data = b""
        if content_length > 0:
            body_data = connection.recv(content_length)

        # Gabungkan header dan body untuk diproses
        full_request = headers_data + body_data
        
        logging.info(f"Request diterima dari {address} (Total size: {len(full_request)} bytes)")

        # Proses data menggunakan "otak" server
        response = httpserver.proses(full_request.decode('latin-1'))
        
        connection.sendall(response)
    except Exception as e:
        logging.error(f"Error saat memproses klien {address}: {e}")
    finally:
        connection.close()
        logging.info(f"Koneksi dengan {address} ditutup.")

def main():
    """Fungsi utama untuk menjalankan server."""
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] (%(threadName)-10s) %(message)s')
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_address = ('0.0.0.0', 8885)
    my_socket.bind(server_address)
    my_socket.listen(5)
    logging.info(f"Process Pool Server berjalan di port {server_address[1]}...")

    with ProcessPoolExecutor(max_workers=20) as executor:
        while True:
            try:
                connection, client_address = my_socket.accept()
                executor.submit(ProcessTheClient, connection, client_address)
            except KeyboardInterrupt:
                logging.info("Server sedang dimatikan.")
                break
    my_socket.close()

if __name__ == "__main__":
    main()
