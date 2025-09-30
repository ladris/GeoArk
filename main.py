import argparse
from db_manager import DBManager
from crawler import Crawler
from parser import load_urls_from_file

def main():
    """
    Main execution function.
    """
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description="A simple Python web crawler to discover and index open data.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--url',
        type=str,
        help="The root URL of the open data portal to crawl.\nExample: --url https://data.cityofdenver.org/datasets"
    )
    group.add_argument(
        '--load',
        type=str,
        help="Path to a text or CSV file containing a list of URLs to scan."
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
    print(f"Database file: {args.db_file}")
    print("-------------------------")

    # 1. Initialize the Database Manager
    db_manager = DBManager(db_path=args.db_file)
    db_manager.initialize_db()

    # Determine which URLs to process
    urls_to_process = []
    if args.load:
        urls_to_process = load_urls_from_file(args.load)
        if not urls_to_process:
            print("No valid URLs found in the specified file. Exiting.")
            db_manager.close()
            return
    else:
        # If --url is used, it's a list with one item
        urls_to_process.append(args.url)

    total_pages_crawled = 0
    total_datasets_found = 0
    interrupted = False

    # Process each URL
    for i, start_url in enumerate(urls_to_process):
        if len(urls_to_process) > 1:
            print(f"\n--- Starting process for URL {i + 1}/{len(urls_to_process)}: {start_url} ---")
        else:
            print(f"Starting crawl at: {start_url}")

        # 2. Initialize the Crawler
        crawler = Crawler(
            start_url=start_url,
            db_manager=db_manager,
            max_pages=args.max_pages
        )

        # 3. Start the crawl
        log_id = None
        status = "completed"
        try:
            log_id = db_manager.start_crawl_log(start_url)
            crawler.crawl()
        except KeyboardInterrupt:
            print("\nCrawling interrupted by user. Stopping all processes.")
            status = "interrupted"
            interrupted = True # Flag to stop processing more URLs
        finally:
            # 4. Log the outcome of this specific crawl
            if log_id is not None:
                print("Logging crawl session...")
                db_manager.end_crawl_log(
                    log_id=log_id,
                    pages_crawled=crawler.pages_crawled,
                    datasets_found=crawler.datasets_found,
                    status=status
                )
            # Aggregate stats
            total_pages_crawled += crawler.pages_crawled
            total_datasets_found += crawler.datasets_found

        if interrupted:
            break

    print("\n--- Crawl Summary ---")
    if args.load:
        print(f"Processed {len(urls_to_process)} URLs from {args.load}.")
    print(f"Total pages crawled across all sessions: {total_pages_crawled}")
    print(f"Total datasets found or updated: {total_datasets_found}")
    print("--------------------")


    print("Closing database connection.")
    db_manager.close()
    print("Done.")

if __name__ == "__main__":
    main()