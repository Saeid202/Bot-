"""Test Supabase connection"""
import requests

SUPABASE_URL = "https://pbkbefdxgskypehrrgvq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBia2JlZmR4Z3NreXBlaHJyZ3ZxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM0MjE5NzcsImV4cCI6MjA3ODk5Nzk3N30.r8bq63S5SjYdennWWjN9rWyH_ga15gvwhcZH-yByhW0"

def test_supabase_connection():
    print("=" * 50)
    print("Testing Supabase Connection")
    print("=" * 50)
    
    url = f"{SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Test 1: Try to read from the table
    print("\n1. Testing READ access...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Successfully connected! Found {len(data)} existing products.")
            if data:
                print(f"   Sample product: {data[0]}")
        elif response.status_code == 404:
            print("   ❌ 404 Error: Table 'products' not found or not accessible")
        elif response.status_code == 401:
            print("   ❌ 401 Error: Authentication failed - check your API key")
        else:
            print(f"   ⚠ Unexpected status: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Try to insert a test product
    print("\n2. Testing INSERT access...")
    test_product = {
        "name": "Test Product",
        "price": "$9.99",
        "source": "Test"
    }
    
    try:
        response = requests.post(url, json=test_product, headers=headers, timeout=10)
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 201:
            data = response.json()
            print(f"   ✓ Successfully inserted test product!")
            print(f"   Inserted: {data}")
            
            # Try to delete the test product
            if isinstance(data, list) and len(data) > 0 and 'id' in data[0]:
                delete_url = f"{url}?id=eq.{data[0]['id']}"
                delete_response = requests.delete(delete_url, headers=headers, timeout=10)
                if delete_response.status_code == 204:
                    print(f"   ✓ Test product deleted successfully")
        elif response.status_code == 400:
            print(f"   ❌ 400 Error: Bad request - {response.text[:200]}")
            print("   This might mean the table schema doesn't match")
        elif response.status_code == 406:
            print("   ❌ 406 Error: Row Level Security (RLS) might be blocking inserts")
        else:
            print(f"   ⚠ Status {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("Supabase test complete!")
    print("=" * 50)

if __name__ == "__main__":
    test_supabase_connection()

