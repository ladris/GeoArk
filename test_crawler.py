import unittest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import WebDriverException
from crawler import Crawler
from db_manager import DBManager

class TestCrawler(unittest.TestCase):

    def setUp(self):
        """Set up a mock DB manager and other components."""
        self.mock_db_manager = MagicMock(spec=DBManager)
        self.start_url = 'http://mocksite.com/data'

    @patch('crawler.Crawler._init_driver')
    def test_crawl_flow(self, mock_init_driver):
        """Test the basic crawling process with Selenium."""
        # --- Mock Driver Setup ---
        mock_driver = MagicMock()
        mock_init_driver.return_value = mock_driver

        # --- Mock a simple two-page website ---
        page1_url = self.start_url
        page2_url = 'http://mocksite.com/data/page2'

        page1_html = """
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

        # Configure mock_driver.get to set page_source based on URL
        def get_side_effect(url):
            if url == page1_url:
                mock_driver.page_source = page1_html
            elif url == page2_url:
                mock_driver.page_source = page2_html
            else:
                mock_driver.page_source = "<html></html>"

        mock_driver.get.side_effect = get_side_effect

        # --- Initialize and run the crawler ---
        crawler = Crawler(start_url=page1_url, db_manager=self.mock_db_manager, max_pages=2)
        crawler.crawl()

        # --- Assertions ---
        # 1. Assert that driver.get was called for both pages
        self.assertEqual(mock_driver.get.call_count, 2)
        mock_driver.get.assert_any_call(page1_url)
        mock_driver.get.assert_any_call(page2_url)

        # 2. Assert that the DB manager's add_or_update method was called
        self.assertEqual(self.mock_db_manager.add_or_update_dataset.call_count, 2)

        # 3. Check data passed to DB manager
        first_call_args = self.mock_db_manager.add_or_update_dataset.call_args_list[0].args[0]
        self.assertEqual(first_call_args['dataset_title'], 'Page 1')
        self.assertEqual(first_call_args['resource_type'], 'CSV')

        second_call_args = self.mock_db_manager.add_or_update_dataset.call_args_list[1].args[0]
        self.assertEqual(second_call_args['dataset_title'], 'Page 2')
        self.assertEqual(second_call_args['resource_type'], 'JSON')

        # 4. Assert driver was shut down
        mock_driver.quit.assert_called_once()

    @patch('crawler.Crawler._init_driver')
    def test_max_pages_limit(self, mock_init_driver):
        """Test that crawling stops when max_pages is reached."""
        # --- Mock Driver Setup ---
        mock_driver = MagicMock()
        mock_init_driver.return_value = mock_driver

        # Mock a site with many links
        mock_driver.page_source = """
        <html>
            <a href="/data/1">1</a> <a href="/data/2">2</a> <a href="/data/3">3</a>
        </html>
        """

        # --- Initialize and run the crawler ---
        crawler = Crawler(start_url=self.start_url, db_manager=self.mock_db_manager, max_pages=2)
        crawler.crawl()

        # driver.get should only be called twice (start_url + one from the page)
        self.assertEqual(mock_driver.get.call_count, 2)
        mock_driver.quit.assert_called_once()

    @patch('crawler.Crawler._init_driver')
    def test_webdriver_error_handling(self, mock_init_driver):
        """Test that the crawler handles WebDriver errors gracefully."""
        # --- Mock Driver Setup ---
        mock_driver = MagicMock()
        mock_init_driver.return_value = mock_driver

        # Configure the mock to raise an exception
        mock_driver.get.side_effect = WebDriverException("Test Selenium Error")

        # --- Initialize and run the crawler ---
        crawler = Crawler(start_url=self.start_url, db_manager=self.mock_db_manager)
        crawler.crawl()

        # The DB manager should not have been called
        self.mock_db_manager.add_or_update_dataset.assert_not_called()
        # The driver should still be shut down
        mock_driver.quit.assert_called_once()


if __name__ == '__main__':
    unittest.main()