#!/usr/bin/env python3
"""
Howard County Council Meeting Scraper
Monitors council meetings, agendas, and voting records
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

# Configure logging
# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/county-council-{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CountyCouncilScraper:
    def __init__(self):
        self.base_url = "https://www.howardcountymd.gov"
        self.council_url = f"{self.base_url}/county-council"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': os.getenv('SCRAPER_USER_AGENT', 
                'Mozilla/5.0 (compatible; HowardCountyNews-Bot/1.0)')
        })
        self.data_dir = "data/county-council"
        os.makedirs(self.data_dir, exist_ok=True)
        
    def setup_driver(self):
        """Setup Chrome WebDriver for JavaScript-heavy pages"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        return webdriver.Chrome(options=chrome_options)

    def scrape_meeting_calendar(self) -> List[Dict[str, Any]]:
        """Scrape upcoming council meetings"""
        meetings = []
        try:
            calendar_url = f"{self.council_url}/meetings-agendas"
            response = self.session.get(calendar_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for meeting calendar items
            meeting_items = soup.find_all(['div', 'article'], class_=['meeting-item', 'calendar-event'])
            
            for item in meeting_items:
                meeting_data = self.extract_meeting_details(item)
                if meeting_data:
                    meetings.append(meeting_data)
                    
            logger.info(f"Found {len(meetings)} upcoming council meetings")
            
        except Exception as e:
            logger.error(f"Error scraping meeting calendar: {e}")
            
        return meetings

    def extract_meeting_details(self, meeting_element) -> Dict[str, Any]:
        """Extract details from a meeting element"""
        try:
            # Extract meeting title
            title_elem = meeting_element.find(['h2', 'h3', 'h4'], class_=['title', 'meeting-title'])
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Meeting"
            
            # Extract date and time
            date_elem = meeting_element.find(['span', 'div'], class_=['date', 'meeting-date'])
            time_elem = meeting_element.find(['span', 'div'], class_=['time', 'meeting-time'])
            
            # Extract agenda link
            agenda_link = None
            agenda_elem = meeting_element.find('a', href=True, string=lambda text: 'agenda' in text.lower() if text else False)
            if agenda_elem:
                agenda_link = self.resolve_url(agenda_elem['href'])
            
            # Extract location
            location_elem = meeting_element.find(['span', 'div'], class_=['location', 'meeting-location'])
            location = location_elem.get_text(strip=True) if location_elem else "County Council Chambers"
            
            meeting_data = {
                'title': title,
                'date': date_elem.get_text(strip=True) if date_elem else None,
                'time': time_elem.get_text(strip=True) if time_elem else None,
                'location': location,
                'agenda_url': agenda_link,
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'county_council_calendar'
            }
            
            return meeting_data
            
        except Exception as e:
            logger.error(f"Error extracting meeting details: {e}")
            return None

    def scrape_recent_minutes(self) -> List[Dict[str, Any]]:
        """Scrape recent meeting minutes and voting records"""
        minutes_data = []
        try:
            minutes_url = f"{self.council_url}/meeting-minutes"
            response = self.session.get(minutes_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find links to recent meeting minutes
            minute_links = soup.find_all('a', href=True, string=lambda text: 'minutes' in text.lower() if text else False)
            
            for link in minute_links[:10]:  # Get last 10 meetings
                minutes_url = self.resolve_url(link['href'])
                minute_data = self.extract_minutes_content(minutes_url, link.get_text(strip=True))
                if minute_data:
                    minutes_data.append(minute_data)
                    
            logger.info(f"Scraped {len(minutes_data)} meeting minutes")
            
        except Exception as e:
            logger.error(f"Error scraping meeting minutes: {e}")
            
        return minutes_data

    def extract_minutes_content(self, minutes_url: str, title: str) -> Dict[str, Any]:
        """Extract content from meeting minutes"""
        try:
            response = self.session.get(minutes_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract voting records
            votes = self.extract_voting_records(soup)
            
            # Extract action items
            actions = self.extract_action_items(soup)
            
            # Extract full text content
            content_elem = soup.find(['div', 'article'], class_=['content', 'main-content', 'minutes-content'])
            full_text = content_elem.get_text(separator=' ', strip=True) if content_elem else ""
            
            return {
                'title': title,
                'url': minutes_url,
                'votes': votes,
                'action_items': actions,
                'full_text': full_text[:5000],  # Truncate for processing
                'scraped_at': datetime.utcnow().isoformat(),
                'source': 'council_minutes'
            }
            
        except Exception as e:
            logger.error(f"Error extracting minutes from {minutes_url}: {e}")
            return None

    def extract_voting_records(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract voting records from meeting minutes"""
        votes = []
        try:
            # Look for voting tables or sections
            vote_sections = soup.find_all(['table', 'div'], class_=['vote-table', 'voting-record'])
            
            for section in vote_sections:
                # Extract individual votes
                vote_items = section.find_all('tr') if section.name == 'table' else section.find_all(['div', 'p'])
                
                for item in vote_items:
                    vote_text = item.get_text(strip=True)
                    if any(keyword in vote_text.lower() for keyword in ['yes', 'no', 'abstain', 'vote', 'motion']):
                        votes.append({
                            'text': vote_text,
                            'extracted_at': datetime.utcnow().isoformat()
                        })
                        
        except Exception as e:
            logger.error(f"Error extracting voting records: {e}")
            
        return votes

    def extract_action_items(self, soup: BeautifulSoup) -> List[str]:
        """Extract action items and decisions from minutes"""
        actions = []
        try:
            # Look for action item indicators
            action_keywords = ['action:', 'decided:', 'approved:', 'motion to', 'resolved:']
            
            text_elements = soup.find_all(['p', 'li', 'div'])
            for elem in text_elements:
                text = elem.get_text(strip=True).lower()
                if any(keyword in text for keyword in action_keywords):
                    actions.append(elem.get_text(strip=True))
                    
        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            
        return actions

    def scrape_council_members(self) -> List[Dict[str, Any]]:
        """Scrape current council member information"""
        members = []
        try:
            members_url = f"{self.council_url}/council-members"
            response = self.session.get(members_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            member_cards = soup.find_all(['div', 'article'], class_=['member-card', 'council-member', 'bio-card'])
            
            for card in member_cards:
                member_data = self.extract_member_info(card)
                if member_data:
                    members.append(member_data)
                    
            logger.info(f"Found {len(members)} council members")
            
        except Exception as e:
            logger.error(f"Error scraping council members: {e}")
            
        return members

    def extract_member_info(self, member_element) -> Dict[str, Any]:
        """Extract council member information"""
        try:
            name_elem = member_element.find(['h2', 'h3', 'h4'])
            name = name_elem.get_text(strip=True) if name_elem else "Unknown"
            
            district_elem = member_element.find(string=lambda text: 'district' in text.lower() if text else False)
            district = district_elem.strip() if district_elem else None
            
            contact_info = {}
            email_elem = member_element.find('a', href=lambda href: href and 'mailto:' in href)
            if email_elem:
                contact_info['email'] = email_elem['href'].replace('mailto:', '')
                
            phone_elem = member_element.find(string=lambda text: text and any(char.isdigit() for char in text) and len([c for c in text if c.isdigit()]) >= 10)
            if phone_elem:
                contact_info['phone'] = phone_elem.strip()
            
            return {
                'name': name,
                'district': district,
                'contact': contact_info,
                'scraped_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error extracting member info: {e}")
            return None

    def resolve_url(self, url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if url.startswith('http'):
            return url
        elif url.startswith('/'):
            return f"{self.base_url}{url}"
        else:
            return f"{self.council_url}/{url}"

    def save_data(self, data: Dict[str, Any], filename: str):
        """Save scraped data to JSON file"""
        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved data to {filepath}")

    def run_scraper(self):
        """Main scraper execution"""
        logger.info("Starting Howard County Council scraper")
        
        # Scrape all data sources
        meetings = self.scrape_meeting_calendar()
        minutes = self.scrape_recent_minutes()
        members = self.scrape_council_members()
        
        # Compile results
        results = {
            'scrape_timestamp': datetime.utcnow().isoformat(),
            'source': 'howard_county_council',
            'data': {
                'upcoming_meetings': meetings,
                'recent_minutes': minutes,
                'council_members': members
            },
            'stats': {
                'meetings_found': len(meetings),
                'minutes_processed': len(minutes),
                'members_found': len(members)
            }
        }
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.save_data(results, f"council_data_{timestamp}.json")
        
        logger.info(f"Scraping complete. Found {results['stats']['meetings_found']} meetings, "
                   f"{results['stats']['minutes_processed']} minutes, "
                   f"{results['stats']['members_found']} members")
        
        return results

if __name__ == "__main__":
    scraper = CountyCouncilScraper()
    scraper.run_scraper()