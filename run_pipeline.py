from chalicelib.persistence.check_results import ResultsChecker
from chalicelib.utils.system_manager import SystemManager
from chalicelib.ingestion.s3_uploader import BulkUploader
from chalicelib.utils.logger import FileAuditLogger 
import time

from chalicelib.utils.trigger_utils import sync_s3_triggers

class CloudInfrastructureOrchestrator:
    def __init__(self, config):
        self.config = config
        # The "Main" orchestrator logger
        self.logger = FileAuditLogger(name="CloudInfraOrchestrator", log_file="infra.log")
        self.manager = SystemManager(config)
        self.uploader = BulkUploader(config['BUCKET'])
        self.results = ResultsChecker() # For Phase 5

    def provision_environment(self):
        """Builds the entire AWS stack from scratch."""
        print("🌟 FEEDBACK ANALYZER: END-TO-END DEPLOYMENT 🌟\n")
        self.logger.log_event("STACK_PROVISION_START", "INFO", f"Initializing environment: {self.config['BUCKET']}")

        try:
                # --- PHASE 1: INFRASTRUCTURE ---
            self.logger.log_event("INFRA_START", "INFO", "Executing Table Creation...")
            self.manager.deploy_infrastructure() 
            # Inside manager.deploy_infrastructure, the TableManager will log its own "ℹ️ already exists"

                # --- PHASE 2: DEPLOYMENT ---
            self.manager.add_worker("LabelWorker", "lambda/label_worker/handler.py")
            self.manager.add_worker("OCRWorker", "lambda/ocr_worker/handler.py")
            # ADD THIS:
            self.manager.add_worker("TranslateWorker", "lambda/translate_worker/handler.py")
            self.manager.add_worker(
                        "SpeechWorker", 
                        "lambda/speech_worker/handler.py",
                        env_vars={"BUCKET_NAME": self.config['BUCKET']} 
                    )
            self.manager.add_worker(
                    "SummaryWorker", 
                    "lambda/summary_worker/handler.py"
                )

            # --- PHASE 3: WIRING ---
            self.manager.finalize_wiring()

            # --- PHASE 4: TESTING ---
            self.uploader.upload_samples('tests/sample_images')

            # --- PHASE 5: VERIFICATION ---
            print("\n⏳ Giving the AI Assembly Line a moment to finish...")
            # INCREASE THIS: 
            # S3 -> OCR (5s) + Stream -> Translate (5s) = 10-15s total
            time.sleep(15) 

            checker = ResultsChecker(self.config['REGION'])
            checker.display_table("Analysis_Labels")
            checker.display_table("Analysis_OCR")
            checker.display_table("Analysis_Translations")
            checker.display_table("Analysis_Summaries")
            checker.display_speech_results(self.config['BUCKET'])

            self.logger.log_event("PIPELINE_COMPLETE", "INFO", "All systems nominal.")
        except Exception as e:
            self.logger.log_event("PROVISIONING_ERROR", "ERROR", f"Failed to build stack: {str(e)}")
            raise e


if __name__ == "__main__":
    CONFIG = {
        'BUCKET': "comp264-edwin-1772030214",
        'REGION': "us-east-1"
    }

    # One line to rule them all
    bootstrapper = CloudInfrastructureOrchestrator(CONFIG)
    bootstrapper.provision_environment()