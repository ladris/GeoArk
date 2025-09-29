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
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_dataset_location';")
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
            'dataset_title': 'Test Dataset 1 Updated', # Title shouldn't change on conflict
            'source_url': 'http://example.com/page1',
            'download_link': 'http://example.com/data1.csv',
            'resource_type': 'CSV',
            'freshness_score': 95, # Score should change
            'source_domain': 'example.com'
        }
        self.db_manager.add_or_update_dataset(dataset1_updated)

        # Verify it was updated
        cursor.execute("SELECT * FROM datasets WHERE download_link=?", (dataset1['download_link'],))
        result = cursor.fetchone()
        self.assertIsNotNone(result)
        # Title remains the same because of how INSERT ON CONFLICT works
        self.assertEqual(result[1], dataset1['dataset_title'])
        self.assertEqual(result[5], dataset1_updated['freshness_score'])

        conn.close()

if __name__ == '__main__':
    unittest.main()