import os
import sys
import logging
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction.spiders.spell_scraper import SpellScraper
from utils.setup_logger import setup_logger

def main():
    """
    Main function to run the spell scraper
    
    This script:
    1. Sets up logging
    2. Initializes the scraper
    3. Runs the scraping process
    4. Handles any errors
    """
    # Setup logging
    logger = setup_logger('spell_scraping', 'data-extraction')
    
    try:
        logger.info("Initializing spell scraping process")
        
        # Initialize and run scraper
        scraper = SpellScraper()
        scraper.run()
        
        logger.info("Spell scraping process completed successfully")
        
    except Exception as e:
        logger.error(f"Fatal error in spell scraping process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_dotenv()
    main()