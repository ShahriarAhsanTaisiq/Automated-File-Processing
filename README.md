# Automated-File-Processing
The Automated File Processor is a Python script designed to automate the retrieval, processing, and monitoring of XML files from an FTP server. This README provides a detailed guide on setting up, configuring, and running the script.
### Features
1. FTP Setup and File Retrieval
2. File Processing and Data Extraction
3. Local Directory Monitoring
4. Cleanup and Maintenance

### Prerequisites
**Before running the script, ensure you have the following:**
- Python 3.x installed
- Required Python packages installed (watchdog)
- Access to an FTP server (or set up a local FTP server using Docker)
### Setup Instruction
  1. **FTP Setup and File Retrieval**
     - Docker Setup for FTP server
       1. Create `docker-compose.yml` file with the following content:
           ```
          version: '3'
           services:
             ftp-server:
               image: stilliard/pure-ftpd:latest
               ports:
                 - "21:21"
                 - "30000-30009:30000-30009"
               environment:
                 FTP_USER_NAME: "username"
                 FTP_USER_PASS: "password"
                 FTP_USER_HOME: "/home/ftpusers/usersHome"
                 PASV_ADDRESS: "localhost" 
           ```
       2. Run the FTP server using Docker Compose:
            ```
               docker-compose up -d
          ```
       - Upload sample XML files to the FTP
            - Upload sample XML files to the FTP server using an FTP client or command-line FTP.
2. **Python Environment Setup**
      1. Clone the repository to your local machine
         ```
         git clone https://github.com/ShahriarAhsanTaisiq/Automated-File-Processing
         ```
      2. Dependencies
         - Install dependencies:
           ```
           pip install watchdog
           ```
         - Update environment variables in `AutomatedFileProcessor.py` if needed (`FTP_HOST`, `FTP_USER`, `FTP_PASS`, `FTP_PORT`).
      3. Start the Python Script
         - Open a terminal.
         - Navigate to the project directory.
         - Run the Python script to continuously monitor and process files:
           ```
           python AutomatedFileProcessor.py
           ```

### Detailed Explanation
1. **FTP Setup and File Retrieval**
    - The script connects to an FTP server to retrieve XML files for processing. It uses ftplib to establish a connection, authenticate, and navigate through directories to locate XML files. The download_files() function manages file retrieval and moves downloaded files to temporary and local directories.
        ```
        import ftplib
        import os
        import logging
        import time
        
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


        # Execute download function
        download_files()
      ```
2. **File Processing and Data Extraction**
    - Once files are downloaded, the script processes each XML file in the local directory. It parses XML content using ElementTree, extracts data into dictionaries, and moves processed files to the trash directory for cleanup.
        ```
      from xml.etree import ElementTree as ET
        
        # function for move a processed file to trash
        def move_to_trash(filepath):
            try:
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    trash_path = os.path.join(TRASH_DIR, filename)
                    os.makedirs(TRASH_DIR, exist_ok=True)
                    os.rename(filepath, trash_path)
                    logging.info(f"Moved {filename} to trash at {trash_path}")
                else:
                    logging.warning(f"File {filepath} does not exist or could not be processed.")
            except Exception as e:
                logging.error(f"Error moving {filepath} to trash: {str(e)}")
        
        # function for process a file
        def process_file(filepath):
            try:
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
        
        # Execute file processing function for a specific file
        process_file("local/sample.xml")
      ```
3. **Local Directory Monitoring**
    - The script uses watchdog to monitor the local directory for new XML files. When a new file is detected, it triggers the processing function (process_file) to extract data and move the file to the trash directory.
        ```
      from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
        
        # class for handle file
        class FileHandler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    logging.info(f"Detected new file {event.src_path} in LOCAL_DIR")
                    process_file(event.src_path)
        
        # function for monitor local folder continuously
        def monitor_folder():
            event_handler = FileHandler()
            observer = Observer()
            observer.schedule(event_handler, LOCAL_DIR, recursive=False)
            observer.start()
            logging.info(f"Monitoring directory {LOCAL_DIR} for new files...")
        
            try:
                while True:
                    time.sleep(5)  # Check every 5 seconds for new files
            except KeyboardInterrupt:
                observer.stop()
                logging.info("Stopping file monitoring.")
        
            observer.join()
        
        # Start monitoring function
        monitor_folder()
      ```
4. **Cleanup and Maintenance**
    - Files processed successfully are moved to the trash directory for archiving and later observation. This ensures that only new, unprocessed files are monitored and processed by the script.
        ```
      # function for move a processed file to trash
        def move_to_trash(filepath):
            try:
                if os.path.exists(filepath):
                    filename = os.path.basename(filepath)
                    trash_path = os.path.join(TRASH_DIR, filename)
                    os.makedirs(TRASH_DIR, exist_ok=True)
                    os.rename(filepath, trash_path)
                    logging.info(f"Moved {filename} to trash at {trash_path}")
                else:
                    logging.warning(f"File {filepath} does not exist or could not be processed.")
            except Exception as e:
                logging.error(f"Error moving {filepath} to trash: {str(e)}")
      ```

### Additional Notes
    - Adjust sleep intervals (time.sleep()) as per your system’s processing capabilities and FTP server response times.
    - Ensure adequate error handling and logging for production use
    - For more details on functions and methods, refer to the comments within the script (AutomatedFileProcessor.py).