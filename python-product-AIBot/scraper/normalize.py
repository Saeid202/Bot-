"""Normalize product data to standardized format"""
from typing import Dict, Any, Optional, List


def normalize_product(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize raw product data to standardized format
    
    Args:
        raw: Raw product dictionary from scraper
        
    Returns:
        Normalized product dictionary with all standard fields
    """
    normalized = {
        "title": raw.get("title", "").strip(),
        "price": raw.get("price", "").strip(),
        "source": raw.get("source", "Unknown"),
        "description": raw.get("description", "").strip(),
        "images": _normalize_images(raw.get("images", [])),
        "rating": _normalize_rating(raw.get("rating")),
        "review_count": _normalize_review_count(raw.get("review_count")),
        "availability": raw.get("availability", "").strip(),
        "url": raw.get("url", "").strip(),
        "currency": raw.get("currency", "").strip()
    }
    
    return normalized


def _normalize_images(images: Any) -> List[str]:
    """Normalize images to list of URLs or base64 data URIs"""
    if not images:
        return []
    
    if isinstance(images, str):
        # Accept HTTP URLs or base64 data URIs
        if images.startswith('http') or images.startswith('data:image'):
            return [images]
        return []
    
    if isinstance(images, list):
        normalized = []
        for img in images:
            if isinstance(img, str):
                # Accept HTTP URLs or base64 data URIs
                if img.startswith('http') or img.startswith('data:image'):
                    normalized.append(img)
                # If it's base64 without data URI prefix, add prefix
                elif len(img) > 100:  # Likely base64
                    normalized.append(f"data:image/png;base64,{img}")
            elif isinstance(img, dict):
                # Handle image dict with 'data' field
                if 'data' in img:
                    img_data = img['data']
                    if isinstance(img_data, str):
                        if img_data.startswith('data:image'):
                            normalized.append(img_data)
                        else:
                            normalized.append(f"data:image/png;base64,{img_data}")
        return normalized
    
    return []


def _normalize_rating(rating: Any) -> Optional[float]:
    """Normalize rating to float (0-5 scale)"""
    if rating is None:
        return None
    
    try:
        rating_float = float(rating)
        # Ensure rating is between 0 and 5
        return max(0.0, min(5.0, rating_float))
    except (ValueError, TypeError):
        return None


def _normalize_review_count(count: Any) -> Optional[int]:
    """Normalize review count to integer"""
    if count is None:
        return None
    
    try:
        return int(count)
    except (ValueError, TypeError):
        return None


def prepare_for_database(normalized_product: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare normalized product for database insertion
    
    Args:
        normalized_product: Normalized product dictionary
        
    Returns:
        Dictionary ready for Supabase insertion
    """
    db_product = {
        "name": normalized_product.get("title", ""),
        "price": normalized_product.get("price", ""),
        "source": normalized_product.get("source", "Unknown"),
        "description": normalized_product.get("description") or None,
        "images": normalized_product.get("images") or [],
        "rating": normalized_product.get("rating"),
        "review_count": normalized_product.get("review_count"),
        "availability": normalized_product.get("availability") or None,
        "product_url": normalized_product.get("url") or None,
        "currency": normalized_product.get("currency") or None
    }
    
    # Remove None values to avoid database issues
    return {k: v for k, v in db_product.items() if v is not None}