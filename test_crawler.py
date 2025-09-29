import unittest
from unittest.mock import MagicMock, patch
import requests
from crawler import Crawler
from db_manager import DBManager

class TestCrawler(unittest.TestCase):

    def setUp(self):
        """Set up a mock DB manager and other components."""
        self.mock_db_manager = MagicMock(spec=DBManager)
        self.start_url = 'http://mocksite.com/data'

    @patch('crawler.requests.get')
    def test_crawl_flow(self, mock_get):
        """Test the basic crawling process."""
        # --- Mock a simple two-page website ---
        page1_url = self.start_url
        page2_url = 'http://mocksite.com/data/page2'

        # Mock HTML content
        page1_html = f"""
        <html>
            <h1>Page 1</h1>
            <a href="/data/page2">Go to page 2</a>
            <a href="data.csv">Download CSV</a>
        </html>
        """
        page2_html = """
        <html>
            <h1>Page 2</h1>
            <a href="data.json">Download JSON</a>
        </html>
        """

        # Mock the response from requests.get
        mock_response1 = MagicMock()
        mock_response1.text = page1_html
        mock_response1.raise_for_status.return_value = None

        mock_response2 = MagicMock()
        mock_response2.text = page2_html
        mock_response2.raise_for_status.return_value = None

        # Return different responses for different URLs
        mock_get.side_effect = [mock_response1, mock_response2]

        # --- Initialize and run the crawler ---
        # Set max_pages to 2 to control the test scope
        crawler = Crawler(start_url=page1_url, db_manager=self.mock_db_manager, max_pages=2)
        crawler.crawl()

        # --- Assertions ---
        # 1. Assert that requests.get was called for both pages
        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_any_call(page1_url, timeout=10, headers={'User-Agent': 'OpenDataCrawler/1.0'})
        mock_get.assert_any_call(page2_url, timeout=10, headers={'User-Agent': 'OpenDataCrawler/1.0'})

        # 2. Assert that the DB manager's add_or_update method was called
        # The parser will find one download link on each page.
        self.assertEqual(self.mock_db_manager.add_or_update_dataset.call_count, 2)

        # 3. Check some of the data that was passed to the DB manager
        first_call_args = self.mock_db_manager.add_or_update_dataset.call_args_list[0].args[0]
        self.assertEqual(first_call_args['dataset_title'], 'Page 1')
        self.assertEqual(first_call_args['resource_type'], 'CSV')
        self.assertEqual(first_call_args['source_url'], page1_url)

        second_call_args = self.mock_db_manager.add_or_update_dataset.call_args_list[1].args[0]
        self.assertEqual(second_call_args['dataset_title'], 'Page 2')
        self.assertEqual(second_call_args['resource_type'], 'JSON')
        self.assertEqual(second_call_args['source_url'], page2_url)

    @patch('crawler.requests.get')
    def test_max_pages_limit(self, mock_get):
        """Test that crawling stops when max_pages is reached."""
        # Mock a site with many links
        html = """
        <html>
            <a href="/data/1">1</a> <a href="/data/2">2</a> <a href="/data/3">3</a>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = html
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Crawl with max_pages = 2
        crawler = Crawler(start_url=self.start_url, db_manager=self.mock_db_manager, max_pages=2)
        crawler.crawl()

        # requests.get should only be called twice (the start_url + one from the page)
        self.assertEqual(mock_get.call_count, 2)

    @patch('crawler.requests.get')
    def test_request_error_handling(self, mock_get):
        """Test that the crawler handles HTTP errors gracefully."""
        # Configure the mock to raise an exception
        mock_get.side_effect = requests.exceptions.RequestException("Test Error")

        crawler = Crawler(start_url=self.start_url, db_manager=self.mock_db_manager)

        # This should run without raising an exception
        crawler.crawl()

        # The DB manager should not have been called
        self.mock_db_manager.add_or_update_dataset.assert_not_called()


if __name__ == '__main__':
    unittest.main()