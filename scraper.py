from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import time
import string
from mtg_card_data import MTGCardData
import random

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

        #Data 
        data = []

        self.startup()
        
    
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
            name = name.replace('\n', '')  #Remove \n at end of name
            self.formatted_card_list.append(name)
        
    def scrape(self, url) -> MTGCardData:
        self.driver.get(url)
        time.sleep(2)    
        scraped_data = MTGCardData()

        #Wait until tabel containing the data we want to scrape is loaded in
        WebDriverWait(self.driver, self.delay).until(EC.presence_of_element_located((By.XPATH, '//dl[@class="labeled row no-gutters mx-auto"]'))) 

        #Get each table description and corresponding value
        for dt in self.driver.find_element_by_xpath('//dl[@class="labeled row no-gutters mx-auto"]').find_elements_by_xpath('.//dt'):
            
            dd = dt.find_element_by_xpath('.//following-sibling::dd')

            #Rarity
            if(dt.text == "Rarity"):
                print("RARITY -> " + dd.find_element_by_xpath('.//span').get_attribute("data-original-title"))
            #Reprints
            elif(dt.text == "Reprints"):
                print("REPRINTS -> " + dd.find_element_by_xpath('.//a').text)
                str = dd.find_element_by_xpath('.//a').text
                str = str[str.find('(') + 1 : str.find(')')]
                print("STR -> " + str)
            #Printed in
            elif(dt.text == "Printed in"):
                print("Printed in")
                pass
            #Availble items
            elif(dt.text == "Available items"):
                print(dt.text + " -> " + dd.text)
            #Prices
            elif(dt.text == "From" or "Price Trend" or "30 days average price" or "7 days average price" or "1 day average price"):
                print(dt.text + " -> " + dd.text)
            else:
                print("Unexpected input: " + dt.text)
           
        #Get Image
        card_image_url = self.driver.find_element_by_xpath('//img[@class="is-front"]').get_attribute("src")
        print("Card url: " + card_image_url)            
            
        #scraped_data.card_name = 1


        return scraped_data


    def run(self) -> list:

        mtgData = []
        
        parse_only_one = True

        self.create_url_list()

        #Load base website url and handle cookies
        self.handle_cookies(self.url_base)

        #Scrape rest of data from urls generated from target list data
        url_head = self.url_base + self.url_mtg_section + self.url_set_name + "/"

        if parse_only_one:
            random_parse = False
            if random_parse:
                self.scrape(url_head + random.choice(self.formatted_card_list))
            else:
                mtgData.append(self.scrape(url_head + self.formatted_card_list[247]))
        else:
            for c in self.formatted_card_list:
                final_url = url_head + c      
                if(debug):
                    print("Scraping: " + final_url)      
                self.scrape(final_url)
        return mtgData

        

if __name__ == "__main__":
    #example url https://www.cardmarket.com/en/Magic/Products/Singles/Kamigawa-Neon-Dynasty/Ancestral-Katana
    target_url = "https://www.cardmarket.com"
    target_list_filepath = "NEO_cardlist.txt"
    set_name = "Kamigawa-Neon-Dynasty"
    debug = True

    scraper = Scraper(target_url, set_name, target_list_filepath, debug)
    mtgData = scraper.run()
    