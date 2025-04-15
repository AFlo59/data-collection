import os
import json
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, TimeoutError, Response
from src.utils.setup_logger import setup_logger

class BestiaryScraper:
    def __init__(self):
        """Initialize the bestiary scraper with configuration and logging"""
        load_dotenv()
        
        # Initialize logger
        self.logger = setup_logger('bestiary', 'data-extraction')
        self.base_url = os.getenv('SCRAPING_BASE_URL', 'https://5e.tools/')
        self.bestiary_url = os.getenv('SCRAPING_BESTIARY_URL', 'https://5e.tools/bestiary.html')
        self.output_dir = os.getenv('SCRAPING_BESTIARY_DIR', './data/scraping/monsters/')
        
        # Ensure output directory exists
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.debug(f"Output directory created: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            raise

    def wait_for_critical_scripts(self, page: Page) -> None:
        """Wait for critical JavaScript files to load"""
        try:
            self.logger.info("Waiting for critical scripts to load...")
            
            # List of critical scripts that need to be loaded
            critical_scripts = [
                'js/parser.js',
                'js/utils.js',
                'lib/jquery.js',
                'js/utils-ui.js',
                'js/bestiary.js'
            ]
            
            # First wait for all script tags to be present
            for script in critical_scripts:
                self.logger.debug(f"Waiting for {script}...")
                page.wait_for_selector(f"script[src*='{script}']", state='attached', timeout=30000)
            
            # Wait for initial document ready state
            page.wait_for_load_state('domcontentloaded')
            
            # Wait for key objects to be defined
            page.wait_for_function("""
                () => {
                    return typeof jQuery !== 'undefined' &&
                           typeof Parser !== 'undefined' &&
                           typeof Utils !== 'undefined';
                }
            """, timeout=60000)
            
            self.logger.info("Critical scripts loaded")
            
        except Exception as e:
            self.logger.error(f"Error waiting for scripts: {str(e)}")
            raise

    def extract_monster_data(self, page: Page) -> Dict[str, Any]:
        """Extract monster data from the page"""
        try:
            # Wait for the monster data to be loaded
            self.logger.info("Extracting monster data...")
            
            # Get the monster data from the JavaScript variables
            monster_data = page.evaluate("""
                () => {
                    const monsters = window.monsters || [];
                    return monsters.map(mon => ({
                        name: mon.name,
                        source: mon.source,
                        type: mon.type,
                        size: mon.size,
                        alignment: mon.alignment,
                        ac: mon.ac,
                        hp: mon.hp,
                        speed: mon.speed,
                        str: mon.str,
                        dex: mon.dex,
                        con: mon.con,
                        int: mon.int,
                        wis: mon.wis,
                        cha: mon.cha,
                        save: mon.save,
                        skill: mon.skill,
                        vulnerable: mon.vulnerable,
                        resist: mon.resist,
                        immune: mon.immune,
                        conditionImmune: mon.conditionImmune,
                        senses: mon.senses,
                        languages: mon.languages,
                        cr: mon.cr,
                        trait: mon.trait,
                        action: mon.action,
                        reaction: mon.reaction,
                        legendary: mon.legendary,
                        legendaryGroup: mon.legendaryGroup,
                        variant: mon.variant,
                        tokenURL: mon.tokenURL,
                        page: mon.page
                    }));
                }
            """)
            
            self.logger.info(f"Extracted data for {len(monster_data)} monsters")
            return monster_data
            
        except Exception as e:
            self.logger.error(f"Error extracting monster data: {str(e)}")
            return []

    def scrape_monsters(self, limit: Optional[int] = None) -> None:
        """
        Main method to scrape monsters by simulating user behavior:
        1. Open page
        2. Accept cookies
        3. Wait for critical scripts
        4. Extract monster data
        5. Save all data
        """
        self.logger.info(f"Starting monster scraping from {self.bestiary_url}")
        
        try:
            with sync_playwright() as p:
                # Configure browser with realistic settings
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--window-size=1920,1080'
                    ]
                )
                
                # Create a realistic browser context
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='Europe/Paris',
                    color_scheme='dark'
                )
                
                # Add anti-bot detection
                context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                """)
                
                page = context.new_page()
                
                # Add realistic headers
                page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                })

                # Load the page
                self.logger.info("Loading bestiary page...")
                response = page.goto(
                    self.bestiary_url,
                    timeout=120000,
                    wait_until='domcontentloaded'
                )
                
                if not response or not response.ok:
                    raise Exception(f"Failed to load page: {response.status if response else 'No response'}")

                # Wait for critical scripts
                self.wait_for_critical_scripts(page)
                
                # Extract monster data
                monster_data = self.extract_monster_data(page)
                
                if limit:
                    monster_data = monster_data[:limit]
                
                # Save all data
                output_file = os.path.join(self.output_dir, "monsters.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(monster_data, f, ensure_ascii=False, indent=4)

                self.logger.info(f"Scraping completed. Saved {len(monster_data)} monsters to {output_file}")
                browser.close()

        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {str(e)}")
            raise

    def run(self, limit: Optional[int] = None) -> None:
        """Run the scraping process with error handling"""
        try:
            self.scrape_monsters(limit)
        except Exception as e:
            self.logger.error(f"Failed to run bestiary scraper: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = BestiaryScraper()
    # By default, scrape all monsters. You can pass a limit to test with fewer monsters
    scraper.run(limit=None)  # For testing, you might want to use limit=10
