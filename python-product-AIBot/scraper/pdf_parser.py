"""PDF parser for extracting text, images, and tables from PDF files"""
import pdfplumber
import io
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class PDFParser:
    """Parser for extracting content from PDF files"""
    
    def __init__(self, pdf_path: str):
        """
        Initialize PDF parser
        
        Args:
            pdf_path: Path to PDF file
        """
        self.pdf_path = pdf_path
        self.pdf_file = None
    
    def __enter__(self):
        """Context manager entry"""
        try:
            self.pdf_file = pdfplumber.open(self.pdf_path)
            return self
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.pdf_file:
            self.pdf_file.close()
    
    def extract_text(self) -> Dict[int, str]:
        """
        Extract text from all pages
        
        Returns:
            Dictionary mapping page number to text content
        """
        text_by_page = {}
        
        if not self.pdf_file:
            return text_by_page
        
        try:
            for page_num, page in enumerate(self.pdf_file.pages, start=1):
                text = page.extract_text()
                if text:
                    text_by_page[page_num] = text.strip()
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
        
        return text_by_page
    
    def extract_tables(self) -> Dict[int, List[List[str]]]:
        """
        Extract tables from all pages
        
        Returns:
            Dictionary mapping page number to list of tables (each table is list of rows)
        """
        tables_by_page = {}
        
        if not self.pdf_file:
            return tables_by_page
        
        try:
            for page_num, page in enumerate(self.pdf_file.pages, start=1):
                tables = page.extract_tables()
                if tables:
                    # Convert tables to list of lists (rows)
                    table_data = []
                    for table in tables:
                        if table:
                            table_data.append(table)
                    if table_data:
                        tables_by_page[page_num] = table_data
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
        
        return tables_by_page
    
    def extract_images(self) -> Dict[int, List[Dict]]:
        """
        Extract images from PDF pages
        
        Returns:
            Dictionary mapping page number to list of image metadata
        """
        images_by_page = {}
        
        if not self.pdf_file:
            return images_by_page
        
        try:
            for page_num, page in enumerate(self.pdf_file.pages, start=1):
                images = []
                # pdfplumber doesn't directly extract images, but we can get image objects
                # For actual image extraction, we'll use pdf2image in image_handler
                # This method provides metadata about images
                if hasattr(page, 'images'):
                    for img in page.images:
                        images.append({
                            'x0': img.get('x0', 0),
                            'y0': img.get('y0', 0),
                            'x1': img.get('x1', 0),
                            'y1': img.get('y1', 0),
                            'width': img.get('width', 0),
                            'height': img.get('height', 0),
                        })
                if images:
                    images_by_page[page_num] = images
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
        
        return images_by_page
    
    def get_page_count(self) -> int:
        """Get total number of pages in PDF"""
        if not self.pdf_file:
            return 0
        return len(self.pdf_file.pages)
    
    def extract_all(self) -> Dict:
        """
        Extract all content from PDF
        
        Returns:
            Dictionary containing text, tables, images, and page count
        """
        return {
            'text': self.extract_text(),
            'tables': self.extract_tables(),
            'images': self.extract_images(),
            'page_count': self.get_page_count(),
            'filename': Path(self.pdf_path).name
        }

