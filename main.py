import argparse
from db_manager import DBManager
from crawler import Crawler

def main():
    """
    Main execution function.
    """
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="A simple Python web crawler to discover and index open data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--url',
        type=str,
        required=True,
        help="The root URL of the open data portal to crawl.\nExample: --url https://data.cityofdenver.org/datasets"
    )
    parser.add_argument(
        '--max_pages',
        type=int,
        default=100,
        help="The maximum number of pages to crawl. Default is 100."
    )
    parser.add_argument(
        '--db_file',
        type=str,
        default='open_data.db',
        help="Path to the SQLite database file. Default is 'open_data.db'."
    )
    args = parser.parse_args()

    print("--- Open Data Crawler ---")
    print(f"Starting crawl at: {args.url}")
    print(f"Database file: {args.db_file}")
    print("-------------------------")

    # 1. Initialize the Database Manager
    db_manager = DBManager(db_path=args.db_file)
    db_manager.initialize_db()

    # 2. Initialize the Crawler
    crawler = Crawler(
        start_url=args.url,
        db_manager=db_manager,
        max_pages=args.max_pages
    )

    # 3. Start the crawl
    log_id = None
    status = "completed"
    try:
        log_id = db_manager.start_crawl_log(args.url)
        crawler.crawl()
    except KeyboardInterrupt:
        print("\nCrawling interrupted by user.")
        status = "interrupted"
    finally:
        # 4. Clean up
        if log_id is not None:
            print("Logging crawl session...")
            db_manager.end_crawl_log(
                log_id=log_id,
                pages_crawled=crawler.pages_crawled,
                datasets_found=crawler.datasets_found,
                status=status
            )

        print("Closing database connection.")
        db_manager.close()
        print("Done.")

if __name__ == "__main__":
    main()