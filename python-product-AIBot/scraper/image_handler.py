"""Image handler for extracting and processing images from PDFs"""
import io
import base64
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

try:
    from pdf2image import convert_from_path
    from PIL import Image
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logging.warning("pdf2image not available. Image extraction will be limited.")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available. Embedded image extraction will be limited.")

logger = logging.getLogger(__name__)


class ImageHandler:
    """Handler for extracting and processing images from PDFs"""
    
    def __init__(self, pdf_path: str, dpi: int = 200):
        """
        Initialize image handler
        
        Args:
            pdf_path: Path to PDF file
            dpi: DPI for image conversion (higher = better quality, larger files)
        """
        self.pdf_path = pdf_path
        self.dpi = dpi
    
    def extract_images_from_pdf(self, page_numbers: Optional[List[int]] = None) -> Dict[int, List[Dict]]:
        """
        Extract images from PDF pages (both embedded images and page images)
        
        Args:
            page_numbers: List of page numbers to extract (None = all pages)
            
        Returns:
            Dictionary mapping page number to list of image data
        """
        images_by_page = {}
        
        # First, try to extract embedded images using PyMuPDF (more accurate)
        if PYMUPDF_AVAILABLE:
            try:
                embedded_images = self._extract_embedded_images_pymupdf(page_numbers)
                # Merge embedded images into result
                for page_num, img_list in embedded_images.items():
                    if page_num not in images_by_page:
                        images_by_page[page_num] = []
                    images_by_page[page_num].extend(img_list)
            except Exception as e:
                logger.warning(f"PyMuPDF image extraction failed: {e}")
        
        # Also extract page images using pdf2image (for OCR and full page capture)
        if PDF2IMAGE_AVAILABLE:
            try:
                page_images = self._extract_page_images_pdf2image(page_numbers)
                # Merge page images into result
                for page_num, img_list in page_images.items():
                    if page_num not in images_by_page:
                        images_by_page[page_num] = []
                    # Add page image if no embedded images found for this page
                    if not images_by_page[page_num]:
                        images_by_page[page_num].extend(img_list)
            except Exception as e:
                logger.warning(f"pdf2image extraction failed: {e}")
        
        if not images_by_page:
            logger.warning("No images extracted from PDF. Check if pdf2image/PyMuPDF are installed and PDF contains images.")
        
        return images_by_page
    
    def _extract_embedded_images_pymupdf(self, page_numbers: Optional[List[int]] = None) -> Dict[int, List[Dict]]:
        """Extract embedded images from PDF using PyMuPDF"""
        images_by_page = {}
        
        try:
            doc = fitz.open(self.pdf_path)
            
            # Determine which pages to process
            pages_to_process = page_numbers if page_numbers else list(range(len(doc)))
            
            for page_idx in pages_to_process:
                if page_idx < 0 or page_idx >= len(doc):
                    continue
                
                page = doc[page_idx]
                page_num = page_idx + 1
                page_images = []
                
                # Get image list for this page
                image_list = page.get_images(full=True)
                
                for img_idx, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]
                        
                        # Convert to PIL Image to get dimensions
                        pil_image = Image.open(io.BytesIO(image_bytes))
                        width, height = pil_image.size
                        
                        # Convert to base64
                        img_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        page_images.append({
                            'data': img_base64,
                            'format': image_ext.upper(),
                            'width': width,
                            'height': height,
                            'mime_type': f'image/{image_ext}',
                            'type': 'embedded'
                        })
                    except Exception as e:
                        logger.warning(f"Error extracting embedded image {img_idx} from page {page_num}: {e}")
                
                if page_images:
                    images_by_page[page_num] = page_images
            
            doc.close()
        except Exception as e:
            logger.error(f"Error in PyMuPDF extraction: {e}")
        
        return images_by_page
    
    def _extract_page_images_pdf2image(self, page_numbers: Optional[List[int]] = None) -> Dict[int, List[Dict]]:
        """Extract page images using pdf2image (converts entire pages to images)"""
        images_by_page = {}
        
        try:
            # Convert PDF pages to images
            if page_numbers:
                images = convert_from_path(self.pdf_path, dpi=self.dpi, first_page=min(page_numbers), last_page=max(page_numbers))
            else:
                images = convert_from_path(self.pdf_path, dpi=self.dpi)
            
            for idx, pil_image in enumerate(images):
                page_num = (page_numbers[idx] if page_numbers else idx + 1)
                
                # Convert PIL Image to base64
                img_buffer = io.BytesIO()
                pil_image.save(img_buffer, format='PNG')
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
                
                # Get image dimensions
                width, height = pil_image.size
                
                images_by_page[page_num] = [{
                    'data': img_base64,
                    'format': 'PNG',
                    'width': width,
                    'height': height,
                    'mime_type': 'image/png',
                    'type': 'page'
                }]
                
        except Exception as e:
            logger.error(f"Error extracting page images with pdf2image: {e}")
        
        return images_by_page
    
    def extract_single_page_image(self, page_number: int) -> Optional[Dict]:
        """
        Extract image from a single PDF page
        
        Args:
            page_number: Page number to extract (1-indexed)
            
        Returns:
            Image data dictionary or None
        """
        result = self.extract_images_from_pdf([page_number])
        if page_number in result and result[page_number]:
            return result[page_number][0]
        return None
    
    def create_thumbnail(self, image_data: Dict, max_size: Tuple[int, int] = (200, 200)) -> Optional[str]:
        """
        Create thumbnail from image data
        
        Args:
            image_data: Image data dictionary with 'data' (base64) field
            max_size: Maximum thumbnail size (width, height)
            
        Returns:
            Base64 encoded thumbnail or None
        """
        try:
            # Decode base64 image
            img_bytes = base64.b64decode(image_data['data'])
            img = Image.open(io.BytesIO(img_bytes))
            
            # Create thumbnail
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Convert back to base64
            thumb_buffer = io.BytesIO()
            img.save(thumb_buffer, format='PNG')
            thumb_base64 = base64.b64encode(thumb_buffer.getvalue()).decode('utf-8')
            
            return thumb_base64
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
            return None
    
    @staticmethod
    def image_to_base64(image_path: str) -> Optional[str]:
        """
        Convert image file to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string or None
        """
        try:
            with open(image_path, 'rb') as img_file:
                return base64.b64encode(img_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error converting image to base64: {e}")
            return None

