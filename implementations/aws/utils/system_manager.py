import time
from chalicelib.utils.deployment_base import CloudWorkerManager
from chalicelib.utils.logger import FileAuditLogger
from chalicelib.utils.trigger_utils import sync_s3_triggers, wire_dynamo_to_lambda
from chalicelib.persistence.table_manager import TableManager
import os
from dotenv import load_dotenv
load_dotenv() # Load the .env file

# Get the key from your local environment

import os

class SystemManager:
    def __init__(self, config=None):
        # 1. Pull from config dict OR environment variables
        self.bucket = (config or {}).get('BUCKET') or os.environ.get('S3_BUCKET_NAME')
        self.region = (config or {}).get('REGION') or os.environ.get('AWS_REGION') or 'us-east-1'
        
        # 2. We need a Role ARN to deploy workers. 
        # If it's not in config, we can try to guess it or you can hardcode it here.
        self.role_arn = (config or {}).get('ROLE_ARN') or os.environ.get('LAMBDA_ROLE_ARN')

        self.tm = TableManager(self.region)
        self.worker_manager = CloudWorkerManager(self.region, self.role_arn)
        self.workers = []
        self.logger = FileAuditLogger(name="SystemManager")

    def deploy_infrastructure(self):
        self.tm.create_all_tables()

    def add_worker(self, name, handler_path, env_vars=None):
        self.logger.log_event("WORKER_DEPLOY", "INFO", f"Deploying {name}...")
        
        # Deploy it
        self.worker_manager.deploy_worker(name, handler_path, env_vars or {})
        
        # Store the NAME so we can get the ARN correctly later
        self.workers.append(name) 
        return name

    def finalize_wiring(self):
        # 1. Standard S3 -> EventBridge wiring
        s3_worker_arns = [self.worker_manager.get_function_arn(name) for name in self.workers 
                         if "Translate" not in name and "Speech" not in name and "Summary" not in name]
        sync_s3_triggers(self.bucket, s3_worker_arns)

        # 2. OCR Table -> TranslateWorker
        ocr_stream_arn = self.tm.get_stream_arn("Analysis_OCR")
        if ocr_stream_arn:
            print("🔗 Wiring OCR Stream to TranslateWorker...")
            wire_dynamo_to_lambda("TranslateWorker", ocr_stream_arn)

        # 3. Translation Table -> SpeechWorker AND SummaryWorker
        trans_stream_arn = self.tm.get_stream_arn("Analysis_Translations")
        if trans_stream_arn:
            print("🔗 Wiring Translation Stream to Speech & Summary Workers...")
            # BOTH workers need to listen to this table!
            wire_dynamo_to_lambda("SpeechWorker", trans_stream_arn)
            wire_dynamo_to_lambda("SummaryWorker", trans_stream_arn)
        else:
            print("⚠️ Stream missing on Translations table!")