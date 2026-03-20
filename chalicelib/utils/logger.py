import logging
import os
from ..interfaces.logger import ILogger

class FileAuditLogger(ILogger):
    def __init__(self, name, log_dir="logs", log_file="audit.log"):
        # 1. Ensure the logs directory exists
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        log_path = os.path.join(log_dir, log_file)

        # 2. Configure the Logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 3. Create a File Handler for the Audit Trail
        # This satisfies Requirement (b)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)

        # 4. Create a Stream Handler (Console) 
        # This replaces print() so you can still see it in your VM terminal
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 5. Create a professional format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 6. Add handlers to the logger
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, status: str, message: str):
        """Mapping the interface method to the standard logging levels"""
        log_entry = f"[{event_type}] {status}: {message}"
        
        if status.upper() == "ERROR":
            self.logger.error(log_entry)
        elif status.upper() == "WARNING":
            self.logger.warning(log_entry)
        else:
            self.logger.info(log_entry)

    def info(self, message: str):
        """Pass-Through method to satisfy direct calls to .info()"""
        self.logger.info(message)