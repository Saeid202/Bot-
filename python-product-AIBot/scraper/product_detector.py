"""Product detection logic for extracting products from PDF content"""
import re
from typing import List, Dict, Optional, Tuple
import logging

try:
    import pytesseract
    from PIL import Image
    import io
    import base64
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    logging.warning("pytesseract/PIL not available. OCR features will be disabled.")

# Note: pytesseract requires Tesseract OCR to be installed on the system
# On Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
# On Linux: sudo apt-get install tesseract-ocr
# On Mac: brew install tesseract

logger = logging.getLogger(__name__)


class ProductDetector:
    """Detector for identifying products in PDF content"""
    
    def __init__(self):
        """Initialize product detector with enhanced patterns"""
        # Enhanced price patterns
        self.price_patterns = [
            r'\$[\d,]+\.?\d*',  # $123.45 or $1,234.56
            r'USD\s*[\d,]+\.?\d*',  # USD 123.45
            r'EUR\s*[\d,]+\.?\d*',  # EUR 123.45
            r'GBP\s*[\d,]+\.?\d*',  # GBP 123.45
            r'CNY\s*[\d,]+\.?\d*',  # CNY 123.45
            r'[\d,]+\.?\d*\s*(USD|EUR|GBP|JPY|CNY|RMB)',  # 123.45 USD
            r'Price[:\s]+[\d,]+\.?\d*',  # Price: 123.45
            r'Cost[:\s]+[\d,]+\.?\d*',  # Cost: 123.45
            r'Amount[:\s]+[\d,]+\.?\d*',  # Amount: 123.45
            r'[\d,]+\.?\d*',  # Just numbers (fallback, but more careful)
        ]
        
        # Enhanced product name indicators
        self.product_indicators = [
            r'Product[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'Item[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'Name[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'Description[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'Model[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'SKU[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
            r'Part[:\s]+(.+?)(?:\n|$|Price|Cost|Amount)',
        ]
        
        # Common product separators
        self.product_separators = [
            r'\n\s*\n',  # Double newline
            r'\n\s*[-=]{3,}',  # Horizontal line
            r'\n\s*\d+\.\s+',  # Numbered list
            r'\n\s*[•·▪▫]\s+',  # Bullet points
        ]
    
    def detect_from_text(self, text: str, page_number: int = 1) -> List[Dict]:
        """
        Detect products from text content with improved accuracy
        
        Args:
            text: Text content to analyze
            page_number: Page number where text was found
            
        Returns:
            List of detected products
        """
        products = []
        
        if not text or len(text.strip()) < 10:
            return products
        
        # Method 1: Try to split by product separators first
        sections = self._split_into_sections(text)
        
        for section in sections:
            product = self._extract_product_from_section(section, page_number)
            if product and self._is_valid_product(product):
                products.append(product)
        
        # Method 2: If no products found, try line-by-line parsing
        if not products:
            products = self._detect_from_lines(text, page_number)
        
        # Method 3: If still no products, try paragraph-based detection
        if not products:
            products = self._detect_unstructured_products(text, page_number)
        
        return products
    
    def _split_into_sections(self, text: str) -> List[str]:
        """Split text into potential product sections"""
        sections = []
        
        # Try different separators
        for separator in self.product_separators:
            parts = re.split(separator, text)
            if len(parts) > 1:
                sections = [p.strip() for p in parts if len(p.strip()) > 20]
                break
        
        # If no clear separators, split by double newlines
        if not sections:
            sections = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 20]
        
        return sections
    
    def _extract_product_from_section(self, section: str, page_number: int) -> Dict:
        """Extract product information from a section of text"""
        product = {}
        lines = [l.strip() for l in section.split('\n') if l.strip()]
        
        if not lines:
            return product
        
        # First line is often the title
        if not product.get('title'):
            first_line = lines[0]
            # Check if it's not just a price or number
            if not re.match(r'^[\d$,\s.]+$', first_line) and len(first_line) > 3:
                product['title'] = first_line[:200]  # Limit title length
        
        # Look for price in all lines
        for line in lines:
            price = self._extract_price(line)
            if price:
                product['price'] = price
                break
        
        # Description is the rest of the text
        if len(lines) > 1:
            desc_lines = lines[1:]
            # Skip lines that are just prices or numbers
            desc_lines = [l for l in desc_lines if not re.match(r'^[\d$,\s.]+$', l)]
            if desc_lines:
                product['description'] = ' '.join(desc_lines[:5])[:500]  # First 5 lines, max 500 chars
        
        product['page_number'] = page_number
        product['source'] = 'PDF Text'
        
        return product
    
    def _detect_from_lines(self, text: str, page_number: int) -> List[Dict]:
        """Detect products by analyzing lines sequentially"""
        products = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        current_product = {}
        for i, line in enumerate(lines):
            # Try to extract title
            if not current_product.get('title'):
                title = self._extract_title(line)
                if title and len(title) > 3:
                    current_product['title'] = title
                    continue
            
            # Try to extract price
            if not current_product.get('price'):
                price = self._extract_price(line)
                if price:
                    current_product['price'] = price
                    # If we have both title and price, this might be a complete product
                    if current_product.get('title'):
                        current_product['description'] = ' '.join(lines[max(0, i-2):i])[:300]
                        current_product['page_number'] = page_number
                        current_product['source'] = 'PDF Text'
                        if self._is_valid_product(current_product):
                            products.append(current_product.copy())
                            current_product = {}
                    continue
            
            # If we have a title but no price yet, accumulate description
            if current_product.get('title') and not current_product.get('price'):
                if len(line) > 10 and not re.match(r'^[\d$,\s.]+$', line):
                    if 'description' not in current_product:
                        current_product['description'] = line
                    else:
                        current_product['description'] += ' ' + line
                    current_product['description'] = current_product['description'][:500]
        
        # Add last product if valid
        if current_product and self._is_valid_product(current_product):
            current_product['page_number'] = page_number
            current_product['source'] = 'PDF Text'
            products.append(current_product)
        
        return products
    
    def detect_from_tables(self, tables: List[List[List[str]]], page_number: int = 1) -> List[Dict]:
        """
        Detect products from tabular data with improved accuracy
        
        Args:
            tables: List of tables (each table is list of rows)
            page_number: Page number where tables were found
            
        Returns:
            List of detected products
        """
        products = []
        
        for table in tables:
            if not table or len(table) < 2:  # Need at least header + one row
                continue
            
            # Try to identify header row (first non-empty row with text)
            header_row = None
            header_row_idx = 0
            for idx, row in enumerate(table):
                if row and any(cell and str(cell).strip() for cell in row):
                    header_row = [str(cell).strip() if cell else '' for cell in row]
                    header_row_idx = idx
                    break
            
            if not header_row:
                continue
            
            header_indices = self._identify_columns(header_row)
            
            # Process data rows (skip header row)
            for row_idx, row in enumerate(table[header_row_idx + 1:], start=header_row_idx + 1):
                if not row or len(row) < len(header_row):
                    continue
                
                # Convert row to strings and clean
                row_data = [str(cell).strip() if cell else '' for cell in row]
                
                # Skip empty rows
                if not any(cell for cell in row_data):
                    continue
                
                product = {}
                
                # Extract based on identified columns
                if 'title' in header_indices:
                    idx = header_indices['title']
                    if idx < len(row_data) and row_data[idx]:
                        product['title'] = row_data[idx][:200]
                
                if 'price' in header_indices:
                    idx = header_indices['price']
                    if idx < len(row_data) and row_data[idx]:
                        price = row_data[idx]
                        product['price'] = self._normalize_price(price)
                
                if 'description' in header_indices:
                    idx = header_indices['description']
                    if idx < len(row_data) and row_data[idx]:
                        product['description'] = row_data[idx][:500]
                
                # If no description column, combine other columns
                if not product.get('description') and len(row_data) > 1:
                    desc_parts = []
                    for col_idx, cell in enumerate(row_data):
                        if col_idx != header_indices.get('title', -1) and col_idx != header_indices.get('price', -1):
                            if cell and len(cell) > 5:
                                desc_parts.append(cell)
                    if desc_parts:
                        product['description'] = ' '.join(desc_parts[:3])[:500]
                
                # If we have at least a title or price, it's a potential product
                if product.get('title') or product.get('price'):
                    product['page_number'] = page_number
                    product['source'] = 'PDF Table'
                    products.append(product)
        
        return products
    
    def detect_from_images(self, image_data: List[Dict], page_number: int = 1) -> List[Dict]:
        """
        Detect products from images using OCR
        
        Args:
            image_data: List of image data dictionaries
            page_number: Page number where images were found
            
        Returns:
            List of detected products
        """
        products = []
        
        if not OCR_AVAILABLE:
            logger.warning("OCR not available. Skipping image-based detection.")
            return products
        
        for img_dict in image_data:
            try:
                # Decode base64 image
                img_bytes = base64.b64decode(img_dict.get('data', ''))
                img = Image.open(io.BytesIO(img_bytes))
                
                # Perform OCR with better config
                ocr_text = pytesseract.image_to_string(img, config='--psm 6')
                
                # Detect products from OCR text
                detected = self.detect_from_text(ocr_text, page_number)
                for product in detected:
                    # Add image reference
                    product['images'] = [f"data:image/png;base64,{img_dict.get('data', '')}"]
                    product['source'] = 'PDF Image (OCR)'
                    products.append(product)
                    
            except Exception as e:
                logger.error(f"Error processing image with OCR: {e}")
        
        return products
    
    def combine_results(self, results: List[List[Dict]]) -> List[Dict]:
        """
        Combine results from multiple detection methods with smart deduplication
        
        Args:
            results: List of product lists from different methods
            
        Returns:
            Merged and deduplicated list of products
        """
        all_products = []
        seen_products = set()
        
        for product_list in results:
            for product in product_list:
                # Create a unique key for deduplication
                key = self._create_product_key(product)
                if key not in seen_products:
                    seen_products.add(key)
                    all_products.append(product)
                else:
                    # If duplicate found, merge information (keep more complete version)
                    for existing in all_products:
                        existing_key = self._create_product_key(existing)
                        if existing_key == key:
                            # Merge missing fields
                            if not existing.get('description') and product.get('description'):
                                existing['description'] = product['description']
                            if not existing.get('price') and product.get('price'):
                                existing['price'] = product['price']
                            if not existing.get('images') and product.get('images'):
                                existing['images'] = product['images']
                            break
        
        return all_products
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract product title from text line with improved logic"""
        # Try product indicators first
        for pattern in self.product_indicators:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                title = match.group(1).strip()
                # Clean up title
                title = re.sub(r'\s+', ' ', title)
                if 3 <= len(title) <= 200:
                    return title
        
        # If line looks like a product name
        text_clean = text.strip()
        if 5 <= len(text_clean) <= 200:
            # Check if it doesn't look like a price, number, or description
            if not re.match(r'^[\d$,\s.]+$', text_clean):  # Not just numbers/currency
                if not text_clean.lower().startswith(('price', 'cost', 'amount', 'total', 'description')):
                    # Remove common prefixes
                    text_clean = re.sub(r'^(Product|Item|Name|Model|SKU)[:\s]+', '', text_clean, flags=re.IGNORECASE)
                    return text_clean.strip()
        
        return None
    
    def _extract_price(self, text: str) -> Optional[str]:
        """Extract price from text with improved accuracy"""
        # Try patterns in order of specificity
        for pattern in self.price_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Return first match, cleaned up
                price = str(matches[0]).strip()
                # Validate it's actually a price (has digits)
                if re.search(r'\d', price):
                    return price
        
        return None
    
    def _normalize_price(self, price: str) -> str:
        """Normalize price string"""
        price = price.strip()
        # Remove extra whitespace but keep currency symbols
        price = re.sub(r'\s+', ' ', price)
        return price
    
    def _is_valid_product(self, product: Dict) -> bool:
        """Check if product has minimum required fields with better validation"""
        has_title = bool(product.get('title') and len(product.get('title', '').strip()) > 2)
        has_price = bool(product.get('price') and len(product.get('price', '').strip()) > 0)
        
        # Must have at least title OR price, and title shouldn't be just numbers
        if has_title or has_price:
            title = product.get('title', '')
            # Reject if title is just numbers/currency
            if title and re.match(r'^[\d$,\s.]+$', title):
                return False
            return True
        
        return False
    
    def _identify_columns(self, header_row: List[str]) -> Dict[str, int]:
        """Identify column indices for product fields with improved matching"""
        indices = {}
        header_lower = [str(h).lower().strip() for h in header_row]
        
        # Look for common column names with better matching
        for idx, header in enumerate(header_lower):
            header_clean = header.replace('_', ' ').replace('-', ' ')
            
            # Title/Name columns
            if any(keyword in header_clean for keyword in ['name', 'product', 'item', 'title', 'description', 'model', 'part', 'sku']):
                if 'title' not in indices:
                    indices['title'] = idx
            
            # Price columns
            elif any(keyword in header_clean for keyword in ['price', 'cost', 'amount', 'usd', 'eur', 'gbp', 'value', 'total']):
                if 'price' not in indices:
                    indices['price'] = idx
            
            # Description columns
            elif any(keyword in header_clean for keyword in ['description', 'desc', 'details', 'spec', 'specification', 'note', 'remark']):
                if 'description' not in indices:
                    indices['description'] = idx
        
        return indices
    
    def _detect_unstructured_products(self, text: str, page_number: int) -> List[Dict]:
        """Detect products from unstructured text with improved heuristics"""
        products = []
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 20]
        
        for para in paragraphs:
            # Look for paragraphs that contain both text and numbers (potential products)
            has_text = bool(re.search(r'[a-zA-Z]{3,}', para))
            has_numbers = bool(re.search(r'\d+', para))
            
            if has_text and has_numbers:
                # Try to extract title and price
                lines = [l.strip() for l in para.split('\n') if l.strip()]
                product = {}
                
                # Check first few lines for title
                for line in lines[:3]:
                    if not product.get('title'):
                        title = self._extract_title(line)
                        if title:
                            product['title'] = title
                    
                    if not product.get('price'):
                        price = self._extract_price(line)
                        if price:
                            product['price'] = price
                
                # If we found something, use rest as description
                if self._is_valid_product(product):
                    desc_lines = lines[3:6] if len(lines) > 3 else lines[1:4]
                    desc_lines = [l for l in desc_lines if l and not re.match(r'^[\d$,\s.]+$', l)]
                    if desc_lines:
                        product['description'] = ' '.join(desc_lines)[:500]
                    product['page_number'] = page_number
                    product['source'] = 'PDF Text (Unstructured)'
                    products.append(product)
        
        return products
    
    def _create_product_key(self, product: Dict) -> str:
        """Create unique key for product deduplication"""
        title = product.get('title', '').lower().strip()[:50]
        price = product.get('price', '').strip()[:20]
        # Normalize for comparison
        title = re.sub(r'\s+', ' ', title)
        return f"{title}|{price}"
