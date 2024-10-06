from robocorp.tasks import task
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as cache
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import logging
import pandas as pd
import time, random

class ThoughfulScraper:
    def __init__(self, *args, **kwargs):
        self.driver = None
        self.logger = logging.getLogger(__name__)
        self.configure_logger()
        self.green = "\033[92m"
        self.red = "\033[91m"
        self.blue = "\033[94m"
        self.yellow = "\033[93m"
        self.reset = "\033[0m"
        #initialize a pandas dataframe to store the data



    def configure_logger(self):
        # Set up logging format and level
        handler = logging.StreamHandler()  # Log to console
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)

        # Set log level and add handler to the logger
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(handler)
        self.logger.propagate = False  # Avoid duplicate logs from the root logger

    def set_chrome_options(self):
        options = webdriver.ChromeOptions()
        # options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--lang=en-US')
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        options.add_argument('--disable-web-security')
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        return options
    
    def set_webdriver(self, browser="Chrome"):
        options = self.set_chrome_options()
        executable_driver_path = cache().install()
        self.logger.warning(f"{self.yellow}Using driver: {executable_driver_path}{self.reset}")
        # Start the Chrome instance correctly
        self.driver = webdriver.Chrome(options=options)


    def wait_time(self, min_num, max_num):
        #to product random delays from min_num to max_num
        rand_num = random.uniform(min_num, max_num)
        return rand_num

    def type_with_random_delay(self, locator, text):
        for char in text:
            time.sleep(self.wait_time(0.03, 0.19))
            locator.send_keys(char)

    def goto_link(self, link):
        self.logger.info(f"{self.blue}Navigating to {link}{self.reset}")
        self.driver.get(link)
        self.logger.info(f"{self.green}Page loaded successfully{self.reset}")

    def explicit_wait_for_element(self, timeout, by, locator):
        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, locator))
        )
        return element

  
    def load_home_page(self):
        #check if the search button seen
        self.logger.info(f"{self.blue}Checking if the search button is seen{self.reset}")
        search_btn_element = self.explicit_wait_for_element(15, By.XPATH, '//button[@class="SearchOverlay-search-button"]')
        self.logger.info(f"{self.green}Expected button seen{self.reset}")
        #clicking the search button
        self.logger.info(f"{self.blue}Attempt to click the search button{self.reset}")
        search_btn_element.click()
        self.logger.info(f"{self.green}Clicked the search button{self.reset}")
        time.sleep(self.wait_time(0.25, 1.25))
        #check if the search input seen
        self.logger.info(f"{self.blue}Checking if the search input is seen{self.reset}")
        search_input_element = self.explicit_wait_for_element(15, By.XPATH, '//input[@placeholder="Keyword Search..."]')
        self.logger.info(f"{self.green}Expected input seen{self.reset}")
        time.sleep(self.wait_time(1, 2))
        #entering the search keyword
        self.logger.info(f"{self.blue}Entering the search keyword{self.reset}")
        time.sleep(self.wait_time(1.2, 2.2))
        search_value = "Hurricane"
        self.type_with_random_delay(search_input_element, search_value)
        self.logger.info(f"{self.green}Entered '{search_value}' in the search bar{self.reset}")
        time.sleep(self.wait_time(0.3, 1.4))
        #searching the keyword
        results_btn_element = self.explicit_wait_for_element(15, By.XPATH, '//button[@class="SearchOverlay-search-submit"]')
        self.logger.info(f"{self.blue}Attempting to click the search result button{self.reset}")
        results_btn_element.click()
        self.logger.info(f"{self.green}Clicked to Search for results...{self.reset}")
        time.sleep(self.wait_time(1, 3))
        # now unfiltered results seen.


    def load_results_and_filter(self):
        #check if category dropdown seen
        self.logger.info(f"{self.blue}Checking if the category dropdown is seen{self.reset}")
        category_dropdown_element = self.explicit_wait_for_element(15, By.XPATH, '//div[@class="SearchFilter-heading"]')
        self.logger.info(f"{self.green}Expected category dropdown seen{self.reset}")
        #clicking the category dropdown
        time.sleep(self.wait_time(1, 2.2))
        self.logger.info(f"{self.blue}Attempting to click the category dropdown{self.reset}")
        category_dropdown_element.click()
        self.logger.info(f"{self.green}Clicked the category dropdown{self.reset}")
        time.sleep(self.wait_time(0.5, 1.5))
        #click the category Live Blogs, the whitespaces need to be there
        category = """
            Live Blogs
        """
        self.logger.info(f"{self.blue}Checking if the focus category is seen{self.reset}")
        category_element = self.explicit_wait_for_element(15, By.XPATH, f'//span[text()="{category}"]')
        self.logger.info(f"{self.green}Expected focus category seen{self.reset}")
        #clicking the category
        self.logger.info(f"{self.blue}Attempting to click the category '{category}'{self.reset}")
        category_element.click()
        self.logger.info(f"{self.green}Clicked the category '{category}'{self.reset}")
        time.sleep(self.wait_time(1.5, 2.5))





    def driver_quit(self):
        if self.driver:
            self.logger.info(f"{self.blue}Quitting the driver{self.reset}")
            self.driver.quit()

@task
def minimal_task():
    scraper = ThoughfulScraper()
    scraper.set_webdriver()
    # Perform scraping tasks here
    try:
        scraper.goto_link("https://apnews.com/")
        scraper.load_home_page()
        scraper.load_results_and_filter()

    except Exception as e:
        #if error string error message that is stripped, has first word "Stacktrace".
        # then print "This error might be a locator issue, please check the locator"
        # else print the error message
        stripped_error = str(e).strip()
        if "Stacktrace" in stripped_error:
            scraper.logger.error(f"{scraper.red}This error might be a locator issue, please check the locator.{scraper.reset}")
        else:
            scraper.logger.error(f"{scraper.red}Error: {e}{scraper.reset}")

    finally:
        # Close the driver
        scraper.driver_quit()


if __name__ == "__main__":
    minimal_task()