
import json
import uuid
import time
import boto3
import os
import logging
import tensorflow as tf
from chalicelib.ingestion.kag_loader import get_prepared_kag_batch
from boto3.dynamodb.conditions import Attr

class FeedbackAnalysisPipeline:
    def __init__(self, ingestor, sanitizer, security, translator, analyzer, persistence, logger, s3_storage, summarizer=None, workers=None):
        # 1. Dependencies
        self.ingestor = ingestor
        self.sanitizer = sanitizer
        self.security = security
        self.translator = translator
        self.analyzer = analyzer
        self.persistence = persistence  
        self.logger = logger
        self.s3_storage = s3_storage
        self.summarizer = summarizer 
        
        # 🎯 FIX: Store local worker instances for the manual 'Baton Pass'
        self.workers = workers or {} 
        
        # 2. Cloud Configuration
        self.bucket = s3_storage.bucket_name
        self.region = "us-east-1" 
        self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
        self.s3_client = boto3.client('s3', region_name=self.region)
        self.lambda_client = boto3.client('lambda', region_name=self.region)
        
        self.logger.log_event("PIPELINE", "INFO", "Pipeline Architecture Initialized")

    
    def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=5):
        """🚀 AWS Cloud Ingestion: Reads local files and uploads to S3"""
        from chalicelib.ingestion.kag_loader import get_prepared_kag_batch
        import random
        import json
        import time
        import os

        # 1. Load samples (Contains paths, not bytes)
        all_samples = get_prepared_kag_batch(base_path, folder_name, limit=100)
        
        if not all_samples:
            print(f"❌ [BRIDGE] No samples found in {folder_name}.")
            return {"status": "error", "message": "No samples found"}

        # 2. Shuffle and Limit
        random.shuffle(all_samples)
        samples = all_samples[:limit]
        
        batch_results = []

        for sample in samples:
            fid = sample['feedback_id']
            abs_path = sample.get('file_path')
            
            # 🎯 THE FIX: Read the binary data from the local VMware path
            if not abs_path or not os.path.exists(abs_path):
                print(f"❌ [FILE ERROR] {fid}: Path not found: {abs_path}")
                continue

            try:
                with open(abs_path, 'rb') as f:
                    img_data = f.read()
            except Exception as e:
                print(f"❌ [READ ERROR] {fid}: Could not read file: {str(e)}")
                continue

            # 3. S3 Configuration
            fname = os.path.basename(abs_path)
            extension = fname.split('.')[-1].lower()
            s3_key = f"datasets/kag_tobacco/email/{fid}.{extension}"
            content_type = 'image/jpeg' if extension in ['jpg', 'jpeg'] else f'image/{extension}'

            # 4. S3 Upload
            print(f"📤 [BRIDGE] Uploading {fname} -> {s3_key}...")
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=img_data,
                    ContentType=content_type,
                    Metadata={"feedback_id": fid} 
                )
                print(f"✅ [S3 SUCCESS] {fid} uploaded.")
            except Exception as e:
                print(f"❌ [S3 UPLOAD ERROR] {fid}: {str(e)}")
                continue

            # 5. Trigger KAG Worker (Synchronous)
            relay_payload = {
                "feedback_id": fid,
                "folder": folder_name,
                "image_url": f"s3://{self.bucket}/{s3_key}",
                "bucket": self.bucket,
                "metadata": sample.get('metadata', {})
            }

            try:
                print(f"🚀 [BRIDGE] Invoking KAG Worker for {fid}...")
                relay_response = self.lambda_client.invoke(
                    FunctionName='kag_worker',
                    InvocationType='RequestResponse',
                    Payload=json.dumps(relay_payload).encode('utf-8')
                )
                
                result = json.loads(relay_response['Payload'].read().decode())
                if result.get('status') == 'success':
                    batch_results.append(fid)
                    print(f"✅ [WORKER SUCCESS] {fid} processed.")
                else:
                    print(f"⚠️ [WORKER FAILED] {fid}: {result.get('message')}")

            except Exception as e:
                print(f"❌ [LAMBDA INVOKE ERROR] {fid}: {str(e)}")

        # 6. Final Return to UI
        return {
            "status": "COMPLETE",
            "ids": batch_results,
            "count": len(batch_results)
        }

    

 

    def trigger_pipeline(self, raw_input: dict):
        """🚀 AWS Cloud Single Processing Path"""
        # 1. Identity & Setup
        user_id = raw_input.get('user_id', 'admin')
        fid = raw_input.get('feedback_id') or f"{user_id}_{uuid.uuid4().hex[:8]}"
        results = {"status": "IN_PROGRESS", "feedback_id": fid, "summary": None}
        
        image_data = raw_input.get('image_data')
        table = self.dynamodb.Table("Analysis_Summaries")

        # 2. Seed DynamoDB
        try:
            table.put_item(Item={
                'feedback_id': fid,
                'user_id': user_id,
                'status': 'PROCESSING',
                'timestamp': str(time.time()),
                'master': '✅ Cloud Orchestrator Initialized'
            })
        except Exception as e:
            yield 0.0, f"❌ DB Seed Error: {str(e)}"
            return

        # 3. Trigger via S3 & Lambda (Direct Relay)
        try:
            ext = image_data['name'].split('.')[-1] if image_data else "txt"
            file_key = f"uploads/{fid}.{ext}"
            body = image_data['bytes'] if image_data else raw_input.get('text', '').encode('utf-8')
            
            self.s3_client.put_object(Bucket=self.bucket, Key=file_key, Body=body)

            relay_payload = {
                "Records": [{"s3": {"bucket": {"name": self.bucket}, "object": {"key": file_key}}}]
            }
            self.lambda_client.invoke(
                FunctionName='master_worker',
                InvocationType='Event',
                Payload=json.dumps(relay_payload).encode('utf-8')
            )
        except Exception as e:
            yield 0.0, f"❌ Cloud Trigger Error: {str(e)}"
            return

        # 4. Polling Loop
        for i in range(45):
            time.sleep(2.0)
            data = table.get_item(Key={'feedback_id': fid}).get('Item', {})
            progress = min((i + 1) / 40, 0.99)
            db_status = str(data.get('status', '')).upper()

            if db_status in ['SUCCESS', 'COMPLETE', 'COMPLETED', 'SUMMARIZED'] or data.get('summary'):
                results["status"] = "COMPLETE"
                results["summary"] = data
                yield 1.0, "✅ Analysis Finished!"
                yield 1.0, results
                return

            msg = data.get('master', "📡 Waiting for workers...")
            yield progress, msg
            yield progress, {"status": "IN_PROGRESS", "summary": data}

        results["status"] = "TIMEOUT"
        yield 1.0, results

    def trigger_mnist_ingestion(self, digit="0", limit=3):
        """🚀 MNIST TFRecord Ingestion (TensorFlow Specialized)"""
        TFRECORD_PATH = "/home/edwin/projects/feedback_analyzer/data/tfrecords/mnist_standard.tfrecord"
        print(f"🚀 [DEBUG] Starting MNIST Ingestion for digit: {digit}", flush=True)

        feature_description = {
            'image': tf.io.FixedLenFeature([], tf.string), 
            'label': tf.io.FixedLenFeature([], tf.int64),
            'filename': tf.io.FixedLenFeature([], tf.string),
        }

        try:
            raw_dataset = tf.data.TFRecordDataset(TFRECORD_PATH)
            parsed_dataset = raw_dataset.map(lambda x: tf.io.parse_single_example(x, feature_description))
            
            target_digit = int(digit)
            digit_samples = parsed_dataset.filter(lambda x: x['label'] == target_digit).shuffle(100).take(limit)

            batch_results = []
            for i, record in enumerate(digit_samples):
                fid = f"mnist_{digit}_{int(time.time())}_{i}"
                img_bytes = record['image'].numpy() 
                s3_key = f"datasets/mnist/{digit}/{fid}.png"

                # 1. S3 Upload
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=img_bytes,
                    ContentType='image/png'
                )

                # 2. Lambda Trigger
                relay_payload = {
                    "feedback_id": fid,
                    "label": str(digit),
                    "image_url": f"s3://{self.bucket}/{s3_key}",
                    "bucket": self.bucket
                }

                self.lambda_client.invoke(
                    FunctionName='mnist_ingestor_worker',
                    InvocationType='Event',
                    Payload=json.dumps(relay_payload).encode('utf-8')
                )
                batch_results.append(fid)
                yield (i + 1) / limit, f"Uploaded {i+1}/{limit} samples..."

            yield 1.0, {"status": "success", "ids": batch_results}

        except Exception as e:
            print(f"❌ [DEBUG] MNIST Error: {str(e)}", flush=True)
            yield 0.0, {"status": "error", "message": str(e)}

    def get_user_feedback(self, username):
        """Used by HistoryUI to list previous analyses."""
        try:
            table = self.dynamodb.Table('Analysis_Summaries')
            response = table.scan(FilterExpression=Attr('user_id').eq(username))
            items = response.get('Items', [])
            return sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
        except Exception as e:
            self.logger.log_event("DATABASE", "ERROR", f"Error: {e}")
            return []

    def _get_table_data(self, table_name, feedback_id):
        """Standard AWS DynamoDB Fetch"""
        try:
            # 🎯 FIX: Force the correct table name regardless of what the UI passes
            # This stops the ResourceNotFoundException during polling
            actual_table = "Analysis_Summaries" 
            table = self.dynamodb.Table(actual_table)
            
            response = table.get_item(Key={'feedback_id': feedback_id})
            return response.get('Item')
        except Exception as e:
            # Log specifically so we can see if it's still failing
            self.logger.log_event("DB_POLLING", "ERROR", f"Polling {actual_table} failed: {e}")
            return None


       
    # def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=5):
    #     """🚀 AWS-Ready Batch Orchestrator using the reliable S3-Trigger logic"""
    #     # 1. Get the samples
    #     samples = get_prepared_kag_batch(base_path, folder_name=folder_name, limit=limit)
    #     sample_ids = []
    #     table = self.dynamodb.Table("Analysis_Summaries")

    #     print(f"📊 [ORCHESTRATOR]: Processing {len(samples)} AWS samples...")

    #     # 2. Seed & Upload Loop (The working logic you sent)
    #     for sample in samples:
    #         fid = sample['feedback_id']
    #         sample_ids.append(fid)
    #         file_path = sample.get('file_path')
            
    #         # --- SEED DYNAMO ---
    #         table.put_item(Item={
    #             'feedback_id': fid,
    #             'user_id': 'admin',
    #             'status': 'PROCESSING',
    #             'timestamp': str(time.time()),
    #             'master': '✅ AWS Orchestrator Initialized'
    #         })

    #         # --- UPLOAD TO S3 (Triggers the Cloud Worker) ---
    #         if file_path and os.path.exists(file_path):
    #             with open(file_path, 'rb') as f:
    #                 body = f.read()
                
    #             ext = file_path.split('.')[-1]
    #             file_key = f"uploads/{fid}.{ext}"
                
    #             # CRITICAL: This Metadata is what makes the Cloud Worker work!
    #             self.s3_client.put_object(
    #                 Bucket=self.bucket,
    #                 Key=file_key,
    #                 Body=body,
    #                 Metadata={"feedback_id": fid}
    #             )
    #             print(f"📤 [TRACE] Uploaded {fid} to S3 bucket {self.bucket}")

    #     # 3. Polling Loop (Watching all IDs in the batch)
    #     print("📡 [ORCHESTRATOR]: Polling AWS for batch results...")
    #     for i in range(60):
    #         time.sleep(2.0)
    #         completed_count = 0
            
    #         for fid in sample_ids:
    #             res = table.get_item(Key={'feedback_id': fid})
    #             data = res.get('Item', {})
    #             db_status = str(data.get('status', '')).upper()
                
    #             # Check for completion markers
    #             if db_status in ['COMPLETE', 'COMPLETED', 'SUCCESS'] or data.get('summary'):
    #                 completed_count += 1
            
    #         print(f"🔍 [POLL {i}] Status: {completed_count}/{len(sample_ids)} finished...")
            
    #         if completed_count == len(sample_ids):
    #             break

    #     # 4. Return to UI (Matches your DatasetUI keys)
    #     return {
    #         "status": "COMPLETE",
    #         "ids": sample_ids,
    #         "message": f"Successfully processed {len(sample_ids)} items on AWS."
    #     }

    # def _get_table_data(self, table_name, feedback_id):
    #     """Fetches a record by feedback_id HASH key."""
    #     try:
    #         table = self.dynamodb.Table(table_name)
    #         response = table.get_item(Key={'feedback_id': feedback_id})
    #         return response.get('Item')
    #     except Exception as e:
    #         self.logger.log_event("DB_POLLING", "ERROR", f"Error: {e}")
    #         return None


# import json
# import uuid
# import time
# import boto3
# import os
# from chalicelib.ingestion.kag_loader import get_prepared_kag_batch
# from chalicelib.models.feedback import FeedbackModel
# from boto3.dynamodb.conditions import Attr

# import json
        
# class FeedbackAnalysisPipeline:
#     def __init__(self, ingestor, sanitizer, security, translator, analyzer, persistence, logger, s3_storage, summarizer=None):
#         # 1. Dependencies
#         self.ingestor = ingestor
#         self.sanitizer = sanitizer
#         self.security = security
#         self.translator = translator
#         self.analyzer = analyzer
#         self.persistence = persistence  
#         self.logger = logger
#         self.s3_storage = s3_storage
#         self.summarizer = summarizer 
        
#         # 2. Cloud Configuration
#         # Ensure we use the same naming convention everywhere
#         import boto3
#         self.bucket = s3_storage.bucket_name
#         self.region = "us-east-1" 
#         self.dynamodb = boto3.resource('dynamodb', region_name=self.region)
#         self.s3_client = boto3.client('s3', region_name=self.region)
#         self.lambda_client = boto3.client('lambda', region_name=self.region)
        
#         self.logger.log_event("PIPELINE", "INFO", "Pipeline Architecture Initialized")


#     def trigger_kag_ingestion(self, base_path, folder_name="Email", limit=5):
#         """
#         🚀 Local Batch Orchestrator with Polling.
#         Replicates the 'trigger_pipeline' logic for local batch processing.
#         """
#         import time
        
#         # 1. Identity & Setup
#         samples = get_prepared_kag_batch(base_path, folder_name=folder_name, limit=limit)
#         sample_ids = [s['feedback_id'] for s in samples]
#         table = self.persistence.summary_service.repo.table
#         kag_worker = self.workers.get("kag")

#         print(f"📊 [ORCHESTRATOR]: Processing {len(samples)} samples...")

#         # 2. Seed DynamoDB (Status: PROCESSING)
#         for sample in samples:
#             table.put_item(Item={
#                 'feedback_id': sample['feedback_id'],
#                 'status': 'PROCESSING',
#                 'user_id': 'admin',
#                 'category': folder_name,
#                 'file_path': sample.get('file_path'),
#                 'timestamp': str(time.time()),
#                 'master': '🚀 Local Full-Chain Started'
#             })

#             # 3. 🎯 Trigger Local Worker (The 'Baton Pass')
#             if kag_worker:
#                 # Local call simulates the 'Event' trigger
#                 # We wrap in try/except so one bad file doesn't kill the batch
#                 try:
#                     kag_worker.lambda_handler({
#                         "feedback_id": sample['feedback_id'],
#                         "file_path": sample.get('file_path'),
#                         "action": "process_single"
#                     }, None)
#                 except Exception as e:
#                     print(f"❌ Worker Error for {sample['feedback_id']}: {e}")

#         # 4. Polling Loop (Matches your example i in range(45))
#         # Since this is a batch, we wait until ALL (or most) are COMPLETED
#         print("📡 [ORCHESTRATOR]: Polling for results...")
#         for i in range(45):
#             time.sleep(1.0) # Checking every second
            
#             completed_in_loop = 0
#             for fid in sample_ids:
#                 data = table.get_item(Key={'feedback_id': fid}).get('Item', {})
#                 db_status = str(data.get('status', '')).upper()
                
#                 if db_status in ['SUCCESS', 'COMPLETE', 'COMPLETED']:
#                     completed_in_loop += 1
            
#             # If all are done, we can return early
#             if completed_in_loop == len(sample_ids):
#                 print("✅ [ORCHESTRATOR]: All samples processed.")
#                 break
                
#             print(f"⏳ [Polling]: {completed_in_loop}/{len(sample_ids)} finished...")

#         # 5. Final Return to UI
#         # We return a standard dict so 'DatasetUI' can set session_state and rerun
#         return {
#             "status": "COMPLETE",
#             "sample_ids": sample_ids,
#             "message": "Batch processing finished."
#         }

#     def trigger_pipeline(self, raw_input: dict):
#         """🚀 Corrected AWS Single Processing Path"""
#         import uuid
#         import time
#         import json

#         # 1. Identity & Setup
#         user_id = raw_input.get('user_id', 'admin')
#         fid = raw_input.get('feedback_id') or f"{user_id}_{uuid.uuid4().hex[:8]}"
        
#         # 🎯 FIX: Initialize the results dictionary HERE
#         results = {"status": "IN_PROGRESS", "feedback_id": fid, "summary": None}
        
#         image_data = raw_input.get('image_data')
#         table = self.dynamodb.Table("Analysis_Summaries")

#         # 2. Seed DynamoDB
#         try:
#             table.put_item(Item={
#                 'feedback_id': fid,
#                 'user_id': user_id,
#                 'status': 'PROCESSING',
#                 'timestamp': str(time.time()),
#                 'master': '✅ Cloud Orchestrator Initialized'
#             })
#         except Exception as e:
#             yield 0.0, f"❌ DB Seed Error: {str(e)}"
#             return

#         # 3. Trigger via S3 & Lambda (Direct Relay)
#         try:
#             ext = image_data['name'].split('.')[-1] if image_data else "txt"
#             file_key = f"uploads/{fid}.{ext}"
#             body = image_data['bytes'] if image_data else raw_input.get('text', '').encode('utf-8')
            
#             self.s3_client.put_object(Bucket=self.bucket, Key=file_key, Body=body)

#             relay_payload = {
#                 "Records": [{"s3": {"bucket": {"name": self.bucket}, "object": {"key": file_key}}}]
#             }
#             self.lambda_client.invoke(
#                 FunctionName='master_worker',
#                 InvocationType='Event',
#                 Payload=json.dumps(relay_payload).encode('utf-8')
#             )
#         except Exception as e:
#             yield 0.0, f"❌ Cloud Trigger Error: {str(e)}"
#             return

#         # 4. Polling Loop
#         for i in range(45):
#             time.sleep(2.0)
#             data = table.get_item(Key={'feedback_id': fid}).get('Item', {})
            
#             progress = min((i + 1) / 40, 0.99)
#             db_status = str(data.get('status', '')).upper()

#             # Check for completion
#             if db_status in ['SUCCESS', 'COMPLETE', 'COMPLETED'] or data.get('summary'):
#                 # 🎯 results is now defined, so this won't crash
#                 results["status"] = "COMPLETE"
#                 results["summary"] = data
#                 yield 1.0, "✅ Analysis Finished!"
#                 yield 1.0, results
#                 return

#             # Yield intermediate state
#             msg = data.get('master', "📡 Waiting for workers...")
#             yield progress, msg
#             yield progress, {"status": "IN_PROGRESS", "summary": data}

#         # 5. Handle Timeout
#         results["status"] = "TIMEOUT"
#         yield 1.0, results

#     def trigger_mnist_ingestion(self, digit="0", limit=3):
#         import tensorflow as tf
#         import os
#         import json
#         import time
#         import logging

#         logger = logging.getLogger("AWS_Pipeline")
#         TFRECORD_PATH = "/home/edwin/projects/feedback_analyzer/data/tfrecords/mnist_standard.tfrecord"
        
#         print(f"🚀 [DEBUG] Starting MNIST Ingestion for digit: {digit}", flush=True)

#         feature_description = {
#             'image': tf.io.FixedLenFeature([], tf.string), 
#             'label': tf.io.FixedLenFeature([], tf.int64),
#             'filename': tf.io.FixedLenFeature([], tf.string),
#         }

#         try:
#             raw_dataset = tf.data.TFRecordDataset(TFRECORD_PATH)
#             parsed_dataset = raw_dataset.map(lambda x: tf.io.parse_single_example(x, feature_description))
            
#             target_digit = int(digit)
#             digit_samples = parsed_dataset.filter(lambda x: x['label'] == target_digit).shuffle(100).take(limit)

#             batch_results = []
#             for i, record in enumerate(digit_samples):
#                 fid = f"mnist_{digit}_{int(time.time())}_{i}"
#                 img_bytes = record['image'].numpy() 
#                 s3_key = f"datasets/mnist/{digit}/{fid}.png"

#                 # 1. S3 Upload
#                 print(f"📤 [DEBUG] Uploading to S3: {s3_key}...", flush=True)
#                 self.s3_client.put_object(
#                     Bucket=self.bucket,
#                     Key=s3_key,
#                     Body=img_bytes,
#                     ContentType='image/png'
#                 )

#                 # 2. Lambda Trigger
#                 relay_payload = {
#                     "feedback_id": fid,
#                     "label": str(digit),
#                     "image_url": f"s3://{self.bucket}/{s3_key}",
#                     "bucket": self.bucket
#                 }

#                 print(f"📡 [DEBUG] Triggering Lambda for {fid}...", flush=True)
#                 self.lambda_client.invoke(
#                     FunctionName='mnist_ingestor_worker',
#                     InvocationType='Event',
#                     Payload=json.dumps(relay_payload).encode('utf-8')
#                 )
#                 batch_results.append(fid)
                
#                 # 🎯 NEW: Yield progress so the UI spinner stays active and informed
#                 yield (i + 1) / limit, f"Uploaded {i+1}/{limit} samples..."

#             print(f"✅ [DEBUG] Batch Complete: {batch_results}", flush=True)
            
#             # 🎯 CRITICAL CHANGE: Yield the final result dictionary at 1.0 (100%)
#             yield 1.0, {"status": "success", "sample_ids": batch_results}

#         except Exception as e:
#             print(f"❌ [DEBUG] Error: {str(e)}", flush=True)
#             yield 0.0, {"status": "error", "message": str(e)}
            
#     def get_user_feedback(self, username):
#         """Used by HistoryUI to list previous analyses."""
#         try:
#             table = self.dynamodb.Table('Analysis_Summaries')
#             response = table.scan(FilterExpression=Attr('user_id').eq(username))
#             items = response.get('Items', [])
#             return sorted(items, key=lambda x: x.get('timestamp', ''), reverse=True)
#         except Exception as e:
#             self.logger.log_event("DATABASE", "ERROR", f"Error: {e}")
#             return []

#     def _get_table_data(self, table_name, feedback_id):
#         """Matches the 'feedback_id' HASH key found in describe-table."""
#         try:
#             table = self.dynamodb.Table(table_name)
#             response = table.get_item(Key={'feedback_id': feedback_id}) # Fixed key name
#             return response.get('Item')
#         except Exception as e:
#             self.logger.log_event("DB_POLLING", "ERROR", f"Error: {e}")
#             return None




    