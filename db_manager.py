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
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_url TEXT NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME,
            pages_crawled INTEGER,
            datasets_found INTEGER,
            status TEXT NOT NULL
        );
        ''')
        self.conn.commit()

    def start_crawl_log(self, start_url):
        """
        Logs the start of a new crawl session.

        Args:
            start_url (str): The starting URL for the crawl.

        Returns:
            int: The ID of the new crawl log entry.
        """
        sql = '''
        INSERT INTO crawl_logs (start_url, start_time, status)
        VALUES (?, ?, ?);
        '''
        start_time = datetime.datetime.now()
        self.cursor.execute(sql, (start_url, start_time, 'in_progress'))
        self.conn.commit()
        return self.cursor.lastrowid

    def end_crawl_log(self, log_id, pages_crawled, datasets_found, status):
        """
        Logs the completion of a crawl session.

        Args:
            log_id (int): The ID of the crawl log entry to update.
            pages_crawled (int): The total number of pages crawled.
            datasets_found (int): The total number of datasets found.
            status (str): The final status of the crawl ('completed' or 'interrupted').
        """
        sql = '''
        UPDATE crawl_logs
        SET end_time = ?, pages_crawled = ?, datasets_found = ?, status = ?
        WHERE id = ?;
        '''
        end_time = datetime.datetime.now()
        self.cursor.execute(sql, (end_time, pages_crawled, datasets_found, status, log_id))
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