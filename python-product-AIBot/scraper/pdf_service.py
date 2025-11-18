"""PDF processing service that orchestrates parsing and product detection"""
import os
import tempfile
from typing import List, Dict, Optional
from pathlib import Path
import logging
from datetime import datetime

from .pdf_parser import PDFParser
from .product_detector import ProductDetector
from .image_handler import ImageHandler

logger = logging.getLogger(__name__)


class PDFService:
    """Service for processing PDFs and extracting products"""
    
    def __init__(self):
        """Initialize PDF service"""
        self.detector = ProductDetector()
    
    def process_pdf(self, pdf_path: str, pdf_filename: str, use_ocr: bool = True) -> Dict:
        """
        Process PDF and extract products
        
        Args:
            pdf_path: Path to PDF file
            pdf_filename: Original filename of PDF
            use_ocr: Whether to use OCR for image-based extraction
            
        Returns:
            Dictionary containing:
                - products: List of extracted products
                - metadata: PDF metadata (page count, etc.)
                - errors: List of any errors encountered
        """
        results = {
            'products': [],
            'metadata': {
                'filename': pdf_filename,
                'processed_at': datetime.now().isoformat(),
                'page_count': 0
            },
            'errors': []
        }
        
        try:
            # Parse PDF
            with PDFParser(pdf_path) as parser:
                pdf_content = parser.extract_all()
                results['metadata']['page_count'] = pdf_content['page_count']
                
                # Extract products from text
                text_products = []
                for page_num, text in pdf_content['text'].items():
                    try:
                        products = self.detector.detect_from_text(text, page_num)
                        text_products.extend(products)
                    except Exception as e:
                        logger.error(f"Error detecting products from text on page {page_num}: {e}")
                        results['errors'].append(f"Page {page_num} text extraction: {str(e)}")
                
                # Extract products from tables
                table_products = []
                for page_num, tables in pdf_content['tables'].items():
                    try:
                        products = self.detector.detect_from_tables(tables, page_num)
                        table_products.extend(products)
                    except Exception as e:
                        logger.error(f"Error detecting products from tables on page {page_num}: {e}")
                        results['errors'].append(f"Page {page_num} table extraction: {str(e)}")
                
                # Extract images from PDF (always, not just for OCR)
                images_by_page = {}
                try:
                    image_handler = ImageHandler(pdf_path)
                    images_by_page = image_handler.extract_images_from_pdf()
                except Exception as e:
                    logger.warning(f"Image extraction failed: {e}")
                    results['errors'].append(f"Image extraction: {str(e)}")
                
                # Extract products from images (if OCR enabled)
                image_products = []
                if use_ocr and images_by_page:
                    try:
                        for page_num, image_list in images_by_page.items():
                            try:
                                products = self.detector.detect_from_images(image_list, page_num)
                                image_products.extend(products)
                            except Exception as e:
                                logger.error(f"Error detecting products from images on page {page_num}: {e}")
                                results['errors'].append(f"Page {page_num} image extraction: {str(e)}")
                    except Exception as e:
                        logger.warning(f"OCR processing failed: {e}")
                        results['errors'].append(f"OCR processing: {str(e)}")
                
                # Combine all results
                all_results = [text_products, table_products, image_products]
                combined_products = self.detector.combine_results(all_results)
                
                # Associate images with products based on page number
                for product in combined_products:
                    page_num = product.get('page_number')
                    if page_num and page_num in images_by_page:
                        # Get images for this page
                        page_images = images_by_page[page_num]
                        if page_images:
                            # Convert image data to base64 data URIs
                            product_images = []
                            for img_dict in page_images:
                                img_data = img_dict.get('data', '')
                                if img_data:
                                    if not img_data.startswith('data:image'):
                                        product_images.append(f"data:image/png;base64,{img_data}")
                                    else:
                                        product_images.append(img_data)
                            
                            # Add images to product (merge with existing if any)
                            if product_images:
                                existing_images = product.get('images', [])
                                # Avoid duplicates
                                for img in product_images:
                                    if img not in existing_images:
                                        existing_images.append(img)
                                product['images'] = existing_images
                
                # Add PDF source and extraction timestamp to each product
                for product in combined_products:
                    product['pdf_source'] = pdf_filename
                    product['extracted_at'] = datetime.now().isoformat()
                    product['status'] = 'pending'
                    # Ensure all required fields exist
                    if 'title' not in product:
                        product['title'] = 'Unknown Product'
                    if 'price' not in product:
                        product['price'] = ''
                    if 'description' not in product:
                        product['description'] = ''
                    if 'images' not in product:
                        product['images'] = []
                    if 'source' not in product:
                        product['source'] = 'PDF'
                
                results['products'] = combined_products
                
        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            results['errors'].append(f"PDF processing failed: {str(e)}")
        
        return results
    
    def process_uploaded_pdf(self, uploaded_file, use_ocr: bool = True) -> Dict:
        """
        Process uploaded PDF file from Streamlit
        
        Args:
            uploaded_file: Streamlit UploadedFile object
            use_ocr: Whether to use OCR
            
        Returns:
            Dictionary with products and metadata
        """
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(uploaded_file.read())
        
        try:
            # Process PDF
            results = self.process_pdf(tmp_path, uploaded_file.name, use_ocr)
            return results
        finally:
            # Clean up temporary file
            try:
                os.unlink(tmp_path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")

