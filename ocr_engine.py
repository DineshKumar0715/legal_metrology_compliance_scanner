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
        # Initialize EasyOCR reader (loads CRAFT + CRNN weights into memory)
        self.reader = easyocr.Reader(languages, gpu=False)

    def extract_text(self, image_bytes: bytes) -> Tuple[str, List[Any]]:
        """Runs fast high-accuracy OCR on the packaging image."""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes")

        # Scale down large images to max 900px for 5x faster CPU inference while preserving OCR accuracy
        h, w = img.shape[:2]
        if max(h, w) > 900:
            scale = 900.0 / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

        results = self.reader.readtext(img)
        extracted_lines = [res[1] for res in results]
        combined_text = "\n".join(extracted_lines)
        return combined_text, results
