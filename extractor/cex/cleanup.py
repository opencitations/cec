
import os
import shutil
import logging
import atexit
import signal
import sys

def clean_folder(folder_path):
    if not os.path.exists(folder_path):
        return
    for entry in os.scandir(folder_path):
        try:
            if entry.is_file():
                os.remove(entry.path)
            elif entry.is_dir():
                shutil.rmtree(entry.path)
        except Exception as e:
            logging.error(f"Error cleaning {entry.path}: {e}")

def register_cleanup(*folders):
    @atexit.register
    def cleanup_on_exit():
        logging.info("Cleaning up on app shutdown.")
        for folder in folders:
            clean_folder(folder)

    def handle_exit_signal(signum, frame):
        logging.info(f"Signal {signum} received. Cleaning up...")
        for folder in folders:
            clean_folder(folder)
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)