"""
Image processing functionality (Enhanced with OpenCV detection & Base64 storage)
"""
import os
import io
import re
import uuid
import base64
import numpy as np
import torch
import fitz  # PyMuPDF
import cv2   # OpenCV
import pytesseract
from PIL import Image, ImageEnhance
from transformers import CLIPProcessor, CLIPModel
from collections import Counter
from typing import List, Dict, Any, Tuple  # <--- THIS WAS MISSING
from .vector_db import VectorDatabase
from ..utils.config import config

class ImageProcessor:
    """Image processing and indexing"""
    
    def __init__(self, vector_db: VectorDatabase):
        self.vector_db = vector_db
        self.clip_processor = None
        self.clip_model = None
        
        #self._initialize_clip()
        
        # Minimum size to consider something an image
        self.min_image_size = (config.rag.min_image_size, config.rag.min_image_size)
    
    def _ensure_model_loaded(self):
        """Lazy load CLIP model"""
        if self.clip_model is None:
            try:
                print("[INFO] Lazy loading CLIP model...")
                self.clip_processor = CLIPProcessor.from_pretrained(config.models.clip_model_name)
                self.clip_model = CLIPModel.from_pretrained(config.models.clip_model_name)
                print("[INFO] CLIP model loaded successfully")
            except Exception as e:
                print(f"[ERROR] Failed to load CLIP model: {e}")
                raise

    def _initialize_clip(self):
        """Initialize CLIP model"""
        try:
            print("[INFO] Loading CLIP model...")
            self.clip_processor = CLIPProcessor.from_pretrained(config.models.clip_model_name)
            self.clip_model = CLIPModel.from_pretrained(config.models.clip_model_name)
            print("[INFO] CLIP model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load CLIP model: {e}")
            raise

    def enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results"""
        if image.mode != 'RGB': image = image.convert('RGB')
        
        # Resize if too small
        if image.width < 300 or image.height < 300:
            scale = max(300/image.width, 300/image.height)
            new_size = (int(image.width * scale), int(image.height * scale))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            
        enhancer = ImageEnhance.Contrast(image); image = enhancer.enhance(1.2)
        enhancer = ImageEnhance.Sharpness(image); image = enhancer.enhance(1.1)
        return image
    
    def _detect_image_regions(self, page):
        """
        Detect image regions using OpenCV (Canny Edge Detection).
        This finds images that might be embedded as graphics/figures, not just raw objects.
        """
        # Render page to image for analysis
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        if pix is None: return []

        # Convert to numpy array
        img_array = np.frombuffer(pix.samples, dtype=np.uint8)
        if pix.n * pix.width * pix.height != len(pix.samples): return []
        img_array = img_array.reshape(pix.height, pix.width, pix.n)

        # Handle color spaces
        if pix.n == 4: img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)
        elif pix.n == 1: img_array = cv2.cvtColor(img_array, cv2.COLOR_GRAY2RGB)

        # Edge detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        kernel = np.ones((3, 3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        image_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Scale back to PDF coordinates (we rendered at 2x)
            x, y, w, h = x//2, y//2, w//2, h//2 

            if w >= self.min_image_size[0] and h >= self.min_image_size[1]:
                image_regions.append((x, y, x+w, y+h))

        return image_regions
    
    def _extract_image_from_region(self, page, region, padding=20):
        """Extract the actual image bytes from the detected region"""
        x1, y1, x2, y2 = region
        # Add padding
        page_rect = page.rect
        x1 = max(page_rect.x0, x1 - padding)
        y1 = max(page_rect.y0, y1 - padding)
        x2 = min(page_rect.x1, x2 + padding)
        y2 = min(page_rect.y1, y2 + padding)

        clip_rect = fitz.Rect(x1, y1, x2, y2)
        mat = fitz.Matrix(2, 2) # High resolution extraction
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)
        
        if pix is None: return None, None
        
        img_data = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_data))
        return img, img_data
    
    def _generate_tags(self, text_content: str):
        """Simple keyword matching for image tags"""
        keywords = re.findall(r'\b(?:starch|protein|enzyme|diagram|figure|test|experiment|activity|cell|bone|joint|plant)\b', text_content.lower())
        return list(dict.fromkeys([tag for tag, _ in Counter(keywords).most_common(5)]))

    def process_pdfs_directory(self, pdf_dir: str = None, text_embedder=None) -> Dict[str, Any]:
        """Process images from all PDFs in a directory"""
        self._ensure_model_loaded()
        if pdf_dir is None: pdf_dir = config.system.pdf_dir
        
        if not os.path.exists(pdf_dir):
            return {"success": False, "error": "Directory not found", "all_images": []}
        
        pdf_files = [os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        
        all_images = []
        successful_pdfs = 0
        
        for pdf_path in pdf_files:
            pdf_name = os.path.basename(pdf_path)
            print(f"[INFO] Processing images: {pdf_name}")
            
            try:
                doc = fitz.open(pdf_path)
                
                for page_num, page in enumerate(doc):
                    # 1. Detect Images
                    image_regions = self._detect_image_regions(page)
                    
                    for idx, region in enumerate(image_regions):
                        try:
                            # 2. Extract Image
                            image, img_bytes = self._extract_image_from_region(page, region)
                            if image is None or image.width < 50 or image.height < 50: continue
                                
                            # 3. OCR & Tagging
                            enhanced_img = self.enhance_image_for_ocr(image)
                            try:
                                ocr_text = pytesseract.image_to_string(enhanced_img, config='--psm 6').strip()
                            except:
                                ocr_text = ""
                                
                            surrounding_text = page.get_text("text", clip=fitz.Rect(region)).strip()
                            full_context = f"{ocr_text} {surrounding_text}"
                            tags = self._generate_tags(full_context)
                            caption = ocr_text[:100] if ocr_text else f"Figure from {pdf_name}, Page {page_num + 1}"
                            
                            # 4. Generate Visual Embedding (CLIP)
                            inputs = self.clip_processor(images=image.convert("RGB"), return_tensors="pt")
                            with torch.no_grad():
                                visual_features = self.clip_model.get_image_features(**inputs)
                            visual_emb = visual_features[0].cpu().tolist()
                            
                            # 5. Store Data (including Base64)
                            img_id = str(uuid.uuid4())
                            image_data = {
                                'id': img_id,
                                'caption': caption,
                                'ocr_text': ocr_text,
                                'data': base64.b64encode(img_bytes).decode('utf-8'), # Save as Base64 string
                                'source_pdf': pdf_name,
                                'page_num': page_num,
                                'tags': tags,
                                'bbox': list(region),
                                'visual_embedding': visual_emb
                            }
                            
                            self.vector_db.add_image_metadata(image_data)
                            all_images.append(image_data)
                            
                        except Exception as e:
                            # print(f"[WARN] Error processing image region: {e}")
                            continue
                
                doc.close()
                successful_pdfs += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to process images from {pdf_name}: {e}")

        print(f"[INFO] Image processing complete: {len(all_images)} images indexed")
        
        return {
            "success": successful_pdfs > 0,
            "total_indexed": len(all_images),
            "all_images": all_images 
        }
    
    def encode_text_query(self, query: str) -> List[float]:
        """Encode text query for CLIP similarity search"""
        self._ensure_model_loaded()
        try:
            text_inputs = self.clip_processor(text=query, return_tensors="pt", padding=True)
            with torch.no_grad():
                clip_query_emb = self.clip_model.get_text_features(**text_inputs)[0]
            return clip_query_emb.cpu().tolist()
        except Exception as e:
            print(f"[ERROR] Failed to encode text query with CLIP: {e}")
            return []
    
    def get_clip_model(self):
        """Get CLIP model and processor"""
        self._ensure_model_loaded()
        return self.clip_model, self.clip_processor