#!/usr/bin/env python3
"""
Emergency Alert Monitor Scraper
Monitors multiple emergency feed sources for Howard County
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import requests
import feedparser
from bs4 import BeautifulSoup
import time

# Configure logging
# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/emergency-alerts-{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EmergencyAlertMonitor:
    def __init__(self):
        self.data_dir = "data/emergency"
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Emergency feed sources (updated with working URLs)
        self.feeds = {
            'hcpss_alerts': 'https://www.hcpss.org/news/alerts/feed/',  # School system alerts (working)
            'weather_nws': 'https://alerts.weather.gov/cap/wwaatmget.php?x=MDC027&y=0',  # NWS Howard County alerts
            'maryland_511': 'https://www.md511.maryland.gov/rss/incidents.rss',  # Maryland traffic incidents
        }
        
        # Web scraping sources (when RSS feeds aren't available)
        self.web_sources = {
            'howard_county_alerts': 'https://www.howardcountymd.gov/emergency-management',
            'howard_county_news': 'https://www.howardcountymd.gov/news'
        }
        
        # Keywords that indicate critical alerts
        self.critical_keywords = [
            'emergency', 'urgent', 'immediate', 'evacuation', 'shelter',
            'tornado', 'severe weather', 'flash flood', 'school closure',
            'road closure', 'water advisory', 'gas leak', 'fire', 'hazmat'
        ]
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': os.getenv('SCRAPER_USER_AGENT', 
                'Mozilla/5.0 (compatible; HowardCountyNews-Bot/1.0)')
        })

    def check_all_feeds(self) -> Dict[str, Any]:
        """Check all emergency feeds and web sources for new alerts"""
        all_alerts = []
        critical_alerts = []
        feed_statuses = {}
        
        # Check RSS feeds
        for feed_name, feed_url in self.feeds.items():
            logger.info(f"Checking {feed_name} feed")
            
            try:
                alerts = self.parse_feed(feed_url, feed_name)
                all_alerts.extend(alerts)
                
                # Check for critical alerts
                critical = [alert for alert in alerts if self.is_critical_alert(alert)]
                critical_alerts.extend(critical)
                
                feed_statuses[feed_name] = {
                    'status': 'success',
                    'alerts_found': len(alerts),
                    'critical_found': len(critical),
                    'last_checked': datetime.utcnow().isoformat()
                }
                
                logger.info(f"{feed_name}: {len(alerts)} alerts, {len(critical)} critical")
                
            except Exception as e:
                logger.error(f"Error checking {feed_name}: {e}")
                feed_statuses[feed_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        # Check web sources (scraping)
        for source_name, source_url in self.web_sources.items():
            logger.info(f"Scraping {source_name} website")
            
            try:
                alerts = self.scrape_web_source(source_url, source_name)
                all_alerts.extend(alerts)
                
                critical = [alert for alert in alerts if self.is_critical_alert(alert)]
                critical_alerts.extend(critical)
                
                feed_statuses[source_name] = {
                    'status': 'success',
                    'alerts_found': len(alerts),
                    'critical_found': len(critical),
                    'last_checked': datetime.utcnow().isoformat()
                }
                
                logger.info(f"{source_name}: {len(alerts)} alerts, {len(critical)} critical")
                
            except Exception as e:
                logger.error(f"Error scraping {source_name}: {e}")
                feed_statuses[source_name] = {
                    'status': 'error',
                    'error': str(e),
                    'last_checked': datetime.utcnow().isoformat()
                }
        
        return {
            'all_alerts': all_alerts,
            'critical_alerts': critical_alerts,
            'feed_statuses': feed_statuses,
            'check_timestamp': datetime.utcnow().isoformat()
        }

    def parse_feed(self, feed_url: str, feed_name: str) -> List[Dict[str, Any]]:
        """Parse RSS/XML feed for alerts"""
        alerts = []
        
        try:
            # Try RSS parsing first
            feed = feedparser.parse(feed_url)
            
            if feed.entries:
                for entry in feed.entries[:20]:  # Limit to recent 20 entries
                    alert = self.parse_feed_entry(entry, feed_name)
                    if alert and self.is_recent_alert(alert):
                        alerts.append(alert)
            else:
                # Fallback to direct HTTP request for non-standard feeds
                response = self.session.get(feed_url)
                response.raise_for_status()
                alerts = self.parse_custom_feed(response.text, feed_name)
                
        except Exception as e:
            logger.error(f"Error parsing feed {feed_url}: {e}")
            
        return alerts

    def parse_feed_entry(self, entry: Any, source: str) -> Optional[Dict[str, Any]]:
        """Parse individual RSS entry into alert format"""
        try:
            # Extract publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6]).isoformat()
            
            alert = {
                'id': getattr(entry, 'id', entry.link),
                'title': getattr(entry, 'title', 'Unknown Alert'),
                'description': getattr(entry, 'summary', getattr(entry, 'description', '')),
                'link': getattr(entry, 'link', ''),
                'published': pub_date,
                'source': source,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
            return alert
            
        except Exception as e:
            logger.error(f"Error parsing feed entry: {e}")
            return None

    def parse_custom_feed(self, content: str, source: str) -> List[Dict[str, Any]]:
        """Parse custom XML/HTML content for alerts"""
        alerts = []
        
        try:
            soup = BeautifulSoup(content, 'xml') or BeautifulSoup(content, 'html.parser')
            
            # Look for alert items based on source
            if 'weather' in source:
                items = soup.find_all(['alert', 'entry', 'item'])
            else:
                items = soup.find_all(['item', 'entry', 'alert'])
            
            for item in items:
                alert = self.extract_alert_from_element(item, source)
                if alert:
                    alerts.append(alert)
                    
        except Exception as e:
            logger.error(f"Error parsing custom feed: {e}")
            
        return alerts

    def extract_alert_from_element(self, element: Any, source: str) -> Optional[Dict[str, Any]]:
        """Extract alert data from XML/HTML element"""
        try:
            title = element.find(['title', 'headline', 'event'])
            title_text = title.get_text(strip=True) if title else 'Unknown Alert'
            
            desc = element.find(['description', 'summary', 'info'])
            desc_text = desc.get_text(strip=True) if desc else ''
            
            link = element.find(['link', 'url'])
            link_href = link.get('href') or link.get_text(strip=True) if link else ''
            
            pub_date = element.find(['pubDate', 'published', 'sent'])
            pub_text = pub_date.get_text(strip=True) if pub_date else None
            
            return {
                'id': f"{source}_{int(time.time())}_{hash(title_text)}",
                'title': title_text,
                'description': desc_text[:1000],  # Truncate long descriptions
                'link': link_href,
                'published': pub_text,
                'source': source,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting alert element: {e}")
            return None

    def is_recent_alert(self, alert: Dict[str, Any]) -> bool:
        """Check if alert is from the last 24 hours"""
        try:
            if not alert.get('published'):
                return True  # Include alerts without dates to be safe
                
            pub_date = datetime.fromisoformat(alert['published'].replace('Z', '+00:00'))
            cutoff = datetime.utcnow() - timedelta(hours=24)
            
            return pub_date >= cutoff
            
        except Exception:
            return True  # Include if we can't parse date

    def is_critical_alert(self, alert: Dict[str, Any]) -> bool:
        """Determine if alert is critical based on content"""
        content = f"{alert.get('title', '')} {alert.get('description', '')}".lower()
        
        return any(keyword in content for keyword in self.critical_keywords)

    def scrape_web_source(self, url: str, source_name: str) -> List[Dict[str, Any]]:
        """Scrape emergency alerts from web pages"""
        alerts = []
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            if 'emergency' in source_name:
                # Look for emergency announcements
                alert_selectors = [
                    '.alert', '.emergency', '.notice', '.announcement',
                    '[class*="alert"]', '[class*="emergency"]', '[class*="notice"]'
                ]
                
                for selector in alert_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if len(text) > 20 and any(keyword in text.lower() for keyword in self.critical_keywords):
                            alerts.append({
                                'id': f"{source_name}_{hash(text)}",
                                'title': text[:100] + '...' if len(text) > 100 else text,
                                'description': text[:500],
                                'link': url,
                                'published': datetime.utcnow().isoformat(),
                                'source': source_name,
                                'scraped_at': datetime.utcnow().isoformat()
                            })
            
            elif 'news' in source_name:
                # Look for recent news that might include emergencies
                article_selectors = [
                    'article', '.news-item', '.card', '[class*="article"]',
                    'h2 a', 'h3 a', '.title a'
                ]
                
                for selector in article_selectors:
                    elements = soup.select(selector)[:10]  # Recent items
                    for elem in elements:
                        if elem.name == 'a':
                            title = elem.get_text(strip=True)
                            link = elem.get('href', '')
                        else:
                            title_elem = elem.find(['h1', 'h2', 'h3', 'h4'])
                            title = title_elem.get_text(strip=True) if title_elem else elem.get_text(strip=True)[:100]
                            link_elem = elem.find('a')
                            link = link_elem.get('href', '') if link_elem else url
                        
                        if any(keyword in title.lower() for keyword in ['emergency', 'alert', 'closure', 'weather']):
                            alerts.append({
                                'id': f"{source_name}_{hash(title)}",
                                'title': title,
                                'description': title,
                                'link': self.resolve_url(link, url),
                                'published': datetime.utcnow().isoformat(),
                                'source': source_name,
                                'scraped_at': datetime.utcnow().isoformat()
                            })
                            
        except Exception as e:
            logger.error(f"Error scraping {source_name}: {e}")
            
        return alerts
    
    def resolve_url(self, link: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if link.startswith('http'):
            return link
        elif link.startswith('/'):
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            return f"{parsed.scheme}://{parsed.netloc}{link}"
        else:
            return f"{base_url.rstrip('/')}/{link}"

    def save_alerts(self, alerts_data: Dict[str, Any]):
        """Save alerts to files with timestamps"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save all alerts
        all_alerts_file = os.path.join(self.data_dir, f"all_alerts_{timestamp}.json")
        with open(all_alerts_file, 'w', encoding='utf-8') as f:
            json.dump(alerts_data, f, indent=2, ensure_ascii=False)
            
        # Save critical alerts separately if any exist
        if alerts_data['critical_alerts']:
            critical_file = os.path.join(self.data_dir, "critical-alerts.json")
            with open(critical_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'alerts': alerts_data['critical_alerts'],
                    'count': len(alerts_data['critical_alerts']),
                    'updated': alerts_data['check_timestamp']
                }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved alerts data to {all_alerts_file}")

    def run_monitor(self):
        """Main monitoring execution"""
        logger.info("Starting emergency alert monitoring")
        
        alerts_data = self.check_all_feeds()
        
        total_alerts = len(alerts_data['all_alerts'])
        critical_count = len(alerts_data['critical_alerts'])
        
        logger.info(f"Monitoring complete. Found {total_alerts} total alerts, "
                   f"{critical_count} critical alerts")
        
        # Save results
        self.save_alerts(alerts_data)
        
        # Return summary for GitHub Actions
        return {
            'total_alerts': total_alerts,
            'critical_alerts': critical_count,
            'feeds_checked': len(self.feeds) + len(self.web_sources),
            'successful_feeds': len([s for s in alerts_data['feed_statuses'].values() 
                                   if s['status'] == 'success']),
            'timestamp': alerts_data['check_timestamp']
        }

if __name__ == "__main__":
    monitor = EmergencyAlertMonitor()
    result = monitor.run_monitor()
    print(json.dumps(result, indent=2))