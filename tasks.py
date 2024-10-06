from robocorp.tasks import task
from robocorp import workitems
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager as cache
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

import logging
import pandas as pd
import time, random
import datetime
import re
import xlsxwriter

class ThoughfulScraper:
    def __init__(self, *args, **kwargs):
        self.driver = None
        self.headless = kwargs['headless']
        self.search_phrase = kwargs['search_phrase']
        self.category_name = kwargs['category_name']
        self.logger = logging.getLogger(__name__)
        self.configure_logger()
        self.green = "\033[92m"
        self.red = "\033[91m"
        self.blue = "\033[94m"
        self.yellow = "\033[93m"
        self.magenta = "\033[95m"
        self.reset = "\033[0m"
        #initialize a pandas dataframe to store the data
        self.df = pd.DataFrame(columns=["Title", "Date","Description", "Picture Filename",
                                        "Count of Search Phrases", "Contains Money Phrase",])


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
        if self.headless:
            self.logger.warning(f"{self.yellow}Running in headless mode{self.reset}")
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--lang=en-US')
        # options.add_argument("--disable-extensions")
        # options.add_argument("--disable-gpu")
        # options.add_argument('--disable-web-security')
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
            
    def retry_page_decorator(func):
        def wrapper(self, *args, **kwargs):
            attempts = 5
            for _ in range(attempts):
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    self.logger.error(f"{self.red}Error: {e}{self.reset}")
                    self.logger.warning(f"{self.yellow}Retrying...{self.reset}")
                    self.driver.refresh()
                    time.sleep(self.wait_time(8,11))
            self.logger.error(f"{self.red}Failed after {attempts} attempts{self.reset}")
            raise Exception("Failed after 3 attempts")
        return wrapper

    @retry_page_decorator
    def goto_link(self, link):
        self.logger.info(f"{self.blue}Goto Link Func Starting{self.reset}")
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
        search_value = self.search_phrase
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


    def check_if_category_is_present(self):
        #click the category Live Blogs, the whitespaces need to be there
        category = f"""
            {self.category_name}
        """
        self.logger.info(f"{self.blue}Checking if the focus category is seen{self.reset}")
        category_element = self.explicit_wait_for_element(15, By.XPATH, f'//span[text()="{category}"]')
        self.logger.info(f"{self.green}Expected focus category seen{self.reset}")
        #clicking the category
        self.logger.info(f"{self.blue}Attempting to click the category '{self.category_name}'{self.reset}")
        category_element.click()
        self.logger.info(f"{self.green}Clicked the category '{self.category_name}'{self.reset}")
        time.sleep(self.wait_time(1.5, 2.5))


    def scrape_data(self):
        #make sure to load the page first
        self.logger.info(f"{self.blue}Loading the data...{self.reset}")
        WebDriverWait(self.driver, 20).until(lambda driver: driver.execute_script("return document.readyState") in ["interactive", "complete"])
        self.logger.info(f"{self.green}All feeds are loaded{self.reset}")
        #check the entry point element
        # self.logger.info(f"{self.blue}Checking if the entry point element is seen{self.reset}")
        # entry_point_element = self.explicit_wait_for_element(15, By.XPATH, '//div[@class="PageList-items"]')
        # self.logger.info(f"{self.green}Expected entry point element seen{self.reset}")
        #loop through the entry point element
        time.sleep(self.wait_time(1, 2))
        #parse with beautifulsoup
        #extract the data
        self.soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        #the main container xpath is //div[@class="PageList-items"]
        #there are multiple cards inside with xpath //div[@class="PageList-items-item"]
        news_card = self.soup.find_all('div', class_="PageList-items")
        main_card = news_card[1].find_all('div', class_="PageList-items-item")
        #get the total number of cards
        len_cards = len(main_card)
        self.logger.info(f"{self.yellow}Total number of cards found: {len_cards}{self.reset}")
        for card in main_card:
            #getting to the inner content divs
            page_promo_div = card.find('div')
            content_div = page_promo_div.find('div', class_="PagePromo-content")
            #get the title
            title_div = content_div.find('div', class_="PagePromo-title")
            title = title_div.find('span').text
            self.logger.info("-------------------------------------------------")
            self.logger.info(f"Title: {self.magenta}{title}{self.reset}")
            #get the date
            date_div = content_div.find('bsp-timestamp', {'data-timestamp': True})
            date_raw:int = int(date_div.get('data-timestamp'))
            date:str = self.convert_timestamp_to_date(date_raw)
            self.logger.info(f"Date: {self.magenta}{date}{self.reset}")
            #get the description
            description_div = content_div.find('div', class_="PagePromo-description")
            description = description_div.find('span').text
            self.logger.info(f"Description: {self.magenta}{description}{self.reset}")

            #get the picture filename
            media_div = page_promo_div.find('div', class_="PagePromo-media")
            picture_filename = media_div.find('img').get('src')
            picture_filename = str(picture_filename)
            self.logger.info(f"Picture Filename: {self.magenta}{picture_filename}{self.reset}")

            #get the count of search phrases
            #combine the title and description
            combined_text = title + " " + description
            count_search_phrases:int = self.get_occurrences(combined_text, self.search_phrase)
            self.logger.info(f"Count of Search Phrases: {self.magenta}{count_search_phrases}{self.reset}")
            
            #check if the combine_text contains the money phrase, Possible formats: $11.1 | $111,111.11 | 11 dollars | 11 USD
            contains_money_phrase:bool = self.contains_money_phrase(combined_text)
            self.logger.info(f"Contains Money Phrase: {self.magenta}{contains_money_phrase}{self.reset}")
            
            #store the data in a dictionary
            data_dict = {"Title": title, "Date": date, "Description": description, "Picture Filename": picture_filename,
                    "Count of Search Phrases": count_search_phrases, "Contains Money Phrase": contains_money_phrase}
            #add the data to the dataframe
            self.data_dict_to_df(data_dict)

        self.logger.info(f"{self.green}Dataframe: {self.df.head()}{self.reset}")
        return self.df


    def data_dict_to_df(self, data_dict:dict):
        new_data = pd.DataFrame([data_dict])
        # Concatenate the new data with the existing DataFrame
        self.df = pd.concat([self.df, new_data], ignore_index=True)
        #show the dataframe


    def contains_money_phrase(self, combine_text) -> bool:
        # Regex pattern to match money phrases
        pattern = r'\$[\d,]+(\.\d{1,2})?|[\d,]+ dollars|[\d,]+ USD'
        # Search for the pattern in the provided text
        return re.search(pattern, combine_text) is not None

    def get_occurrences(self, text, search_phrase) -> int:
        # Create a regex pattern to match the search phrase, ignoring case and surrounding punctuation
        pattern = r'\b' + re.escape(search_phrase) + r'\b'
        matches = re.findall(pattern, text, re.IGNORECASE)  # Use re.IGNORECASE for case-insensitive matching
        return len(matches)  # Return the number of matches found

    def convert_timestamp_to_date(self, timestamp_ms:int):
        # Convert the timestamp from milliseconds to seconds
        timestamp_s = timestamp_ms / 1000  # Convert to seconds
        # Convert to a human-readable format
        readable_date = datetime.datetime.fromtimestamp(timestamp_s).strftime('%m-%d-%Y')
        return readable_date


    def save_to_excel(self, df, filename):
        self.logger.info(f"{self.blue}Saving the data to Excel...{self.reset}")
        # Open the existing Excel file (or create it)
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            # Write the DataFrame to the worksheet starting from row 1, column 0 (A1)
            df.to_excel(writer, sheet_name='Sheet1', index=False)
            worksheet = writer.sheets['Sheet1'] # Ensure you target the right sheet
            # set the column width to fit 100 characters
            worksheet.set_column('A:A', 100)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 100)
            worksheet.set_column('D:D', 100)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 20)
        self.logger.info(f"{self.green}Data saved to Excel{self.reset}")


    def driver_quit(self):
        if self.driver:
            self.logger.info(f"{self.blue}Quitting the driver{self.reset}")
            self.driver.quit()

@task
def minimal_task():
    item = workitems.inputs.current
    print("Received payload:", item.payload)
    search_phrase = item.payload.get("search_phrase")
    category_name = item.payload.get("category_name")
    scraper = ThoughfulScraper(search_phrase = search_phrase,
                                category_name = category_name, headless = True)
    scraper.set_webdriver()
    # Perform scraping tasks here
    try:
        filename = "output/apnews_data.xlsx"
        scraper.goto_link("https://apnews.com/")
        scraper.load_home_page()
        scraper.load_results_and_filter()
        scraper.check_if_category_is_present()
        df = scraper.scrape_data()
        scraper.save_to_excel(df, filename)


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
    scraper = ThoughfulScraper(search_phrase = "Laundering",
                                category_name = "Videos", headless = True)
    scraper.set_webdriver()
    # Perform scraping tasks here
    try:
        filename = "output/apnews_data.xlsx"
        scraper.goto_link("https://apnews.com/")
        scraper.load_home_page()
        scraper.load_results_and_filter()
        scraper.check_if_category_is_present()
        df = scraper.scrape_data()
        scraper.save_to_excel(df, filename)


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