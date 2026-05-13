import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime

class GuardianIngestor:
    """
    Scrapes articles from The Guardian to create IELTS-style reading materials.
    """
    def __init__(self, base_url="https://www.theguardian.com"):
        self.base_url = base_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def fetch_section(self, section="science"):
        """Fetches article URLs from a specific Guardian section."""
        url = f"{self.base_url}/{section}"
        print(f"Fetching section: {url}")
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links - Guardian often uses data-link-name="article" or similar
            # Look for <a> tags with class 'u-faux-block-link__overlay' or simply links within cards
            links = []
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Filter for actual articles, avoiding section landing pages
                if section in href and len(href.split('/')) > 4 and not href.endswith(section):
                    if not href.startswith('http'):
                        href = self.base_url + href
                    if href not in links:
                        links.append(href)
            
            return links[:10] # Limit to 10 for now
        except Exception as e:
            print(f"Error fetching section {section}: {e}")
            return []

    def scrape_article(self, url):
        """Scrapes content from an article URL."""
        print(f"Scraping article: {url}")
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.find('h1').get_text().strip() if soup.find('h1') else "Untitled"
            
            # Content is usually in div with class 'article-body-commercial-selector' or 'content__article-body'
            content_div = soup.find('div', class_='article-body-commercial-selector') or \
                          soup.find('div', class_='content__article-body') or \
                          soup.find('div', class_='dcr-1qy8y9m') # Common data class
            
            if not content_div:
                # Fallback: get all <p> tags
                paragraphs = soup.find_all('p')
                content = "\n\n".join([p.get_text().strip() for p in paragraphs if len(p.get_text()) > 50])
            else:
                paragraphs = content_div.find_all('p')
                content = "\n\n".join([p.get_text().strip() for p in paragraphs])
            
            return {
                "title": title,
                "content": content,
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "source": "The Guardian"
            }
        except Exception as e:
            print(f"Error scraping article {url}: {e}")
            return None

    def ingest(self, sections=["science", "environment", "world"]):
        """Main ingestion loop."""
        all_articles = []
        for section in sections:
            urls = self.fetch_section(section)
            for url in urls:
                article = self.scrape_article(url)
                if article and len(article['content']) > 500: # Ensure substantial content
                    all_articles.append(article)
        
        return all_articles

def save_articles(articles, filename="data/guardian_articles.json"):
    """Saves articles to a JSON file."""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    # Load existing if available
    existing = []
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            existing = json.load(f)
    
    # Merge and avoid duplicates based on url
    urls = {a['url'] for a in existing}
    new_count = 0
    for a in articles:
        if a['url'] not in urls:
            existing.append(a)
            new_count += 1
    
    with open(filename, 'w') as f:
        json.dump(existing, f, indent=2)
    
    print(f"Saved {new_count} new articles to {filename}. Total: {len(existing)}")

if __name__ == "__main__":
    ingestor = GuardianIngestor()
    articles = ingestor.ingest()
    save_articles(articles)
