#Python SFTP Download Script for Paycom
#Enoch Wright
#2024-10-11 - Implemented exception handling and simplified directory creation.
#2024-10-09 - Rewrote script to allow multiple file downloads via SFTP. Fixed folder definition, using try for closing SFTP connection, reorganized code, changed email, added folder structure params.
#2024-08-13 - Initial finalized script for downloading PTO file via SFTP and sending email notification

# Python Imports
import os
import hashlib
import shutil
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Install missing paramiko if not found
import subprocess
import sys
try:
    import paramiko
except ImportError:
    print("Paramiko is not installed. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "paramiko"])
    import paramiko
    print("Paramiko has been successfully installed.")

# SFTP Settings
SFTP_HOST = 'push.paycomonline.net'
SFTP_USERNAME = 'xxxxxxxxxx'
SFTP_PASSWORD = 'xxxxxxxxxx'
SFTP_REMOTE_DIR = '/Outbound'

# Local Settings
LOCAL_DIR = os.getcwd()
DOWNLOAD_DIR = os.path.join(LOCAL_DIR, 'download')
CHECKSUM_FILE = 'checksum.txt'
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
if not os.path.exists(CHECKSUM_FILE):
    with open(CHECKSUM_FILE, 'w') as file:
        pass

# Email Settings
subject = "SFTP Downloader"
to_email = "xxxxxxxxxx"
from_email = "xxxxxxxxxx"
smtp_server = "xxxxxxxxxx"
smtp_port = 587
smtp_user = "xxxxxxxxxx"
smtp_password = "xxxxxxxxxx"

# File List Settings
FILE_LIST = [
    {
        "FILE_STR": "Report_1",
        "TRANSFER_DIR": "Transfer_1"
    },
    {
        "FILE_STR": "Report_2",
        "TRANSFER_DIR": "Transfer_2"
    }
]

# Connect to SFTP
def connect_to_sftp():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(SFTP_HOST, username=SFTP_USERNAME, password=SFTP_PASSWORD)
    sftp = client.open_sftp()
    return sftp

# Download files from SFTP
def download_files(sftp):
    body = ""
    for record in FILE_LIST:
        FILE_STR = record["FILE_STR"]
        TRANSFER_DIR = record["TRANSFER_DIR"]
        sftp.chdir(SFTP_REMOTE_DIR)
        files = sftp.listdir()
        newest_file = None
        for file_name in files:
            if FILE_STR in file_name:
                remote_path = os.path.join(SFTP_REMOTE_DIR, file_name)
                file_timestamp = sftp.stat(remote_path).st_mtime
                if newest_file is None or file_timestamp > newest_file[1]:
                    newest_file = (file_name, file_timestamp)
        # Could simplify this subsection:
        if newest_file is not None:
            newest_file_name, _ = newest_file
            remote_path = os.path.join(SFTP_REMOTE_DIR, newest_file_name)
            local_path = os.path.join(DOWNLOAD_DIR, newest_file_name)
            try:
                sftp.get(remote_path, local_path)
            except Exception as e:
                body += f"Failed to download {newest_file_name}: {str(e)}\n"
                continue
            calculated_checksum = calculate_checksum(local_path)
            if not calculated_checksum:
                body += f"Error calculating checksum for {newest_file_name}, skipping file.\n"
                continue
            if check_file(FILE_STR,calculated_checksum):
                # Make sure directory exists and if not, use transfer folder
                if not os.path.isdir(TRANSFER_DIR):
                    os.makedirs("transfer", exist_ok=True)
                    TRANSFER_DIR = "transfer"
                destination_path = os.path.join(TRANSFER_DIR, os.path.basename(local_path))
                if not os.path.exists(destination_path):
                    shutil.move(local_path, TRANSFER_DIR)
                    body += f"{FILE_STR} - Updated \n   Checksum: {calculated_checksum} \n   File: {local_path}\n\n\n"
                else:
                    os.remove(local_path)
                    body += f"{FILE_STR} - File already exists \n   Checksum: {calculated_checksum} \n   File: {local_path}\n\n\n"
            else:
                os.remove(local_path)
                body += f"{FILE_STR} - No Update \n   Checksum: {calculated_checksum} \n   File: {local_path}\n\n\n"
            save_checksum(local_path, calculated_checksum)
    return body

# Checksum
def calculate_checksum(file_path):
    checksum = hashlib.sha256()
    try:
        with open(file_path, 'rb') as file:
            for chunk in iter(lambda: file.read(8192), b""):
                checksum.update(chunk)
        return checksum.hexdigest()
    except Exception as e:        
        print(f"Error calculating checksum for {file_path}: {str(e)}")
        return None

def save_checksum(file_path, checksum):
    with open(CHECKSUM_FILE, 'a') as file:
        file.write(f"{file_path},{checksum},{datetime.now()}\n")

def check_file(file_path, checksum):
    try:
        with open(CHECKSUM_FILE, 'r') as file:
            for line in file:
                saved_file_path, saved_checksum, _ = line.strip().split(',')
                if checksum == saved_checksum and file_path in saved_file_path:
                    return False
        return True
    except Exception as e:
        print(f"Error checking checksum file: {str(e)}")
        return True

# Send Email Code
def send_email(subject, body, to_email, from_email, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable security
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

# Main
def main():
    sftp = None
    try:
        sftp = connect_to_sftp()
        body = download_files(sftp)
    finally:
        if sftp:
            sftp.close()
    send_email(subject, body, to_email, from_email, smtp_server, smtp_port, smtp_user, smtp_password)
    print(f'Done')

if __name__ == '__main__':
    main()
