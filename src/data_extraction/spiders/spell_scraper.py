import os
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from utils.setup_logger import setup_logger
import json

class SpellScraper:
    """
    Scraper for D&D 5e spells from 5e.tools
    """
    
    def __init__(self):
        """Initialize the spell scraper with configuration and logging"""
        load_dotenv()
        
        # Initialize logger
        self.logger = setup_logger('spells', 'data-extraction')
        self.url = os.getenv('SCRAPING_SPELLS_URL')
        self.output_dir = os.getenv('SCRAPING_SPELLS_DIR')
        
        # Ensure output directory exists
        try:
            os.makedirs(self.output_dir, exist_ok=True)
            self.logger.debug(f"Output directory created: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"Failed to create output directory: {str(e)}")
            raise

    def setup_driver(self):
        """Configure and return a webdriver instance"""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            driver = webdriver.Chrome(options=options)
            self.logger.debug("Webdriver initialized successfully")
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup webdriver: {str(e)}")
            raise

    def get_spell_list(self, driver):
        """Get list of all spells from the main page"""
        try:
            self.logger.info("Starting to fetch spell list")
            driver.get(self.url)
            
            # Wait for the spell list to load
            spell_list = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#list.list.list--stats"))
            )
            
            # Get all spell rows
            spell_rows = spell_list.find_elements(By.CSS_SELECTOR, "div.lst__row.ve-flex-col")
            
            spells_data = []
            for row in spell_rows:
                try:
                    link = row.find_element(By.CSS_SELECTOR, "a.lst__row-inner")
                    spell_name = link.text
                    spell_href = link.get_attribute('href')
                    spells_data.append({
                        'name': spell_name,
                        'href': spell_href
                    })
                except Exception as e:
                    self.logger.warning(f"Failed to process spell row: {str(e)}")
                    continue
            
            self.logger.info(f"Found {len(spells_data)} spells")
            return spells_data
            
        except Exception as e:
            self.logger.error(f"Failed to get spell list: {str(e)}")
            raise

    def get_spell_details(self, driver, spell):
        """Get detailed information for a specific spell"""
        try:
            self.logger.debug(f"Fetching details for spell: {spell['name']}")
            driver.get(spell['href'])
            
            # Wait for content to load
            content = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div#wrp-pagecontent table#pagecontent"))
            )
            
            # Extract spell details from table rows
            details = {}
            rows = content.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                try:
                    # Process each row to extract information
                    # This will vary based on the specific data you want to extract
                    pass
                except Exception as e:
                    self.logger.warning(f"Failed to process row for spell {spell['name']}: {str(e)}")
                    continue
                    
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get details for spell {spell['name']}: {str(e)}")
            raise

    def save_data(self, data, filename):
        """Save scraped data to JSON file"""
        try:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Data saved successfully to {filepath}")
        except Exception as e:
            self.logger.error(f"Failed to save data: {str(e)}")
            raise

    def run(self):
        """Main execution method"""
        self.logger.info("Starting spell scraping process")
        driver = None
        try:
            driver = self.setup_driver()
            
            # Get list of all spells
            spells = self.get_spell_list(driver)
            
            # Get details for each spell
            detailed_spells = []
            for spell in spells:
                details = self.get_spell_details(driver, spell)
                if details:  # Only add if we got details
                    detailed_spells.append(details)
            
            # Save all data to a single spells.json file
            combined_data = {
                "spell_list": spells,
                "spell_details": detailed_spells
            }
            self.save_data(combined_data, 'spells.json')
            self.logger.info("Spell scraping completed successfully")
            
        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {str(e)}")
            raise
        finally:
            if driver:
                driver.quit()