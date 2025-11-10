"""
Web scraper utility for fetching and cleaning HTML content from URLs.
"""

import requests
from bs4 import BeautifulSoup
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_html_cleaned(url: str) -> Optional[str]:
    """
    Fetch HTML content from a URL and return cleaned text.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        Optional[str]: Cleaned HTML content as text, or None if failed
        
    Raises:
        requests.RequestException: If there's an error fetching the URL
        ValueError: If the URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        logger.info(f"Fetching content from: {url}")
        
        # Set headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Make the request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get both HTML and text content
        html_content = str(soup)
        text_content = soup.get_text()
        
        # Clean up whitespace for text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = ' '.join(chunk for chunk in chunks if chunk)
        
        logger.info(f"Successfully scraped {len(cleaned_text)} characters from {url}")
        return cleaned_text
        
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping {url}: {str(e)}")
        return None


def fetch_html_raw(url: str) -> Optional[str]:
    """
    Fetch raw HTML content from a URL without cleaning.
    
    Args:
        url (str): The URL to scrape
        
    Returns:
        Optional[str]: Raw HTML content, or None if failed
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")
    
    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        logger.info(f"Fetching raw HTML from: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        logger.info(f"Successfully fetched {len(response.text)} characters from {url}")
        return response.text
        
    except requests.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {str(e)}")
        return None
