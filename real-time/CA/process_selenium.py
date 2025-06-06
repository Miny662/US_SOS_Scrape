from tempfile import mkdtemp

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ProcessSelenium(object):
    def __init__(self):
        self.driver = None

    # Initialize driver driver browser without head.    
    def initialize_driver(self):
        print("Initializing Chrome webdriver...")        

        options = webdriver.ChromeOptions()
        service = webdriver.ChromeService("/opt/chromedriver")

        options.binary_location = '/opt/chrome/chrome'
        options.add_argument("--headless=new")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        options.add_argument(f"--user-data-dir={mkdtemp()}")
        options.add_argument(f"--data-path={mkdtemp()}")
        options.add_argument(f"--disk-cache-dir={mkdtemp()}")
        options.add_argument("--remote-debugging-port=9222")
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('--disable-blink-features=AutomationControlled')

        self.driverBrowser = webdriver.Chrome(options=options, service=service)

    # closure for resource optimization
    def close_driver(self):
        self.driverBrowser.quit()

    # msg script abruptly terminated        
    def script_terminated(self):
        dct = {}
        print("___________________________________________________________________________________")
        dct["code"] = "0x500"
        dct["message"] = "Number of failed attempts. Script abruptly terminated...!"
        print(dct)
        print("___________________________________________________________________________________")
        self.close_driver()
        sys.exit()

    def retry(self, n):
        N_ATTEMPS = 5
        WAIT_TIME = 5
        print("reconnecting...", flush=True)
        time.sleep(WAIT_TIME)
        return False if n == N_ATTEMPS else True

    # Validate the status of the page
    def status_page(self, xpath_element_located, url):
        loop = True
        count = 0
        while loop:
            try:
                self.driverBrowser.get(url)
                # Wait explicitly
                wait = WebDriverWait(self.driverBrowser, 120)
                element = wait.until(EC.presence_of_element_located((By.XPATH, xpath_element_located)))
            except TimeoutException:
                loop = True
                count = count + 1
                if not self.retry(count):
                    self.script_terminated()
            else:
                loop = False
        return True

    # Wait while you find an item on the page        
    def presence_of_element(self, css, wait_time=10):
        try:
            element = WebDriverWait(self.driverBrowser, wait_time).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
            )
        except TimeoutException as ex:
            return None
        else:            
            return element

    def by_css_containing_text(self, selector, text):
        exits = False
        elements = self.driverBrowser.find_elements_by_css_selector(selector)
        for i, element in enumerate(elements): 
            if text in element.text.strip():
                exits = True
                return i
        return False

    def element_clickable(self, id_):
        element = WebDriverWait(self.driverBrowser, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input#{}".format(id_))))

        #element = WebDriverWait(self.driverBrowser, 20).until(EC.element_to_be_clickable((By.ID, id_)))
        
        return element

    def element_click(self, element):
        ActionChains(self.driverBrowser).move_to_element(element).click().perform()
