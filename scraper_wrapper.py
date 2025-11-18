"""Wrapper to run scraper in a way compatible with Streamlit"""
import subprocess
import json
import sys
import os
from pathlib import Path

# Get the project root
ROOT = Path(__file__).resolve().parent

def scrape_in_thread(url, max_results, site_name=None):
    """Run scraper in a separate subprocess to avoid event loop conflicts"""
    try:
        # Run scraper in a completely separate process
        # This avoids all event loop conflicts
        script_path = ROOT / "run_scraper_standalone.py"
        python_exe = sys.executable
        
        # Set environment variables for Windows event loop
        env = os.environ.copy()
        if sys.platform == 'win32':
            # Force ProactorEventLoop for subprocess support
            env['PYTHONASYNCIODEBUG'] = '1'
        
        # Build command with optional site_name
        cmd = [python_exe, str(script_path), url, str(max_results)]
        if site_name:
            cmd.append(site_name)
        
        # Run the standalone scraper script
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 minute timeout
            cwd=str(ROOT),
            env=env
        )
        
        if result.returncode != 0:
            return None, f"Scraper process failed: {result.stderr}"
        
        # Parse JSON output
        try:
            output = json.loads(result.stdout)
            if output.get("success"):
                return output.get("products", []), None
            else:
                return None, output.get("error", "Unknown error occurred")
        except json.JSONDecodeError:
            return None, f"Failed to parse scraper output: {result.stdout}"
            
    except subprocess.TimeoutExpired:
        return None, "Timeout: Scraping took too long (over 2 minutes)"
    except Exception as e:
        return None, f"Error running scraper: {str(e)}"

