import unittest
import os
import sqlite3
from db_manager import DBManager
import datetime

class TestDBManager(unittest.TestCase):

    def setUp(self):
        """Set up a temporary database for testing."""
        self.db_path = 'test_open_data.db'
        self.db_manager = DBManager(db_path=self.db_path)
        self.db_manager.initialize_db()

    def tearDown(self):
        """Clean up the temporary database."""
        self.db_manager.close()
        os.remove(self.db_path)

    def test_initialization(self):
        """Test that the database and table are created."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='datasets';")
        self.assertIsNotNone(cursor.fetchone())
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_download_link';")
        self.assertIsNotNone(cursor.fetchone())
        conn.close()

    def test_add_and_update_dataset(self):
        """Test adding a new dataset and updating it."""
        dataset1 = {
            'dataset_title': 'Test Dataset 1',
            'source_url': 'http://example.com/page1',
            'download_link': 'http://example.com/data1.csv',
            'resource_type': 'CSV',
            'freshness_score': 80,
            'source_domain': 'example.com'
        }

        # Add the dataset
        self.db_manager.add_or_update_dataset(dataset1)

        # Verify it was added
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE download_link=?", (dataset1['download_link'],))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        self.assertEqual(result[1], dataset1['dataset_title'])
        self.assertEqual(result[5], dataset1['freshness_score'])

        # Update the dataset
        dataset1_updated = {
            'dataset_title': 'Test Dataset 1 Updated', # Title SHOULD change now
            'source_url': 'http://example.com/page1_updated',
            'download_link': 'http://example.com/data1.csv', # This is the key
            'resource_type': 'CSV_UPDATED',
            'freshness_score': 95, # Score should change
            'source_domain': 'example.com_updated'
        }
        self.db_manager.add_or_update_dataset(dataset1_updated)

        # Verify it was updated
        cursor.execute("SELECT * FROM datasets WHERE download_link=?", (dataset1['download_link'],))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        # All fields should be updated now
        self.assertEqual(result[1], dataset1_updated['dataset_title'])
        self.assertEqual(result[2], dataset1_updated['source_url'])
        self.assertEqual(result[4], dataset1_updated['resource_type'])
        self.assertEqual(result[5], dataset1_updated['freshness_score'])
        self.assertEqual(result[7], dataset1_updated['source_domain'])

        conn.close()

    def test_link_exists(self):
        """Test the link_exists method."""
        link = 'http://example.com/unique_data.zip'
        self.assertFalse(self.db_manager.link_exists(link))

        dataset = {
            'dataset_title': 'Unique Dataset',
            'source_url': 'http://example.com/page_unique',
            'download_link': link,
            'resource_type': 'ZIP',
            'freshness_score': 100,
            'source_domain': 'example.com'
        }
        self.db_manager.add_or_update_dataset(dataset)

        self.assertTrue(self.db_manager.link_exists(link))
        self.assertFalse(self.db_manager.link_exists('http://example.com/other.zip'))


if __name__ == '__main__':
    unittest.main()