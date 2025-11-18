"""Run the bot with custom parameters"""
import sys
from pathlib import Path

# Add the project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python-product-AIBot"))

from scraper.connector.run_aibot import run_bot

if __name__ == "__main__":
    # You can customize these parameters:
    query = "power bank"  # Change this to search for different products
    max_results = 5       # Change this to get more/fewer products
    
    print(f"Running bot with query: '{query}', max_results: {max_results}")
    print("=" * 50)
    
    run_bot(query=query, max_results=max_results)

