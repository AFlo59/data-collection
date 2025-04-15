import os
import sys
from dotenv import load_dotenv

# Add the src directory to the path to allow imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.data_extraction.spiders.spell_scraper import SpellScraper
from src.utils.setup_logger import setup_logger

def main():
    """Main function to run the spell scraper"""
    # Setup logging
    logger = setup_logger('spell_scraping_process', 'data-extraction')
    
    try:
        logger.info("=== Starting Spell Scraping Process ===")
        
        # Initialize and run scraper
        scraper = SpellScraper()
        
        # Get limit from environment or default to None (scrape all)
        limit_str = os.getenv('SCRAPING_SPELL_LIMIT')
        limit = int(limit_str) if limit_str and limit_str.isdigit() else None
        
        if limit:
            logger.info(f"Running with limit of {limit} spells")
        else:
            logger.info("Running without limit (scraping all spells)")
            
        scraper.run(limit=limit)
        
        logger.info("=== Spell Scraping Process Completed Successfully ===")
        
    except Exception as e:
        logger.error(f"Fatal error in spell scraping process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run the main function
    main()
