import os
import json
import time
import random
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, TimeoutError, Response
from src.utils.setup_logger import setup_logger

class SpellScraper:
    def __init__(self):
        """Initialize the spell scraper with configuration and logging"""
        load_dotenv()
        
        # Initialize logger
        self.logger = setup_logger('spell', 'data-extraction')
        self.base_url = os.getenv('SCRAPING_BASE_URL', 'https://5e.tools/')
        self.spell_url = os.getenv('SCRAPING_SPELL_URL', 'https://5e.tools/spells.html')
        self.output_dir = os.getenv('SCRAPING_SPELL_DIR', './data/scraping/spells/')
        
        # Ensure output directory exists
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.debug(f"Output directory created: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            raise
    
    def debug_page(self, page: Page):
        """Debug the page"""
        self.logger.debug(f"Page content: {page.content()}")

    def debug_page_state(self, page: Page) -> None:
        """Debug the current state of the page"""
        try:
            # Get page content
            content = page.content()
            self.logger.debug("=== Page Content ===")
            self.logger.debug(content[:1000] + "...")  # First 1000 chars
            
            # Check JavaScript variables
            js_state = page.evaluate("""() => {
                return {
                    spellList: typeof spellList,
                    spellData: typeof spellData,
                    windowVars: Object.keys(window).filter(k => k.startsWith('spell')),
                    documentReady: document.readyState,
                    scriptsLoaded: Array.from(document.scripts).map(s => s.src).filter(Boolean)
                };
            }""")
            
            self.logger.debug("=== JavaScript State ===")
            self.logger.debug(f"spellList type: {js_state['spellList']}")
            self.logger.debug(f"spellData type: {js_state['spellData']}")
            self.logger.debug(f"Window variables: {js_state['windowVars']}")
            self.logger.debug(f"Document ready state: {js_state['documentReady']}")
            self.logger.debug(f"Loaded scripts: {js_state['scriptsLoaded']}")
            
        except Exception as e:
            self.logger.error(f"Error during page debug: {str(e)}")

    def wait_for_js_data(self, page: Page, timeout: int = 120) -> bool:
        """
        Wait for JavaScript data to be available on the page.
        
        Args:
            page: The Playwright page object
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if data is available, False otherwise
        """
        try:
            # Wait for the spellList variable to be defined and populated
            page.wait_for_function("""
                () => {
                    return typeof spellList !== 'undefined' && 
                           spellList && 
                           spellList.length > 0 &&
                           typeof spellData !== 'undefined' &&
                           spellData &&
                           Object.keys(spellData).length > 0;
                }
            """, timeout=timeout * 1000)
            return True
        except TimeoutError:
            self.logger.warning("Timeout waiting for JavaScript data to load")
            return False
        except Exception as e:
            self.logger.error(f"Error waiting for JavaScript data: {str(e)}")
            return False

    def handle_cookie_consent(self, page: Page) -> None:
        """Handle the cookie consent banner"""
        try:
            self.logger.info("Looking for cookie consent banner...")
            
            # Wait for the cookie consent iframe or banner
            consent_frame = None
            try:
                # Look for common consent frame names/ids
                for frame_selector in ['#consent', '#cookie-consent', 'iframe[id*="cookie"]', 'iframe[title*="cookie"]']:
                    consent_frame = page.frame_locator(frame_selector).first
                    if consent_frame:
                        break
            except:
                pass

            # If we found a frame, look for buttons there, otherwise look in main page
            target = consent_frame if consent_frame else page
            
            # Common consent button selectors
            accept_selectors = [
                'text="Accept all"',
                'text="Accept"',
                'text="Agree"',
                '[aria-label*="Accept"]',
                'button:has-text("Accept")',
                'button:has-text("Agree")',
                '[class*="accept"]',
                '[id*="accept"]'
            ]
            
            for selector in accept_selectors:
                try:
                    if target.locator(selector).count() > 0:
                        self.logger.info(f"Found accept button with selector: {selector}")
                        target.locator(selector).click(force=True)
                        page.wait_for_timeout(2000)
                        return
                except Exception as e:
                    continue
            
            self.logger.warning("Could not find or click the accept button")
            
        except Exception as e:
            self.logger.error(f"Error handling cookie consent: {str(e)}")

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
                'js/spells.js'
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

    def extract_spell_data(self, page: Page) -> Dict[str, Any]:
        """Extract spell data from the page"""
        try:
            # Wait for the spell data to be loaded
            self.logger.info("Extracting spell data...")
            
            # Get the spell data from the JavaScript variables
            spell_data = page.evaluate("""
                () => {
                    const spells = window.spellList || [];
                    return spells.map(spell => ({
                        name: spell.name,
                        source: spell.source,
                        level: spell.level,
                        school: spell.school,
                        time: spell.time,
                        range: spell.range,
                        components: spell.components,
                        duration: spell.duration,
                        classes: spell.classes,
                        entries: spell.entries,
                        damageInflict: spell.damageInflict,
                        savingThrow: spell.savingThrow,
                        opposedCheck: spell.opposedCheck,
                        meta: spell.meta,
                        page: spell.page
                    }));
                }
            """)
            
            self.logger.info(f"Extracted data for {len(spell_data)} spells")
            return spell_data
            
        except Exception as e:
            self.logger.error(f"Error extracting spell data: {str(e)}")
            return []

    def scrape_spells(self, limit: Optional[int] = None) -> None:
        """
        Main method to scrape spells by simulating user behavior:
        1. Open page
        2. Wait for critical scripts
        3. Extract spell data
        4. Save all data
        """
        self.logger.info(f"Starting spell scraping from {self.spell_url}")
        
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
                self.logger.info("Loading spells page...")
                response = page.goto(
                    self.spell_url,
                    timeout=120000,
                    wait_until='domcontentloaded'
                )
                
                if not response or not response.ok:
                    raise Exception(f"Failed to load page: {response.status if response else 'No response'}")

                # Wait for critical scripts
                self.wait_for_critical_scripts(page)
                
                # Extract spell data
                spell_data = self.extract_spell_data(page)
                
                if limit:
                    spell_data = spell_data[:limit]
                
                # Save all data
                output_file = os.path.join(self.output_dir, "spells.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(spell_data, f, ensure_ascii=False, indent=4)

                self.logger.info(f"Scraping completed. Saved {len(spell_data)} spells to {output_file}")
                browser.close()

        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {str(e)}")
            raise

    def run(self, limit: Optional[int] = None) -> None:
        """Run the scraping process with error handling"""
        try:
            self.scrape_spells(limit)
        except Exception as e:
            self.logger.error(f"Failed to run spell scraper: {str(e)}")
            raise

if __name__ == "__main__":
    scraper = SpellScraper()
    # By default, scrape all spells. You can pass a limit to test with fewer spells
    scraper.run(limit=None)  # For testing, you might want to use limit=10

