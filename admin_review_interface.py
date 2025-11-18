"""Admin review interface for PDF-extracted products"""
import streamlit as st
import sys
from pathlib import Path
import requests
from typing import List, Dict, Optional
from datetime import datetime

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

# Supabase config
SUPABASE_URL = "https://pbkbefdxgskypehrrgvq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBia2JlZmR4Z3NreXBlaHJyZ3ZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MjE5NzcsImV4cCI6MjA3ODk5Nzk3N30.r8bq63S5SjYdennWWjN9rWyH_ga15gvwhcZH-yByhW0"

# Page configuration
st.set_page_config(
    page_title="Admin Review - Product Scraper",
    page_icon="📋",
    layout="wide"
)

# Initialize session state
if 'pending_products' not in st.session_state:
    st.session_state.pending_products = []
if 'edited_products' not in st.session_state:
    st.session_state.edited_products = {}

# Database functions
def insert_pending_products(products: List[Dict]) -> Dict:
    """Insert products with status='pending' into Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Prepare products for database
    db_products = []
    for product in products:
        db_product = {
            "name": product.get("title", "Unknown Product"),
            "price": product.get("price", ""),
            "source": product.get("source", "PDF"),
            "description": product.get("description") or None,
            "images": product.get("images", []),
            "product_url": product.get("url") or None,
            "currency": product.get("currency") or None,
            "status": "pending",
            "pdf_source": product.get("pdf_source"),
            "extracted_at": product.get("extracted_at")
        }
        # Remove None values
        db_product = {k: v for k, v in db_product.items() if v is not None}
        db_products.append(db_product)
    
    resp = requests.post(url, json=db_products, headers=headers)
    resp.raise_for_status()
    return resp.json()

def update_product(product_id: int, updates: Dict) -> Dict:
    """Update product in Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/products?id=eq.{product_id}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    resp = requests.patch(url, json=updates, headers=headers)
    resp.raise_for_status()
    return resp.json()

def approve_product(product_id: int, approved_by: str = "Admin") -> Dict:
    """Approve a product"""
    updates = {
        "status": "approved",
        "approved_by": approved_by,
        "approved_at": datetime.now().isoformat()
    }
    return update_product(product_id, updates)

def reject_product(product_id: int, reason: Optional[str] = None, rejected_by: str = "Admin") -> Dict:
    """Reject a product"""
    updates = {
        "status": "rejected",
        "rejection_reason": reason,
        "approved_by": rejected_by,
        "approved_at": datetime.now().isoformat()
    }
    return update_product(product_id, updates)

def get_pending_products() -> List[Dict]:
    """Fetch pending products from Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/products?status=eq.pending&order=extracted_at.desc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

def get_products_by_status(status: str) -> List[Dict]:
    """Fetch products by status"""
    url = f"{SUPABASE_URL}/rest/v1/products?status=eq.{status}&order=extracted_at.desc"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.json()

# Title
st.title("📋 Admin Review - PDF Product Extraction")
st.markdown("Upload PDF files to extract products, review extracted data, and approve products for the database.")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to:", ["PDF Upload", "Review Products"])
    
    st.header("Filters")
    status_filter = st.selectbox("Filter by Status", ["All", "Pending", "Approved", "Rejected"])
    
    st.header("Statistics")
    try:
        pending_count = len(get_pending_products())
        st.metric("Pending", pending_count)
    except:
        st.metric("Pending", "N/A")

# Main content
if page == "PDF Upload":
    st.header("📤 Upload PDF")
    st.markdown("Upload a PDF file (catalog, invoice, spec sheet) to extract products.")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
    
    if uploaded_file is not None:
        use_ocr = st.checkbox("Use OCR for scanned PDFs", value=True)
        
        if st.button("🚀 Extract Products", type="primary"):
            with st.spinner("Processing PDF and extracting products..."):
                try:
                    from scraper.pdf_service import PDFService
                    from scraper.normalize import normalize_product, prepare_for_database
                    
                    service = PDFService()
                    results = service.process_uploaded_pdf(uploaded_file, use_ocr=use_ocr)
                    
                    if results['products']:
                        st.success(f"✅ Extracted {len(results['products'])} products from PDF!")
                        
                        # Show summary
                        st.subheader("📊 Extraction Summary")
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Products Found", len(results['products']))
                        with col2:
                            st.metric("Pages Processed", results['metadata']['page_count'])
                        with col3:
                            st.metric("Errors", len(results['errors']))
                        
                        if results['errors']:
                            with st.expander("⚠️ Errors Encountered"):
                                for error in results['errors']:
                                    st.warning(error)
                        
                        # Normalize products
                        normalized = [normalize_product(p) for p in results['products']]
                        db_products = [prepare_for_database(p) for p in normalized]
                        
                        # Add PDF metadata
                        for product in db_products:
                            product['pdf_source'] = uploaded_file.name
                            product['extracted_at'] = datetime.now().isoformat()
                            product['status'] = 'pending'
                        
                        # Insert into database
                        try:
                            inserted = insert_pending_products(db_products)
                            st.success(f"✅ {len(inserted)} products saved for review!")
                            st.info("Go to 'Review Products' tab to review and approve them.")
                        except Exception as e:
                            st.error(f"❌ Failed to save products: {e}")
                            # Store in session state as fallback
                            st.session_state.pending_products = db_products
                            st.warning("Products stored in session. Please try saving again.")
                    else:
                        st.warning("⚠️ No products found in PDF. Try enabling OCR or check the PDF format.")
                        if results['errors']:
                            with st.expander("Error Details"):
                                for error in results['errors']:
                                    st.error(error)
                
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {e}")
                    st.exception(e)

elif page == "Review Products":
    st.header("🔍 Review Products")
    
    # Fetch products
    try:
        if status_filter == "All":
            products = get_products_by_status("pending") + get_products_by_status("approved") + get_products_by_status("rejected")
        elif status_filter == "Pending":
            products = get_pending_products()
        else:
            status = status_filter.lower()
            products = get_products_by_status(status)
        
        if not products:
            st.info(f"No {status_filter.lower()} products found.")
        else:
            st.subheader(f"📦 {len(products)} Products ({status_filter})")
            
            # Search
            search_term = st.text_input("🔍 Search products", "")
            if search_term:
                products = [p for p in products if search_term.lower() in str(p.get('name', '')).lower()]
                st.write(f"Found {len(products)} matching products")
            
            # Display products
            for idx, product in enumerate(products):
                with st.expander(f"Product {idx + 1}: {product.get('name', 'Unknown')} - {product.get('status', 'unknown').upper()}", expanded=False):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Editable fields
                        product_id = product.get('id')
                        edited_key = f"product_{product_id}"
                        
                        if edited_key not in st.session_state.edited_products:
                            st.session_state.edited_products[edited_key] = product.copy()
                        
                        edited = st.session_state.edited_products[edited_key]
                        
                        # Title
                        edited['name'] = st.text_input(
                            "Title",
                            value=edited.get('name', ''),
                            key=f"title_{product_id}"
                        )
                        
                        # Price
                        edited['price'] = st.text_input(
                            "Price",
                            value=edited.get('price', ''),
                            key=f"price_{product_id}"
                        )
                        
                        # Description
                        edited['description'] = st.text_area(
                            "Description",
                            value=edited.get('description', ''),
                            key=f"desc_{product_id}",
                            height=100
                        )
                        
                        # Images
                        st.write("**Images:**")
                        images = edited.get('images', [])
                        if images:
                            cols = st.columns(min(len(images), 3))
                            for img_idx, img_url in enumerate(images[:3]):
                                with cols[img_idx]:
                                    try:
                                        if img_url.startswith('data:image') or img_url.startswith('http'):
                                            st.image(img_url, use_container_width=True)
                                        else:
                                            st.write(f"Image {img_idx + 1}: {img_url[:50]}...")
                                    except Exception:
                                        st.write(f"Image {img_idx + 1}: Unable to display")
                        
                        # Metadata
                        st.write("**Metadata:**")
                        col_meta1, col_meta2 = st.columns(2)
                        with col_meta1:
                            st.caption(f"Source: {edited.get('source', 'N/A')}")
                            st.caption(f"PDF: {edited.get('pdf_source', 'N/A')}")
                        with col_meta2:
                            extracted = edited.get('extracted_at', 'N/A')
                            if extracted != 'N/A':
                                try:
                                    dt = datetime.fromisoformat(extracted.replace('Z', '+00:00'))
                                    st.caption(f"Extracted: {dt.strftime('%Y-%m-%d %H:%M')}")
                                except:
                                    st.caption(f"Extracted: {extracted}")
                    
                    with col2:
                        # Status badge
                        status = edited.get('status', 'pending')
                        if status == 'approved':
                            st.success("✅ Approved")
                        elif status == 'rejected':
                            st.error("❌ Rejected")
                        else:
                            st.warning("⏳ Pending")
                        
                        # Actions
                        st.write("**Actions:**")
                        
                        # Save edits
                        if st.button("💾 Save Edits", key=f"save_{product_id}"):
                            try:
                                updates = {
                                    "name": edited['name'],
                                    "price": edited['price'],
                                    "description": edited.get('description'),
                                    "images": edited.get('images', [])
                                }
                                update_product(product_id, updates)
                                st.success("✅ Saved!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                        
                        # Approve
                        if status == 'pending':
                            if st.button("✅ Approve", key=f"approve_{product_id}", type="primary"):
                                try:
                                    approve_product(product_id)
                                    st.success("✅ Approved!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                            
                            # Reject
                            reject_reason = st.text_input(
                                "Rejection reason (optional)",
                                key=f"reject_reason_{product_id}"
                            )
                            if st.button("❌ Reject", key=f"reject_{product_id}"):
                                try:
                                    reject_product(product_id, reject_reason if reject_reason else None)
                                    st.success("❌ Rejected!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        
                        # Change status
                        if status != 'pending':
                            if st.button("↩️ Reset to Pending", key=f"reset_{product_id}"):
                                try:
                                    update_product(product_id, {"status": "pending"})
                                    st.success("↩️ Reset to pending!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
            
            # Bulk actions
            if status_filter == "Pending":
                st.divider()
                st.subheader("Bulk Actions")
                col_bulk1, col_bulk2 = st.columns(2)
                
                with col_bulk1:
                    if st.button("✅ Approve All Pending", type="primary"):
                        try:
                            pending = get_pending_products()
                            for p in pending:
                                approve_product(p['id'])
                            st.success(f"✅ Approved {len(pending)} products!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                
                with col_bulk2:
                    if st.button("❌ Reject All Pending"):
                        try:
                            pending = get_pending_products()
                            for p in pending:
                                reject_product(p['id'], "Bulk rejection")
                            st.success(f"❌ Rejected {len(pending)} products!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    except Exception as e:
        st.error(f"❌ Error loading products: {e}")
        st.exception(e)

