import ftplib
import os
import logging
import time
from xml.etree import ElementTree as ET

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# environment variables
FTP_HOST = os.getenv("FTP_HOST", "localhost")
FTP_USER = os.getenv("FTP_USER", "nybsys")
FTP_PASS = os.getenv("FTP_PASS", "12345")
FTP_PORT = int(os.getenv("FTP_PORT", 21))

TEMP_DIR = "temp"
LOCAL_DIR = "local"
TRASH_DIR = "trash"

# check necessary directories exist
for dir_path in [TEMP_DIR, LOCAL_DIR, TRASH_DIR]:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
        logging.info(f"Created directory {dir_path}")

# set to keep track of processed files
processed_files = set()


# function for download files
def download_files():
    try:
        ftp = ftplib.FTP()
        ftp.connect(FTP_HOST, FTP_PORT)
        ftp.login(FTP_USER, FTP_PASS)
        ftp.cwd('/')

        filenames = ftp.nlst('*.xml')
        for filename in filenames:
            local_temp_path = os.path.join(TEMP_DIR, filename)
            if filename not in processed_files:
                if not os.path.exists(local_temp_path):
                    with open(local_temp_path, 'wb') as f:
                        ftp.retrbinary('RETR ' + filename, f.write)
                    logging.info(f"Downloaded {filename} to TEMP_DIR at {local_temp_path}")
                    time.sleep(5)
                    local_final_path = os.path.join(LOCAL_DIR, filename)
                    if os.path.exists(local_temp_path):  # Check if file exists in TEMP_DIR
                        os.rename(local_temp_path, local_final_path)
                        logging.info(f"Moved {filename} from TEMP_DIR to LOCAL_DIR at {local_final_path}")
                    else:
                        logging.error(f"{local_temp_path} does not exist. Failed to move to {LOCAL_DIR}")
                else:
                    logging.info(f"File {filename} already exists in LOCAL_DIR, skipping download.")
            else:
                logging.info(f"File {filename} already processed, skipping download.")

        ftp.quit()

    except Exception as e:
        logging.error(f"Error during file download or processing: {str(e)}")
        if 'ftp' in locals():
            ftp.quit()


# function for move a processed file to trash
def move_to_trash(filepath):
    try:
        if os.path.exists(filepath):
            filename = os.path.basename(filepath)
            trash_path = os.path.join(TRASH_DIR, filename)
            os.makedirs(TRASH_DIR, exist_ok=True)
            os.rename(filepath, trash_path)
            logging.info(f"Moved {filename} to trash at {trash_path}")
            processed_files.add(filename)  # Add to set of processed files
        else:
            logging.warning(f"File {filepath} does not exist or could not be processed.")
    except Exception as e:
        logging.error(f"Error moving {filepath} to trash: {str(e)}")


# class for handle file
class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            logging.info(f"Detected new file {event.src_path} in LOCAL_DIR")
            time.sleep(3)
            process_file(event.src_path)


# function for process a file
def process_file(filepath):
    try:
        if os.path.basename(filepath) in processed_files:
            logging.info(f"File {filepath} already processed, skipping.")
            return

        tree = ET.parse(filepath)
        root = tree.getroot()

        data_dict = {}

        def parse_element(element):
            if element.tag not in data_dict:
                data_dict[element.tag] = []

            if element.text is not None:
                try:
                    value = float(element.text)
                except ValueError:
                    value = element.text
                data_dict[element.tag].append(value)

            for child in element:
                parse_element(child)

        parse_element(root)

        if data_dict:
            logging.info(f"Extracted data from {filepath}: {data_dict}")
        else:
            logging.info(f"No data extracted from {filepath}")

        move_to_trash(filepath)

    except Exception as e:
        logging.error(f"Error processing file {filepath}: {str(e)}")


# function for monitor local folder continuously
def monitor_folder():
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, LOCAL_DIR, recursive=False)
    observer.start()
    logging.info(f"Monitoring directory {LOCAL_DIR} for new files...")

    try:
        while True:
            # check every 10 second for new files
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
        logging.info("Stopping file monitoring.")

    observer.join()


if __name__ == "__main__":
    # check if directories are exist
    for dir_path in [TEMP_DIR, LOCAL_DIR, TRASH_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    # download process in a separate thread to continuously check for new files
    from threading import Thread


    def download_thread():
        while True:
            download_files()
            # check every 10 seconds for new files
            time.sleep(5)


    Thread(target=download_thread, daemon=True).start()

    # monitor local directory for new files
    monitor_folder()
