import os
import time

def get_prepared_kag_batch(base_path, folder_name="Email", limit=5):
    """
    KAG Loader: Specialized for the Tobacco Industry Dataset.
    Scans local JPGs and prepares them for the Cloud Bridge.
    """
    # 🎯 target: data/kag_reviews/dataset/Email
    target_dir = os.path.join(base_path, folder_name)
    
    if not os.path.exists(target_dir):
        print(f"❌ [LOADER] Directory not found: {target_dir}")
        return []

    # Filter for JPG files
    files = [f for f in os.listdir(target_dir) if f.endswith(('.jpg', '.jpeg'))][:limit]
    samples = []

    print(f"📂 [LOADER] Extracting {len(files)} real documents from {folder_name}...")

    for i, filename in enumerate(files):
        file_path = os.path.join(target_dir, filename)
        
        # Create a unique Feedback ID for the cloud pipeline
        fid = f"kag_{folder_name.lower()}_{int(time.time())}_{i}"
        
        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        samples.append({
            'feedback_id': fid,
            'image_bytes': image_bytes,
            'folder': folder_name,
            'filename': filename,
            'metadata': {
                'source': 'Kaggle_Tobacco_Tobacco3482',
                'category': folder_name,
                'original_name': filename
            }
        })
    
    return samples
import os
import shutil
import time

def get_prepared_kag_batch(base_path, folder_name="Email", limit=5, save_samples=True):
    """
    KAG Loader: Prepares Tobacco JPGs and copies them to a local /samples folder.
    """
    target_dir = os.path.join(base_path, folder_name)
    sample_dir = "samples"
    
    if not os.path.exists(target_dir):
        print(f"❌ [LOADER] Source path not found: {target_dir}")
        return []

    if save_samples and not os.path.exists(sample_dir):
        os.makedirs(sample_dir)

    # Grab JPGs
    files = [f for f in os.listdir(target_dir) if f.endswith(('.jpg', '.jpeg'))][:limit]
    samples = []

    for i, filename in enumerate(files):
        file_path = os.path.join(target_dir, filename)
        fid = f"kag_{folder_name.lower()}_{int(time.time())}_{i}"
        
        # 💾 Save a copy to the local project /samples folder
        if save_samples:
            shutil.copy(file_path, os.path.join(sample_dir, f"{fid}.jpg"))

        with open(file_path, 'rb') as f:
            image_bytes = f.read()

        # 🎯 FIX: Explicitly include the 'metadata' key that the Bridge expects
        samples.append({
            'feedback_id': fid,
            'image_bytes': image_bytes,
            'filename': filename,
            'folder': folder_name,
            'metadata': {  # <--- This was missing!
                'source': 'Kaggle_Tobacco_Set',
                'category': folder_name,
                'local_sample_path': f"{sample_dir}/{fid}.jpg"
            }
        })
    
    return samples