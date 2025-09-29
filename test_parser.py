import unittest
from bs4 import BeautifulSoup
from parser import Parser

class TestParser(unittest.TestCase):

    def setUp(self):
        """Set up the Parser instance."""
        self.base_url = 'http://testdomain.com'
        self.parser = Parser(base_url=self.base_url)

    def test_find_title(self):
        """Test the title extraction heuristics by calling the private method."""
        html_h1 = "<html><body><h1>Main Title</h1></body></html>"
        html_h2 = '<html><body><section><h2>Second Title</h2></section></body></html>'
        html_class = '<html><body><div class="dataset-heading">Class Title</div></body></html>'
        html_none = "<html><body><p>No title here</p></body></html>"

        soup_h1 = BeautifulSoup(html_h1, 'html.parser')
        soup_h2 = BeautifulSoup(html_h2, 'html.parser')
        soup_class = BeautifulSoup(html_class, 'html.parser')
        soup_none = BeautifulSoup(html_none, 'html.parser')

        self.assertEqual(self.parser._find_title(soup_h1), 'Main Title')
        self.assertEqual(self.parser._find_title(soup_h2), 'Second Title')
        self.assertEqual(self.parser._find_title(soup_class), 'Class Title')
        self.assertIsNone(self.parser._find_title(soup_none))

    def test_find_download_links(self):
        """Test the download link extraction logic."""
        html = """
        <html><body>
            <h1>Test Data</h1>
            <a href="http://testdomain.com/data.csv">Download CSV</a>
            <a href="/data/archive.zip">Zipped Data</a>
            <a href="https://otherdomain.com/data.json">External JSON</a>
            <a href="mailto:a@b.com">Email</a>
            <a href="/page2">Next Page</a>
            <a href="http://testdomain.com/api/endpoint">API Endpoint</a>
            <a class="btn" href="download?id=123">Download Button</a>
        </body></html>
        """
        page_url = self.base_url + "/page1"
        soup = BeautifulSoup(html, 'html.parser')
        links = self.parser._find_download_links(soup, page_url)

        self.assertEqual(len(links), 5)

        urls = {d['url'] for d in links}
        types = {d['type'] for d in links}

        self.assertIn('http://testdomain.com/data.csv', urls)
        self.assertIn('http://testdomain.com/data/archive.zip', urls)
        self.assertIn('https://otherdomain.com/data.json', urls)
        self.assertIn('http://testdomain.com/api/endpoint', urls)
        self.assertIn('http://testdomain.com/download?id=123', urls)

        self.assertIn('CSV', types)
        self.assertIn('ZIP', types)
        self.assertIn('API', types)
        self.assertIn('JSON', types)
        self.assertIn('Unknown', types)


    def test_discover_new_links(self):
        """Test the discovery of new, relevant links to crawl."""
        html = """
        <html><body>
            <a href="/datasets/page1">Dataset Page 1</a>
            <a href="http://testdomain.com/catalog/all">Full Catalog</a>
            <a href="http://external.com/other">External Link</a>
            <a href="#section2">Anchor Link</a>
            <a href="/about-us">Irrelevant Page</a>
        </body></html>
        """
        page_url = self.base_url
        soup = BeautifulSoup(html, 'html.parser')
        new_links = self.parser._discover_new_links(soup, page_url)

        self.assertEqual(len(new_links), 2)
        self.assertIn('http://testdomain.com/datasets/page1', new_links)
        self.assertIn('http://testdomain.com/catalog/all', new_links)

    def test_date_clue_extraction(self):
        """Test the extraction of text snippets containing date-related keywords."""
        html = """
        <html><body>
            <p>This dataset was last updated on March 5, 2023.</p>
            <div><span>Published: 2024-01-01</span></div>
            <p>This is a long paragraph with the word update in it, but it's probably not a useful date clue because it is far too long and contains a lot of other text that would confuse the parser and make it difficult to extract the correct date information reliably.</p>
            <p>Release Date: Jan 2022</p>
        </body></html>
        """
        soup = BeautifulSoup(html, 'html.parser')
        clues = self.parser._find_date_clues(soup)

        self.assertEqual(len(clues), 3)
        self.assertIn('This dataset was last updated on March 5, 2023.', clues)
        self.assertIn('Published: 2024-01-01', clues)
        self.assertIn('Release Date: Jan 2022', clues)

if __name__ == '__main__':
    unittest.main()