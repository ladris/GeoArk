import requests
import time
from collections import deque
from urllib.parse import urlparse

# Assuming parser, scorer, and db_manager are in the same directory
from parser import Parser
from scorer import Scorer
from db_manager import DBManager

class Crawler:
    """
    Navigates a website to discover and process dataset pages.
    """

    def __init__(self, start_url, db_manager, max_pages=100, delay=1):
        """
        Initializes the Crawler.

        Args:
            start_url (str): The root URL to begin crawling.
            db_manager (DBManager): An instance of the database manager.
            max_pages (int): The maximum number of pages to crawl.
            delay (int): The delay in seconds between HTTP requests.
        """
        self.start_url = start_url
        self.db_manager = db_manager
        self.max_pages = max_pages
        self.delay = delay

        self.url_queue = deque([start_url])
        self.visited_urls = {start_url}

        self.parser = Parser(base_url=start_url)
        self.scorer = Scorer()
        self.domain = urlparse(start_url).netloc

    def crawl(self):
        """
        Executes the crawling process.
        """
        pages_crawled = 0
        while self.url_queue and pages_crawled < self.max_pages:
            current_url = self.url_queue.popleft()
            print(f"Crawling: {current_url}")

            try:
                response = requests.get(current_url, timeout=10, headers={'User-Agent': 'OpenDataCrawler/1.0'})
                response.raise_for_status() # Raise an exception for bad status codes
            except requests.RequestException as e:
                print(f"Error fetching {current_url}: {e}")
                continue

            # Pass content to parser
            datasets, new_links = self.parser.parse(response.text, current_url)

            # Process found datasets
            for dataset in datasets:
                # Calculate freshness score
                freshness_score = self.scorer.calculate_freshness_score(
                    dataset['date_clues'], dataset['title_clues']
                )

                # Prepare data for DB insertion
                db_data = {
                    'dataset_title': dataset['dataset_title'],
                    'source_url': dataset['source_url'],
                    'download_link': dataset['download_link'],
                    'resource_type': dataset['resource_type'],
                    'freshness_score': freshness_score,
                    'source_domain': self.domain
                }

                print(f"  Found dataset: {db_data['dataset_title']} ({db_data['resource_type']}) -> Score: {freshness_score}")
                self.db_manager.add_or_update_dataset(db_data)

            # Add new, unvisited links to the queue
            for link in new_links:
                if link not in self.visited_urls:
                    self.visited_urls.add(link)
                    self.url_queue.append(link)

            pages_crawled += 1
            print(f"  Found {len(new_links)} new links. Queue size: {len(self.url_queue)}")

            # Politeness delay
            time.sleep(self.delay)

        print(f"\nCrawling finished. Visited {pages_crawled} pages.")