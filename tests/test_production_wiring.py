import uuid
import os
from chalicelib.local.local_factory import LocalPipelineFactory

def test_batch_multimodal_with_identity():
    print("🚀 STARTING IDENTITY-ENFORCED BATCH VERIFICATION")
    # Setup the stack (Orchestrator, AI Provider, and Services)
    pipeline, user_service = LocalPipelineFactory.create_local_stack()
    
    # 1. ENFORCE IDENTITY
    test_username = "analyst_edwin"
    try:
        user_service.register(test_username, "password123", role="admin")
        print(f"👤 Identity Verified: Admin '{test_username}' is now active.")
    except Exception:
        # If user already exists in local DynamoDB
        print(f"👤 Identity Found: Continuing as '{test_username}'.")
    
    active_user = user_service.get_user(test_username)
    results_log = [] 

    # 2. Dataset: Diverse inputs to be translated to English
    test_batch = [
        {"type": "IMAGE", "path": "/home/edwin/projects/feedback_analyzer/tests/sample_images/french.jpg", "lang": "French"},
        {"type": "IMAGE", "path": "/home/edwin/projects/feedback_analyzer/tests/sample_images/spanish.jpg", "lang": "Spanish"},
        {"type": "TEXT", "content": "The UI is clean but the export feature is slow.", "lang": "English"},
        {"type": "TEXT", "content": "Me encanta la rapidez de la respuesta.", "lang": "Spanish"}
    ]

    # 3. Execution Loop
    results_log = [] 
    for entry in test_batch:
        job_id = str(uuid.uuid4())
        
        payload = {
            "feedback_id": job_id,
            "user_id": active_user.username, 
            "source_type": entry["type"],
            "file_path": entry.get("path"),
            "text": entry.get("content"),
            "target_lang": "English"
        }

        print(f"\n📦 Processing {entry['type']} ({entry['lang']} -> English)...")

        for progress, status in pipeline.run(payload):
            if progress == 1.0:
                # 'status' is now the FeedbackModel object returned by the orchestrator
                print(f"✅ Success: Job {job_id[:8]}... linked to {test_username}")
                results_log.append(status) 
            elif progress == 0.0:
                print(f"💥 PIPELINE ERROR: {status}")

    # 4. Final Verification: Querying Permanent Storage
    print("\n" + "="*60)
    print("📊 FINAL STANDARDIZED BATCH SUMMARY (FROM PERMANENT STORAGE)")
    print("="*60)

    for record in results_log:
        try:
            # Re-fetch from the database
            db_record = pipeline.persistence.get_unified_view(record['feedback_id'])
            
            # Accessing via ['key'] because db_record is a dictionary
            f_id = db_record['feedback_id']
            user = db_record['user_id']
            sent = db_record.get('sentiment', 'UNKNOWN')
            status = db_record.get('status', 'PENDING')
            content = db_record.get('content', 'No summary available')
            audio = db_record.get('audio_path', 'No audio generated')

            print(f"ID: {f_id[:8]}... | User: {user}")
            print(f"Sentiment: {sent} | Status: {status}")
            print(f"English Summary: {content[:150]}...")
            
            if audio and audio != 'No audio generated':
                print(f"🔊 Audio Location: {audio}")
                
            print("-" * 30)
        except Exception as e:
            print(f"❌ Storage Retrieval Error: {e}")

    print("="*60)

if __name__ == "__main__":
    test_batch_multimodal_with_identity()