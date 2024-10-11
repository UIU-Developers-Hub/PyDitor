# File: utils/temp_file_manager.py

import os
import tempfile
import logging
import time
import psutil  # Ensure psutil is installed

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def create_temp_file(code, suffix=".py"):
    """Create a temporary file with the given code and suffix."""
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            temp_filename = temp_file.name
            temp_file.write(code.encode())
        logging.info(f"Temporary file created: {temp_filename}")
        return temp_filename
    except Exception as e:
        logging.error(f"Failed to create temporary file: {str(e)}")
        return None


def delete_temp_file(temp_filename, retries=3, delay=0.5):
    """Attempt to delete the temporary file multiple times."""
    for attempt in range(retries):
        try:
            if os.path.exists(temp_filename):
                if not is_file_in_use(temp_filename):
                    os.remove(temp_filename)
                    logging.debug(f"Successfully deleted temp file: {temp_filename}")
                    return True
                else:
                    logging.warning(f"File {temp_filename} is in use. Retrying...")
            else:
                logging.debug(f"File {temp_filename} does not exist.")
                return False
        except PermissionError:
            logging.warning(f"Permission error when trying to delete {temp_filename}. Retrying...")
        time.sleep(delay)

    logging.error(f"Failed to delete temporary file '{temp_filename}' after {retries} attempts.")
    return False


def is_file_in_use(file_path):
    """Check if the file is currently in use by any process."""
    for proc in psutil.process_iter():
        try:
            for file in proc.open_files():
                if file.path == file_path:
                    logging.debug(f"File {file_path} is being used by process {proc.pid}.")
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    logging.debug(f"File {file_path} is not in use.")
    return False
