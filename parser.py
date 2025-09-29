from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse

class Parser:
    """
    Parses HTML content to extract dataset information and new links.
    """

    def __init__(self, base_url):
        """
        Initializes the Parser.

        Args:
            base_url (str): The base URL of the site being crawled.
                            Used to resolve relative links.
        """
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc

    def parse(self, html_content, page_url):
        """
        Parses the HTML of a page to find datasets and new links.

        Args:
            html_content (str): The HTML content of the page.
            page_url (str): The URL of the page being parsed.

        Returns:
            tuple: A tuple containing:
                - list: A list of dictionaries, where each dictionary is a dataset.
                - set: A set of new, valid URLs to crawl.
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        datasets = []

        # --- Information Extraction Heuristics ---

        # 1. Find Dataset Title
        title = self._find_title(soup)
        if not title:
            # If no clear title, we might not be on a dataset page.
            # We can still look for links, but won't associate them with a title.
            pass

        # 2. Find Download Links & Resource Types
        download_links = self._find_download_links(soup, page_url)

        # 3. Find Freshness Clues
        date_clues = self._find_date_clues(soup)

        # Create a dataset entry for each download link found
        for link_info in download_links:
            dataset = {
                'dataset_title': title if title else "Untitled Dataset",
                'source_url': page_url,
                'download_link': link_info['url'],
                'resource_type': link_info['type'],
                'date_clues': date_clues,
        'title_clues': [title] if title else []
            }
            datasets.append(dataset)

        # 4. Discover new links to crawl
        new_links_to_crawl = self._discover_new_links(soup, page_url)

        return datasets, new_links_to_crawl

    def _find_title(self, soup):
        """Finds the main title of the dataset on the page."""
        # Heuristic 1: Look for common heading tags
        for tag in ['h1', 'h2']:
            if soup.find(tag):
                return soup.find(tag).get_text(strip=True)
        # Heuristic 2: Look for elements with common class names
        for class_name in ['dataset-heading', 'asset-name']:
            element = soup.find(class_=class_name)
            if element:
                return element.get_text(strip=True)
        return None

    def _find_download_links(self, soup, page_url):
        """Finds all potential download links on the page."""
        links = []
        data_extensions = ['.csv', '.json', '.zip', '.geojson', '.shp', '.kml', '.xls', '.xlsx']

        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href'].lower()
            link_text = a_tag.get_text().lower()

            # Check by extension
            if any(href.endswith(ext) for ext in data_extensions):
                link_type = href.split('.')[-1].upper()
                full_url = urljoin(page_url, a_tag['href'])
                links.append({'url': full_url, 'type': link_type})
                continue

            # Check by keyword in text or link
            if 'api' in href or 'api' in link_text or 'endpoint' in link_text:
                full_url = urljoin(page_url, a_tag['href'])
                links.append({'url': full_url, 'type': 'API'})
                continue

            if 'download' in link_text and not any(href.endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
                 full_url = urljoin(page_url, a_tag['href'])
                 # Can't determine type, but flag it for now
                 links.append({'url': full_url, 'type': 'Unknown'})


        return links

    def _find_date_clues(self, soup):
        """Extracts text nodes that may contain date information."""
        clues = []
        # Find text containing keywords like 'update', 'modified', 'published', 'released'
        # Limit search to a reasonable text length to avoid huge blobs
        text_nodes = soup.find_all(string=re.compile(r'(?i)update|modified|published|release|date'))
        for node in text_nodes:
            # Heuristic: only consider relatively short text snippets
            if len(node.strip()) < 150:
                clues.append(node.strip())
        return clues

    def _discover_new_links(self, soup, page_url):
        """
        Discovers new, crawlable links on the page.
        This is intentionally broad to ensure wide traversal.
        """
        new_links = set()
        # Common file extensions to avoid crawling directly
        file_extensions = [
    '.csv', '.json', '.zip', '.geojson', '.shp', '.kml', '.xls', '.xlsx',
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xml', '.rdf', '.txt',
    '.png', '.jpg', '.jpeg', '.gif', '.svg'
]


        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']

            # Skip mailto, javascript, and anchor links
            if href.startswith(('mailto:', 'javascript:', '#')):
                continue

            # Resolve the URL relative to the page URL
            full_url = urljoin(page_url, href)

            # Basic check to skip URLs that are clearly file downloads
            if any(full_url.lower().endswith(ext) for ext in file_extensions):
                continue

            # Ensure we are staying on the same domain and it's a http/https link
            parsed_full_url = urlparse(full_url)
            if parsed_full_url.netloc == self.domain and parsed_full_url.scheme in ['http', 'https']:
                new_links.add(full_url)

        return new_links