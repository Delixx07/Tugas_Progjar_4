import os
import io
import cgi
from datetime import datetime
from email.message import Message

class HttpServer:
    def __init__(self):
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.png'] = 'image/png'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'
        os.makedirs('uploads', exist_ok=True)

    def response(self, kode=404, message='Not Found', messagebody=b'', headers=None):
        if headers is None:
            headers = {}
        tanggal = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
        resp = [
            f"HTTP/1.0 {kode} {message}\r\n",
            f"Date: {tanggal}\r\n",
            "Connection: close\r\n",
            "Server: myserver/1.0\r\n",
            f"Content-Length: {len(messagebody)}\r\n"
        ]
        for key, value in headers.items():
            resp.append(f"{key}: {value}\r\n")
        resp.append("\r\n")
        
        response_headers = ''.join(resp).encode('latin-1')
        if not isinstance(messagebody, bytes):
            messagebody = str(messagebody).encode('latin-1')
        return response_headers + messagebody

    def proses(self, data):
        parts = data.split(b'\r\n\r\n', 1)
        headers_part = parts[0]
        body = parts[1] if len(parts) > 1 else b""
        requests_lines = headers_part.decode('latin-1').split('\r\n')
        baris_pertama = requests_lines[0]
        
        headers_dict = {}
        for line in requests_lines[1:]:
            if ':' in line:
                key, value = line.split(':', 1)
                headers_dict[key.strip().lower()] = value.strip()
        
        try:
            method, path, _ = baris_pertama.split(" ")
            if method.upper() == 'GET':
                return self.http_get(path)
            elif method.upper() == 'POST':
                return self.http_post(path, headers_dict, body)
            elif method.upper() == 'DELETE':
                return self.http_delete(path)
            else:
                return self.response(501, 'Not Implemented', b'Method Not Implemented')
        except ValueError:
            return self.response(400, 'Bad Request', b'Malformed Request Line')

    def http_get(self, path):
        if path == '/list':
            try:
                all_main_items = sorted(os.listdir('.'))
                main_files_only = [item for item in all_main_items if os.path.isfile(item) and not item.startswith('.')]

                all_upload_items = sorted(os.listdir('uploads'))
                upload_files_only = [item for item in all_upload_items if os.path.isfile(os.path.join('uploads', item))]

                text_body = "File in Main Directory:\n"
                text_body += "-------------------------\n"
                for item in main_files_only:
                    text_body += f"- {item}\n"
                
                text_body += "\nFile di Directory 'uploads':\n"
                text_body += "----------------------------\n"
                if not upload_files_only:
                    text_body += "(Kosong)\n"
                else:
                    for item in upload_files_only:
                        text_body += f"- {item}\n"
                
                headers = {'Content-Type': 'text/plain'}
                return self.response(200, 'OK', text_body.encode('utf-8'), headers)
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e).encode('utf-8'))
        
        filepath = path.strip('/')
        if os.path.exists(filepath) and os.path.isfile(filepath):
            with open(filepath, 'rb') as f:
                content = f.read()
            fext = os.path.splitext(filepath)[1]
            content_type = self.types.get(fext.lower(), 'application/octet-stream')
            return self.response(200, 'OK', content, {'Content-Type': content_type})
        else:
            return self.response(404, 'Not Found', b'File atau Halaman tidak ditemukan')

    def http_post(self, path, headers, body):
        if path == '/upload':
            try:
                header_message = Message()
                for key, val in headers.items():
                    header_message.add_header(key, val)

                environ = {'REQUEST_METHOD': 'POST', 'CONTENT_TYPE': headers.get('content-type', ''), 'CONTENT_LENGTH': headers.get('content-length', str(len(body)))}
                
                form = cgi.FieldStorage(fp=io.BytesIO(body), headers=header_message, environ=environ, keep_blank_values=1)
                
                if 'file' in form:
                    file_item = form['file']
                    if file_item.filename:
                        fn = os.path.basename(file_item.filename)
                        filepath = os.path.join('uploads', fn)
                        
                        with open(filepath, 'wb') as f:
                            f.write(file_item.file.read())
                        return self.response(200, 'OK', f'File "{fn}" uploaded successfully to uploads folder..'.encode())
                
                return self.response(400, 'Bad Request', b'Field "file" not found.')
            except Exception as e:
                return self.response(500, 'Internal Server Error', str(e).encode())
        return self.response(404, 'Not Found', b'Endpoint not found.')

    def http_delete(self, path):
        if path.startswith('/delete/'):
            filename = os.path.basename(path)
            
            if '/' in filename or '..' in filename:
                return self.response(400, 'Bad Request', b'Nama file tidak valid.')

            path_in_uploads = os.path.join('uploads', filename)
            path_in_root = filename

            filepath_to_delete = None

            if os.path.exists(path_in_uploads) and os.path.isfile(path_in_uploads):
                filepath_to_delete = path_in_uploads
            elif os.path.exists(path_in_root) and os.path.isfile(path_in_root):
                filepath_to_delete = path_in_root

            if filepath_to_delete:
                try:
                    os.remove(filepath_to_delete)
                    return self.response(200, 'OK', f"File '{filename}' deleted successfully.".encode())
                except Exception as e:
                    return self.response(500, 'Internal Server Error', str(e).encode())
            else:
                return self.response(404, 'Not Found', f"File '{filename}' not found.".encode())
        else:
            return self.response(400, 'Bad Request', b'Format DELETE tidak valid. Gunakan /delete/<filename>')
