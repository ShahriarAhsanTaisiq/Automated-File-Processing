import ftplib
import os
import time
import xml.etree.ElementTree as ET

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

# ftp info
FTP_HOST = "localhost"
FTP_USER = "nybsys"
FTP_PASS = "12345"
FTP_PORT = 21

# paths of directory
TEMP_DIR = "temp"
LOCAL_DIR = "local"
TRASH_DIR = "trash"


# Function for download files from FTP Server
def download_files():
    ftp = ftplib.FTP()
    ftp.connect(FTP_HOST, FTP_PORT)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd('/')

    filenames = ftp.nlst()

    for filename in filenames:
        local_temp_path = os.path.join(TEMP_DIR, filename)
        with open(local_temp_path, 'wb') as f:
            ftp.retrbinary('RETR ' + filename, f.write)

            local_final_path = os.path.join(LOCAL_DIR, filename)
            os.rename(local_temp_path, local_final_path)
    ftp.quit()


# Function for process the file
def process_file(filepath):
    tree = ET.parse(filepath)
    root = tree.getroot()

    data_dict = {}
    for elements in root.iter():
        data_dict[elements.tag] = elements.text

    print(data_dict)
    move_to_trash(filepath)


# Function for move processed file to trash
def move_to_trash(filepath):
    filename = os.path.basename(filepath)
    trash_path = os.path.join(TRASH_DIR, filename)
    os.rename(filepath, trash_path)


# Class to handle file system events
class FileHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        process_file(event.src_path)


# Function for monitoring local folder
def monitor_folder():
    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, LOCAL_DIR, recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
