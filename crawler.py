import time
from collections import deque
from urllib.parse import urlparse

import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.common.exceptions import WebDriverException

from parser import Parser
from scorer import Scorer
from db_manager import DBManager
from webdriver_setup import get_driver_info


class Crawler:
    """
    Navigates a website to discover and process dataset pages using Selenium
    to handle dynamic, JavaScript-rendered content.
    """

    def __init__(self, start_url, db_manager, max_pages=100, delay=1):
        """
        Initializes the Crawler.
        """
        self.start_url = start_url
        self.db_manager = db_manager
        self.max_pages = max_pages
        self.delay = delay

        self.url_queue = deque([start_url])
        self.visited_urls = {start_url}

        self.pages_crawled = 0
        self.datasets_found = 0

        self.parser = Parser(base_url=start_url)
        self.scorer = Scorer()
        self.domain = urlparse(start_url).netloc
        self.driver = self._init_driver()

    def _init_driver(self):
        """Initializes a headless Chrome WebDriver."""
        print("Initializing WebDriver...")

        try:
            driver_path, driver_url = get_driver_info()
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

        if not driver_path.exists():
            print("--- Chromedriver Not Found ---", file=sys.stderr)
            print(f"Chromedriver is required to run this crawler.", file=sys.stderr)
            print(f"Please download the correct version for your system from:", file=sys.stderr)
            print(f"URL: {driver_url}", file=sys.stderr)
            print(f"And place it in the current directory as 'chromedriver'", file=sys.stderr)
            sys.exit(1)

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=OpenDataCrawler/1.0')

        try:
            service = ChromeService(executable_path=str(driver_path))
            driver = webdriver.Chrome(service=service, options=options)
            print("WebDriver initialized successfully.")
            return driver
        except Exception as e:
            print(f"Error initializing WebDriver: {e}", file=sys.stderr)
            raise

    def crawl(self):
        """
        Executes the crawling process.
        """
        try:
            while self.url_queue and self.pages_crawled < self.max_pages:
                current_url = self.url_queue.popleft()
                print(f"Crawling: {current_url}")

                try:
                    self.driver.get(current_url)
                    # Optional: wait for JS to load. A fixed delay is simple,
                    # but explicit waits for specific elements are better.
                    time.sleep(2) # Wait a bit for JS rendering
                    html_content = self.driver.page_source
                except WebDriverException as e:
                    print(f"Error fetching {current_url} with Selenium: {e}")
                    continue

                # Pass content to parser
                datasets, new_links = self.parser.parse(html_content, current_url)

                # Process found datasets
                self.datasets_found += len(datasets)
                for dataset in datasets:
                    freshness_score = self.scorer.calculate_freshness_score(
                        dataset['date_clues'], dataset['title_clues']
                    )
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

                self.pages_crawled += 1
                print(f"  Found {len(new_links)} new links. Queue size: {len(self.url_queue)}")

                # Politeness delay
                time.sleep(self.delay)

        finally:
            print("\nCrawling finished or interrupted.")
            self.shutdown()

    def shutdown(self):
        """Shuts down the WebDriver."""
        if self.driver:
            print("Shutting down WebDriver...")
            self.driver.quit()