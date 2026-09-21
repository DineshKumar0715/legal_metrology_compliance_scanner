import io
import sys
import numpy as np
import cv2

# Set Windows console encoding to UTF-8 if available
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


class OCREngine:
    def __init__(self, gpu: bool = False):
        """
        Initialize OCR reader for English text extraction.
        Prioritizes EasyOCR as per specification; falls back to RapidOCR (ONNX)
        if PyTorch DLLs are restricted by OS Application Control policies (WDAC).
        """
        self.engine_type = "easyocr"
        self.reader = None
        self.rapid_reader = None

        try:
            import easyocr
            self.reader = easyocr.Reader(["en"], gpu=gpu)
            self.engine_type = "easyocr"
        except Exception as e:
            # Fallback to RapidOCR (ONNX Runtime engine)
            print(f"[OCR] EasyOCR initialization fallback ({e}). Using ONNX OCR engine.", flush=True)
            try:
                from rapidocr_onnxruntime import RapidOCR
                self.rapid_reader = RapidOCR()
                self.engine_type = "rapidocr"
            except Exception as e2:
                print(f"[OCR] Failed to load ONNX OCR engine: {e2}", flush=True)

    def preprocess_image(self, image_bytes: bytes) -> np.ndarray:
        """
        Preprocess image for optimal OCR extraction:
        1. Decode buffer using cv2.imdecode
        2. Convert to Grayscale
        3. Apply Bilateral Filter for edge-preserving denoising
        4. Apply Adaptive Gaussian Thresholding
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Failed to decode image buffer. Invalid image format.")

        # Convert to Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Bilateral Filter for edge-preserving smoothing
        denoised = cv2.bilateralFilter(gray, 9, 75, 75)

        # Apply Adaptive Thresholding
        processed = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2
        )

        return processed

    def _enhance_contrast(self, img_bgr: np.ndarray) -> np.ndarray:
        """Apply CLAHE on the L channel of LAB color space to boost text readability."""
        try:
            lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_enhanced = clahe.apply(l)
            merged = cv2.merge((l_enhanced, a, b))
            return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        except Exception:
            return img_bgr

    def extract_text(self, image_bytes: bytes) -> tuple[str, list]:
        """
        Extract text from image bytes using a multi-pass OCR strategy:
        Pass 1: High-resolution RGB / Enhanced color image (preserves anti-aliasing and color contrast)
        Pass 2: Adaptive preprocessed image (for stamped ink-jet codes or dot matrix text)
        Combines and deduplicates recognized lines.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        raw_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if raw_img is None:
            raise ValueError("Failed to decode image buffer. Invalid image format.")

        enhanced_img = self._enhance_contrast(raw_img)
        processed_img = self.preprocess_image(image_bytes)

        extracted_lines = []
        bounding_boxes = []
        seen_texts = set()

        if self.engine_type == "easyocr" and self.reader is not None:
            # Run on enhanced RGB image first
            results = self.reader.readtext(enhanced_img)
            
            # If low detection count, also run on raw and preprocessed
            if len(results) < 5:
                results_raw = self.reader.readtext(raw_img)
                results_prep = self.reader.readtext(processed_img)
                all_results = results + results_raw + results_prep
            else:
                all_results = results

            for bbox, text, conf in all_results:
                clean_text = text.strip()
                norm_key = clean_text.lower().replace(" ", "")
                if clean_text and len(clean_text) >= 2 and norm_key not in seen_texts:
                    seen_texts.add(norm_key)
                    extracted_lines.append(clean_text)
                    bounding_boxes.append({
                        "box": [[int(coord[0]), int(coord[1])] for coord in bbox],
                        "text": clean_text,
                        "confidence": float(conf),
                    })

        elif self.rapid_reader is not None:
            # Pass 1: Run RapidOCR on Enhanced RGB image
            result_enhanced, _ = self.rapid_reader(enhanced_img)
            # Pass 2: Run RapidOCR on Raw RGB image
            result_raw, _ = self.rapid_reader(raw_img)
            
            combined = []
            if result_enhanced:
                combined.extend(result_enhanced)
            if result_raw:
                combined.extend(result_raw)
                
            # If detection is sparse, run on thresholded preprocessed image
            if len(combined) < 4:
                result_prep, _ = self.rapid_reader(processed_img)
                if result_prep:
                    combined.extend(result_prep)

            for item in combined:
                # item format: [ [ [x1,y1],[x2,y2],[x3,y3],[x4,y4] ], text, score ]
                box = item[0]
                text = item[1].strip()
                conf = float(item[2])
                norm_key = text.lower().replace(" ", "")

                # Filter out pure noise characters and duplicates
                if text and len(text) >= 2 and norm_key not in seen_texts:
                    seen_texts.add(norm_key)
                    extracted_lines.append(text)
                    bounding_boxes.append({
                        "box": [[int(pt[0]), int(pt[1])] for pt in box],
                        "text": text,
                        "confidence": conf,
                    })

        text_output = "\n".join(extracted_lines)
        return text_output, bounding_boxes
