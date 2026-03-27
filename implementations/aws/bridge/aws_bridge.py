import os
import boto3
from chalicelib.interfaces.pipeline import IPipelineBridge

import os
import boto3
from chalicelib.interfaces.pipeline import IPipelineBridge

class AWSPipelineBridge(IPipelineBridge):
    def __init__(self, cloud_orchestrator):
        """
        Matches the local style: takes the engine it needs to run.
        In AWS, that engine is your FeedbackAnalysisPipeline.
        """
        self.orchestrator = cloud_orchestrator

    def trigger_pipeline(self, data, file=None):
        """
        Translates the simple UI 'data' and 'file' into the 
        complex payload your FeedbackAnalysisPipeline.run() expects.
        """
        # Prepare the 'raw_input' for your Cloud Pipeline
        raw_input = {
            "user_id": data.get("user_id", "admin"),
            "feedback_id": data.get("feedback_id"),
            "text": data.get("text", ""),
        }

        # Add the file bytes if a file was uploaded
        if file:
            raw_input["image_data"] = {
                "name": data.get("filename"),
                "bytes": file.getvalue() # Gets the raw binary for S3
            }

        # CRITICAL: We return the generator (yields) so the progress bar works!
        return self.orchestrator.run(raw_input)