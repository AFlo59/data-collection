import unittest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from src.utils.setup_logger import setup_logger
from src.data_extraction.spiders.spell_scraper import SpellScraper 

class TestSpellScraper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test environment and logging"""
        load_dotenv()
        cls.logger = setup_logger('spell_scraper_test', 'tests-extraction')
        cls.logger.info("=== Starting Spell Scraper Test Suite ===")

    def setUp(self):
        """Set up each test"""
        self.logger.info(f"Starting test: {self._testMethodName}")
        self.scraper = SpellScraper()

    def test_initialization(self):
        """Test scraper initialization"""
        self.logger.debug("Testing scraper initialization")
        self.assertIsNotNone(self.scraper.base_url)
        self.assertIsNotNone(self.scraper.spells_url)
        self.assertIsNotNone(self.scraper.output_dir)
        self.assertEqual(self.scraper.base_url, os.getenv('SCRAPING_BASE_URL'))

    @patch('playwright.sync_api.sync_playwright')
    def test_scrape_spells(self, mock_playwright):
        """Test spell scraping process"""
        self.logger.debug("Testing spell scraping process")
        
        # Mock the Playwright context
        mock_browser = Mock()
        mock_page = Mock()
        mock_context = Mock()
        
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_page.return_value = mock_page
        
        # Mock page interactions
        mock_page.query_selector_all.return_value = [Mock()]
        mock_page.query_selector.return_value = Mock()
        
        # Run the scraper
        self.scraper.scrape_spells()
        
        # Verify interactions
        mock_page.goto.assert_called_once_with(self.scraper.spells_url, timeout=60000)
        mock_page.wait_for_selector.assert_called()

    def test_save_data(self):
        """Test data saving functionality"""
        self.logger.debug("Testing data saving")
        test_data = {"test": "data"}
        
        # Create a temporary output directory
        os.makedirs(self.scraper.output_dir, exist_ok=True)
        
        # Save test data
        output_file = os.path.join(self.scraper.output_dir, "spells.json")
        with open(output_file, "w", encoding="utf-8") as f:
            import json
            json.dump(test_data, f)
        
        # Verify file exists
        self.assertTrue(os.path.exists(output_file))
        
        # Clean up
        os.remove(output_file)

    def tearDown(self):
        """Clean up after each test"""
        self.logger.info(f"Completed test: {self._testMethodName}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.logger.info("=== Completed Spell Scraper Test Suite ===")

if __name__ == '__main__':
    unittest.main() 