import os
import mimetypes
import uuid
import logging
import requests 
import sys


logging.basicConfig(level=logging.INFO, 
                    format='[%(asctime)s] %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

BASE_URL = "http://127.0.0.1:8889" 

def get_file_list():
    logging.info(f"\n\n--- Requesting file list from {BASE_URL} ---")
    try:
        response = requests.get(f"{BASE_URL}/list", timeout=10) 
        response.raise_for_status()
        
        logging.info("Response Headers:\n%s", response.headers)
        print("\nResponse Body:\n%s" % response.text) 
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection refused to {BASE_URL}. Is the server running?")
    except requests.exceptions.Timeout:
        logging.error(f"Request to {BASE_URL}/list timed out.")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during GET /list: {e}")

def upload_file(filepath):
    logging.info(f"\n\n--- Uploading file '{filepath}' to {BASE_URL} ---")
    
    if not os.path.exists(filepath):
        logging.error(f"Error: File '{filepath}' not found.")
        return

    filename = os.path.basename(filepath)
    
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (filename, f, mimetypes.guess_type(filename)[0] or 'application/octet-stream')}
            response = requests.post(f"{BASE_URL}/upload", files=files, timeout=10)
            response.raise_for_status()

            logging.info("Response Headers:\n%s", response.headers)
            print("\nResponse Body:\n%s" % response.text)
            
    except requests.exceptions.ConnectionError:
        logging.error(f"Connection refused to {BASE_URL}. Is the server running?")
    except requests.exceptions.Timeout:
        logging.error(f"Request to {BASE_URL}/upload timed out.")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during POST /upload: {e}")


def delete_file(filename):
    logging.info(f"\n\n--- Deleting file '{filename}' from {BASE_URL} ---")
    try:
        response = requests.delete(f"{BASE_URL}/delete/{filename}", timeout=10)
        response.raise_for_status()

        logging.info("Delete Response Headers:\n%s", response.headers)
        print("Delete Response Body:\n%s" % response.text)

    except requests.exceptions.ConnectionError:
        logging.error(f"Connection refused to {BASE_URL}. Is the server running?")
    except requests.exceptions.Timeout:
        logging.error(f"Request to {BASE_URL}/delete timed out.")
    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred during DELETE /delete/{filename}: {e}")


def main():
    # file_name = "test.txt"
    file_name = "donalbebek.jpg"

    logging.info(f"\n\n##### Testing HTTP Operations with Server on {BASE_URL} #####")
    
    get_file_list()
    upload_file(file_name)
    get_file_list() 
    delete_file(os.path.basename(file_name)) # <-- Baris ini diaktifkan
    get_file_list() 
    
if __name__ == "__main__":
    main()
