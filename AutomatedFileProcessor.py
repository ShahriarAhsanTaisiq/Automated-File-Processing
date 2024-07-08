import ftplib
import os
import xml.etree.ElementTree as ET

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
