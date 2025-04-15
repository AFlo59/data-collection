import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.data_extraction.spiders import BestiaryScraper
from src.utils.setup_logger import setup_logger

def main():
    """
    Main function to run the bestiary scraper
    """
    # Setup logging
    logger = setup_logger('bestiary_scraping_process', 'data-extraction')
    
    try:
        logger.info("=== Starting Bestiary Scraping Process ===")
        
        # Initialize and run the scraper
        scraper = BestiaryScraper()
        scraper.run()
        
        logger.info("=== Bestiary Scraping Process Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Fatal error in bestiary scraping process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main function
    main() 