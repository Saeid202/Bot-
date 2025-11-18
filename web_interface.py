"""Web interface for the product scraper bot"""
import streamlit as st
import sys
from pathlib import Path
import nest_asyncio

# Allow nested event loops (needed for Playwright + Streamlit)
nest_asyncio.apply()

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

import requests

# Supabase config
SUPABASE_URL = "https://pbkbefdxgskypehrrgvq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBia2JlZmR4Z3NreXBlaHJyZ3ZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MjE5NzcsImV4cCI6MjA3ODk5Nzk3N30.r8bq63S5SjYdennWWjN9rWyH_ga15gvwhcZH-yByhW0"

def insert_products_supabase(products):
    """Insert products into Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    resp = requests.post(url, json=products, headers=headers)
    resp.raise_for_status()
    return resp.json()

# Page configuration
st.set_page_config(
    page_title="Product Scraper Bot",
    page_icon="🛒",
    layout="wide"
)

# Navigation - MUST be at the very top of sidebar
with st.sidebar:
    st.title("🔀 Navigation")
    st.markdown("**Select Mode:**")
    page_mode = st.radio(
        "Choose an option:",
        ["Scrape from URL", "Upload PDF"],
        label_visibility="collapsed",
        key="page_mode_selector"
    )
    st.markdown("---")

# Title and description
if page_mode == "Upload PDF":
    st.title("📄 PDF Product Extraction")
    st.markdown("""
    Upload a PDF file (catalog, invoice, spec sheet) to extract products automatically.
    Extracted products will be saved for review and approval.
    """)
else:
    st.title("🛒 Multi-Site Product Scraper Bot")
    st.markdown("""
    Enter any e-commerce product listing URL below, and the bot will automatically detect the site and scrape products.
    Supports Amazon, eBay, Alibaba, AliExpress, and more!
    """)

# Import site detector
from scraper.site_detector import detect_site_from_url, get_all_supported_sites

# PDF Upload Mode
if page_mode == "Upload PDF":
    st.header("📤 Upload PDF File")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload a PDF catalog, invoice, or product specification sheet"
    )
    
    if uploaded_file is not None:
        use_ocr = st.checkbox("Use OCR for scanned PDFs", value=True, help="Enable this for scanned PDFs or PDFs with images")
        
        if st.button("🚀 Extract Products from PDF", type="primary", use_container_width=True):
            with st.spinner("Processing PDF and extracting products... This may take a minute..."):
                try:
                    from scraper.pdf_service import PDFService
                    from scraper.normalize import normalize_product, prepare_for_database
                    from datetime import datetime
                    
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
                        
                        # Display extracted products in a table
                        st.subheader("📦 Extracted Products")
                        
                        # Create a comprehensive table
                        import pandas as pd
                        
                        # Prepare table data
                        table_data = []
                        for idx, product in enumerate(normalized, 1):
                            table_data.append({
                                "#": idx,
                                "Title": product.get('title', 'N/A')[:80] + "..." if len(product.get('title', '')) > 80 else product.get('title', 'N/A'),
                                "Price": product.get('price', 'N/A'),
                                "Description": (product.get('description', '')[:100] + "...") if len(product.get('description', '')) > 100 else product.get('description', 'N/A'),
                                "Page": product.get('page_number', 'N/A'),
                                "Source": product.get('source', 'PDF'),
                                "Has Image": "✅" if product.get('images') else "❌"
                            })
                        
                        df = pd.DataFrame(table_data)
                        
                        # Display table with better formatting
                        st.dataframe(
                            df,
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "#": st.column_config.NumberColumn("", width="small"),
                                "Title": st.column_config.TextColumn("Product Title", width="large"),
                                "Price": st.column_config.TextColumn("Price", width="medium"),
                                "Description": st.column_config.TextColumn("Description", width="large"),
                                "Page": st.column_config.NumberColumn("Page", width="small"),
                                "Source": st.column_config.TextColumn("Source", width="small"),
                                "Has Image": st.column_config.TextColumn("Image", width="small")
                            }
                        )
                        
                        # Detailed view with expandable sections (optional, below table)
                        st.subheader("📋 Detailed View")
                        for idx, product in enumerate(normalized, 1):
                            with st.expander(f"🔹 {product['title'][:60]}...", expanded=False):
                                col1, col2 = st.columns([2, 1])
                                
                                with col1:
                                    st.write(f"**Title:** {product['title']}")
                                    if product.get('price'):
                                        st.write(f"**Price:** {product['price']}")
                                    if product.get('description'):
                                        st.write(f"**Description:** {product['description']}")
                                    st.caption(f"**Source:** {product.get('source', 'PDF')} | **Page:** {product.get('page_number', 'N/A')}")
                                
                                with col2:
                                    if product.get('images'):
                                        try:
                                            img = product['images'][0]
                                            if img.startswith('data:image'):
                                                st.image(img, width=200)
                                        except:
                                            pass
                        
                        # Insert into database
                        try:
                            inserted = insert_products_supabase(db_products)
                            st.success(f"✅ {len(inserted)} products saved with status 'pending' for review!")
                            st.info("💡 Go to Admin Review interface to review and approve these products.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"❌ Failed to save products: {e}")
                            st.warning("Products were extracted but not saved. Please try again.")
                    else:
                        st.warning("⚠️ No products found in PDF. Try enabling OCR or check the PDF format.")
                        if results['errors']:
                            with st.expander("Error Details"):
                                for error in results['errors']:
                                    st.error(error)
                
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {e}")
                    st.exception(e)
    
    # Link to admin review
    st.markdown("---")
    st.info("💡 **Want to review and approve extracted products?** Run: `streamlit run admin_review_interface.py`")
    
    st.stop()

# URL Scraping Mode (original functionality)
# Input section
st.header("📋 Enter Product Page URL")
url_input = st.text_input(
    "E-commerce URL",
    placeholder="https://www.amazon.com/s?k=laptop or https://www.ebay.com/sch/i.html?_nkw=phone",
    help="Paste any e-commerce product listing page URL here"
)

# Auto-detect site
detected_site = None
if url_input:
    detected_site = detect_site_from_url(url_input)

# Site selection
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    max_results = st.number_input("Max Products", min_value=1, max_value=100, value=10, step=1)
with col2:
    supported_sites = ["Auto-detect"] + get_all_supported_sites() + ["Generic"]
    selected_site = st.selectbox(
        "Website",
        supported_sites,
        index=0 if not detected_site else (supported_sites.index(detected_site) if detected_site in supported_sites else 0),
        help="Select website type or use auto-detect"
    )
with col3:
    save_to_db = st.checkbox("Save to DB", value=True)

# Show detected site
if detected_site and selected_site == "Auto-detect":
    st.info(f"🔍 Detected site: **{detected_site}**")
elif selected_site != "Auto-detect":
    st.info(f"🌐 Using: **{selected_site}**")

# Scrape button
if st.button("🚀 Scrape Products", type="primary", use_container_width=True):
    if not url_input:
        st.error("❌ Please enter a URL")
    else:
        # Determine site name
        site_name = None if selected_site == "Auto-detect" else selected_site
        
        with st.spinner("🔄 Scraping products... This may take a moment..."):
            try:
                # Use threading wrapper to avoid event loop conflicts
                from scraper_wrapper import scrape_in_thread
                
                # Run scraper in separate thread with its own event loop
                raw_products, error = scrape_in_thread(url_input, max_results, site_name=site_name)
                
                if error:
                    st.error(f"❌ Error: {error}")
                    if "Timeout" in error:
                        st.info("💡 Try reducing the max_results value or try again later.")
                    st.stop()
                
                if raw_products is None:
                    raw_products = []
                
                if raw_products:
                    st.success(f"✅ Successfully scraped {len(raw_products)} products!")
                    
                    # Display products
                    st.header("📦 Scraped Products")
                    
                    # Normalize products
                    from scraper.normalize import normalize_product, prepare_for_database
                    normalized = [normalize_product(p) for p in raw_products]
                    
                    # Prepare for database
                    supabase_products = [prepare_for_database(p) for p in normalized]
                    
                    # Display products with extended information
                    for idx, product in enumerate(normalized, 1):
                        with st.expander(f"🔹 {product['title'][:60]}...", expanded=(idx == 1)):
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.subheader(product['title'])
                                if product.get('description'):
                                    st.write(product['description'][:200] + "..." if len(product.get('description', '')) > 200 else product['description'])
                                
                                col_price, col_rating = st.columns(2)
                                with col_price:
                                    if product.get('price'):
                                        st.metric("Price", product['price'])
                                with col_rating:
                                    if product.get('rating'):
                                        st.metric("Rating", f"{product['rating']:.1f} ⭐")
                                        if product.get('review_count'):
                                            st.caption(f"({product['review_count']} reviews)")
                                
                                if product.get('availability'):
                                    st.info(f"📦 {product['availability']}")
                                
                                if product.get('url'):
                                    st.link_button("View Product", product['url'])
                            
                            with col2:
                                if product.get('images'):
                                    try:
                                        st.image(product['images'][0], width=200)
                                    except:
                                        st.write("Image unavailable")
                                st.caption(f"Source: {product.get('source', 'Unknown')}")
                                if product.get('currency'):
                                    st.caption(f"Currency: {product['currency']}")
                    
                    # Show summary table
                    st.subheader("📊 Summary Table")
                    import pandas as pd
                    df = pd.DataFrame([
                        {
                            "Title": p["title"][:50] + "..." if len(p["title"]) > 50 else p["title"],
                            "Price": p.get("price", "N/A"),
                            "Rating": f"{p.get('rating', 0):.1f}" if p.get('rating') else "N/A",
                            "Reviews": p.get('review_count', 'N/A'),
                            "Source": p.get("source", "Unknown")
                        }
                        for p in normalized
                    ])
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Save to database if requested
                    if save_to_db:
                        with st.spinner("💾 Saving to database..."):
                            try:
                                inserted = insert_products_supabase(supabase_products)
                                st.success(f"✅ Successfully saved {len(inserted)} products to Supabase!")
                                st.balloons()
                            except Exception as e:
                                st.error(f"❌ Failed to save to database: {str(e)}")
                                st.info("Products were scraped successfully but not saved to database.")
                                st.exception(e)
                    
                    # Download as CSV option
                    csv_df = pd.DataFrame([
                        {
                            "Title": p["title"],
                            "Price": p.get("price", ""),
                            "Description": p.get("description", "")[:200],
                            "Rating": p.get("rating", ""),
                            "Review Count": p.get("review_count", ""),
                            "Availability": p.get("availability", ""),
                            "Source": p.get("source", ""),
                            "URL": p.get("url", "")
                        }
                        for p in normalized
                    ])
                    csv = csv_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download as CSV",
                        data=csv,
                        file_name="scraped_products.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("⚠️ No products found on this page.")
                    st.markdown("""
                    **Possible reasons:**
                    - 🔒 **CAPTCHA/Blocking**: The website detected automated access
                    - 🏗️ **Page Structure**: The page structure doesn't match expected patterns
                    - 🔗 **Invalid URL**: The URL might not be a product listing page
                    - 🔐 **Login Required**: The page might require authentication
                    - ⏱️ **Loading Time**: Content might be loading too slowly
                    
                    **Try:**
                    - Use a different URL from the same site
                    - Try a product listing/search results page instead of homepage
                    - Check if the site requires login
                    - Wait a moment and try again
                    """)
                    
                    # Show diagnostic info
                    with st.expander("🔍 Diagnostic Information"):
                        st.write("**URL tested:**", url_input)
                        detected = detect_site_from_url(url_input) if url_input else None
                        st.write("**Detected site:**", detected or "Unknown")
                        st.write("**Selected scraper:**", selected_site)
                        st.info("💡 Tip: Try using a search results page URL (e.g., Amazon search, eBay search) rather than a homepage.")
                    
            except Exception as e:
                st.error(f"❌ Error occurred: {str(e)}")
                st.exception(e)

# Sidebar with instructions (only show for URL scraping mode)
if page_mode == "Scrape from URL":
    with st.sidebar:
        st.header("📖 Instructions")
        st.markdown("""
        1. **Copy a URL** from an Alibaba product listing page
        2. **Paste it** in the input field above
        3. **Set max products** (how many to scrape)
        4. **Click "Scrape Products"**
        5. **Review** the scraped products
        6. **Save to database** (if enabled)
        """)
        
        st.header("🔗 Example URLs")
        st.markdown("""
        **Amazon:**
        - `https://www.amazon.com/s?k=laptop`
        
        **eBay:**
        - `https://www.ebay.com/sch/i.html?_nkw=phone`
        
        **Alibaba:**
        - `https://www.alibaba.com/trade/search?SearchText=power+bank`
        
        **AliExpress:**
        - `https://www.aliexpress.com/wholesale?SearchText=watch`
        
        Any e-commerce product listing page!
        """)
        
        st.header("⚙️ Settings")
        st.info("""
        **Database:** Supabase
        **Max Products:** Adjustable
        **Auto-save:** Toggleable
        **Multi-site:** Auto-detection enabled
        """)
        
        st.header("✅ Supported Sites")
        supported = get_all_supported_sites()
        for site in supported:
            st.write(f"• {site}")
        st.write("• Generic (fallback for unknown sites)")
        
        st.header("⚠️ Notes")
        st.warning("""
        - CAPTCHA may block scraping
        - Some pages may require login
        - Scraping speed depends on page load time
        """)

# Footer
st.markdown("---")
st.markdown("**Product Scraper Bot** | Built with Streamlit & Playwright")

