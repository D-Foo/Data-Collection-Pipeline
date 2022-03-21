from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import string

class Scraper:

    def __init__(self, target_url, set_name, target_list_filepath, debug) -> None:
        
        #Control
        self.debug = debug

        #Url
        self.url_base = target_url
        self.url_mtg_section = "/en/Magic/Products/Singles/"
        self.url_set_name = set_name
        self.target_list_filepath = target_list_filepath
        self.formatted_card_list = []
        
        #Webdriver
        self.driver = webdriver.Firefox()
        self.delay = 10

        self.startup()
        pass
    
    def startup(self):
        if(self.debug):
            print("Startup")
        self.driver.get(self.url_base)
        time.sleep(2) # Wait a couple of seconds, so the website doesn't suspect we're a bot


    def handle_cookies(self, url):
        if(self.debug):
            print("Handle_Cookies")

        try: 
            WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//div[@id="CookiesConsent"]')))
            accept_cookies_button = self.driver.find_element_by_xpath('//button[@aria-label="Accept All Cookies"]')
            accept_cookies_button.click()
        except TimeoutException:
            print("Loading took much time (>" + string(self.delay) + "s)")
        except BaseException as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

    def create_url_list(self):
        if(self.debug):
            print("Create_Url_List")

        #load NEO_cardlist.txt
        cardlist_filename = self.target_list_filepath
        card_namelist = []
        try:
            with open(cardlist_filename, 'r') as f:
                card_namelist = f.readlines()
        except BaseException as err:
            print("Could not open " + cardlist_filename + " for reading.")
            print(f"Unexpected {err=}, {type(err)=}")   
            raise
                            
        #Convert name to url syntax
        for name in card_namelist:
            name = name.replace(" // ", '-')  #Replace the " // " substring with a hyphen
            name = name.translate({ord(c):None for c in "',"}) #Remove any apostrophes or commas in the string
            name = name.replace(' ', '-')  #Replace any spaces with hyphens
            self.formatted_card_list.append(name)
        

    def scrape(self, url):
        self.driver.get(url)
        time.sleep(2)
        

    def run(self):
        self.create_url_list()
        #Load base website url and handle cookies
        self.handle_cookies(self.url_base)

        #Scrape rest of data from urls generated from target list data
        url_head = self.url_base + self.url_mtg_section + self.url_set_name + "/"

        for c in self.formatted_card_list:
            final_url = url_head + c      
            if(debug):
                print("Scraping: " + final_url)      
            self.scrape(final_url)

        pass

if __name__ == "__main__":
    #example url https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    target_url = "https://www.cardmarket.com"
    target_list_filepath = "NEO_cardlist.txt"
    set_name = "Kamigawa-Neon-Dynasty"
    debug = True

    scraper = Scraper(target_url, set_name, target_list_filepath, debug)
    scraper.run()
    pass