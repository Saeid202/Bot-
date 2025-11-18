# PDF Product Extraction Feature

## Overview

The PDF product extraction feature allows admins to upload PDF files (catalogs, invoices, spec sheets) and automatically extract product information. Extracted products are saved with `status='pending'` and can be reviewed, edited, and approved before being added to the main products database.

## Features

- **Multi-format PDF support**: Text-based, scanned, and mixed format PDFs
- **Multiple extraction methods**:
  - Structured text extraction
  - Table extraction
  - OCR for scanned PDFs
  - Pattern matching for product names and prices
- **Admin review interface**: Review, edit, and approve/reject extracted products
- **Edit before approval**: Modify extracted data before approving
- **Bulk actions**: Approve or reject multiple products at once

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements-pdf.txt
```

### 2. Install Tesseract OCR (for OCR features)

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**Mac:**
```bash
brew install tesseract
```

### 3. Run Database Migration

Execute `supabase_migration_pdf_review.sql` in your Supabase SQL Editor to add:
- `status` column (pending/approved/rejected)
- `pdf_source` column
- `extracted_at` timestamp
- `approved_by`, `approved_at` fields
- `rejection_reason` field

## Usage

### Running the Admin Review Interface

```bash
streamlit run admin_review_interface.py
```

### Workflow

1. **Upload PDF**: Go to "PDF Upload" tab and upload a PDF file
2. **Extract Products**: Click "Extract Products" to process the PDF
3. **Review Products**: Go to "Review Products" tab to see extracted products
4. **Edit Products**: Click on a product to edit title, price, description
5. **Approve/Reject**: 
   - Click "Approve" to add product to database
   - Click "Reject" to mark as rejected (with optional reason)
   - Use bulk actions to approve/reject multiple products

## File Structure

- `python-product-AIBot/scraper/pdf_parser.py` - PDF text and table extraction
- `python-product-AIBot/scraper/image_handler.py` - Image extraction from PDFs
- `python-product-AIBot/scraper/product_detector.py` - Product detection logic
- `python-product-AIBot/scraper/pdf_service.py` - Main PDF processing service
- `admin_review_interface.py` - Streamlit admin interface
- `supabase_migration_pdf_review.sql` - Database migration

## Product Detection

The system uses multiple strategies to detect products:

1. **Text-based detection**: Looks for product names, prices, descriptions in text
2. **Table extraction**: Extracts products from tabular data
3. **OCR detection**: Uses OCR to extract text from scanned PDFs
4. **Pattern matching**: Regex patterns for common product formats

## Database Schema

Products extracted from PDFs have these additional fields:
- `status`: 'pending', 'approved', or 'rejected'
- `pdf_source`: Original PDF filename
- `extracted_at`: Timestamp when extracted
- `approved_by`: Admin who approved (optional)
- `approved_at`: Approval timestamp (optional)
- `rejection_reason`: Reason for rejection (optional)

## Troubleshooting

### OCR not working
- Ensure Tesseract OCR is installed and in PATH
- Check that `pytesseract` can find Tesseract: `pytesseract.get_tesseract_version()`

### No products extracted
- Try enabling OCR for scanned PDFs
- Check PDF format (some PDFs may need different extraction methods)
- Review error messages in the extraction summary

### Images not displaying
- Base64 images are stored in the database
- Large images may cause performance issues
- Consider using Supabase Storage for large images

## Future Enhancements

- AI/LLM-based product detection
- Automatic product categorization
- Image upload to Supabase Storage
- Export approved products to CSV
- Product deduplication
- Confidence scores for extracted data

