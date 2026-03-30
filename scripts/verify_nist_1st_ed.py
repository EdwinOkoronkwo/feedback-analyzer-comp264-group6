import numpy as np
from PIL import Image
import os

def verify_1st_ed_data(mit_path, mis_path, output_name="verify_nist.png"):
    # 1. Read the .mit (Map) to find where the first image is
    # In 1st Ed, .mit files are often text-based or fixed-width binary
    with open(mit_path, 'r') as f:
        # Looking for the first line with offsets (e.g., "0 128 128")
        first_map_entry = f.readline().split()
    
    # Typical NIST .mit format: [index, offset, width, height, ...]
    # Let's assume standard 128x128 for the first test
    width, height = 128, 128
    bytes_per_image = (width * height) // 8

    # 2. Extract from .mis (Muscle)
    with open(mis_path, 'rb') as f:
        raw_bits = f.read(bytes_per_image)

    # 3. Convert Bits to Pixels
    # NIST 1st Ed uses bitpacked data (1 bit per pixel)
    bits = np.unpackbits(np.frombuffer(raw_bits, dtype=np.uint8))
    pixels = bits.reshape((height, width)) * 255
    
    # 4. Save to verify
    img = Image.fromarray(pixels.astype(np.uint8))
    img.save(output_name)
    print(f"✅ Success! Created {output_name} in your project root.")

if __name__ == "__main__":
    base = "/home/edwin/projects/feedback_analyzer/data/nist_sd19/1stEdition1995/data/by_class/4a/"
    mit = os.path.join(base, "hsf_1.mit")
    mis = os.path.join(base, "hsf_1.mis")
    
    verify_1st_ed_data(mit, mis)