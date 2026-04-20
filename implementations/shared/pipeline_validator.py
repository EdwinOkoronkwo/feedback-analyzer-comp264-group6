import os
from PIL import Image
import io

class PipelineValidator:
    """
    Centralized validation for AI Sentinel Pipeline constraints.
    Aligned strictly with AWS Service Quotas (Textract, Comprehend, Polly)
    and Mistral Context Windows.
    """

    # --- CONSTANTS DERIVED FROM AWS & MISTRAL LIMITS ---
    LIMITS = {
        "max_mb": 10,              # Textract Max (PDF, TIFF, JPG, PNG)
        "min_dim": 200,            # Internal safety floor
        "max_dim": 10000,          # Textract max dimension (approx)
        "min_chars": 5,            # Minimum for meaningful analysis
        "max_chars": 3000,         # Polly Bottleneck (Strict System Limit)
        "max_batch": 15,           # Infrastructure safety cap
        "allowed_ext": [".png", ".jpg", ".jpeg", ".pdf", ".tiff", ".tif"],
        "approx_token_ratio": 4    # ~4 chars per token for English
    }

    HINTS = {
        "image": f"Upload {', '.join(LIMITS['allowed_ext'])} (Max {LIMITS['max_mb']}MB)",
        "text": f"Input limit: {LIMITS['max_chars']} characters (required for AWS Polly compatibility)",
        "batch": f"Select up to {LIMITS['max_batch']} files for batch ingestion"
    }

    # --- 1. FILE & IMAGE CONSTRAINTS ---

    @staticmethod
    def validate_file_type(filename):
        """Ensures file extension is within the AWS Textract allowed list."""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in PipelineValidator.LIMITS["allowed_ext"]:
            return False, f"Unsupported file type '{ext}'. Allowed: {PipelineValidator.LIMITS['allowed_ext']}"
        return True, "TYPE_OK"

    @staticmethod
    def validate_image_spec(uploaded_file):
        """
        Validates file size and type based on AWS Textract limits (10MB).
        """
        if uploaded_file is None:
            return True, "No image provided."

        # 1. Type Check (Includes PDF/TIFF/JPG/PNG)
        type_ok, type_msg = PipelineValidator.validate_file_type(uploaded_file.name)
        if not type_ok:
            return False, type_msg

        # 2. Size check (AWS Textract Limit: 10MB)
        file_size = uploaded_file.size / (1024 * 1024)
        if file_size > PipelineValidator.LIMITS["max_mb"]:
            return False, f"File exceeds AWS 10MB limit (Current: {file_size:.2f}MB)."

        # 3. Dimension check for Image formats
        if uploaded_file.name.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.tif')):
            try:
                img = Image.open(uploaded_file)
                width, height = img.size
                if width < PipelineValidator.LIMITS["min_dim"] or height < PipelineValidator.LIMITS["min_dim"]:
                    return False, f"Resolution too low ({width}x{height}) for reliable OCR."
            except Exception as e:
                return False, f"Invalid Image File: {str(e)}"

        return True, "IMAGE_OK"

    # --- 2. TEXT & CONTEXT CONSTRAINTS ---

    @staticmethod
    def validate_text_length(text):
        """
        Enforces a 3,000 character limit.
        Even though Comprehend/Translate allow 5k and Mistral allows more, 
        AWS Polly caps at 3k per request, which defines our system's max throughput.
        """
        clean_text = text.strip() if text else ""
        length = len(clean_text)
        
        if length < PipelineValidator.LIMITS["min_chars"]:
            return False, f"Input too short ({length} chars). Min: {PipelineValidator.LIMITS['min_chars']}"
        
        if length > PipelineValidator.LIMITS["max_chars"]:
            return False, (f"Input exceeds system bottleneck of {PipelineValidator.LIMITS['max_chars']} characters "
                          f"(AWS Polly Limit). Please shorten your input.")
            
        return True, "TEXT_OK"

    # --- 3. BATCH CONSTRAINTS ---

    @staticmethod
    def validate_batch_size(count):
        """Prevents system overload during batch ingestion."""
        if count > PipelineValidator.LIMITS["max_batch"]:
            return False, f"Batch size {count} exceeds safety limit of {PipelineValidator.LIMITS['max_batch']}."
        return True, "BATCH_OK"