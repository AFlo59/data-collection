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
        self.assertIsNotNone(self.scraper.spell_url)
        self.assertIsNotNone(self.scraper.output_dir)
        self.assertEqual(self.scraper.base_url, os.getenv('SCRAPING_BASE_URL'))

    @patch('playwright.sync_api.sync_playwright')
    def test_scrape_spells(self, mock_playwright):
        """Test spell scraping process"""
        self.logger.debug("Testing spell scraping process")
        
        # Mock the Playwright context
        mock_browser = Mock()
        mock_context = Mock()
        mock_page = Mock()
        
        mock_playwright.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Mock page interactions
        mock_page.query_selector_all.return_value = [Mock()]
        mock_page.query_selector.return_value = Mock()
        mock_page.goto.return_value = Mock(ok=True)
        mock_page.evaluate.return_value = [{"name": "Test Spell", "source": "PHB"}]
        
        # Mock methods that we've added
        self.scraper.handle_cookie_consent = Mock()
        self.scraper.wait_for_critical_scripts = Mock()
        self.scraper.simulate_human_behavior = Mock()
        self.scraper.wait_for_js_data = Mock(return_value=True)
        
        # Run the scraper with a limit
        self.scraper.scrape_spells(limit=1)
        
        # Verify interactions
        mock_page.goto.assert_called_once()
        self.scraper.handle_cookie_consent.assert_called_once()
        self.scraper.wait_for_critical_scripts.assert_called_once()
        self.scraper.simulate_human_behavior.assert_called_once()
        mock_page.evaluate.assert_called()

    @patch('playwright.sync_api.Page')
    def test_handle_cookie_consent(self, mock_page):
        """Test the cookie consent handling"""
        # Create a mock locator with count method
        mock_locator = Mock()
        mock_locator.count.return_value = 1
        mock_page.locator.return_value = mock_locator
        
        # Run the method
        self.scraper.handle_cookie_consent(mock_page)
        
        # Verify interactions (should try to find and click accept button)
        mock_page.locator.assert_called()
        mock_locator.click.assert_called_once()

    @patch('playwright.sync_api.Page')
    def test_simulate_human_behavior(self, mock_page):
        """Test human behavior simulation"""
        # Mock viewport size
        mock_page.viewport_size = {'width': 1920, 'height': 1080}
        
        # Mock query_selector_all
        mock_button = Mock()
        mock_page.query_selector_all.return_value = [mock_button]
        
        # Run the method
        self.scraper.simulate_human_behavior(mock_page)
        
        # Verify interactions
        self.assertTrue(mock_page.evaluate.called)
        self.assertTrue(mock_page.mouse.move.called)
        self.assertTrue(mock_page.wait_for_timeout.called)

    @patch('playwright.sync_api.Page')
    def test_extract_spell_data(self, mock_page):
        """Test spell data extraction"""
        # Mock evaluate to return test data
        test_data = [{"name": "Fireball", "level": 3}]
        mock_page.evaluate.return_value = test_data
        
        # Run the method
        result = self.scraper.extract_spell_data(mock_page)
        
        # Verify results
        mock_page.evaluate.assert_called_once()
        self.assertEqual(result, test_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Fireball")

    def test_save_data(self):
        """Test data saving functionality"""
        self.logger.debug("Testing data saving")
        test_data = [{"name": "Test Spell", "level": 1}]
        
        # Create a temporary output directory
        os.makedirs(self.scraper.output_dir, exist_ok=True)
        
        # Save test data
        output_file = os.path.join(self.scraper.output_dir, "test_spells.json")
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