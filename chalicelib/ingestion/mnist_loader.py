# chalicelib/ingestion/mnist_loader.py
import io
from PIL import Image

def get_prepared_batch(dataset, limit=1):
    """
    Handles all TF and PIL logic here. 
    Converts Tensors to PNG bytes ready for S3.
    """
    prepared_samples = []
    logger.info(f"[PIPELINE] PREPARING: Extracting {limit} samples from dataset...")
    
    for i, (image_tensor, label_tensor) in enumerate(dataset.take(limit)):
        # 1. Convert Tensor to PNG bytes (Rescale 0-1 to 0-255)
        img_array = (image_tensor.numpy() * 255).astype('uint8').reshape(28, 28)
        img = Image.fromarray(img_array)
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        
        # Extract label safely (handles both scalar and array labels)
        label_val = label_tensor.numpy()
        label = int(label_val[0]) if label_val.ndim > 0 else int(label_val)
        
        prepared_samples.append({
            "label": label,
            "image_bytes": img_byte_arr.getvalue(),
            "index": i
        })
    
    return prepared_samples