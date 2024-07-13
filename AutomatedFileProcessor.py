import ftplib
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
            if not os.path.exists(local_temp_path):
                with open(local_temp_path, 'wb') as f:
                    ftp.retrbinary('RETR ' + filename, f.write)

                local_final_path = os.path.join(LOCAL_DIR, filename)
                os.rename(local_temp_path, local_final_path)
                logging.info(f"Downloaded {filename} to {LOCAL_DIR}")

        ftp.quit()

    except Exception as e:
        logging.error(f"Error during file download or processing: {str(e)}")
        if 'ftp' in locals():
            ftp.quit()
