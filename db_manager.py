import sqlite3
import datetime

class DBManager:
    """Handles all interactions with the local SQLite database."""

    def __init__(self, db_path='open_data.db'):
        """
        Initializes the DBManager.

        Args:
            db_path (str): The path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def initialize_db(self):
        """
        Creates the database schema if it doesn't already exist.
        """
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_title TEXT NOT NULL,
            source_url TEXT NOT NULL,
            download_link TEXT NOT NULL,
            resource_type TEXT,
            freshness_score INTEGER,
            last_crawled_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_domain TEXT NOT NULL
        );
        ''')
        self.cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_dataset_location
        ON datasets (source_url, download_link);
        ''')
        self.conn.commit()

    def add_or_update_dataset(self, dataset_data):
        """
        Adds a new dataset to the database or updates an existing one.

        Args:
            dataset_data (dict): A dictionary containing the dataset information.
                                 Expected keys: 'dataset_title', 'source_url',
                                 'download_link', 'resource_type',
                                 'freshness_score', 'source_domain'.
        """
        sql = '''
        INSERT INTO datasets (
            dataset_title, source_url, download_link, resource_type,
            freshness_score, source_domain, last_crawled_timestamp
        ) VALUES (:dataset_title, :source_url, :download_link, :resource_type,
                  :freshness_score, :source_domain, :last_crawled_timestamp)
        ON CONFLICT(source_url, download_link) DO UPDATE SET
            freshness_score = excluded.freshness_score,
            last_crawled_timestamp = excluded.last_crawled_timestamp;
        '''
        dataset_data['last_crawled_timestamp'] = datetime.datetime.now()
        self.cursor.execute(sql, dataset_data)
        self.conn.commit()

    def close(self):
        """Closes the database connection."""
        self.conn.close()