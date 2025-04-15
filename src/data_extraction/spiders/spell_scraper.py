import os
import json
import time
import random
import traceback
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, TimeoutError, Response
from src.utils.setup_logger import setup_logger

def user_agent_string():
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

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
            scripts_found = True
            for script in critical_scripts:
                try:
                    self.logger.debug(f"Waiting for {script}...")
                    page.wait_for_selector(f"script[src*='{script}']", state='attached', timeout=10000)
                except Exception as e:
                    self.logger.warning(f"Could not find script {script}: {str(e)}")
                    scripts_found = False
            
            if not scripts_found:
                self.logger.warning("Not all scripts were found. Continuing anyway.")
            
            # Wait for initial document ready state
            self.logger.debug("Waiting for DOM content loaded...")
            page.wait_for_load_state('domcontentloaded')
            
            # Check if key objects are defined without waiting
            self.logger.debug("Checking for key JavaScript objects...")
            js_objects_defined = page.evaluate("""
                () => {
                    return {
                        jQuery: typeof jQuery !== 'undefined',
                        Parser: typeof Parser !== 'undefined',
                        Utils: typeof Utils !== 'undefined',
                        spellList: typeof spellList !== 'undefined',
                        spellData: typeof spellData !== 'undefined'
                    };
                }
            """)
            
            self.logger.info(f"JavaScript objects status: {js_objects_defined}")
            
            # Take screenshot for debugging
            debug_dir = os.path.join(self.output_dir, "debug")
            os.makedirs(debug_dir, exist_ok=True)
            page.screenshot(path=os.path.join(debug_dir, "before_scripts_loaded.png"), full_page=True)
            
            # Only wait for key objects if they aren't already defined
            if not js_objects_defined.get('jQuery', False) or not js_objects_defined.get('Parser', False):
                self.logger.debug("Waiting for key objects to be defined (with shorter timeout)...")
                try:
                    page.wait_for_function("""
                        () => {
                            return typeof jQuery !== 'undefined' &&
                                   typeof Parser !== 'undefined' &&
                                   typeof Utils !== 'undefined';
                        }
                    """, timeout=15000)  # Reduced timeout
                except Exception as e:
                    self.logger.warning(f"Timeout waiting for key JavaScript objects: {str(e)}")
                    self.logger.warning("Attempting to continue without all scripts loaded")
            
            self.logger.info("Critical scripts load step completed")
            
        except Exception as e:
            self.logger.error(f"Error waiting for scripts: {str(e)}")
            self.logger.warning("Continuing execution despite script loading issues")

    def simulate_human_behavior(self, page: Page) -> None:
        """Simulate real human interaction to bypass bot detection"""
        try:
            self.logger.info("Simulating human-like behavior...")
            
            # Scroll the page slowly in a natural pattern
            for i in range(5):
                # Random scroll distance
                scroll_distance = random.randint(100, 300)
                page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                # Random pause between scrolls (300-800ms)
                page.wait_for_timeout(random.randint(300, 800))
            
            # Perform some random mouse movements
            viewport_size = page.viewport_size
            if viewport_size:
                for i in range(3):
                    x = random.randint(100, viewport_size['width'] - 200)
                    y = random.randint(100, viewport_size['height'] - 200)
                    page.mouse.move(x, y)
                    page.wait_for_timeout(random.randint(200, 500))
            
            # Click on some non-destructive elements
            try:
                # Try to click on a filter button that won't break functionality
                filter_buttons = page.query_selector_all('#filtertools button')
                if filter_buttons and len(filter_buttons) > 0:
                    random_button = random.choice(filter_buttons)
                    random_button.click()
                    page.wait_for_timeout(1000)
                    # Click it again to return to original state
                    random_button.click()
            except:
                pass
            
            # Final random pause
            page.wait_for_timeout(random.randint(1000, 2000))
            
            self.logger.info("Human behavior simulation completed")
            
        except Exception as e:
            self.logger.error(f"Error simulating human behavior: {str(e)}")

    def extract_spell_data(self, page: Page) -> List[Dict[str, Any]]:
        """Extract spell data from the page"""
        try:
            # Wait for the spell data to be loaded
            self.logger.info("Extracting spell data...")
            
            # Get the spell data from the JavaScript variables
            spell_data = page.evaluate("""
                () => {
                    // Try to access spellList directly
                    if (typeof spellList !== 'undefined' && spellList && spellList.length > 0) {
                        return spellList.map(spell => ({
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
                    
                    // Alternative approach: try to access data from the list elements
                    try {
                        const spellElements = Array.from(document.querySelectorAll('ul.spells li.row'));
                        if (spellElements.length > 0) {
                            return spellElements.map(el => {
                                const nameEl = el.querySelector('.name');
                                const sourceEl = el.querySelector('.source');
                                const levelEl = el.querySelector('.level');
                                const timeEl = el.querySelector('.time');
                                const schoolEl = el.querySelector('.school');
                                const rangeEl = el.querySelector('.range');
                                const classesEl = el.querySelector('.classes');
                                
                                return {
                                    name: nameEl ? nameEl.textContent.trim() : '',
                                    source: sourceEl ? sourceEl.textContent.trim() : '',
                                    level: levelEl ? levelEl.textContent.trim() : '',
                                    school: schoolEl ? schoolEl.className.split('_')[1] || '' : '',
                                    time: timeEl ? timeEl.textContent.trim() : '',
                                    range: rangeEl ? rangeEl.textContent.trim() : '',
                                    classes: classesEl ? classesEl.textContent.trim() : ''
                                };
                            });
                        }
                    } catch (e) {
                        console.error("Error extracting from DOM:", e);
                    }
                    
                    // If all else fails, return empty array
                    return [];
                }
            """)
            
            if not spell_data or len(spell_data) == 0:
                self.logger.warning("No spell data extracted, attempting direct JSON data extraction...")
                
                # Try to find the direct source of the JSON data
                json_data = page.evaluate("""
                    () => {
                        // Look for data loaded in typical JSON data patterns
                        try {
                            // Check for common global data objects
                            if (window.data && window.data.spell) return window.data.spell;
                            
                            // Search for JSON script tags which might contain the data
                            const jsonScripts = Array.from(document.querySelectorAll('script[type="application/json"]'));
                            for (const script of jsonScripts) {
                                try {
                                    const parsed = JSON.parse(script.textContent);
                                    if (parsed.spell || parsed.spells) return parsed.spell || parsed.spells;
                                } catch (e) {}
                            }
                            
                            // Check network requests
                            const cachedResponses = performance.getEntriesByType('resource')
                                .filter(r => r.name.includes('.json') && r.name.includes('spell'));
                            
                            if (cachedResponses.length) {
                                // We found potential JSON resources, but we can't access their content directly
                                // Just returning their URLs for diagnostic purposes
                                return { urls: cachedResponses.map(r => r.name) };
                            }
                            
                            return null;
                        } catch (e) {
                            console.error("Error finding JSON data:", e);
                            return null;
                        }
                    }
                """)
                
                if json_data:
                    self.logger.info(f"Found potential JSON data sources: {json_data}")
                    # Additional logic could be added here to fetch these JSON files directly
            
            self.logger.info(f"Extracted data for {len(spell_data)} spells")
            return spell_data
            
        except Exception as e:
            self.logger.error(f"Error extracting spell data: {str(e)}")
            return []

    def direct_json_fetch(self) -> List[Dict[str, Any]]:
        """
        Try to fetch spell data directly from the JSON API endpoint
        Returns a list of spell data dictionaries
        """
        self.logger.info("Attempting to fetch spell data directly from JSON files...")
        
        try:
            with sync_playwright() as p:
                # Configure a simple browser for direct API access
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
                )
                
                # Start with index file which contains references to all spell data files
                page = context.new_page()
                
                # Try different possible JSON endpoints
                possible_endpoints = [
                    f"{self.base_url}data/spells/index.json",
                    f"{self.base_url}data/spells.json",
                    f"{self.base_url}data/spells/spells-phb.json"
                ]
                
                all_spells = []
                
                for endpoint in possible_endpoints:
                    try:
                        self.logger.info(f"Trying endpoint: {endpoint}")
                        response = page.goto(endpoint, timeout=30000, wait_until='networkidle')
                        
                        if response and response.ok:
                            content_type = response.headers.get('content-type', '')
                            if 'application/json' in content_type or 'text/plain' in content_type:
                                # Parse as JSON
                                json_text = page.content()
                                # Extract content inside <pre> tag if necessary
                                if '<pre>' in json_text:
                                    import re
                                    match = re.search(r'<pre>(.*?)</pre>', json_text, re.DOTALL)
                                    if match:
                                        json_text = match.group(1)
                                
                                try:
                                    json_data = json.loads(json_text)
                                    
                                    # Handle different formats
                                    if isinstance(json_data, list):
                                        # Direct list of spells
                                        all_spells.extend(json_data)
                                        self.logger.info(f"Found {len(json_data)} spells in list format")
                                    elif isinstance(json_data, dict):
                                        # Check for common structures
                                        if 'spell' in json_data:
                                            all_spells.extend(json_data['spell'])
                                            self.logger.info(f"Found {len(json_data['spell'])} spells in 'spell' key")
                                        elif 'spells' in json_data:
                                            all_spells.extend(json_data['spells'])
                                            self.logger.info(f"Found {len(json_data['spells'])} spells in 'spells' key")
                                        else:
                                            # Dictionary of objects might be the spells themselves
                                            for key, value in json_data.items():
                                                if isinstance(value, dict) and 'name' in value and 'source' in value:
                                                    all_spells.append(value)
                                    
                                    if all_spells:
                                        self.logger.info(f"Successfully extracted {len(all_spells)} spells from {endpoint}")
                                        # If we found spells, no need to check other endpoints
                                        break
                                        
                                except json.JSONDecodeError as e:
                                    self.logger.warning(f"Failed to parse JSON from {endpoint}: {str(e)}")
                    
                    except Exception as e:
                        self.logger.warning(f"Error fetching from {endpoint}: {str(e)}")
                
                browser.close()
                return all_spells
                
        except Exception as e:
            self.logger.error(f"Error during direct JSON fetch: {str(e)}")
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
        
        spell_data = []
        
        try:
            # First try the direct browser automation approach
            spell_data = self._scrape_with_browser()
            
            # If that fails, try the direct JSON fetch approach
            if not spell_data:
                self.logger.info("Browser scraping failed, trying direct JSON fetch...")
                spell_data = self.direct_json_fetch()
            
            # Apply limit
            if limit and len(spell_data) > limit:
                self.logger.info(f"Limiting results to {limit} spells")
                spell_data = spell_data[:limit]
            
            # Save all data if we have any
            if spell_data:
                output_file = os.path.join(self.output_dir, "spells.json")
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(spell_data, f, ensure_ascii=False, indent=4)
                self.logger.info(f"Scraping completed. Saved {len(spell_data)} spells to {output_file}")
            else:
                self.logger.error("Failed to extract any spell data using all available methods")
            
        except Exception as e:
            self.logger.error(f"Fatal error during scraping: {str(e)}")
            raise

    def _scrape_with_browser(self) -> List[Dict[str, Any]]:
        """
        The original browser automation approach to scrape spells
        Returns a list of spell dictionaries or empty list if failed
        """
        try:
            with sync_playwright() as p:
                # Configure browser with realistic settings
                browser = p.chromium.launch(
                    headless=False,  # Headless mode is more likely to be detected
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--window-size=1920,1080',
                        '--disable-features=IsolateOrigins,site-per-process',  # Disable site isolation
                        '--disable-web-security',  # Allow cross-origin requests
                        '--disable-site-isolation-trials'
                    ]
                )
                
                # Create a realistic browser context with more advanced fingerprint
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='Europe/Paris',
                    color_scheme='dark',
                    permissions=['geolocation', 'notifications'],
                    java_script_enabled=True,
                    has_touch=False,
                    is_mobile=False
                )
                
                # Add more sophisticated anti-bot detection
                context.add_init_script("""
                    // Advanced fingerprint spoofing
                    Object.defineProperty(navigator, 'webdriver', { get: () => false });
                    Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'fr'] });
                    Object.defineProperty(navigator, 'plugins', { get: () => [
                        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: 'Portable Document Format' },
                        { name: 'Native Client', filename: 'internal-nacl-plugin', description: 'Native Client Executable' }
                    ]});
                    
                    // Mock hardware concurrency to show a normal value
                    Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });
                    
                    // Mock WebGL to avoid fingerprinting
                    const getParameterProto = WebGLRenderingContext.prototype.getParameter;
                    WebGLRenderingContext.prototype.getParameter = function(parameter) {
                        // Spoof renderer and vendor strings
                        if (parameter === 37445) return 'Intel Inc.';
                        if (parameter === 37446) return 'Intel(R) Iris(TM) Graphics 6100';
                        return getParameterProto.apply(this, arguments);
                    };
                
                    // Add randomized Canvas fingerprint
                    const toDataURLProto = HTMLCanvasElement.prototype.toDataURL;
                    HTMLCanvasElement.prototype.toDataURL = function() {
                        if (this.width > 16 && this.height > 16) {
                            // Return original to avoid breaking functionality
                            const result = toDataURLProto.apply(this, arguments);
                            return result;
                        }
                        return toDataURLProto.apply(this, arguments);
                    };
                    
                    // Spoof screen resolution
                    Object.defineProperty(window.screen, 'width', { get: () => 1920 });
                    Object.defineProperty(window.screen, 'height', { get: () => 1080 });
                    Object.defineProperty(window.screen, 'availWidth', { get: () => 1920 });
                    Object.defineProperty(window.screen, 'availHeight', { get: () => 1040 });
                    Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
                    Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
                """)
                
                page = context.new_page()
                
                # Add realistic headers
                page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0'
                })

                # Intercept network requests to mimic real browser behavior
                page.route('**/*', lambda route: route.continue_())

                # Load the page
                self.logger.info("Loading spells page...")
                try:
                    response = page.goto(
                        self.spell_url,
                        timeout=60000,
                        wait_until='domcontentloaded'
                    )
                    
                    if not response or not response.ok:
                        self.logger.error(f"Failed to load page: {response.status if response else 'No response'}")
                        browser.close()
                        return []
                        
                except Exception as e:
                    self.logger.error(f"Error during page load: {str(e)}")
                    browser.close()
                    return []

                # Handle cookie consent
                self.handle_cookie_consent(page)

                # Wait for critical scripts
                self.wait_for_critical_scripts(page)
                
                # Simulate human behavior
                self.simulate_human_behavior(page)
                
                # Wait for full page load and JavaScript execution
                try:
                    page.wait_for_load_state('networkidle', timeout=20000)
                except:
                    self.logger.warning("Timeout waiting for network idle state")
                
                # Wait for JavaScript data to be available
                if not self.wait_for_js_data(page, timeout=30):
                    # Debug page state if data is not loaded
                    self.debug_page_state(page)
                    
                    # Try to force data load through direct evaluation
                    page.evaluate("""
                        () => {
                            // Try to trigger data loading
                            if (typeof ExcludeUtil !== 'undefined' && typeof ExcludeUtil.initialise === 'function') {
                                ExcludeUtil.initialise();
                            }
                            if (typeof multisourceLoad === 'function') {
                                multisourceLoad("data/spells/", "spell", pageInit, addSpells);
                            }
                        }
                    """)
                    
                    # Wait again for JS data
                    self.wait_for_js_data(page, timeout=20)
                
                # Extract spell data
                spell_data = self.extract_spell_data(page)
                
                if not spell_data or len(spell_data) == 0:
                    self.logger.warning("No spell data was extracted. Attempting to capture page state...")
                    self.debug_page_state(page)
                    
                    # Save page screenshot and HTML for debugging
                    debug_dir = os.path.join(self.output_dir, "debug")
                    os.makedirs(debug_dir, exist_ok=True)
                    
                    page.screenshot(path=os.path.join(debug_dir, "failed_page.png"), full_page=True)
                    with open(os.path.join(debug_dir, "page_html.html"), "w", encoding="utf-8") as f:
                        f.write(page.content())
                
                # Close browser
                browser.close()
                return spell_data

        except Exception as e:
            self.logger.error(f"Error during browser scraping: {str(e)}")
            return []

    def provide_manual_extraction_instructions(self) -> None:
        """
        Provide instructions for manually extracting spell data from the website.
        Creates a JavaScript snippet to be run in the browser console.
        """
        self.logger.info("Creating manual extraction instructions...")
        
        # Create the output directory for manual extraction
        manual_dir = os.path.join(self.output_dir, "manual")
        os.makedirs(manual_dir, exist_ok=True)
        
        # Create a JavaScript file to be run in browser console
        js_file = os.path.join(manual_dir, "extract_spells.js")
        
        js_code = """
// Instructions: 
// 1. Open https://5e.tools/spells.html in your browser
// 2. Wait for the page to fully load (you should see the spell list)
// 3. Open browser developer tools (F12 or right-click -> Inspect)
// 4. Go to the Console tab
// 5. Paste this entire script and press Enter
// 6. Wait for it to complete and download the spells.json file
// 7. Move the downloaded file to the data/scraping/spells/ directory

// This function extracts all spell data
function extractSpellData() {
    console.log("Starting spell extraction...");
    
    // Check if the spell data is loaded
    if (typeof spellList === 'undefined' || !spellList || !spellList.length) {
        console.error("Spell data is not loaded yet. Please wait for the page to fully load.");
        return null;
    }
    
    console.log(`Found ${spellList.length} spells. Processing...`);
    
    // Map to extract the relevant properties
    const extractedSpells = spellList.map(spell => ({
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
    
    console.log(`Successfully processed ${extractedSpells.length} spells.`);
    return extractedSpells;
}

// This function downloads the data as a JSON file
function downloadSpellData(spellData) {
    const dataStr = JSON.stringify(spellData, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'spells.json';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    console.log("Download initiated. Save the file to data/scraping/spells/spells.json");
}

// Main execution
try {
    console.log("Extracting spell data from 5e.tools...");
    const spellData = extractSpellData();
    
    if (spellData && spellData.length > 0) {
        console.log(`Preparing to download data for ${spellData.length} spells...`);
        downloadSpellData(spellData);
        console.log("Extraction completed successfully!");
    } else {
        console.error("Failed to extract spell data. Please try again after the page has fully loaded.");
    }
} catch (error) {
    console.error("Error during extraction:", error);
}
"""
        
        # Write the JavaScript to a file
        with open(js_file, "w", encoding="utf-8") as f:
            f.write(js_code)
        
        # Create a readme file with instructions
        readme_file = os.path.join(manual_dir, "README.md")
        readme_content = """# Manual Spell Data Extraction

## Why Manual Extraction?
The website uses bot detection which blocks automated scraping. Manual extraction is more reliable.

## Instructions

1. **Open the website**:
   - Visit https://5e.tools/spells.html in your browser
   - Wait for the page to fully load

2. **Open browser developer tools**:
   - Press F12 or right-click anywhere and select "Inspect"
   - Go to the "Console" tab

3. **Run the extraction script**:
   - Open the `extract_spells.js` file in this directory
   - Copy the entire content
   - Paste it into the browser console
   - Press Enter

4. **Save the downloaded file**:
   - The script will automatically download a `spells.json` file
   - Move this file to the `data/scraping/spells/` directory

5. **Verify the data**:
   - The JSON file should contain an array of spell objects
   - Each spell should have properties like name, level, school, etc.

## Troubleshooting

If you encounter any issues:

- Make sure the page is fully loaded before running the script
- Check that JavaScript is enabled in your browser
- Try refreshing the page and waiting longer before running the script
- If the console shows errors, wait for all scripts to load and try again

"""
        
        # Write the README to a file
        with open(readme_file, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        self.logger.info(f"Manual extraction instructions created at {manual_dir}")
        self.logger.info(f"JavaScript extraction file: {js_file}")
        self.logger.info(f"README instructions: {readme_file}")

    def run(self, limit: Optional[int] = None) -> None:
        """
        Run the scraping process with automatic and manual fallback options.
        
        Args:
            limit (Optional[int]): Maximum number of spells to scrape. None for all spells.
        """
        try:
            self.logger.info("Starting spell scraping process...")
            
            # First attempt: Try automated scraping
            self.logger.info("Attempting automated scraping...")
            spells = self.scrape_spells(limit=limit)
            
            # Check if we got meaningful data
            if spells and len(spells) > 0:
                self.logger.info(f"Successfully scraped {len(spells)} spells automatically!")
                
                # Ensure output directory exists
                os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
                
                # Save the data
                with open(self.output_file, 'w', encoding='utf-8') as f:
                    json.dump(spells, f, indent=2, ensure_ascii=False)
                
                self.logger.info(f"Spell data saved to {self.output_file}")
                return
            
            # If we reach here, automated scraping failed or returned no data
            self.logger.warning("Automated scraping failed or returned no data.")
            self.logger.info("Falling back to manual extraction process...")
            
            # Generate manual extraction instructions
            self.provide_manual_extraction_instructions()
            
            # Print instructions to console for visibility
            self.logger.info("\nMANUAL EXTRACTION REQUIRED:")
            self.logger.info("1. Open https://5e.tools/spells.html in your browser")
            self.logger.info("2. Complete the Cloudflare verification if present")
            self.logger.info("3. Once on the spells page, open browser dev tools (F12)")
            self.logger.info("4. Check the manual/README.md file for detailed instructions")
            self.logger.info("5. Use the script in manual/extract_spells.js to extract the data")
            
        except Exception as e:
            self.logger.error(f"Error during scraping process: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise

if __name__ == "__main__":
    scraper = SpellScraper()
    # By default, scrape all spells. You can pass a limit to test with fewer spells
    scraper.run(limit=None)  # For testing, you might want to use limit=10

