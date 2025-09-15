#!/usr/bin/env python3
"""
Universal Howard County Data Scraper
Uses configuration-driven approach to scrape multiple source types
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import feedparser
from urllib.parse import urljoin, urlparse
import time

# Configure logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/universal-scraper-{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UniversalScraper:
    def __init__(self, config_path: str = 'config/sources.hoco.mvp.json'):
        self.config_path = config_path
        self.config = self.load_config()
        self.data_dir = "data/universal"
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': os.getenv('SCRAPER_USER_AGENT', 
                'Mozilla/5.0 (compatible; HowardCountyNews-Bot/1.0)')
        })
        
    def load_config(self) -> Dict[str, Any]:
        """Load the sources configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {self.config_path}: {e}")
            return {'sources': []}
    
    def scrape_all_sources(self, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Scrape all sources or specific source IDs"""
        results = {
            'scrape_timestamp': datetime.utcnow().isoformat(),
            'config_version': self.config.get('version', 'unknown'),
            'sources_scraped': [],
            'total_items': 0,
            'errors': []
        }
        
        sources_to_scrape = self.config.get('sources', [])
        if source_ids:
            sources_to_scrape = [s for s in sources_to_scrape if s['id'] in source_ids]
        
        for source in sources_to_scrape:
            logger.info(f"Scraping source: {source['name']} ({source['id']})")
            
            try:
                items = self.scrape_source(source)
                
                source_result = {
                    'id': source['id'],
                    'name': source['name'], 
                    'category': source['category'],
                    'items_found': len(items),
                    'items': items,
                    'scraped_at': datetime.utcnow().isoformat(),
                    'status': 'success'
                }
                
                results['sources_scraped'].append(source_result)
                results['total_items'] += len(items)
                
                logger.info(f"Successfully scraped {len(items)} items from {source['name']}")
                
            except Exception as e:
                error_msg = f"Error scraping {source['id']}: {str(e)}"
                logger.error(error_msg)
                
                results['errors'].append({
                    'source_id': source['id'],
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                results['sources_scraped'].append({
                    'id': source['id'],
                    'name': source['name'],
                    'status': 'error',
                    'error': error_msg,
                    'items_found': 0
                })
        
        return results
    
    def scrape_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape a single source based on its strategy"""
        strategy = source.get('strategy')
        
        if strategy == 'discover_rss_on_page':
            return self.discover_rss_on_page(source)
        elif strategy == 'scrape_list':
            return self.scrape_list(source)
        elif strategy == 'follow_event_then_download_ics':
            return self.follow_event_then_download_ics(source)
        elif strategy == 'discover_ics_subscribe_link':
            return self.discover_ics_subscribe_link(source)
        else:
            logger.warning(f"Unknown strategy: {strategy} for source {source['id']}")
            return []
    
    def discover_rss_on_page(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover RSS feeds on a page and parse them"""
        items = []
        
        try:
            response = self.session.get(source['discovery_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for RSS links
            rss_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '').lower()
                if 'rss' in href or 'feed' in href or href.endswith('.xml'):
                    rss_url = urljoin(source['discovery_url'], link['href'])
                    rss_links.append(rss_url)
            
            # Also check for <link> tags in head
            for link in soup.find_all('link', type='application/rss+xml'):
                if link.get('href'):
                    rss_url = urljoin(source['discovery_url'], link['href'])
                    rss_links.append(rss_url)
            
            # Parse discovered RSS feeds
            for rss_url in rss_links[:3]:  # Limit to first 3 feeds
                try:
                    feed = feedparser.parse(rss_url)
                    for entry in feed.entries[:10]:  # Recent 10 items per feed
                        items.append(self.normalize_rss_entry(entry, source, rss_url))
                except Exception as e:
                    logger.error(f"Error parsing RSS {rss_url}: {e}")
                    
        except Exception as e:
            logger.error(f"Error discovering RSS on {source['discovery_url']}: {e}")
        
        return items
    
    def scrape_list(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scrape HTML list/table based on selectors"""
        items = []
        
        try:
            response = self.session.get(source['list_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            selectors = source.get('selectors', {})
            
            # Find all items
            item_elements = soup.select(selectors['item'])
            
            if not item_elements:
                logger.warning(f"No items found with selector: {selectors['item']}")
                # Save HTML snapshot for debugging
                self.save_debug_html(source, response.text)
            
            for element in item_elements[:20]:  # Limit to 20 items
                try:
                    item_data = {
                        'source_id': source['id'],
                        'category': source['category']
                    }
                    
                    # Extract title
                    if selectors.get('title'):
                        title_elem = element.select_one(selectors['title'])
                        item_data['title'] = title_elem.get_text(strip=True) if title_elem else 'Unknown'
                    else:
                        item_data['title'] = element.get_text(strip=True)[:100]
                    
                    # Extract link
                    if selectors.get('link'):
                        link_elem = element.select_one(selectors['link'])
                        if link_elem:
                            href = link_elem.get('href', '')
                            item_data['url'] = urljoin(source['list_url'], href)
                    
                    # Extract date
                    if selectors.get('date'):
                        date_elem = element.select_one(selectors['date'])
                        if date_elem:
                            item_data['date'] = date_elem.get_text(strip=True)
                    
                    item_data['scraped_at'] = datetime.utcnow().isoformat()
                    
                    if item_data.get('title'):  # Only add if we have a title
                        items.append(item_data)
                        
                except Exception as e:
                    logger.error(f"Error parsing item element: {e}")
                    
        except Exception as e:
            logger.error(f"Error scraping list from {source['list_url']}: {e}")
        
        return items
    
    def follow_event_then_download_ics(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Follow event links and download ICS files"""
        items = []
        
        try:
            # First get the event list
            response = self.session.get(source['list_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            selectors = source.get('selectors', {})
            
            event_elements = soup.select(selectors['item'])[:10]  # Limit events
            
            for event_elem in event_elements:
                try:
                    # Get event link
                    link_elem = event_elem.select_one(selectors['link'])
                    if not link_elem:
                        continue
                    
                    event_url = urljoin(source['list_url'], link_elem.get('href', ''))
                    title_elem = event_elem.select_one(selectors['title'])
                    title = title_elem.get_text(strip=True) if title_elem else 'Unknown Event'
                    
                    # Follow event link to find ICS
                    ics_url = self.find_ics_on_page(event_url, selectors)
                    
                    if ics_url:
                        ics_data = self.download_ics(ics_url)
                        if ics_data:
                            items.append({
                                'source_id': source['id'],
                                'category': source['category'],
                                'title': title,
                                'url': event_url,
                                'ics_url': ics_url,
                                'ics_data': ics_data[:1000],  # Truncate for storage
                                'scraped_at': datetime.utcnow().isoformat()
                            })
                    
                except Exception as e:
                    logger.error(f"Error processing event: {e}")
                    
        except Exception as e:
            logger.error(f"Error following events from {source['list_url']}: {e}")
        
        return items
    
    def discover_ics_subscribe_link(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Discover ICS calendar subscription link"""
        items = []
        
        try:
            response = self.session.get(source['discovery_url'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for calendar subscription links
            ics_links = []
            
            # Check for various subscription link patterns
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True).lower()
                
                if ('.ics' in href or 
                    'subscribe' in text and 'calendar' in text or
                    'ical' in href.lower()):
                    ics_links.append(urljoin(source['discovery_url'], href))
            
            # Download and parse ICS files
            for ics_url in ics_links[:2]:  # Limit to 2 calendars
                try:
                    ics_data = self.download_ics(ics_url)
                    if ics_data:
                        items.append({
                            'source_id': source['id'],
                            'category': source['category'],
                            'title': f"Calendar: {source['name']}",
                            'url': source['discovery_url'],
                            'ics_url': ics_url,
                            'ics_data': ics_data[:2000],  # Truncate
                            'scraped_at': datetime.utcnow().isoformat()
                        })
                except Exception as e:
                    logger.error(f"Error downloading ICS {ics_url}: {e}")
                    
        except Exception as e:
            logger.error(f"Error discovering ICS links on {source['discovery_url']}: {e}")
        
        return items
    
    def find_ics_on_page(self, url: str, selectors: Dict[str, str]) -> Optional[str]:
        """Find ICS download link on an event page"""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Use provided selector for ICS link
            if selectors.get('ics_link'):
                ics_elem = soup.select_one(selectors['ics_link'])
                if ics_elem:
                    return urljoin(url, ics_elem.get('href', ''))
            
            # Fallback: look for common ICS patterns
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '.ics' in href or 'ical' in href.lower():
                    return urljoin(url, href)
                    
        except Exception as e:
            logger.error(f"Error finding ICS on {url}: {e}")
        
        return None
    
    def download_ics(self, ics_url: str) -> Optional[str]:
        """Download ICS file content"""
        try:
            response = self.session.get(ics_url)
            response.raise_for_status()
            
            if response.headers.get('content-type', '').startswith('text/calendar'):
                return response.text
            elif 'BEGIN:VCALENDAR' in response.text:
                return response.text
                
        except Exception as e:
            logger.error(f"Error downloading ICS from {ics_url}: {e}")
        
        return None
    
    def normalize_rss_entry(self, entry: Any, source: Dict[str, Any], feed_url: str) -> Dict[str, Any]:
        """Normalize RSS entry to standard format"""
        return {
            'source_id': source['id'],
            'category': source['category'],
            'title': getattr(entry, 'title', 'Unknown'),
            'description': getattr(entry, 'summary', getattr(entry, 'description', ''))[:500],
            'url': getattr(entry, 'link', ''),
            'published': getattr(entry, 'published', ''),
            'feed_url': feed_url,
            'scraped_at': datetime.utcnow().isoformat()
        }
    
    def save_debug_html(self, source: Dict[str, Any], html_content: str):
        """Save HTML snapshot for debugging failed selectors"""
        debug_dir = os.path.join(self.data_dir, 'debug')
        os.makedirs(debug_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{source['id']}_{timestamp}.html"
        filepath = os.path.join(debug_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"Saved debug HTML to {filepath}")
        except Exception as e:
            logger.error(f"Error saving debug HTML: {e}")
    
    def save_results(self, results: Dict[str, Any]):
        """Save scraping results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"scrape_results_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Results saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def run_scraper(self, source_ids: Optional[List[str]] = None):
        """Main scraper execution"""
        logger.info(f"Starting universal scraper with config: {self.config.get('name', 'unknown')}")
        
        results = self.scrape_all_sources(source_ids)
        self.save_results(results)
        
        logger.info(f"Scraping complete. Total items: {results['total_items']}, "
                   f"Sources: {len(results['sources_scraped'])}, "
                   f"Errors: {len(results['errors'])}")
        
        return results

if __name__ == "__main__":
    import sys
    
    scraper = UniversalScraper()
    
    # Allow running specific sources from command line
    if len(sys.argv) > 1:
        source_ids = sys.argv[1].split(',')
        results = scraper.run_scraper(source_ids)
    else:
        results = scraper.run_scraper()
    
    # Print summary
    print(json.dumps({
        'total_items': results['total_items'],
        'sources_processed': len(results['sources_scraped']),
        'errors': len(results['errors']),
        'timestamp': results['scrape_timestamp']
    }, indent=2))