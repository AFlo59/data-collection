import os
import sys
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_extraction.spiders.spell_scraper import SpellScraper
from utils.setup_logger import setup_logger

def main():
    """Main function to run the spell scraper"""
    # Setup logging
    logger = setup_logger('spell_scraping_process', 'data-extraction')
    
    try:
        logger.info("=== Starting Spell Scraping Process ===")
        
        # Initialize and run scraper
        scraper = SpellScraper()
        scraper.run()
        
        logger.info("=== Spell Scraping Process Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Fatal error in spell scraping process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    load_dotenv()
    main()