import os
import sys
from typing import List, Tuple, Any

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import cv2
import numpy as np
import easyocr

class OCREngine:
    def __init__(self, languages: List[str] = ['en']):
        # Initialize EasyOCR reader (loads weights into memory)
        # gpu=False by default here; change to True if GPU is available and configured
        self.reader = easyocr.Reader(languages, gpu=False)

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """Decodes, denoises, and applies adaptive thresholding."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Bilateral filter to reduce noise while keeping edges sharp
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Adaptive thresholding for varied label illumination
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 31, 2
        )
        return thresh

    def extract_text(self, image_bytes: bytes) -> Tuple[str, List[Any]]:
        """Runs OCR on the preprocessed image and returns full text + bounding data."""
        processed_img = self.preprocess_image(image_bytes)
        results = self.reader.readtext(processed_img)

        extracted_lines = [res[1] for res in results]
        combined_text = "\n".join(extracted_lines)
        return combined_text, results
