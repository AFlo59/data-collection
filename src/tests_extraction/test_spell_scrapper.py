import unittest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from utils.setup_logger import setup_logger
from data_extraction.spiders.spell_scraper import SpellScraper 

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
        self.assertIsNotNone(self.scraper.url)
        self.assertIsNotNone(self.scraper.output_dir)
        self.assertEqual(self.scraper.url, os.getenv('SCRAPING_SPELLS_URL'))

    @patch('selenium.webdriver.Chrome')
    def test_get_spell_list(self, mock_chrome):
        """Test spell list scraping"""
        self.logger.debug("Testing spell list scraping")
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        
        # Mock the necessary selenium calls
        mock_element = Mock()
        mock_element.text = "Test Spell"
        mock_element.get_attribute.return_value = "http://test.url"
        mock_driver.find_elements.return_value = [mock_element]
        
        result = self.scraper.get_spell_list(mock_driver)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    def test_save_data(self):
        """Test data saving functionality"""
        self.logger.debug("Testing data saving")
        test_data = {"test": "data"}
        test_file = "test_spells.json"
        
        self.scraper.save_data(test_data, test_file)
        
        file_path = os.path.join(self.scraper.output_dir, test_file)
        self.assertTrue(os.path.exists(file_path))
        
        # Clean up
        os.remove(file_path)

    def tearDown(self):
        """Clean up after each test"""
        self.logger.info(f"Completed test: {self._testMethodName}")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.logger.info("=== Completed Spell Scraper Test Suite ===")

if __name__ == '__main__':
    unittest.main()