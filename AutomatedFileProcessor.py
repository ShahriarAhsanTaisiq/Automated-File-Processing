import os
import logging


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
