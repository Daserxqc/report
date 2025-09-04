import requests
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

class WebContentCollector:
    def __init__(self, max_workers=5):
        self.max_workers = max_workers

    def fetch_single_url(self, url: str) -> str:
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # A simple approach to get the main content
            paragraphs = soup.find_all('p')
            text_content = '\n'.join([p.get_text() for p in paragraphs])
            
            return text_content
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return ""

    def fetch_all_urls(self, urls: List[str]) -> List[str]:
        contents = [""] * len(urls)
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {executor.submit(self.fetch_single_url, url): i for i, url in enumerate(urls)}
            for future in as_completed(future_to_url):
                index = future_to_url[future]
                try:
                    contents[index] = future.result()
                except Exception as e:
                    print(f"Error processing url at index {index}: {e}")
        return contents

    def enrich_search_results(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        urls = [result['url'] for result in search_results]
        contents = self.fetch_all_urls(urls)
        
        for i, result in enumerate(search_results):
            if contents[i]:
                result['full_content'] = contents[i]
            else:
                result['full_content'] = result.get('content', '') # Fallback to original content
        
        return search_results

if __name__ == '__main__':
    collector = WebContentCollector()
    sample_results = [
        {'url': 'https://www.example.com', 'content': 'Summary of example.'},
        {'url': 'https://www.google.com', 'content': 'Summary of google.'}
    ]
    enriched_results = collector.enrich_search_results(sample_results)
    for result in enriched_results:
        print(f"URL: {result['url']}\nContent Length: {len(result['full_content'])}\n---")