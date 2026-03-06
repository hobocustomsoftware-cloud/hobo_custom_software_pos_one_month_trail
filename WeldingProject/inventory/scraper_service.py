"""
Web Scraper Service for CBM Forex Website
Scrapes USD exchange rate from https://forex.cbm.gov.mm/
Uses BeautifulSoup for HTML parsing with robust error handling (SRE standards).
"""
import logging
import requests
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from django.utils import timezone

logger = logging.getLogger(__name__)


def scrape_cbm_usd_rate():
    """
    Scrape USD exchange rate from CBM forex website.
    
    Returns:
        Decimal: USD rate (MMK per 1 USD) or None if scraping fails
        
    Raises:
        Exception: Logged but not raised (graceful degradation)
    """
    url = 'https://forex.cbm.gov.mm/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        logger.info(f'Scraping USD rate from {url}')
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Strategy 1: Look for USD in tables
        usd_rate = None
        
        # Try to find USD rate in common table structures
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    # Check if first cell contains "USD" or "US Dollar"
                    first_cell_text = cells[0].get_text(strip=True).upper()
                    if 'USD' in first_cell_text or 'US DOLLAR' in first_cell_text or 'US$' in first_cell_text:
                        # Second cell should contain the rate
                        rate_text = cells[1].get_text(strip=True)
                        usd_rate = _parse_rate_text(rate_text)
                        if usd_rate:
                            logger.info(f'Found USD rate in table: {usd_rate}')
                            break
                if usd_rate:
                    break
            if usd_rate:
                break
        
        # Strategy 2: Look for USD in divs/spans with common class names
        if not usd_rate:
            for selector in [
                'div[class*="usd"]',
                'span[class*="usd"]',
                'div[class*="rate"]',
                'span[class*="rate"]',
                '[data-currency="USD"]',
                '[id*="usd"]',
            ]:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    rate = _parse_rate_text(text)
                    if rate:
                        usd_rate = rate
                        logger.info(f'Found USD rate in element: {usd_rate}')
                        break
                if usd_rate:
                    break
        
        # Strategy 3: Search entire page for rate pattern (e.g., "2,100.00" near "USD")
        if not usd_rate:
            page_text = soup.get_text()
            # Look for patterns like "USD 2,100.00" or "2,100.00 MMK"
            import re
            patterns = [
                r'USD[:\s]+([\d,]+\.?\d*)',
                r'([\d,]+\.?\d*)\s*MMK.*USD',
                r'US\s*Dollar[:\s]+([\d,]+\.?\d*)',
            ]
            for pattern in patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    rate_text = match.group(1)
                    usd_rate = _parse_rate_text(rate_text)
                    if usd_rate:
                        logger.info(f'Found USD rate via regex: {usd_rate}')
                        break
        
        if usd_rate:
            logger.info(f'Successfully scraped USD rate: {usd_rate} MMK')
            return usd_rate
        else:
            logger.warning('USD rate not found in scraped content')
            return None
            
    except requests.RequestException as e:
        logger.error(f'Network error while scraping CBM: {e}', exc_info=True)
        return None
    except Exception as e:
        logger.error(f'Unexpected error while scraping CBM: {e}', exc_info=True)
        return None


def _parse_rate_text(text):
    """
    Parse rate text (e.g., "2,100.00" or "2100.00") to Decimal.
    
    Args:
        text: String containing rate (may include commas, spaces)
        
    Returns:
        Decimal or None if parsing fails
    """
    if not text:
        return None
    
    try:
        # Remove commas, spaces, and non-numeric characters except decimal point
        cleaned = ''.join(c for c in text if c.isdigit() or c == '.')
        if not cleaned:
            return None
        
        rate = Decimal(cleaned)
        # Sanity check: USD rate should be between 1000 and 10000 MMK
        if 1000 <= rate <= 10000:
            return rate
        else:
            logger.warning(f'Parsed rate {rate} is outside expected range (1000-10000)')
            return None
    except (InvalidOperation, ValueError) as e:
        logger.warning(f'Failed to parse rate text "{text}": {e}')
        return None
