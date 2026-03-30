import json
import os
import boto3
import io
import tensorflow as tf
import os
import time
import logging
import json
import time
from PIL import Image
from chalicelib.ingestion.mnist_loader import get_prepared_batch
from chalicelib.interfaces.pipeline import IPipelineBridge

logger = logging.getLogger("AWS_Pipeline")

class AWSPipelineBridge(IPipelineBridge):
    def __init__(self, cloud_orchestrator=None):
        """
        Initializes the bridge with necessary AWS clients for the Hybrid flow.
        """
        self.orchestrator = cloud_orchestrator
        self.s3 = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # ✅ FIXED: Initialized the lambda_client for Cloud Relay
        self.lambda_client = boto3.client('lambda', region_name='us-east-1')
        
        self.bucket = 'comp264-edwin-1772030214'

    def trigger_pipeline(self, data, file=None):
        """Standard interface method for single feedback."""
        if self.orchestrator:
            return self.orchestrator.run(data)
        return {"status": "skipped", "reason": "No local orchestrator"}

    def trigger_dataset_ingestion(self, config):
        """Standard MNIST Ingestion Path - Decoupled from Data Format"""
        limit = config.get('limit', 1)
        dataset = config.get('dataset')
        
        if dataset is None:
            return {"status": "error", "message": "No dataset object provided"}

        # Use your helper to get clean, ready-to-upload data
        samples = get_prepared_batch(dataset, limit)
        batch_results = []

        for sample in samples:
            fid = f"mnist_full_{int(time.time())}_{sample['index']}"
            s3_key = f"datasets/mnist/images/{fid}.png"

            logger.info(f"[PIPELINE] 📤 UPLOAD: Sending {fid} to S3 (Label: {sample['label']})")

            # 1. Upload PNG bytes to S3
            self.s3.put_object(
                Bucket=self.bucket, 
                Key=s3_key, 
                Body=sample['image_bytes'],
                ContentType='image/png'
            )

            # 2. Invoke MNIST Cloud Worker (mnist_ingestor_worker)
            relay_payload = {
                "feedback_id": fid,
                "label": str(sample['label']), # Stringify for standard relay
                "image_url": f"s3://{self.bucket}/{s3_key}",
                "bucket": self.bucket
            }

            logger.info(f"[PIPELINE] 🚀 TRIGGER: Invoking cloud ingestor for {fid}")
            self.lambda_client.invoke(
                FunctionName='mnist_ingestor_worker',
                InvocationType='Event',
                Payload=json.dumps(relay_payload).encode('utf-8')
            )
            batch_results.append(fid)

        return {
            "status": "success", # Changed to 'success' to match your UI expectation
            "count": len(batch_results),
            "sample_ids": batch_results 
        }

    
    def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=5):
        """
        Kaggle Tobacco Ingestion Path: 
        1. Loads real JPGs from local VMware folders.
        2. Uploads to S3 with verified ETag.
        3. Triggers the KAG Worker with a Synchronous handshake for debugging.
        """
        from chalicelib.ingestion.kag_loader import get_prepared_kag_batch

        from chalicelib.ingestion.kag_loader import get_prepared_kag_batch
        import random # 1. Import random

        samples = get_prepared_kag_batch(base_path, folder_name, limit=100) # Get more than you need
        
        # 2. 🎲 Shuffle the list of samples before we process them
        if samples:
            random.shuffle(samples)
            samples = samples[:limit] # Now take only the amount requested
        
        batch_results = []

        if not samples:
            print(f"❌ [BRIDGE] No samples found in {folder_name}. Check: {base_path}")
            return {"status": "error", "message": "No samples found"}

        for sample in samples:
            fid = sample['feedback_id']
            extension = sample['filename'].split('.')[-1].lower()
            
            # 🎯 ALIGNMENT: Match the manual path that worked
            # We use 'email' lowercase to match the S3 folder structure
            s3_key = f"datasets/kag_tobacco/email/{fid}.{extension}"

            # 1. Upload to S3 with Verification
            print(f"📤 [BRIDGE] Uploading {sample['filename']} -> {s3_key}...")
            content_type = 'image/jpeg' if extension in ['jpg', 'jpeg'] else f'image/{extension}'

            try:
                response = self.s3.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=sample['image_bytes'],
                    ContentType=content_type
                )
                print(f"✅ [S3 CONFIRMED] File uploaded. ETag: {response.get('ETag')}")
            except Exception as e:
                print(f"❌ [S3 ERROR] Failed to upload {fid}: {str(e)}")
                continue

            # 🛡️ ANTI-RACE CONDITION: Ensure S3 index is ready
            time.sleep(2.0)

            # 2. Trigger the KAG Worker
            relay_payload = {
                "feedback_id": fid,
                "folder": "Email",
                "image_url": f"s3://{self.bucket}/{s3_key}",
                "bucket": self.bucket,
                "metadata": sample['metadata']
            }

            print(f"🚀 [BRIDGE] Invoking KAG Worker for {fid}...")
            try:
                # Switching to RequestResponse so we see errors in the VMware console
                relay_response = self.lambda_client.invoke(
                    FunctionName='kag_worker',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(relay_payload).encode('utf-8')
                )
                
                # Parse the worker's internal response
                result = json.loads(relay_response['Payload'].read().decode())
                print(f"☁️ [CLOUD RESPONSE] {result}")
                
                if result.get('status') == 'success':
                    batch_results.append(fid)
                else:
                    print(f"⚠️ [WORKER WARNING] Worker accepted but reported: {result.get('message')}")

            except Exception as e:
                print(f"❌ [LAMBDA ERROR] Could not reach kag_worker: {str(e)}")

            time.sleep(1.0) # Rate limiting

        return {
            "status": "kag_triggered",
            "count": len(batch_results),
            "sample_ids": batch_results
        }
    

    # Inside your Bridge class
    def trigger_mnist_ingestion(self, digit="0", limit=3):
        """Passes the request to the pipeline and ensures the UI gets the result."""
        print(f"🌉 [BRIDGE] Handoff to Pipeline for digit {digit}...")
        
        # 1. Execute the pipeline logic
        result = self.pipeline.trigger_mnist_ingestion(digit=digit, limit=limit)
        
        # 2. Print for terminal visibility
        print(f"🌉 [BRIDGE] Pipeline returned: {result}")
        
        # 3. Explicitly return the dict so the UI knows we are DONE
        return result