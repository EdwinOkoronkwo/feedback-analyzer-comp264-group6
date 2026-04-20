from PIL import Image
import os
import numpy as np

def create_large_test_image(filename="test_12MB_image.png", target_mb=12):
    """
    Generates a large uncompressed-style PNG to test file size limits.
    The file will be saved in the current working directory.
    """
    # Estimate dimensions for a 3-channel (RGB) image to hit target size.
    # 1 byte per channel per pixel. 2000x2000x3 is approx 12MB.
    # We use a slightly larger factor because PNG compression (even at low levels)
    # will shrink the random noise slightly.
    side = int(np.sqrt((target_mb * 1024 * 1024) / 3))
    
    print(f"Generating random pixel data for {side}x{side} image...")
    
    # Generate random noise using NumPy (standard Python numerical library)
    # We use uint8 to represent pixel values (0-255)
    random_data = np.random.randint(0, 256, (side, side, 3), dtype=np.uint8)
    
    # Convert the array to a PIL Image object
    img = Image.fromarray(random_data)
    
    # Save as PNG with 0 compression to ensure the file size stays large
    # This will be saved to the local directory
    img.save(filename, format="PNG", compress_level=0)
    
    file_size_mb = os.path.getsize(filename) / (1024 * 1024)
    
    print(f"✅ Success!")
    print(f"Path: {os.path.abspath(filename)}")
    print(f"Dimensions: {side}x{side} px")
    print(f"Resulting Size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    # Ensure Pillow is installed: pip install Pillow numpy
    try:
        create_large_test_image("test_12MB_image.png", 12)
    except ImportError:
        print("❌ Error: Please install dependencies first: pip install Pillow numpy")